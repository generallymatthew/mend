# Links

Every testable URL in one place, split by **Local** (needs something running on your machine) vs **Live** (always up, nothing to start). When both exist for the same page, they're listed together so you can tell at a glance which one you're on.

## Local setup, if you need it

```bash
./run_all.sh
```

Run from the repo root (needs `caddy` — see the root `README.md`). Puts spool, thimble, suture, and post-session-app (all under `apps/`) behind one port, `:8080`, with the same path prefixes Render uses live (`/intake/`, `/joint/`, `/post/`) — so a local URL and its live equivalent below differ only in the host, nothing else. `joint-session-audio` is opt-in (needs `livekit-server` and its own agent worker — see that app's own README) and is skipped automatically if that setup hasn't been done. `seam` (Seam) and `splice` (Splice) aren't wired into this proxy yet — run them standalone.

Docs and standalone HTML files (Roadmap, Status, product spec, pitch page, design handoffs) need a plain file server instead, from the repo root:

```bash
python3 -m http.server 8000
```

## The product

| Page | Local | Live |
|---|---|---|
| Spool | [localhost:8080/](http://localhost:8080/) | [mend-mvp.onrender.com/](https://mend-mvp.onrender.com/) |
| Thimble | [localhost:8080/intake/](http://localhost:8080/intake/) | [mend-mvp.onrender.com/intake/](https://mend-mvp.onrender.com/intake/) |
| Joint session · Employee A | [localhost:8080/joint/?code=links&role=a](http://localhost:8080/joint/?code=links&role=a) | — not deployed |
| Joint session · Employee B | [localhost:8080/joint/?code=links&role=b](http://localhost:8080/joint/?code=links&role=b) | — not deployed |
| Post-session check-in | [localhost:8080/post/](http://localhost:8080/post/) | — not deployed |
| Joint session · audio (opt-in, needs LiveKit) | [localhost:8080/joint-audio/](http://localhost:8080/joint-audio/) | — not deployed |
| About (why this matters) | [localhost:8080/about](http://localhost:8080/about) or [localhost:8000/about.html](http://localhost:8000/about.html) | [mend-mvp.onrender.com/about](https://mend-mvp.onrender.com/about) |

Only spool + thimble are in the live Render deploy (`render.yaml`/`deploy/start.sh`) — everything else above only exists locally. Open both Employee A and Employee B links (two tabs, or send B to someone else) for a real two-person joint session.

## QA / internal tools

| Page | Local | Live |
|---|---|---|
| Thimble states (every avatar state, side by side) | [localhost:8080/intake/static/thimble-states.html](http://localhost:8080/intake/static/thimble-states.html) | [mend-mvp.onrender.com/intake/static/thimble-states.html](https://mend-mvp.onrender.com/intake/static/thimble-states.html) |
| Launchpad (this same link list, as a page) | [localhost:8080/launchpad](http://localhost:8080/launchpad) or [localhost:8000/launchpad.html](http://localhost:8000/launchpad.html) | [mend-mvp.onrender.com/launchpad](https://mend-mvp.onrender.com/launchpad) |
| Phrase review (classifier training-data labeling tool) | [localhost:8000/apps/classifier/data/review_page.html](<http://localhost:8000/apps/classifier/data/review_page.html>) | — local only |

## Documents

| Page | Local | Live |
|---|---|---|
| Product spec | [localhost:8000/product-spec.html](http://localhost:8000/product-spec.html) | — not deployed (see the claude.ai artifact below instead) |
| Pitch page | [localhost:8000/Mend Pitch/Mend Pitch v2.dc.html](<http://localhost:8000/Mend Pitch/Mend Pitch v2.dc.html>) | [mend-mvp.onrender.com/pitch](https://mend-mvp.onrender.com/pitch) |
| Roadmap | [localhost:8000/ROADMAP.md](http://localhost:8000/ROADMAP.md) | — local only |
| Status | [localhost:8000/STATUS.md](http://localhost:8000/STATUS.md) | — local only |
| Public links page (Spool's own, not this file) | — | [mend-mvp.onrender.com/links](https://mend-mvp.onrender.com/links) |

## Design handoffs

Static `.dc.html` mockups for engineering/design handoff — same templated format as the pitch page, so they also need a real file server (`python3 -m http.server 8000`), not `file://`. Local only, nothing deployed.

| Page | Local |
|---|---|
| Mend Intake | [localhost:8000/pitch/design_handoffs/mend_sessions/Mend Intake.dc.html](<http://localhost:8000/pitch/design_handoffs/mend_sessions/Mend Intake.dc.html>) |
| Mend Joint Session | [localhost:8000/pitch/design_handoffs/mend_sessions/Mend Joint Session.dc.html](<http://localhost:8000/pitch/design_handoffs/mend_sessions/Mend Joint Session.dc.html>) |
| Simple Agent Presence (circle + mouth) | [localhost:8000/pitch/design_handoffs/simple_agent_presence/Simple Agent.dc.html](<http://localhost:8000/pitch/design_handoffs/simple_agent_presence/Simple Agent.dc.html>) |

## Hosted elsewhere (claude.ai, always up, no server needed)

- [Thimble shape options](https://claude.ai/artifact/QxwTAwoqh4GpiYvG5Y5GmF) — the four dome/cone/barrel candidates compared against empathizing's shape
- [Product spec (live artifact)](https://claude.ai/artifact/PRQ4kwizN721tXCAf6ACpt)
- [Workflow diagram](https://claude.ai/artifact/3PmW3kE6ejoq4B8XxS9rH1)

## GitHub Pages

- [generallymatthew.github.io/mend/](https://generallymatthew.github.io/mend/) — public landing page (pitch + spec). **Currently down**: the GitHub account is suspended, pending appeal — see the repositories note below.

## Conflict resolution reference videos

YouTube videos on workplace conflict / conflict resolution, kept for reference and as candidates for embedding on `story.html` or elsewhere.

- [Embedded on story.html](https://youtu.be/MnaLS7OE2pk)
- [youtu.be/WfQeH3092Sc](https://youtu.be/WfQeH3092Sc)
- [Why Conflict at Work Is a Good Thing — Margaret Heffernan](https://www.themuse.com/advice/video-pick-why-conflict-at-work-is-a-good-thing)
- [The Secret to Conflict Resolution — Shannon Pearson, TEDxSurrey](https://www.youtube.com/watch?v=DoCi_JECwvY)
- [3 Ways to Resolve a Conflict — Dorothy Walker](https://www.youtube.com/watch?v=r4xPwhcnS-Q)
- [Conflict Resolution: Skills for Leadership & Professional Development](https://www.youtube.com/watch?v=jojnzqX4HRY)
- [How to Manage Conflict in the Workplace](https://www.youtube.com/watch?v=LR_DLCYqGnA)
- [Conflict Resolution Techniques](https://www.youtube.com/watch?v=NJH0XV9jGIE)

## Repositories

- GitHub (`origin`, only remote and live deploy source): `github.com/generallymatthew/mend` — account restored 2026-10-14; `git push` with no remote means `origin`, just do it (see root `CLAUDE.md`).
- GitLab: `git@gitlab.com:generallymatthew-group/mend.git` — retired as a remote on 2026-10-23, no longer in use.
