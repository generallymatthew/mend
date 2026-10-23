# Mend

A confidential, AI-facilitated conflict resolution tool for workplace teams. See `product-spec.html` for the full elevator pitch and mission, `STATUS.md` for what's recently happened, and `ROADMAP.md` for the phase-level view of what's next.

## What's here

Top level is split into: live site files (this README, `product-spec.html`, `about.html`/`story.html`/`testers.html`/`launchpad.html`/`index.html`, `Mend Pitch/`, `CNAME` — all served directly by GitHub Pages at `pitch.trymend.solutions`, so none of these move into a subfolder), the rolling project docs (`STATUS.md`, `ROADMAP.md`, `IDEAS.md`, `CLAUDE.md`, `LINKS.md`), local dev infra (`run_all.sh`, `Caddyfile`, `deploy/`, `render.yaml`), and two subfolders that hold everything else:

- **`apps/`** — every local FastAPI prototype, plus the `facilitator-*-system-prompt.md` files and `joint-session-architecture.md` they're built from (kept as siblings of the apps so each app's own `../facilitator-*.md` references still resolve). See [Local prototypes](#local-prototypes) below for what's runnable and what each one tests.
- **`pitch/`** — everything pitch/marketing-adjacent that *isn't* part of the live site: `Social media/`, `cf-prompts/`, `pitch-scripts/`, `microsite/`, `archive/` (old pitch exports + a couple of not-yet-reviewed scratch files), `design_handoffs/` (design-reference implementations handed off for porting into the real apps — Thimble avatar motion, the Mend Sessions UI pass + brand kit).
- **`IDEAS.md`** — a dumping ground for ideas worth capturing but not worth working on yet (positioning angles, adjacent markets, feature concepts, the seven app-codename concepts), each tagged with where it could plug in and why it's not active.

## Live version

`product-spec.html` is also published and kept in sync at:
https://claude.ai/artifact/PRQ4kwizN721tXCAf6ACpt

## Local prototypes

Local FastAPI apps, all under `apps/`, each its own venv and `.env` (see each `README.md`), no persistence beyond the running process unless noted:

| App | Port | What it tests |
|---|---|---|
| `apps/spool/` | 8423 | Sign-up + anonymous-invite UX, links through the three below in order |
| `apps/thimble/` | 8420 | Private processing conversation, text + voice memo. Covers both the employee-conflict path and the manager-coaching path (a manager rehearsing a hard conversation with a direct report) — the latter used to be a separate `manager-coaching-app`, since removed as redundant once it was folded into this app's own system prompt |
| `apps/suture/` | 8421 | The joint session, two real participants (each connects with their own role link) |
| `apps/post-session-app/` | 8422 | Post-session follow-up, with a scenario picker since it doesn't chain from a real joint session |
| `apps/joint-session-audio/` | 8424 | Standalone proof of the real audio delay buffer (LiveKit + streaming STT + the real hard-cut classifier) — not yet integrated with `suture/`'s conversational logic. Needs `brew install livekit` and its own `agent.py` worker in addition to uvicorn; see its `README.md`. |
| `apps/seam/` | — | Case management for a manager working through conflict between two of their team members — a persisted, role-anonymized running action plan, distinct from `thimble`'s manager-coaching path above (that's solo rehearsal; this is an ongoing case). Can hand off into a real `suture` room. Not yet wired into `run_all.sh`/`Caddyfile` — run standalone per its own `README.md`. |
| `apps/splice/` | — | Live group consensus-building over a real Zoom call (companion panel via the Zoom Apps SDK): shared room, chat, proposals, voting, Thimble as a visible named participant. Opposite trust model from the apps above — no safety floor, no confidentiality, driving an explicit visible group decision instead. Not yet wired into `run_all.sh`/`Caddyfile` — run standalone per its own `README.md`. |
| `apps/classifier/` | — | Fine-tuned toxic-bert model for the real-time hard-cut tier of the joint session; not a web app, see its own `README.md`. |

**Run the core four at once:** `./run_all.sh` from the repo root starts `spool`, `thimble`, `suture`, and `post-session-app` (each in its own venv) plus a local Caddy reverse proxy, and puts the whole walkthrough behind one address: **http://localhost:8080/**. Requires `caddy` (`brew install caddy`) and each app's own venv/dependencies already set up per its `README.md`. Ctrl-C stops everything together. `seam` and `splice` aren't part of this walkthrough yet — run them standalone.

Prefer running one app in isolation to debug it (e.g. while iterating on its system prompt)? Each app still works standalone on its own port from the table above — just note that cross-app links (Spool's buttons, the "continue" banners) point at the proxy's paths (`/intake/`, `/joint/`, `/post/`) and only resolve correctly when browsing through `run_all.sh`'s `:8080`, not when an app is opened directly on its own port.

`thimble` and `suture` each show a "continue" banner once the facilitator's own signal says the next step is ready — you don't have to guess when to move on. None of these run in GitHub Pages; they need a local server and your own Anthropic API key.

## Status

Pre-legal-review draft. Several sections are explicitly flagged as needing real employment counsel before this goes anywhere near a customer (the trigger definitions in particular). See Section 10 of the spec.
