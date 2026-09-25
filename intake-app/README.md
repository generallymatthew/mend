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

## Optional: video avatar (Tavus)

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
