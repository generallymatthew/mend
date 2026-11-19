# Swatch intake prototype (local, text only)

A local-only prototype of Swatch's first phase: a private, one-on-one
conversation with one reviewer about one specific design artifact, driven
by `../facilitator-swatch-intake-system-prompt.md`. Text only, no voice.
Multi-session, in-memory only, nothing persisted to disk.

Turns a reviewer's raw, unfiltered gut reaction ("I hate this") into a
concrete, objective observation grounded in a real design heuristic
(visual hierarchy, cognitive load, etc.), which the reviewer reviews and
confirms before it's recorded. Unlike Loom's retro output, a confirmed note
is **attributed** -- shown with the reviewer's own name, no anonymization,
no minimum-contributor floor, no distillation step. See the system prompt
and `swatch-product-roadmap.md` for why.

This is intake only. There is no live group session yet (the "Workflow"
six-step presenting/consensus process, audio-only through Thimble, video
bring-your-own via Zoom/Teams and muted -- see the roadmap), and no
anonymous clarification-relay layer (anyone routing a follow-up question
through Thimble instead of asking in the open). Both are designed, neither
is built.

## Setup

```bash
cd swatch
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You need your own Anthropic API key. Create `.env` in this directory
(git-ignored):

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
uvicorn server:app --reload --port 8426
```

Open http://localhost:8426.

## What's real

- A real multi-turn conversation against the actual facilitator system
  prompt and the live Anthropic API.
- The raw-reaction -> probe -> heuristic -> confirm flow, verified live:
  "I hate this checkout flow, it's cluttered" correctly resolved into "four
  CTAs competing for attention, no clear visual hierarchy pointing to the
  primary action" after one probing turn, read back verbatim, and only
  recorded to `/api/notes` once a real "yes" confirmed that exact wording.
- `GET /api/notes?artifact=<name>` returns every confirmed note for an
  artifact, attributed -- the "View confirmed notes" link in the UI calls
  this directly.

## What's not real / not built

- No live group session -- this is one reviewer's private pass, nothing
  else.
- No anonymous clarification relay.
- No persistence -- a server restart loses every session and note.
