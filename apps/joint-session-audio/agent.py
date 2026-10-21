"""
LiveKit Agents worker: the server-side "bridge" participant from
../joint-session-architecture.md. Joins every joint-session-audio room,
subscribes to each employee's raw mic track, and republishes a
buffer_seconds-delayed, classifier-gated copy to the *other* employee only.
Employee A and B never auto-subscribe to each other's raw track -- only this
bridge does -- so the only audio either of them can ever receive from the
other side is what this agent chooses to release. That per-participant
publish/subscribe control is exactly what ../joint-session-architecture.md
calls out as the reason this can't sit on a vendor avatar API alone.

This connects the STT leg (stt.py) and the delay/classify leg
(delay_buffer.py) that are each independently testable on their own -- see
tests/test_delay_buffer.py for the deterministic proof of the gate itself,
which does not require a running LiveKit server.

NOTE: LiveKit Agents' exact API (JobContext, AutoSubscribe, track
subscription-permission calls) is version-sensitive. Method/kwarg names
below have been checked against the installed livekit-agents/livekit-rtc/
livekit-api (1.x) in this environment -- e.g. set_track_subscription_
permissions' real keyword is allow_all_participants, not the
all_participants_allowed an earlier draft guessed. What's NOT verified is
behavior against a live, running livekit-server with real connected
participants (no camera/mic hardware in this environment) -- see
README.md's "Known gaps" for exactly what that leaves unproven.

Run (after `livekit-server --dev` is already running -- see README.md):
    python agent.py dev
"""
import asyncio
import json
import logging
import multiprocessing
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Forces a genuinely fresh interpreter (exec, not a memory-copying fork) for
# RealtimeSTT's transcription-worker subprocess (imported below, transitively
# via stt.py). Kept as real, independent hardening even though it turned out
# NOT to be the fix for the segfault below -- see KMP_DUPLICATE_LIB_OK.
if multiprocessing.get_start_method(allow_none=True) != "spawn":
    multiprocessing.set_start_method("spawn", force=True)

# The actual fix for a SIGSEGV in __kmp_fork_barrier that kept killing the
# worker process partway through STT init, found live even after the spawn
# change above made no difference: torch and ctranslate2 each bundle their
# OWN separate copy of Intel's OpenMP runtime (.venv/.../torch/lib/libiomp5.
# dylib vs .venv/.../ctranslate2/.dylibs/libiomp5.dylib) -- classifier (torch)
# and STT (ctranslate2, inside RealtimeSTT) both load in this same process
# tree, so both copies end up loaded together, a documented crash trigger for
# Intel's OpenMP runtime. KMP_DUPLICATE_LIB_OK alone turned out NOT to be
# enough -- confirmed live, it only silences the runtime's own duplicate-load
# *detection* (which would otherwise abort cleanly with "OMP: Error #15"), it
# does not make running two copies' thread teams concurrently actually safe,
# and the crash still happened with only this set. Capping both to a single
# thread avoids the actual unsafe code path (the two-copies' barrier/fork
# logic that was segfaulting in __kmp_fork_barrier) rather than just hiding
# its warning -- confirmed fixed via a standalone repro (classifier load
# followed by STT init, single and twice back-to-back) before trusting this
# against a real room again.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import httpx
from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli

from breakout_gate import BreakoutGate, SessionState
from delay_buffer import DEFAULT_BUFFER_SECONDS, DEFAULT_CUT_THRESHOLD, DelayBuffer, load_default_classifier
from prosody import SpeakerBaseline, analyze_segment
from stt import SAMPLE_RATE, StreamingSTT
from video_parity import RoomVideoMode, VideoParityGate

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("mend.joint_session_audio.agent")

BUFFER_SECONDS = float(os.environ.get("BUFFER_SECONDS", DEFAULT_BUFFER_SECONDS))
CUT_THRESHOLD = float(os.environ.get("CLASSIFIER_CUT_THRESHOLD", DEFAULT_CUT_THRESHOLD))

# Real transport for prosody.py's flags -- see ../suture/server.py's
# POST /api/room/{code}/prosody-signal and README.md's "Prosody / tone
# signal" section for the full scope line. The two apps are still two
# independently-run prototypes with no shared session-discovery layer, so
# this only does anything useful when the operator has started a
# suture session under the SAME code as this LiveKit room --
# otherwise it's a harmless best-effort POST that either 404s (app not
# running) or lands in a session nobody's connected to yet.
JOINT_SESSION_APP_URL = os.environ.get("JOINT_SESSION_APP_URL", "http://localhost:8421")
_prosody_http = httpx.AsyncClient(timeout=3.0)

# should_cut() is a blocking torch call (classifier/inference.py has no async
# API) -- keep it off the event loop via a small dedicated pool, shared by
# both employees' DelayBuffers in a room.
CLASSIFIER_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="classifier")

# StreamingSTT construction spawns RealtimeSTT's own transcription-worker
# subprocess, which loads a ctranslate2/MKL whisper model -- found live, the
# hard way: with both employees' bridges initializing at once, their two
# subprocesses hit Intel's OpenMP runtime (libiomp5) concurrently during
# model load and segfaulted (SIGSEGV in __kmp_fork_call), taking the whole
# worker process down mid-session. Serializing the two loads through this
# lock avoids the concurrent-init race entirely; it costs a few extra
# seconds of startup staggering, not a real slowdown once both are warm.
STT_INIT_LOCK = asyncio.Lock()


def prewarm(proc: JobProcess):
    # Loading the classifier (torch + transformers + the checkpoint) takes
    # several real seconds -- found live, the hard way: LiveKit Agents runs
    # each job in a subprocess with a default 10s initialize_process_timeout
    # (see WorkerOptions below), and doing this load inside entrypoint()
    # instead of here blew that timeout on every attempt, so the agent
    # never actually joined the room for a real job (confirmed against a
    # live livekit-server -- "no process became available after 3
    # attempts"). prewarm_fnc runs once when a worker process starts, before
    # any job is assigned, so this cost is paid before a room needs the
    # agent, not during it.
    proc.userdata["classifier"] = load_default_classifier(cut_threshold=CUT_THRESHOLD)


class ParticipantBridge:
    """Wires one employee's inbound audio -> STT -> DelayBuffer -> an
    outbound track this bridge publishes for the *other* employee to hear."""

    def __init__(self, room: rtc.Room, participant_identity: str, other_identity: str, classifier):
        self.room = room
        self.participant_identity = participant_identity
        self.other_identity = other_identity
        # server.py's token() mints room_name = f"joint-audio-{code}" -- the
        # inverse, needed to address ../suture/server.py's
        # identically-coded session (see JOINT_SESSION_APP_URL above).
        self.code = room.name.removeprefix("joint-audio-")
        self._out_source = rtc.AudioSource(SAMPLE_RATE, 1)
        self._out_track = rtc.LocalAudioTrack.create_audio_track(
            f"bridge-to-{other_identity}", self._out_source
        )
        self.buffer = DelayBuffer(
            participant_id=participant_identity,
            classifier=classifier,
            buffer_seconds=BUFFER_SECONDS,
            executor=CLASSIFIER_EXECUTOR,
            on_release=self._publish_release,
            on_cut=lambda text, scores, latency: logger.warning(
                "hard cut: %s -> %s withheld (latency=%.3fs)",
                participant_identity, other_identity, latency,
            ),
        )
        # Deliberately NOT constructed here -- see construct_stt() below. Frames
        # that arrive before it's ready are buffered here (see push_frame),
        # not dropped -- STT init takes 15-35s, and the previous behavior of
        # only starting to read the track's AudioStream *after* init
        # finished silently discarded a live speaker's first 15-35s of
        # speech every single time. Found live: this was why real
        # microphone testing never once produced a prosody flag all
        # session, independent of and on top of every crash/dispatch bug
        # fixed earlier.
        self.stt: StreamingSTT | None = None
        self._recorder: StreamingSTT | None = None
        self._pending_frames: list[bytes] = []
        # Set while the room is paused for a private side conversation --
        # see BreakoutGate. STT/DelayBuffer keep running underneath (so
        # nothing is lost/desynced when the pause ends), only the release
        # onto the other employee's bridge track is withheld.
        self.paused = False
        # Auxiliary tension signal (prosody.py) -- pitch/energy/pace judged
        # against THIS participant's own running baseline, logged for a
        # human or a future facilitator prompt to weigh alongside the
        # transcript. Deliberately not read by DelayBuffer/the classifier
        # above: it doesn't influence the real-time cut decision, only
        # observability -- see prosody.py's module docstring for why.
        self.prosody_baseline = SpeakerBaseline()
        # _on_segment/_log_prosody fire from RealtimeSTT's own recording-
        # worker thread (StreamingSTT's on_recording_stop callback), not the
        # event loop thread -- captured here while __init__ is still
        # guaranteed to run on the loop thread (see construct_stt's own
        # comment on why the rest of __init__ can't move off it).
        self._loop = asyncio.get_event_loop()

    async def publish(self):
        # Scope this track so only `other_identity` may subscribe to it --
        # the whole point of the bridge is that the *raw* mic track from
        # `participant_identity` is never itself subscribable by the other
        # employee. See module docstring re: API version sensitivity.
        # (allow_all_participants is this installed version's real kwarg
        # name -- verified against livekit-agents 1.x's rtc.LocalParticipant,
        # not the all_participants_allowed guessed in an earlier draft.
        # set_track_subscription_permissions itself is synchronous in this
        # installed version -- confirmed via source, `-> None`, not a
        # coroutine -- awaiting it raised "NoneType can't be used in
        # 'await' expression" every time this ran, silently, since it's
        # called from a fire-and-forget asyncio.create_task with no one
        # ever awaiting the task or checking its exception. Found live
        # while testing the new breakout gate below, which copied this
        # same call.)
        options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        publication = await self.room.local_participant.publish_track(self._out_track, options)
        self.room.local_participant.set_track_subscription_permissions(
            allow_all_participants=False,
            participant_permissions=[
                rtc.ParticipantTrackPermission(
                    participant_identity=self.other_identity,
                    allow_all=False,
                    allowed_track_sids=[publication.sid],
                )
            ],
        )

    def construct_stt(self):
        # Split out of __init__ so it can run in a worker thread (see
        # on_track_subscribed) -- constructing StreamingSTT loads the
        # faster-whisper model synchronously, ~30-60s on first run, which
        # must never happen on the event loop (see that call site for why).
        # The rest of __init__ stays on the loop thread deliberately: several
        # of those calls (e.g. rtc.AudioSource) implicitly grab the running
        # event loop via asyncio.get_event_loop() and raise if there isn't
        # one, which a plain worker thread doesn't have.
        #
        # Deliberately just the model load -- see drain_pending_stt below for
        # why the backlog replay is a separate step, run outside the caller's
        # STT_INIT_LOCK. self.stt stays None until that replay finishes (see
        # push_frame), same buffering behavior as before this split.
        self._recorder = StreamingSTT(self.participant_identity, self._on_segment)

    def drain_pending_stt(self):
        # Runs after construct_stt, deliberately NOT under STT_INIT_LOCK --
        # found live: with both employees' bridges sharing that lock across
        # the whole of what used to be init_stt(), the second participant's
        # pending-frame queue kept growing for the ENTIRE duration of the
        # first's real-time-paced replay below (not just their model load,
        # the actual race this lock exists for), and its own replay then
        # took that same duration again -- 82s becoming a 230s backlog in a
        # two-participant test in this environment, not the "few extra
        # seconds of startup staggering" this lock was meant to cost. Only
        # StreamingSTT's own construction above needs serializing (the two
        # employees' faster-whisper model loads racing is what segfaults,
        # see STT_INIT_LOCK) -- this replay loop touches only this
        # participant's own recorder and pending-frame list, safe to run
        # concurrently with the other participant's construct_stt/replay.
        pending, self._pending_frames = self._pending_frames, []
        logger.info(
            "init_stt draining participant=%s pending_frames=%d pending_bytes=%d",
            self.participant_identity, len(pending), sum(len(c) for c in pending),
        )
        # Replaying the whole backlog in a tight loop (no pacing) fed
        # RealtimeSTT's VAD a multi-second block of audio all at once --
        # confirmed live to reach the recorder (peak_amplitude=32767, real
        # signal, not silence) but never once produced a finalized segment.
        # RealtimeSTT's voice-activity segmentation tracks silence by
        # elapsed wall-clock time between push_audio calls, same as it
        # would from a live mic feed -- a call to push_audio does not by
        # itself scream "this many ms of audio"; it is the CALL that
        # implicitly is timed. Replaying at roughly the original real-time
        # cadence (this runs in a worker thread, so a plain blocking sleep
        # here costs nothing on the event loop) lets it see the backlog the
        # same way it would have lived through it.
        for chunk in pending:
            self._recorder.push_audio(chunk)
            time.sleep(len(chunk) / 2 / SAMPLE_RATE)
        # Only now does push_frame start feeding the recorder directly --
        # any frames that arrived live during this replay were appended to
        # self._pending_frames same as before (push_frame still checks
        # self.stt is None), so this drains them too instead of losing them.
        # A second drain pass keeps the same real-time cadence for whatever
        # arrived while this one was running.
        more, self._pending_frames = self._pending_frames, []
        for chunk in more:
            self._recorder.push_audio(chunk)
            time.sleep(len(chunk) / 2 / SAMPLE_RATE)
        self.stt = self._recorder

    def push_frame(self, frame: rtc.AudioFrame):
        data = bytes(frame.data)
        if self.stt is None:
            self._pending_frames.append(data)
            return
        self.stt.push_audio(data)

    def _on_segment(self, audio_bytes: bytes, text: str):
        # Found live: this fires from RealtimeSTT's own recording-worker
        # thread (stt.py's on_recording_stop callback), not the event loop
        # thread -- plain asyncio.create_task() raised "RuntimeError: no
        # running event loop" every time, and because RealtimeSTT's worker
        # loop has no outer try/except around invoking this callback, that
        # exception silently killed the ENTIRE recording-worker thread.
        # Confirmed live: a participant's very first finalized segment was
        # also its last -- STT looked "stuck" afterward (still fed audio,
        # never produced another segment) because the thread that would
        # have produced one was already dead. run_coroutine_threadsafe is
        # the correct cross-thread scheduling call here; self._loop was
        # captured in __init__ while still on the loop thread.
        self._log_prosody(audio_bytes, text)
        asyncio.run_coroutine_threadsafe(self.buffer.submit(audio_bytes, text), self._loop)

    def _log_prosody(self, audio_bytes: bytes, text: str):
        # Plain numpy on a handful of ~30ms frames -- cheap enough (unlike
        # the classifier's BERT call, which does need the executor below)
        # to run inline here without blocking the event loop.
        features = analyze_segment(audio_bytes, text)
        flags = self.prosody_baseline.flags(features)
        logger.info("prosody segment participant=%s text=%r flags=%s", self.participant_identity, text, flags)
        if flags:
            logger.info(
                "prosody participant=%s flags=%s pitch=%s energy=%.3f pace=%s text=%r",
                self.participant_identity, flags,
                f"{features.pitch_mean_hz:.0f}Hz" if features.pitch_mean_hz else "n/a",
                features.energy_mean,
                f"{features.speaking_rate_wps:.1f}wps" if features.speaking_rate_wps else "n/a",
                text,
            )
            # Same off-loop-thread constraint as _on_segment above.
            asyncio.run_coroutine_threadsafe(self._send_prosody_signal(flags), self._loop)
        self.prosody_baseline.update(features)

    async def _send_prosody_signal(self, flags):
        # Best-effort only -- see JOINT_SESSION_APP_URL's module-level
        # comment for why a failure here (suture not running,
        # or running under a different code) is expected, not exceptional,
        # and must never affect the audio bridge itself.
        try:
            resp = await _prosody_http.post(
                f"{JOINT_SESSION_APP_URL}/api/room/{self.code}/prosody-signal",
                json={"speaker": self.participant_identity, "flags": flags},
            )
            resp.raise_for_status()
        except Exception as e:
            logger.info("couldn't deliver prosody signal to suture (%s): %s", JOINT_SESSION_APP_URL, e)

    def _publish_release(self, audio_bytes: bytes):
        if self.paused:
            return
        frame = rtc.AudioFrame(
            data=audio_bytes,
            sample_rate=SAMPLE_RATE,
            num_channels=1,
            samples_per_channel=len(audio_bytes) // 2,
        )
        asyncio.create_task(self._out_source.capture_frame(frame))


def other_of(identity: str) -> str | None:
    # Room convention: exactly two employee identities, "employee_a" and
    # "employee_b" -- matches ../suture/server.py's ROLE_SLUGS.
    if identity == "employee_a":
        return "employee_b"
    if identity == "employee_b":
        return "employee_a"
    return None


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_NONE)
    room = ctx.room
    classifier = ctx.proc.userdata["classifier"]
    bridges: dict[str, ParticipantBridge] = {}

    # Video parity: video is NOT bridged through this agent the way audio
    # is -- there's no content-moderation need for it (see video_parity.py
    # and README.md's Scope boundaries), so employees subscribe to each
    # other's video track directly. This agent only needs to (a) know each
    # track's SID (from the publish event, without itself subscribing --
    # keeps the SUBSCRIBE_NONE posture above) and (b) actually revoke that
    # subscription room-wide the moment parity breaks, via the RoomService
    # admin API -- a different surface than set_track_subscription_permissions
    # above, which only lets a participant restrict who subscribes to
    # tracks *it* published itself, not tracks the employees publish.
    # ctx.api is the framework's own LiveKitAPI, sharing its HTTP session
    # lifecycle with the job -- confirmed via source
    # (JobContext.api: credentials sourced from the same LIVEKIT_URL/
    # LIVEKIT_API_KEY/LIVEKIT_API_SECRET env vars WorkerOptions already
    # exports). Using this instead of constructing our own client also
    # resolves what would otherwise be a leaked, never-closed client.
    lkapi = ctx.api
    video_track_sids: dict[str, str] = {}

    def on_video_mode_changed(old_mode: RoomVideoMode, new_mode: RoomVideoMode):
        logger.warning("video parity: %s -> %s", old_mode, new_mode)
        asyncio.create_task(_apply_video_mode(new_mode))

    async def _apply_video_mode(new_mode: RoomVideoMode):
        if new_mode == "avatar_audio_only":
            # Mutual teardown: revoke both directions, not just the side
            # that dropped -- nobody keeps a one-sided view of the room.
            for viewer, other in (
                ("employee_a", "employee_b"),
                ("employee_b", "employee_a"),
            ):
                sid = video_track_sids.get(other)
                if not sid:
                    continue
                try:
                    await lkapi.room.update_subscriptions(
                        api.UpdateSubscriptionsRequest(
                            room=room.name, identity=viewer, track_sids=[sid], subscribe=False,
                        )
                    )
                except Exception:
                    logger.exception("failed to revoke %s's subscription to %s's video", viewer, other)
        try:
            room.local_participant.publish_data(
                json.dumps({"type": "video_mode", "mode": new_mode}).encode(),
                reliable=True,
            )
        except Exception:
            logger.exception("failed to broadcast video_mode=%s", new_mode)

    video_gate = VideoParityGate(("employee_a", "employee_b"), on_mode_changed=on_video_mode_changed)

    # Private side-conversation (breakout) isolation -- see breakout_gate.py.
    # checkin_pub holds the one active private track's publication SID
    # between enter_checkin and resume; there's at most one at a time
    # (BreakoutGate rejects a second target while already paused).
    checkin_pub: dict[str, str] = {}

    def on_breakout_state_changed(old_state: SessionState, new_state: SessionState, target: str | None):
        logger.warning("breakout: %s -> %s (target=%s)", old_state, new_state, target)
        asyncio.create_task(_apply_breakout_state(new_state, target))

    async def _apply_breakout_state(new_state: SessionState, target: str | None):
        if new_state == "paused_checkin" and target:
            other = breakout_gate.other_identity
            for identity in (target, other):
                bridge = bridges.get(identity)
                if bridge:
                    bridge.paused = True
            # A private, subscription-restricted track for `target` alone --
            # inert for now (no facilitator TTS wired in, deliberately out
            # of scope, see breakout_gate.py's module docstring), this just
            # proves the isolation mechanism itself: the same
            # set_track_subscription_permissions call ParticipantBridge.publish
            # already uses for the human-to-human bridge tracks, applied here
            # to reserve a private channel only `target` can subscribe to.
            source = rtc.AudioSource(SAMPLE_RATE, 1)
            track = rtc.LocalAudioTrack.create_audio_track(f"facilitator-checkin-{target}", source)
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            try:
                publication = await room.local_participant.publish_track(track, options)
                room.local_participant.set_track_subscription_permissions(
                    allow_all_participants=False,
                    participant_permissions=[
                        rtc.ParticipantTrackPermission(
                            participant_identity=target,
                            allow_all=False,
                            allowed_track_sids=[publication.sid],
                        )
                    ],
                )
                checkin_pub["sid"] = publication.sid
            except Exception:
                logger.exception("failed to open private check-in track for %s", target)
            try:
                room.local_participant.publish_data(
                    json.dumps({"type": "session_paused", "checkin_target": target}).encode(),
                    reliable=True,
                )
            except Exception:
                logger.exception("failed to broadcast session_paused")
        elif new_state == "active":
            for identity in ("employee_a", "employee_b"):
                bridge = bridges.get(identity)
                if bridge:
                    bridge.paused = False
            sid = checkin_pub.pop("sid", None)
            if sid:
                try:
                    await room.local_participant.unpublish_track(sid)
                except Exception:
                    logger.exception("failed to close private check-in track")
            try:
                room.local_participant.publish_data(
                    json.dumps({"type": "session_resumed"}).encode(),
                    reliable=True,
                )
            except Exception:
                logger.exception("failed to broadcast session_resumed")

    breakout_gate = BreakoutGate(("employee_a", "employee_b"), on_state_changed=on_breakout_state_changed)

    @room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        # Control channel for the breakout gate -- see server.py's
        # POST /api/room/{code}/checkin|resume, the manual/test-only trigger
        # documented there. A real facilitator-LLM integration would send
        # these same two message shapes from wherever it runs.
        try:
            msg = json.loads(data.data.decode())
        except Exception:
            return
        if msg.get("type") == "breakout_checkin":
            target = msg.get("target")
            if target:
                breakout_gate.enter_checkin(target)
        elif msg.get("type") == "breakout_resume":
            breakout_gate.resume()

    @room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication, participant: rtc.RemoteParticipant):
        logger.info("track_subscribed kind=%s participant=%s", track.kind, participant.identity)
        if track.kind != rtc.TrackKind.KIND_AUDIO:
            return
        other = other_of(participant.identity)
        if other is None:
            logger.warning("unexpected participant identity: %s", participant.identity)
            return
        async def init_stt_in_background(bridge: "ParticipantBridge"):
            # ParticipantBridge.__init__ itself must stay on the loop
            # thread -- rtc.AudioSource grabs the running event loop
            # internally and raises in a plain worker thread. Only
            # construct_stt() (the faster-whisper model load, ~30-60s on
            # first run: download + the ctranslate2 float32 conversion)
            # goes through the executor, so that cost can never block
            # the loop and trip livekit-agents' own unresponsive-process
            # watchdog again -- found live: it killed the job mid-session
            # the first time this ran on the loop directly. Run as its own
            # background task (not awaited inline before reading frames
            # below) -- see bridge_and_read_frames for why.
            #
            # STT_INIT_LOCK wraps ONLY construct_stt (the model load that
            # actually segfaults when two employees' loads race -- see the
            # lock's own definition). drain_pending_stt runs after the lock
            # is released -- found live: holding the lock across the whole
            # of what used to be one init_stt() call let the second
            # participant's pending-frame queue keep growing for the
            # ENTIRE duration of the first's real-time-paced replay, not
            # just their model load, compounding into minutes of lag
            # instead of the "few extra seconds" this lock was meant to
            # cost. See drain_pending_stt's own docstring-comment.
            loop = asyncio.get_event_loop()
            async with STT_INIT_LOCK:
                await loop.run_in_executor(None, bridge.construct_stt)
            await loop.run_in_executor(None, bridge.drain_pending_stt)

        async def bridge_and_read_frames():
            bridge = bridges.get(participant.identity)
            if bridge is None:
                bridge = ParticipantBridge(room, participant.identity, other, classifier)
                bridges[participant.identity] = bridge
                await bridge.publish()
                asyncio.create_task(init_stt_in_background(bridge))
            # sample_rate=SAMPLE_RATE forces LiveKit's own resampler to
            # convert down from the track's native 48kHz to the 16kHz this
            # whole pipeline (StreamingSTT, prosody.py) assumes -- without
            # this the default was 48kHz, fed straight into RealtimeSTT as
            # if it were 16kHz raw PCM, corrupting every frame. And this
            # stream is created and read starting now, NOT after awaiting
            # init_stt above (previously it was, which meant the 15-35s STT
            # load silently ate a live speaker's first utterances every
            # time -- push_frame buffers frames itself until self.stt
            # exists, see ParticipantBridge.push_frame/init_stt).
            stream = rtc.AudioStream(track, sample_rate=SAMPLE_RATE, num_channels=1)
            async for event in stream:
                bridge.push_frame(event.frame)

        asyncio.create_task(bridge_and_read_frames())

    @room.on("track_published")
    def on_track_published(publication, participant: rtc.RemoteParticipant):
        logger.info("track_published kind=%s participant=%s", publication.kind, participant.identity)
        if other_of(participant.identity) is None:
            return
        if publication.kind == rtc.TrackKind.KIND_AUDIO:
            # Client publishes its mic *after* room.connect() resolves (see
            # index.html), i.e. after this agent's participant_connected
            # handler already ran and found no audio publications to seed --
            # this is the only path that ever subscribes to it. Without this,
            # track_subscribed never fires for audio and the whole bridge
            # (STT, delay buffer, prosody) silently never runs.
            publication.set_subscribed(True)
            return
        if publication.kind != rtc.TrackKind.KIND_VIDEO:
            return
        video_track_sids[participant.identity] = publication.sid
        video_gate.set_camera_live(participant.identity, True)

    @room.on("track_unpublished")
    def on_track_unpublished(publication, participant: rtc.RemoteParticipant):
        if publication.kind != rtc.TrackKind.KIND_VIDEO:
            return
        if other_of(participant.identity) is None:
            return
        video_track_sids.pop(participant.identity, None)
        video_gate.set_camera_live(participant.identity, False)

    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(
            "participant_connected identity=%s existing_publications=%s",
            participant.identity, [p.kind for p in participant.track_publications.values()],
        )
        # Bridge always subscribes to the raw mic track -- the two employees
        # never do (see entrypoint's SUBSCRIBE_NONE connect above, which
        # applies to this agent's own auto-subscribe default; each employee
        # client must itself connect with autoSubscribe=false and rely on
        # set_track_subscription_permissions above for what it's allowed to
        # hear instead).
        for pub in participant.track_publications.values():
            if pub.kind == rtc.TrackKind.KIND_AUDIO:
                pub.set_subscribed(True)

        if other_of(participant.identity) is not None:
            consented = participant.attributes.get("video_consent") == "true"
            video_gate.set_consent(participant.identity, consented)
            # A video track already published before this connected-handler
            # ran (rare, but possible on reconnect) won't fire its own
            # "track_published" event -- seed it here too so it's not missed.
            for pub in participant.track_publications.values():
                if pub.kind == rtc.TrackKind.KIND_VIDEO:
                    video_track_sids[participant.identity] = pub.sid
                    video_gate.set_camera_live(participant.identity, True)

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        if other_of(participant.identity) is None:
            return
        video_track_sids.pop(participant.identity, None)
        video_gate.set_camera_live(participant.identity, False)

    # room.on("participant_connected") only fires for participants who join
    # AFTER this point -- it does not replay for whoever connected while this
    # job was still spawning/loading its model weights (real, and not rare:
    # cold worker startup measured ~33s against a live server, easily longer
    # than both employees take to open their links). Without this, a normal
    # "both employees already in the room" job start never subscribes to
    # either mic at all -- the whole bridge (STT, delay buffer, prosody)
    # silently never runs, found live testing against real audio.
    for participant in room.remote_participants.values():
        on_participant_connected(participant)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        # Default is 10s -- confirmed too short for this app's cold classifier
        # load against a live worker; see prewarm's docstring above. Prewarm
        # already moves that cost out of the per-job path, this is headroom
        # for the process-spawn itself, not a substitute for prewarm.
        initialize_process_timeout=60.0,
        # `dev` mode's own default is 0 idle processes -- it only spins one
        # up once a job actually arrives, so the very first job on a fresh
        # worker always cold-starts. Found live: that cold start (~30s on
        # this machine) lost the race against livekit-server's own dispatch-
        # acceptance timeout, which logged "no servers available" and
        # silently dropped the room -- not a crash, just a job nobody ever
        # picked up. Forcing one warm process keeps that race from
        # happening at all, first job included.
        num_idle_processes=2,
    ))
