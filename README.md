# Mend

A confidential, AI-facilitated conflict resolution tool for workplace teams. See `product-spec.html` for the full elevator pitch and mission.

## What's here

- **`product-spec.html`** — the full product spec: mission, core principles, the employee- and manager-initiated flows, the trigger/escalation system, data and privacy architecture, power-imbalance safeguards, IP strategy, open risks, and a running log of ideas considered and deliberately rejected (with the reasoning kept, not just the decision). Open it directly in a browser; the two flow diagrams render via the hosted version, [linked below](#live-version).
- **`Mend Pitch/`** — the external-facing pitch: a pitch page, a one-minute workflow video, and a session-opening (intake/joint-session/caucus) video, built as animated `.dc.html` pages with a shared design system. See that folder's own `README.md` for how to serve it locally. (`Mend Pitch standalone/` is the old bundled export, deprecated — see its own `README.md` for why.)
- **`Product pitch redesign help.zip`** — supporting material for the pitch redesign (not yet unpacked/reviewed).
- **`intake-app/`, `joint-session-app/`, `post-session-app/`, `demo-app/`** — local FastAPI prototypes of the actual facilitator conversations, each backed by its matching `facilitator-*-system-prompt.md`. `demo-app/` is the entry point: a sign-up/invite screen plus links through the other three in order. See [Local prototypes](#local-prototypes) below.

## Live version

`product-spec.html` is also published and kept in sync at:
https://claude.ai/artifact/PRQ4kwizN721tXCAf6ACpt

## Local prototypes

Four local FastAPI apps, each its own venv and `.env` (see each `README.md`), no persistence beyond the running process:

| App | Port | What it tests |
|---|---|---|
| `demo-app/` | 8423 | Sign-up + anonymous-invite UX, links through the three below in order |
| `intake-app/` | 8420 | Private processing conversation, text + voice memo |
| `joint-session-app/` | 8421 | Joint session, you play both employees |
| `post-session-app/` | 8422 | Post-session follow-up, with a scenario picker since it doesn't chain from a real joint session |

Run all four (each in its own terminal, from that app's folder) and start at `demo-app` for the full walkthrough. `intake-app` and `joint-session-app` each show a "continue" banner once the facilitator's own signal says the next step is ready — you don't have to guess when to move on. None of these run in GitHub Pages; they need a local server and your own Anthropic API key.

## Status

Pre-legal-review draft. Several sections are explicitly flagged as needing real employment counsel before this goes anywhere near a customer (the trigger definitions in particular). See Section 10 of the spec.
