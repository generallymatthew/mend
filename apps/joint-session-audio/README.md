# joint-session-audio (real audio delay buffer, standalone proof)

Proves the one piece `../joint-session-architecture.md:82` calls the "core
unbuilt piece" of the whole joint-session design: a real audio delay buffer,
gated per rolling STT chunk by the same real classifier
(`../classifier/inference.py`'s `ConflictClassifier`, `mend-conflict-classifier-v3`
checkpoint) that `../suture/server.py` already runs against typed
text. Two employees connect over LiveKit; neither can ever subscribe to the
other's raw microphone track -- only a server-side "bridge" agent can, and it
republishes each employee's audio to the other side only after it clears the
delay buffer and the classifier both.

**What this is not**: a rewrite of `../suture/`, which keeps
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
- `breakout_gate.py` -- the private side-conversation ("breakout") state
  gate (see "Private side conversation" below). No LiveKit dependency,
  unit-testable on its own -- same split as the other two.
- `prosody.py` -- pitch/energy/pace feature extraction and a per-speaker
  baseline (see "Prosody / tone signal" below). No LiveKit dependency,
  unit-testable on its own -- same split as the other three.
- `agent.py` -- the LiveKit Agents worker that's the actual "bridge"
  participant: subscribes to each employee's mic, wires STT -> delay buffer,
  republishes gated audio to the other employee only; also enforces video
  parity and breakout-room isolation (see below).
- `server.py` -- mints LiveKit tokens (including each employee's video
  consent), serves the mic/camera-capture debug page, and exposes the
  manual/test-only breakout-room trigger (`POST /api/room/{code}/checkin`
  and `.../resume`). Does not touch audio or video itself.
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

## Private side conversation (breakout room)

`../joint-session-architecture.md`'s "Not yet designed" list used to flag
"how the private breakout sub-room is implemented in LiveKit specifically
(room composition vs a second room with re-publish)" as unbuilt. It's
implemented now, as room composition: LiveKit's `move_participant`/
`forward_participant` APIs (a second-room approach) are Cloud/Private-Cloud
only -- confirmed against the installed SDK's own docstrings -- not usable
against the self-hosted `livekit-server --dev` this repo runs, so
`breakout_gate.py`'s `BreakoutGate` + `agent.py`'s wiring instead reuse the
same self-hosted-compatible primitives the video-parity code above already
proves work: `set_track_subscription_permissions` and a data-channel
broadcast.

When the room enters a check-in for one employee (`enter_checkin`): both
`ParticipantBridge`s pause their cross-publish (so neither employee hears
the other for the duration -- symmetric, not just one direction), the other
employee gets a content-free `{"type": "session_paused"}` data event, and a
private, subscription-restricted track (`facilitator-checkin-{identity}`)
opens for the target employee alone. `resume()` reverses all of it. This is
**transport only** -- the private track is inert, no facilitator voice
publishes into it, and nothing here decides *when* a check-in should
happen. Giving this bridge a real facilitator voice, driven live by
`../suture`'s existing text-only facilitator LLM (which already
implements this exact `paused_checkin`/`checkin_target` state machine, just
over WebSocket text, with zero relationship to this app today) is a
separate, larger integration, deliberately out of scope here.

Since this process never itself joins the room (`server.py` only mints
tokens), the only way to reach a running `agent.py` job is the room's own
data channel via the admin `RoomService.send_data` API --
`POST /api/room/{code}/checkin` (body `{"target": "employee_a"}`) and
`POST /api/room/{code}/resume` send the exact same two control-message
shapes a real facilitator-LLM integration would send from wherever it
runs. These two endpoints are that seam, not a decision-maker.

## Prosody / tone signal

A text transcript alone can't carry tone -- a flat, deadpan "sure, that's
fine" reads identically to a sincere one once it's been transcribed. Real
audio-only sarcasm/intent detection is a hard, unsolved research problem
though, and this product leans hard toward precision over false positives
everywhere it makes an automated call (`../classifier/README.md`'s Results
section shows what happens when an under-validated signal gets trusted too
early, even with good intentions behind it). So this starts narrow and
deliberately auxiliary, not as a sarcasm classifier: `prosody.py` extracts a
few interpretable acoustic features per STT-finalized segment --
pitch (F0), loudness/energy, speaking rate, pause ratio -- and
`SpeakerBaseline` compares each new segment against *that same speaker's*
own running average (Welford's streaming mean/variance) rather than a fixed
population threshold, since baseline pitch/pace varies enormously person to
person. When a segment is notably elevated or flattened relative to that
speaker's own baseline (z-score >= 1.5), `agent.py` logs a human-readable
flag line (`pitch_elevated`, `energy_elevated`, `pace_elevated`,
`pace_slowed`, `pitch_flattened`, `hesitant`) -- see `ParticipantBridge.
_log_prosody`.

**Deliberately not wired into the real-time cut decision.** `delay_buffer.py`
and `../classifier/inference.py` are unchanged -- flags never influence the
hard-cut gate, only the facilitator LLM (see below).

**Wired into `../suture`'s facilitator LLM, for real.** When
`_log_prosody` finds non-empty flags, `ParticipantBridge._send_prosody_signal`
POSTs them to that app's `POST /api/room/{code}/prosody-signal` (URL
configurable via `JOINT_SESSION_APP_URL`, default `http://localhost:8421`;
`self.code` is this room's code, recovered from `room.name`'s
`joint-audio-{code}` convention). Best-effort and non-blocking -- a failed
or timed-out POST (the other app isn't running, or running under a
different code) is logged and swallowed, never affects the audio bridge
itself. See that app's README for the receiving end (`Session.pending_prosody`,
consumed into the annotated transcript line the next time that speaker
actually sends a message) and for what this changes in practice: a live,
two-participant, real-server-code test found the facilitator moved from
raising a tension pattern in front of both employees (no signal) to pulling
the flagged employee aside for a private check-in (with the signal) on the
exact same words.

**What "wired in" doesn't mean here**: the two apps still have no shared
session-discovery layer (an operator starts both under the same code by
hand), and `suture` is still text-only -- this moves tone
*signal* between two independently-run prototypes, it doesn't merge them
into one voice-driven session. Real STT-transcript-replaces-typed-messages
integration, and facilitator TTS carrying replies back to both employees,
remain a separate, larger project, same scope as the breakout room's
facilitator-voice gap above.

Before this was wired for real, `../suture/poc_prosody_in_prompt.py`
tested whether the idea had real value at all, without any live
integration -- same finding, on hand-constructed annotations instead of the
real wire above. Kept as a cheaper, more controlled way to test new
scenarios than driving full WebSocket sessions -- see that app's README.

Pure feature extraction + baseline logic, no LiveKit dependency, fully
unit-tested with synthetic tones (see `tests/test_prosody.py`).

**Also validated against real synthesized speech** (macOS `say` -- genuine
formants/harmonics/prosody, not sine tones; still not a live human
recording, this sandboxed environment has no microphone -- see
`tests/validate_prosody_real_speech.py`, runnable standalone). Pitch, energy,
and speaking-rate tracking all behave correctly on real speech: pitch stays
stable (168-175Hz) across six different calm utterances from the same
voice, a genuinely loud+fast segment correctly fires `energy_elevated`/
`pace_elevated`, and a genuinely pitch-shifted segment correctly fires
`pitch_elevated` too.

**This real-speech run also caught a real bug, not just a data point**: an
earlier version of `pitch_flattened` compared a segment's *average* pitch
against the baseline average, which conflates "lower pitch" with "flatter,
less-varying pitch" -- two different things (a resigned, quieter tone vs. a
genuinely monotone/deadpan one). Fixed in `prosody.py`: `pitch_lowered`
(average pitch dropped) and `pitch_flattened` (this segment's own
pitch_std_hz -- how much pitch moves around *within* the segment -- dropped
relative to how much it usually does for this speaker) are now two separate
checks, both covered in `tests/test_prosody.py` with synthetic audio built
specifically to isolate one from the other.

**What real-speech validation could *not* confirm**: whether
`pitch_flattened` fires correctly on genuine human deadpan/sarcastic
delivery. macOS's TTS has no real "flat affect" mode -- slowing the rate
down on a short, punctuated, deliberately sarcastic-sounding line
("Sure. That's just great. No problem at all.") produced *more* pitch
variability than the calm baseline, not less, because each short sentence
gets its own falling terminal pitch contour from the TTS engine. That's an
honest limit of what TTS can validate, not evidence the flag itself is
wrong -- the controlled synthetic test proves the underlying logic
correctly detects reduced variability when it's actually present. Whether
it fires the way a human reviewer would expect on genuine sarcastic
delivery still needs real recorded human speech, which remains blocked on
this sandboxed environment having no microphone.

## Setup

```bash
cd joint-session-audio
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes torch + transformers for the classifier -- same sizable download as ../suture
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

`tests/test_delay_buffer.py`, `tests/test_video_parity.py`, and
`tests/test_breakout_gate.py` exercise the buffer/classifier gate, the
video-parity gate, and the breakout gate directly, no
LiveKit/STT/audio/camera hardware needed:

```bash
python tests/test_delay_buffer.py
python tests/test_video_parity.py
python tests/test_breakout_gate.py
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

`test_breakout_gate.py` proves: entering a check-in pauses the room for the
named target; resume returns to active and clears the target; an unknown
identity is rejected with no state change; a redundant enter/resume call is
a no-op (no double transition); switching the check-in target mid-pause is
rejected, the original target holds.

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
- **The breakout room, actually exercised against a live `livekit-server
  --dev`**: connected two fake employee participants (LiveKit's Python
  client, publishing silent audio -- no camera/mic hardware needed for this
  one), waited out the agent's cold classifier-load, then drove
  `POST /api/room/{code}/checkin` and `.../resume` against a real running
  room. Confirmed on the wire (LiveKit server's own log): the private
  `facilitator-checkin-employee_a` track actually gets added and later
  removed, and `agent.py`'s own log shows clean `active -> paused_checkin
  -> active` transitions with no exceptions.
- **A real, pre-existing bug this run surfaced and fixed**:
  `set_track_subscription_permissions` is synchronous in the installed SDK
  (`rtc/participant.py`'s own signature: `-> None`, not a coroutine), but
  `ParticipantBridge.publish()` was `await`-ing it anyway -- since that
  call happens inside a fire-and-forget `asyncio.create_task` with nothing
  ever awaiting the task or checking its exception, this `TypeError` was
  silently swallowed on every real session, meaning the actual audio
  bridge (the one thing this whole prototype exists to prove) had never
  successfully completed `publish()` against a live server before now.
  Fixed here (dropped the stray `await`) alongside the same mistake in the
  new breakout-room code, which had copied the same wrong pattern.
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
- Stale note removed here: this app *is* wired into `run_all.sh` (starts
  `livekit-server --dev`, `agent.py`, and this app's own `uvicorn`, all three
  torn down together with everything else on Ctrl-C) and into `Caddyfile`
  (`/joint-audio/*` -> port 8424). It's opt-in only -- `run_all.sh` skips it
  gracefully if `.venv` or the `livekit-server` binary (`brew install
  livekit`) aren't set up yet -- not unwired.
- No re-enable-after-drop flow, and no video content moderation -- both
  deliberately out of scope, see the plan's "Scope boundaries".
- The breakout room's private track is inert (no facilitator TTS), and
  nothing here decides when a check-in should happen -- that decision
  lives entirely in `../suture`'s facilitator LLM today, over
  text/WebSocket, with no live connection to this app. Wiring the two
  together is a separate, larger integration, deliberately out of scope.
- **Prosody (see "Prosody / tone signal" above) is validated against real
  synthesized speech, not real human speech** -- `tests/validate_prosody_real_speech.py`
  confirmed pitch/energy/rate tracking behave correctly on genuine speech
  audio (not just sine tones) and caught a real bug (`pitch_flattened` was
  conflating average-pitch-drop with reduced-variability, now fixed and
  split into two checks). What it could not confirm: whether the flags,
  `pitch_flattened` especially, fire the way a human would expect on
  genuine deadpan/sarcastic delivery -- macOS TTS has no real "flat affect"
  mode to test that against. Needs real recorded human speech (this
  sandboxed environment has no microphone, same constraint as the video-
  opt-in gap above). Now wired into `../suture`'s facilitator LLM
  for real (see "Prosody / tone signal" above) -- still not wired into the
  hard-cut decision, by design, and the two apps still have no shared
  session-discovery layer (an operator starts both under the same code by
  hand).
