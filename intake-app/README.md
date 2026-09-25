# Mend intake prototype (local, text + voice memo)

A local-only prototype of the employee-initiated intake conversation (private processing → decision point → pre-session screen → initial caucus), driven by `../facilitator-intake-system-prompt.md`. Text and voice-memo input, text replies. Single-user, in-memory conversation, nothing persisted to disk or a database, consistent with the "nothing recorded" principle in `../product-spec.html`.

## Setup

```bash
cd intake-app
python3.11 -m venv .venv   # or any Python 3.10-3.12; matches the classifier/ setup
source .venv/bin/activate
pip install -r requirements.txt
```

You need your own Anthropic API key (from console.anthropic.com). Create a file called `.env` in this directory (it's git-ignored, never commit it or paste it anywhere else) containing:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
uvicorn server:app --reload --port 8420
```

Open http://localhost:8420 in a browser. Voice memo recording needs microphone permission and works over `localhost` or HTTPS (browsers block mic access on plain HTTP for any other host).

## Layout

A call, not a chat app: the avatar, captions, and controls are the main event in the center pane, sized and centered like a video call tile. The message-by-message transcript is reference material, docked in a scrollable column on the right rather than inline in the main flow. Narrow windows (under 760px) stack the transcript below instead of beside.

## The avatar shape, captions, and better voice quality

Always on, no config needed: a plain circle, with a mouth that opens and closes with whatever audio is actually playing, no realistic face. It reacts to any audio through the page's `<audio>` element via the Web Audio API, so it works the same regardless of which TTS produced that audio. Four states, visually distinct on purpose so listening never looks like talking: idle (closed mouth, nothing happening), listening (the whole circle pulses in size with your own mic volume while recording, mouth stays shut), thinking (three pulsing dots while waiting on the facilitator), talking (mouth opens and closes with the facilitator's own TTS audio).

Under the avatar, a caption line shows the words being spoken, revealed in sync with playback. Neither TTS backend gives real per-word timestamps, so the reply is split into short chunks and each chunk's start time is estimated from its share of the total character count. It's an approximation, close enough to read like real subtitles, not frame-accurate.

The voice itself matters more than the shape. By default it's macOS's built-in `say` (the "Samantha" voice, functional but robotic). For a more natural voice, add an OpenAI key to `.env`:

```
OPENAI_API_KEY=sk-...
```

That's it: `synthesize_speech` tries OpenAI's TTS (`gpt-4o-mini-tts`) first when the key is set, and only falls back to `say` if that call fails. Pick a different built-in voice with `OPENAI_TTS_VOICE` in `.env` (default `alloy`; also available: `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`, `verse`, `marin`, `cedar`).

## Live conversation (hands-free)

The "Go live" button next to the mic turns voice memo's click-to-record/click-to-stop into an automatic loop: it listens, detects when you've stopped talking (voice-activity detection on your mic volume, not a real speech model), sends and gets a reply, plays it back, then starts listening again on its own. Click "End live conversation" to leave the loop.

This isn't a real-time streaming conversation, since neither TTS backend here does streaming STT: each turn is still a full record-then-transcribe-then-reply round trip, just without you clicking anything between turns. It also doesn't support interrupting the facilitator while it's talking (barge-in); wait for it to finish before the mic starts listening again.

The auto-stop threshold (`VAD_THRESHOLD` in `static/index.html`, currently `0.06` on the same 0..1 scale the avatar's own reactivity uses) is a guess. If it's cutting you off mid-sentence, raise the silence window (`VAD_SILENCE_MS`) or lower the threshold; if it's not noticing you've stopped, do the opposite. It depends on your mic and room noise.

## Why voice used to feel stuck on "transcribing..."

Two real fixes, not just tuning:

- `faster-whisper`'s model used to load (and on first run, download from Hugging Face) lazily, on the *first* voice message of a session. That download/load is genuinely slow, and it was landing on whatever turn happened to be first, live mode included, not on server startup where it belongs. It's now loaded eagerly in a startup hook, so `uvicorn` takes longer to report "Application startup complete" but every actual voice message afterward is fast.
- The default model dropped from `small.en` to `base.en`, a real speed-for-accuracy trade worth knowing about. Override with `WHISPER_MODEL` in `.env` (e.g. `small.en` or `medium.en` for more accuracy and a slower turnaround, `tiny.en` for the fastest but least accurate option).

## Testing shortcut: a one-sentence intro

Reloading and sitting through the full multi-paragraph opening every time you test gets old fast. Set `TEST_SHORT_INTRO=1` in `.env` and the opening line collapses to one short sentence (still a real model call, still gets a real `mend_signal`, just less to read and less TTS to wait on per reload). Leave it unset for anything where the actual scripted opening matters.

## Optional: realistic video avatar (Tavus)

A separate, parked path if a photorealistic video face is ever wanted instead of the abstract shape above. More setup (its own account, a public tunnel, a custom-LLM shim), so it's kept as an independent option rather than the default.

Bolted on alongside text/voice memo, not a replacement for it: a "Start video call" button appears once this is configured, and puts the same facilitator (same system prompt, same Claude backend) in front of a talking video avatar instead of a text thread. Text/voice-memo mode still works exactly as above either way.

This needs a Tavus account (tavus.io) and a way for Tavus's cloud to reach this app over the internet, since their video pipeline calls back into a custom LLM endpoint per turn. Steps:

1. Sign up at tavus.io and get an API key from the PAL Maker.
2. Pick a stock face from your Tavus dashboard's face library and note its `face_id`.
3. Make up a random string for `LLM_SHIM_SECRET`. This is a shared secret between this app and Tavus, not a real provider key. It stops randoms who find your tunnel URL from making Anthropic-billed calls through it.
4. Add to `.env`:
   ```
   TAVUS_API_KEY=...
   TAVUS_FACE_ID=...
   LLM_SHIM_SECRET=...
   ```
5. Start this server (`uvicorn server:app --reload --port 8420`), then in another terminal, open a public tunnel to it. The simplest option needs no account: `brew install cloudflared && cloudflared tunnel --url http://localhost:8420`. Copy the `https://*.trycloudflare.com` URL it prints.
6. Add that URL to `.env` as `PUBLIC_LLM_BASE_URL`, then run the one-time setup script:
   ```
   python tavus_setup.py
   ```
   It creates a Tavus PAL pointed at your tunnel and prints a `TAVUS_PAL_ID` to add to `.env`.
7. Restart this server so it picks up `TAVUS_PAL_ID`. Reload the page: "Start video call" should now appear.

Rough edges worth knowing about, since this is a prototype wiring, not production:

- A `cloudflared` quick tunnel gets a new URL every time it restarts. If you restart the tunnel, re-run `tavus_setup.py` with the new `PUBLIC_LLM_BASE_URL` and update `TAVUS_PAL_ID`.
- While the tunnel is running, this whole app (not just the video shim) is briefly reachable from the public internet at that URL. Fine for a quick test; don't leave it running unattended.
- The video call's transcript lives in Tavus's own conversation object, not in this app's memory. Only the parsed `mend_signal` (for the "ready for joint session" banner) makes it back here, polled every few seconds while a call is active.
- The `<mend_signal>` control block is stripped before Tavus ever sees it, the same way it's stripped from what gets shown/spoken in text mode, so the avatar never speaks the raw JSON.

## What this is and isn't

This is a conversation-quality prototype: does the facilitator's tone, pacing, and phase logic (from the system prompt) actually feel right when you talk to it. It is not the real architecture — no persistence layer, no auth, no real escalation routing (the `<mend_signal>` block is parsed and available but not wired to anything downstream yet), and voice transcription runs locally via `faster-whisper` rather than the low-latency hosted STT the real product would need for a live call. See `../joint-session-architecture.md` for what the production pipeline actually needs to look like.
