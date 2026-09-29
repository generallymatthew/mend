# joint-session-audio (real audio delay buffer, standalone proof)

Proves the one piece `../joint-session-architecture.md:82` calls the "core
unbuilt piece" of the whole joint-session design: a real audio delay buffer,
gated per rolling STT chunk by the same real classifier
(`../classifier/inference.py`'s `ConflictClassifier`, `mend-conflict-classifier-v3`
checkpoint) that `../joint-session-app/server.py` already runs against typed
text. Two employees connect over LiveKit; neither can ever subscribe to the
other's raw microphone track -- only a server-side "bridge" agent can, and it
republishes each employee's audio to the other side only after it clears the
delay buffer and the classifier both.

**What this is not**: a rewrite of `../joint-session-app/`, which keeps
working unmodified. This does not yet integrate with that app's facilitator
LLM, turn-taking, or `<mend_signal>` state machine -- it proves the audio
mechanism in isolation first. See the root plan for the follow-up milestone
that wires real STT transcripts into that existing conversational logic.

**What this is not, part 2**: a validated safety system. Same caveats as
`../classifier/README.md`'s "Before this goes anywhere near a real session"
section -- small/synthetic training data, unvalidated 0.9 threshold, no bias
audit. Treat a cut firing (or not) here as this checkpoint's current
behavior, not a guarantee.

## Components

- `delay_buffer.py` -- the buffer + classifier-gate decision itself. No
  LiveKit dependency, unit-testable on its own (see `tests/`).
- `stt.py` -- wraps `RealtimeSTT` (faster-whisper-based, VAD built in) to
  turn raw PCM frames into finalized (audio, text) segments.
- `video_parity.py` -- the symmetric video opt-in gate (see "Video opt-in"
  below). No LiveKit dependency either, unit-testable on its own.
- `agent.py` -- the LiveKit Agents worker that's the actual "bridge"
  participant: subscribes to each employee's mic, wires STT -> delay buffer,
  republishes gated audio to the other employee only; also enforces video
  parity (see below).
- `server.py` -- mints LiveKit tokens (including each employee's video
  consent) and serves the mic/camera-capture debug page. Does not touch
  audio or video itself.
- `static/index.html` -- a bare debug harness (not real product UI): captures
  a video-consent choice, connects, publishes mic (+ camera if consented),
  plays back whatever the bridge grants.

## Video opt-in (symmetric camera parity)

Each employee chooses, before connecting, to show real camera video or stay
on voice + a neutral avatar. If either party never consented, or their
camera goes live and then drops mid-session, **both** employees fall back to
voice + avatar, permanently for that session -- nobody keeps a one-sided
view of the room. `video_parity.py`'s `VideoParityGate` is the pure decision
logic (one-way latch, no re-enable); `agent.py` wires real LiveKit events
into it and does the actual enforcement: it revokes both directions' video
subscription via the LiveKit RoomService API the moment parity breaks (not
just a UI signal -- the SFU actually stops forwarding that video), then
broadcasts a `{"type": "video_mode", "mode": ...}` data message so both
clients update their tiles and show a toast
("Session switched to Voice & Avatar mode.").

Video is not routed through the bridge the way audio is -- there's no
content-moderation requirement for it (the hard-cut classifier stays
audio/text-only), so employees subscribe to each other's video track
directly once parity allows it; the agent only observes track-lifecycle
events and revokes subscriptions, it never decodes video itself.

## Setup

```bash
cd joint-session-audio
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes torch + transformers for the classifier -- same sizable download as ../joint-session-app
cp .env.example .env
brew install livekit   # gives you the livekit-server binary
```

## Run (three processes, in order)

```bash
livekit-server --dev                 # terminal 1 -- local dev-mode SFU, ws://localhost:7880
python agent.py dev                  # terminal 2 -- the bridge worker
uvicorn server:app --reload --port 8424   # terminal 3
```

Open both role links (two tabs, or two browser profiles so mic permission
prompts don't collide):

```
http://localhost:8424/?code=test1&role=a
http://localhost:8424/?code=test1&role=b
```

Speak normally on one side -- after roughly `BUFFER_SECONDS` (default 1.5s,
`.env`-overridable), the other side should hear it. Say something that trips
the classifier (e.g. a scripted violent threat) and the other side should
hear nothing for that segment; the agent's own terminal logs the cut and its
scores.

## Testing the gate logic without any of the above

`tests/test_delay_buffer.py` and `tests/test_video_parity.py` exercise the
buffer/classifier gate and the video-parity gate directly, no
LiveKit/STT/audio/camera hardware needed:

```bash
python tests/test_delay_buffer.py
python tests/test_video_parity.py
```

`test_delay_buffer.py` submits one ordinary line and one scripted
floor-tripping line as pre-transcribed text (this test's job is the
buffer+classifier timing and gating logic, not proving STT accuracy) and
asserts the ordinary one releases after `buffer_seconds` while the tripping
one never does. It also prints the measured classify latency, to
sanity-check the `buffer_seconds` default against this machine's real
numbers instead of the unvalidated ~500-800ms guess in
`../joint-session-architecture.md:68`.

`test_video_parity.py` proves: both-consent-both-live reaches
`video_active`; a never-consenting participant keeps the room at
`avatar_audio_only` forever; a drop after both were live falls back exactly
once; the dropped side's camera coming back live does not revert the mode
(the one-way latch); a disconnect triggers the same fallback as an explicit
camera-off.

## Known gaps (see the plan / architecture doc)

- **Actually exercised against a live `livekit-server --dev` in this
  environment** (not just structurally checked): installed `livekit-server`
  1.13.7 via `brew install livekit` and `RealtimeSTT`/`PyAudio` via
  `brew install portaudio` first, ran `agent.py dev` + `server.py`, and drove
  two real browser tabs through the consent flow and `room.connect()`.
  Confirmed on the wire: token minting including the `video_consent`
  attribute (decoded a minted JWT), a real room join
  (`connected to Livekit Server ... room: joint-audio-livetest ...
  participant: employee_a`), and the agent worker itself joining as a real
  participant (`agent-AJ_...` in the LiveKit server's own log) with no
  errors from any of `agent.py`'s LiveKit/rtc calls. `set_track_subscription_
  permissions`'s real keyword is `allow_all_participants`, not the
  `all_participants_allowed` an earlier draft guessed -- caught and fixed
  from this live run, not by inspection.
- **A real bug this live run surfaced and fixed**: the agent's first attempt
  to join a room failed three times and gave up
  (`RuntimeError: no process became available after 3 attempts`). Cause:
  LiveKit Agents runs each job in a subprocess with a default 10s
  `initialize_process_timeout`, and loading the classifier (torch +
  transformers + the checkpoint) inside `entrypoint()` blew that timeout on
  every attempt. Fixed by moving the classifier load into a `prewarm_fnc`
  (runs once per worker process, before any job is assigned, stashed in
  `proc.userdata`) and raising `initialize_process_timeout` to 60s as
  headroom. Re-ran live after the fix: process init took 23.76s and
  succeeded. Also switched from constructing our own `api.LiveKitAPI(...)`
  to the framework-provided `ctx.api` (shares the job's own HTTP session
  lifecycle -- found via reading `JobContext.api`'s source), which also
  resolves what would otherwise have been a leaked, never-closed client.
- **Still not exercised live**: this sandboxed environment's browser has no
  camera/mic hardware (`getUserMedia` requests are blocked), so the actual
  video-parity enforcement path -- a real `track_published` video event,
  `video_gate` reaching `video_active`, and `update_subscriptions` actually
  revoking a live video subscription -- has not been observed end-to-end.
  The pure decision logic is proven deterministically instead
  (`tests/test_video_parity.py`). If you have a real camera, this is the
  one thing actually worth manually testing next.
- Per-segment delay/classify is independent and concurrent; nothing
  sequences overlapping segments if one classifies slower than another
  started after it. Fine for proving the gate, not for production ordering
  guarantees.
- The video-parity `on_mode_changed` handler's `LiveKitAPI` client
  (`agent.py`) is never explicitly closed -- fine for one job's lifetime in
  this prototype, not for a long-running deployment.
- Not wired into `run_all.sh`/`Caddyfile` port 8424 entry's `livekit-server`
  process management -- `run_all.sh` starts/stops it same as Caddy, but you
  still need `brew install livekit` done once yourself first.
- No re-enable-after-drop flow, and no video content moderation -- both
  deliberately out of scope, see the plan's "Scope boundaries".
