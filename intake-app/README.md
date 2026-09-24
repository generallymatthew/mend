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

## What this is and isn't

This is a conversation-quality prototype: does the facilitator's tone, pacing, and phase logic (from the system prompt) actually feel right when you talk to it. It is not the real architecture — no persistence layer, no auth, no real escalation routing (the `<mend_signal>` block is parsed and available but not wired to anything downstream yet), and voice transcription runs locally via `faster-whisper` rather than the low-latency hosted STT the real product would need for a live call. See `../joint-session-architecture.md` for what the production pipeline actually needs to look like.
