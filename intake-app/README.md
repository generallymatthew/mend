# Mend intake prototype (local, text + voice memo)

A local-only prototype of the employee-initiated intake conversation (private processing → decision point → pre-session screen → initial side conversation), driven by `../facilitator-intake-system-prompt.md`. Text and voice-memo input, text replies. Single-user, in-memory conversation, nothing persisted to disk or a database, consistent with the "nothing recorded" principle in `../product-spec.html`.

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

Running this as part of the full walkthrough instead of standalone? Use `../run_all.sh` and open http://localhost:8080/intake/ instead — the "continue to joint session" banner link only resolves correctly when browsed that way (see the repo root `README.md`).

## Optional: tester access gate

Unset by default (local dev needs no setup). Set `TESTER_ACCESS_CODE` in `.env` (and on Render, before sending the live URL to anyone) to require a shared passcode before any page or `/api/*` call is served — a lightweight wall against random crawlers/scrapers hitting the paid LLM/voice endpoints, not real per-user auth. A tester without the cookie gets redirected to `/gate` (or a 401 on API calls), enters the code once, and it's remembered via a cookie for 30 days.

## Layout

A call, not a chat app: the avatar, captions, and controls are the main event in the center pane, sized and centered like a video call tile. The message-by-message transcript is reference material, docked in a scrollable column on the right rather than inline in the main flow. Narrow windows (under 760px) stack the transcript below instead of beside.

## Two modes: Talk and Practice

Two buttons above the call tile switch what the session is for, each starting its own fresh conversation (switching mid-conversation asks first, since it discards whatever's there):

- **Talk**: the normal intake side conversation, exactly as described throughout this README and `../facilitator-intake-system-prompt.md`.
- **Practice**: skips the side-conversation opening and disclosures entirely and goes straight to rehearsal, per that same prompt's "Practicing the conversation (roleplay)" section, which already covers how the facilitator plays the other person. This just puts the choice up front, in the employee's hands, instead of waiting for the facilitator to organically offer it mid-conversation. The facilitator still gathers context first (who, what happened, a concrete example, how they plan to open it) before stepping into character. Whenever it's in character, a badge above the caption reads "In character: playing the other person", tied to the same `roleplay_active` signal the prompt already emits, so it's never ambiguous who you're actually talking to.

## The avatar shape, captions, and better voice quality

Always on, no config needed: a plain circle with a mouth, geometry and per-state motion matching `../design_handoff_simple_agent_presence/`. It reacts to any audio through the page's `<audio>` element via the Web Audio API, so it works the same regardless of which TTS produced that audio. States, visually distinct on purpose so listening never looks like talking: idle/listening (closed mouth, a slow breathing scale and an occasional nod, not driven by your own mic volume), thinking (mouth shrinks and slides side to side on a dimmer, smaller circle), talking (mouth opens and closes with the facilitator's own TTS audio). Empathizing and Calming are implemented per the handoff but not yet wired to any trigger in this prototype.

Under the avatar, a caption line shows the words being spoken, revealed in sync with playback. Neither TTS backend gives real per-word timestamps, so the reply is split into short chunks and each chunk's start time is estimated from its share of the total character count. It's an approximation, close enough to read like real subtitles, not frame-accurate.

The voice itself matters more than the shape. By default it's macOS's built-in `say` (the "Samantha" voice, functional but robotic). For a more natural voice, add an OpenAI key to `.env`:

```
OPENAI_API_KEY=sk-...
```

That's it: `synthesize_speech` tries OpenAI's TTS (`gpt-4o-mini-tts`) first when the key is set, and only falls back to `say` if that call fails. Pick a different built-in voice with `OPENAI_TTS_VOICE` in `.env` (default `alloy`; also available: `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`, `verse`, `marin`, `cedar`).

## Streaming STT (Deepgram), replacing local-Whisper VAD/partials

By default, voice turns use local `faster-whisper` plus a client-side silence
timer (VAD) to guess when you've stopped talking -- see "Live conversation"
below. Add a Deepgram key to `.env` to switch to real streaming transcription
instead:

```
DEEPGRAM_API_KEY=...
```

With that set, the browser streams raw mic audio to the server over a
WebSocket (`/ws/voice`), which relays it straight through to Deepgram's live
API and forwards transcripts back. Deepgram's own server-side endpointing
(from the real audio, not a fixed client-side silence timer) decides when a
turn ends, so there's no more guessing at `VAD_SILENCE_MS`, and the turn's
transcript is already fully available the instant it ends -- no separate
transcription round trip, no VAD cutoff/false-trigger tuning. Without a key,
`/api/voice/config` reports `deepgram: false` and the frontend falls back to
the local-Whisper path entirely, unchanged -- this is additive, not a
replacement for the OPENAI_API_KEY-free, fully-local setup above it.

Not yet verified with real speech/a real mic in this environment (same
sandboxed-browser limitation as the rest of Voice view, see STATUS.md) --
verified only that the relay correctly refuses a connection when no key is
set and that the rest of the app is unaffected either way.

## Live conversation (hands-free)

The "Go live" button next to the mic turns voice memo's click-to-record/click-to-stop into an automatic loop: it listens, detects when you've stopped talking (voice-activity detection on your mic volume, not a real speech model), sends and gets a reply, plays it back, then starts listening again on its own. Click "End live conversation" to leave the loop.

This isn't a real-time streaming conversation, since neither TTS backend here does streaming STT: each turn is still a full record-then-transcribe-then-reply round trip, just without you clicking anything between turns. It also doesn't support interrupting the facilitator while it's talking (barge-in); wait for it to finish before the mic starts listening again.

The auto-stop threshold (`VAD_THRESHOLD` in `static/index.html`, currently `0.06` on the same 0..1 scale the avatar's own reactivity uses) is a guess. If it's cutting you off mid-sentence, raise the silence window (`VAD_SILENCE_MS`) or lower the threshold; if it's not noticing you've stopped, do the opposite. It depends on your mic and room noise.

## Why voice used to feel stuck on "transcribing..."

Several real fixes, not just tuning:

- `faster-whisper`'s model used to load (and on first run, download from Hugging Face) lazily, on the *first* voice message of a session. That download/load is genuinely slow, and it was landing on whatever turn happened to be first, live mode included, not on server startup where it belongs. It's now loaded eagerly in a startup hook, so `uvicorn` takes longer to report "Application startup complete" but every actual voice message afterward is fast.
- The default model dropped from `small.en` to `base.en` to `tiny.en` over time, a real speed-for-accuracy trade worth knowing about at each step. Override with `WHISPER_MODEL` in `.env` (e.g. `base.en`, `small.en`, or `medium.en` for more accuracy and a slower turnaround).
- `faster-whisper`'s own `cpu_threads=0` default (its own internal heuristic) measured meaningfully slower than just handing it every logical core on this machine -- no accuracy cost, unlike the model-size trade above, just using the hardware that's actually available. Now defaults to `os.cpu_count()`, override with `WHISPER_CPU_THREADS` if you want to leave headroom for something else running on the same machine.
- `/api/voice`, `/api/message`, and `/api/start` used to also run TTS synthesis inline before returning anything, meaning the *entire* reply -- transcription/LLM call *and* voice synthesis -- sat behind one "transcribing..."/"facilitator is responding..." label, typically 25-30s combined, TTS alone often the biggest single piece of that (scales with reply length). Reply text now comes back on its own, fast, and the frontend fetches audio in a second round trip via `POST /api/speak` afterward, not blocking the input on it. See `facilitator_reply()`'s docstring in `server.py`.
- Real numbers, measured on an Intel i5-8210Y MacBook Air (dual-core, no GPU/Neural Engine -- there's no Metal/Core ML acceleration path for local Whisper on this class of hardware, only faster CPU config or a smaller model help locally) for a ~9.5s clip: `base.en` at the old default thread count, 5.16s; `base.en` with `cpu_threads=4`, 3.58s; `tiny.en` with `cpu_threads=4` (now the default), 2.24s. A cloud STT API (OpenAI's `gpt-4o-mini-transcribe`, measured 1.81s for the same clip) would be faster still, but was deliberately not adopted here: it would send the employee's raw voice memo off the machine, a real step down in privacy posture for a product whose entire pitch is "nothing recorded" -- kept local-only on purpose, even in this dev prototype.

## Testing shortcut: a one-sentence intro

Reloading and sitting through the full multi-paragraph opening every time you test gets old fast. Set `TEST_SHORT_INTRO=1` in `.env` and the opening line collapses to one short sentence (still a real model call, still gets a real `mend_signal`, just less to read and less TTS to wait on per reload). Leave it unset for anything where the actual scripted opening matters.

## Post-session feedback survey

A separate page (`static/survey.html`, served at `/survey`) collects an overall rating plus a set of research questions -- trust/safety (felt safe being honest, trusted the privacy claim, whether Thimble seemed to take sides), whether it actually understood the situation and changed how the tester plans to approach it, a comparison against talking to an HR rep/manager/friend instead, an NPS-style recommend score, an emotional-shift check, a "You and Thimble" section (how they related to it -- tool, presence, or person-like; whether it felt comforting; whether they found themselves granting it any authority, and what they think that authority came from, if any; and a general, Thimble-independent comfort-with-AI scale), two open "what stood out"/"what would build more trust" questions, plus technical issues and general comments. Always reachable via the "Leave feedback" link in the header; also shown automatically -- a toast, then a redirect -- once Thimble signals the conversation has reached its natural end point (`ready_for_joint_session` or `conversation_structured` in its `mend_signal`), timed to wait until it's actually done talking so it never interrupts a reply.

Every response is logged locally (`survey_responses.jsonl`, git-ignored, and also printed to stdout) regardless of setup below -- that's the fallback. The real durable store, meant to actually be checked later, is a Google Sheet. One-time setup, done in Google Cloud Console/Sheets, not in this repo:

1. In [Google Cloud Console](https://console.cloud.google.com), create or reuse a project, then enable the **Google Sheets API** for it.
2. Create a **Service Account** (IAM & Admin → Service Accounts), then generate a JSON key for it and download the file.
3. Create a new Google Sheet (or reuse one) with a header row matching the columns this app appends, in this exact order: `timestamp, overall_rating, felt_fair, felt_safe, trusted_privacy, sided, understood_situation, changed_approach, readiness, comparison, would_reuse, nps, emotional_shift, thimble_relation, thimble_comforting, granted_authority, authority_source, ai_comfort_general, standout_moment, trust_improvement, issues, comments`. (If you already have a Sheet from before the "You and Thimble" section was added, just add the five new header cells -- `thimble_relation, thimble_comforting, granted_authority, authority_source, ai_comfort_general` -- right after `emotional_shift` and before `standout_moment`; existing rows are unaffected, new ones will fill the new columns in.)
4. Share that Sheet with the service account's own email (looks like `...@...iam.gserviceaccount.com`, found in the downloaded key file's `client_email` field) as an **Editor**.
5. Add to `.env` (and to Render's Environment tab for the live deploy):
   ```
   GOOGLE_SHEET_ID=...        # the id segment of the Sheet's URL, between /d/ and /edit
   GOOGLE_SERVICE_ACCOUNT_JSON=...   # the ENTIRE downloaded JSON key file's contents, as one line
   ```
   Never commit the key file or paste its contents anywhere other than these env vars -- it's a real credential with write access to that Sheet.

Without those two env vars set, `get_survey_sheet()` just logs why and returns `None`; the survey still works end to end, it just only lands in the local file/stdout log instead of the Sheet.

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
