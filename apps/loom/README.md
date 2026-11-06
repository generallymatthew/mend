# Loom intake prototype (local, text only)

A local-only prototype of Loom's one phase so far: a private, one-on-one
retro interview with a single team member after a sprint or project wraps,
driven by `../facilitator-loom-intake-system-prompt.md`. Text only, no
voice. Single-user, in-memory conversation, nothing persisted to disk.

This is intake only. There is no group session, no voting, and no
across-the-team pattern distillation yet -- see `loom-product-roadmap.md`
for what's still unbuilt. Each run captures one person's interview and the
structured `<loom_signal>` findings it produces; nothing here aggregates
multiple people's interviews into a report yet.

## Setup

```bash
cd loom
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
uvicorn server:app --reload --port 8425
```

Open http://localhost:8425.

## What's real

- A real multi-turn interview against the actual facilitator system prompt
  and the real model, not a scripted flow.
- `<loom_signal>` accumulates structured findings (summary, sentiment,
  likely structural cause) turn by turn, shown in the dev-only signal panel
  on the page -- not shown to a real interviewee in a non-dev build.

## What's not real yet

- No team-level distillation: nothing here reads more than one person's
  interview or produces an aggregated pattern report.
- No minimum-team-size floor for when "patterns" stop being anonymous by
  elimination -- flagged as unresolved in `loom-product-roadmap.md`.
- No auth, no room codes, no persistence -- one conversation, in memory,
  lost on restart, same convention as every other app in this repo.
