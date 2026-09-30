# Mend manager-coaching prototype (local, text + voice memo)

A local-only prototype of the manager-coaching conversation: a manager preparing for, or rehearsing, a hard conversation with a direct report (a performance issue, a conduct problem, conflict that needs addressing before it escalates to HR or a formal mediation), driven by `../facilitator-manager-coaching-system-prompt.md`. Built from `../intake-app`'s own mechanics rather than a new architecture — same avatar UI, same Talk/Practice split, same voice-memo + TTS pipeline, same "nothing recorded, single in-memory conversation" principle — but the content, system prompt, and labels are aimed at the manager side of a hard conversation, not an employee processing a conflict with a peer.

The product insight behind this: people who are great at their individual craft (doctors, researchers, engineers, anyone) routinely get promoted into managing others with zero training in the actually hard part of the job — hard conversations with direct reports. This gives them a private space to think one through, structure it, and rehearse it before they're in the room.

Text and voice-memo input, text replies. Single-user, in-memory conversation, nothing persisted to disk or a database, consistent with the "nothing recorded" principle in `../product-spec.html`.

## Setup

```bash
cd manager-coaching-app
python3.11 -m venv .venv   # or any Python 3.10-3.12; matches the classifier/intake-app setup
source .venv/bin/activate
pip install -r requirements.txt
```

You need your own Anthropic API key (from console.anthropic.com). Create a file called `.env` in this directory (it's git-ignored, never commit it or paste it anywhere else) containing:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
uvicorn server:app --reload --port 8425
```

Open http://localhost:8425 in a browser. Voice memo recording needs microphone permission and works over `localhost` or HTTPS (browsers block mic access on plain HTTP for any other host).

Running this as part of the full walkthrough instead of standalone? Use `../run_all.sh` and open http://localhost:8080/coach/ instead (see `../Caddyfile` and the repo root `README.md`).

## Layout

A call, not a chat app: the avatar, captions, and controls are the main event in the center pane, sized and centered like a video call tile. The message-by-message transcript is reference material, docked in a scrollable column on the right rather than inline in the main flow. Narrow windows (under 760px) stack the transcript below instead of beside.

## Two modes: Talk and Practice

Two buttons above the call tile switch what the session is for, each starting its own fresh conversation (switching mid-conversation asks first, since it discards whatever's there):

- **Talk**: the manager thinks the situation through with the facilitator — framing the issue, structuring what to actually say (the behavior, why it matters, what needs to change), and anticipating how the direct report is likely to react. Exactly as described in `../facilitator-manager-coaching-system-prompt.md`'s Phases 1-3.
- **Practice**: skips straight to rehearsal, per that same prompt's "Practicing the conversation (roleplay)" section (Phase 4), which already covers how the facilitator plays the direct report. This just puts the choice up front, in the manager's hands, instead of waiting for the facilitator to organically offer it mid-conversation. The facilitator still gathers enough context first (who, what's the issue, how they plan to open it) to play a realistic version of that direct report. Whenever it's in character, a badge above the caption reads "In character: playing the other person", tied to the same `roleplay_active` signal the prompt already emits, so it's never ambiguous who the manager is actually talking to.

## The avatar shape, captions, and better voice quality

Always on, no config needed: a plain circle with a mouth, geometry and per-state motion matching `../design_handoff_simple_agent_presence/`. It reacts to any audio through the page's `<audio>` element via the Web Audio API, so it works the same regardless of which TTS produced that audio. States, visually distinct on purpose so listening never looks like talking: idle/listening (closed mouth, a slow breathing scale and an occasional nod, not driven by your own mic volume), thinking (mouth shrinks and slides side to side on a dimmer, smaller circle), talking (mouth opens and closes with the facilitator's own TTS audio). Empathizing and Calming are implemented per the handoff but not yet wired to any trigger in this prototype.

Under the avatar, a caption line shows the words being spoken, revealed in sync with playback. Neither TTS backend gives real per-word timestamps, so the reply is split into short chunks and each chunk's start time is estimated from its share of the total character count. It's an approximation, close enough to read like real subtitles, not frame-accurate.

The voice itself matters more than the shape. By default it's macOS's built-in `say` (the "Samantha" voice, functional but robotic). For a more natural voice, add an OpenAI key to `.env`:

```
OPENAI_API_KEY=sk-...
```

That's it: `synthesize_speech` tries OpenAI's TTS (`tts-1`) first when the key is set, and only falls back to `say` if that call fails. Pick a different built-in voice with `OPENAI_TTS_VOICE` in `.env` (default `alloy`; also available: `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`, `verse`, `marin`, `cedar`).

## Live conversation (hands-free)

The "Go live" button next to the mic turns voice memo's click-to-record/click-to-stop into an automatic loop: it listens, detects when you've stopped talking (voice-activity detection on your mic volume, not a real speech model), sends and gets a reply, plays it back, then starts listening again on its own. Click "End live conversation" to leave the loop.

This isn't a real-time streaming conversation, since neither TTS backend here does streaming STT: each turn is still a full record-then-transcribe-then-reply round trip, just without you clicking anything between turns. It also doesn't support interrupting the facilitator while it's talking (barge-in); wait for it to finish before the mic starts listening again.

The auto-stop threshold (`VAD_THRESHOLD` in `static/index.html`, currently `0.06` on the same 0..1 scale the avatar's own reactivity uses) is a guess. If it's cutting you off mid-sentence, raise the silence window (`VAD_SILENCE_MS`) or lower the threshold; if it's not noticing you've stopped, do the opposite. It depends on your mic and room noise.

## What this is and isn't

This is a conversation-quality prototype: does the facilitator's tone, pacing, and phase logic (from `../facilitator-manager-coaching-system-prompt.md`) actually feel right when a manager talks to it. It is not the real architecture — no persistence layer, no auth, no real escalation routing (the `<mend_signal>` block is parsed and available but not wired to anything downstream yet), and voice transcription runs locally via `faster-whisper` rather than the low-latency hosted STT the real product would need for a live call. See `../joint-session-architecture.md` for what the production pipeline actually needs to look like (that doc is written for the employee-facing flow, but the same transport/latency constraints apply here).

This app is deliberately a close sibling of `../intake-app`, not a from-scratch design: same server mechanics (rate limiting, TTS staging, Whisper transcription, optional Tavus video avatar), same frontend (avatar canvas, captions, live mode, transcript panel), same brand tokens (Evergreen/Pink/Honey/Oat, Manrope) — only the system prompt, kickoff copy, and a handful of labels (`manager`/`direct report` in place of `employee`/`the other person` where the framing genuinely differs) are different. See `../intake-app/README.md` for the fuller explanation of mechanics shared verbatim here (voice-memo latency history, VAD calibration notes, the Tavus video-avatar setup steps) rather than duplicating all of it.

## Optional: realistic video avatar (Tavus)

Same optional path as `../intake-app`: a "Start video call" button appears once `TAVUS_API_KEY`, `TAVUS_FACE_ID`, `LLM_SHIM_SECRET`, and `TAVUS_PAL_ID` are set in `.env` (run `python tavus_setup.py` once a public tunnel to this app, e.g. via `cloudflared`, is running on port 8425). See `../intake-app/README.md`'s "Optional: realistic video avatar (Tavus)" section for the full step-by-step — identical here except this app listens on port 8425, not 8420.
