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
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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

# should_cut() is a blocking torch call (classifier/inference.py has no async
# API) -- keep it off the event loop via a small dedicated pool, shared by
# both employees' DelayBuffers in a room.
CLASSIFIER_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="classifier")


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
        self.stt = StreamingSTT(participant_identity, self._on_segment)
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

    def push_frame(self, frame: rtc.AudioFrame):
        self.stt.push_audio(bytes(frame.data))

    def _on_segment(self, audio_bytes: bytes, text: str):
        self._log_prosody(audio_bytes, text)
        asyncio.create_task(self.buffer.submit(audio_bytes, text))

    def _log_prosody(self, audio_bytes: bytes, text: str):
        # Plain numpy on a handful of ~30ms frames -- cheap enough (unlike
        # the classifier's BERT call, which does need the executor below)
        # to run inline here without blocking the event loop.
        features = analyze_segment(audio_bytes, text)
        flags = self.prosody_baseline.flags(features)
        if flags:
            logger.info(
                "prosody participant=%s flags=%s pitch=%s energy=%.3f pace=%s text=%r",
                self.participant_identity, flags,
                f"{features.pitch_mean_hz:.0f}Hz" if features.pitch_mean_hz else "n/a",
                features.energy_mean,
                f"{features.speaking_rate_wps:.1f}wps" if features.speaking_rate_wps else "n/a",
                text,
            )
        self.prosody_baseline.update(features)

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
    # "employee_b" -- matches ../joint-session-app/server.py's ROLE_SLUGS.
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
        if track.kind != rtc.TrackKind.KIND_AUDIO:
            return
        other = other_of(participant.identity)
        if other is None:
            logger.warning("unexpected participant identity: %s", participant.identity)
            return
        bridge = bridges.setdefault(
            participant.identity,
            ParticipantBridge(room, participant.identity, other, classifier),
        )
        asyncio.create_task(bridge.publish())

        async def read_frames():
            stream = rtc.AudioStream(track)
            async for event in stream:
                bridge.push_frame(event.frame)

        asyncio.create_task(read_frames())

    @room.on("track_published")
    def on_track_published(publication, participant: rtc.RemoteParticipant):
        if publication.kind != rtc.TrackKind.KIND_VIDEO:
            return
        if other_of(participant.identity) is None:
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


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        # Default is 10s -- confirmed too short for this app's cold classifier
        # load against a live worker; see prewarm's docstring above. Prewarm
        # already moves that cost out of the per-job path, this is headroom
        # for the process-spawn itself, not a substitute for prewarm.
        initialize_process_timeout=60.0,
    ))
