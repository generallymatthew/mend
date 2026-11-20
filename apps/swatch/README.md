# Swatch design-crit prototype (local, text only)

A local-only prototype of Swatch's design-crit side: a private, one-on-one
conversation with one reviewer about one specific design artifact, driven
by `../facilitator-swatch-intake-system-prompt.md`; then a live group
session where confirmed notes actually get presented and discussed,
driven by `../facilitator-swatch-live-system-prompt.md`. Text only, no
voice. Multi-session, in-memory only, nothing persisted to disk.

Turns a reviewer's raw, unfiltered gut reaction ("I hate this") into a
concrete, objective observation grounded in a real design heuristic
(visual hierarchy, cognitive load, etc.), which the reviewer reviews and
confirms before it's recorded. Unlike Loom's retro output, a confirmed note
is **attributed** -- shown with the reviewer's own name, no anonymization,
no minimum-contributor floor, no distillation step. See the intake system
prompt and `swatch-product-roadmap.md` for why.

The live session is text-first in this build -- any number of named
participants join a room keyed by artifact name, and once someone sends
`start`, Thimble presents each confirmed note in turn and opens the floor.
Not yet built: real audio (the "Workflow" six-step preflight-collaboration
process, audio-only through Thimble, video bring-your-own via Zoom/Teams
and muted -- see the roadmap), and the anonymous clarification-relay layer
(anyone routing a follow-up question through Thimble instead of asking in
the open).

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

- The live crit session, verified live: joined as "Sam", sent `start`,
  Thimble presented the one confirmed note on "Checkout flow v3" attributed
  with its heuristic and asked for the designer's reaction; a reply from
  "Sam" broadcast to the room and got a facilitator follow-up. No console
  errors.

## What's not real / not built

- No real audio in the live session -- text broadcast over a WebSocket
  only, no TTS, no turn-taking classifier.
- No preflight-collaboration "Workflow" (warm-up, solo work,
  consensus/reaction aggregation) -- the live session only covers the
  crit side's "present notes, discuss" shape.
- No anonymous clarification relay.
- No persistence -- a server restart loses every session, note, and live
  room.
