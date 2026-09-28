# Mend

A confidential, AI-facilitated conflict resolution tool for workplace teams. See `product-spec.html` for the full elevator pitch and mission.

## What's here

- **`product-spec.html`** — the full product spec: mission, core principles, the employee- and manager-initiated flows, the trigger/escalation system, data and privacy architecture, power-imbalance safeguards, IP strategy, open risks, and a running log of ideas considered and deliberately rejected (with the reasoning kept, not just the decision). Open it directly in a browser; the two flow diagrams render via the hosted version, [linked below](#live-version).
- **`Mend Pitch/`** — the external-facing pitch: a pitch page, a one-minute workflow video, and a session-opening (intake/joint-session/caucus) video, built as animated `.dc.html` pages with a shared design system. See that folder's own `README.md` for how to serve it locally. (`Mend Pitch standalone/` is the old bundled export, deprecated — see its own `README.md` for why.)
- **`Product pitch redesign help.zip`** — supporting material for the pitch redesign (not yet unpacked/reviewed).
- **`intake-app/`, `joint-session-app/`, `post-session-app/`, `demo-app/`** — local FastAPI prototypes of the actual facilitator conversations, each backed by its matching `facilitator-*-system-prompt.md`. `demo-app/` is the entry point: a sign-up/invite screen plus links through the other three in order. See [Local prototypes](#local-prototypes) below.
- **`joint-session-audio/`** — standalone proof of the real audio delay buffer from `joint-session-architecture.md` (LiveKit + streaming STT gating a per-participant buffer via the real hard-cut classifier). Not yet integrated with `joint-session-app/`'s conversational logic — see its own `README.md`.
- **`run_all.sh` + `Caddyfile`** — runs all four apps behind one local address instead of four separate ports. See [Local prototypes](#local-prototypes).

## Live version

`product-spec.html` is also published and kept in sync at:
https://claude.ai/artifact/PRQ4kwizN721tXCAf6ACpt

## Local prototypes

Four local FastAPI apps, each its own venv and `.env` (see each `README.md`), no persistence beyond the running process:

| App | Port | What it tests |
|---|---|---|
| `demo-app/` | 8423 | Sign-up + anonymous-invite UX, links through the three below in order |
| `intake-app/` | 8420 | Private processing conversation, text + voice memo |
| `joint-session-app/` | 8421 | The joint session, two real participants (each connects with their own role link) |
| `post-session-app/` | 8422 | Post-session follow-up, with a scenario picker since it doesn't chain from a real joint session |
| `joint-session-audio/` | 8424 | Standalone proof of the real audio delay buffer (LiveKit + streaming STT + the real hard-cut classifier) — not yet integrated with `joint-session-app/`'s conversational logic. Needs `brew install livekit` and its own `agent.py` worker in addition to uvicorn; see its `README.md`. |

**Run everything at once:** `./run_all.sh` from the repo root starts all four (each in its own venv) plus a local Caddy reverse proxy, and puts the whole walkthrough behind one address: **http://localhost:8080/**. Requires `caddy` (`brew install caddy`) and each app's own venv/dependencies already set up per its `README.md`. Ctrl-C stops everything together.

Prefer running one app in isolation to debug it (e.g. while iterating on its system prompt)? Each app still works standalone on its own port from the table above — just note that cross-app links (demo-app's buttons, the "continue" banners) point at the proxy's paths (`/intake/`, `/joint/`, `/post/`) and only resolve correctly when browsing through `run_all.sh`'s `:8080`, not when an app is opened directly on its own port.

`intake-app` and `joint-session-app` each show a "continue" banner once the facilitator's own signal says the next step is ready — you don't have to guess when to move on. None of these run in GitHub Pages; they need a local server and your own Anthropic API key.

## Status

Pre-legal-review draft. Several sections are explicitly flagged as needing real employment counsel before this goes anywhere near a customer (the trigger definitions in particular). See Section 10 of the spec.
