# Links

Every testable URL in one place, split by **Local** (needs something running on your machine) vs **Live** (always up, nothing to start). When both exist for the same page, they're listed together so you can tell at a glance which one you're on.

## Local setup, if you need it

```bash
./run_all.sh
```

Run from the repo root (needs `caddy` — see the root `README.md`). Puts demo-app, intake-app, joint-session-app, and post-session-app behind one port, `:8080`, with the same path prefixes Render uses live (`/intake/`, `/joint/`, `/post/`) — so a local URL and its live equivalent below differ only in the host, nothing else.

Docs (Roadmap, Status, product spec, pitch page) need a plain file server instead, from the repo root:

```bash
python3 -m http.server 8000
```

## The product

| Page | Local | Live |
|---|---|---|
| Demo hub | [localhost:8080/](http://localhost:8080/) | [mend-mvp.onrender.com/](https://mend-mvp.onrender.com/) |
| Intake | [localhost:8080/intake/](http://localhost:8080/intake/) | [mend-mvp.onrender.com/intake/](https://mend-mvp.onrender.com/intake/) |
| Joint session · Employee A | [localhost:8080/joint/?code=links&role=a](http://localhost:8080/joint/?code=links&role=a) | — not deployed |
| Joint session · Employee B | [localhost:8080/joint/?code=links&role=b](http://localhost:8080/joint/?code=links&role=b) | — not deployed |
| Post-session check-in | [localhost:8080/post/](http://localhost:8080/post/) | — not deployed |

Joint/post-session only exist locally right now — `render.yaml`/`deploy/start.sh` only run demo-app + intake-app. Open both Employee A and Employee B links (two tabs, or send B to someone else) for a real two-person joint session.

## QA / internal tools

| Page | Local | Live |
|---|---|---|
| Thimble states (every avatar state, side by side) | [localhost:8080/intake/static/thimble-states.html](http://localhost:8080/intake/static/thimble-states.html) | [mend-mvp.onrender.com/intake/static/thimble-states.html](https://mend-mvp.onrender.com/intake/static/thimble-states.html) |
| Launchpad (this same link list, as a page) | [localhost:8080/launchpad](http://localhost:8080/launchpad) or [localhost:8000/launchpad.html](http://localhost:8000/launchpad.html) | [mend-mvp.onrender.com/launchpad](https://mend-mvp.onrender.com/launchpad) |

## Documents

| Page | Local | Live |
|---|---|---|
| Product spec | [localhost:8000/product-spec.html](http://localhost:8000/product-spec.html) | — not deployed (see the claude.ai artifact below instead) |
| Pitch page | [localhost:8000/Mend Pitch/Mend Pitch v2.dc.html](<http://localhost:8000/Mend Pitch/Mend Pitch v2.dc.html>) | [mend-mvp.onrender.com/pitch](https://mend-mvp.onrender.com/pitch) |
| Roadmap | [localhost:8000/ROADMAP.md](http://localhost:8000/ROADMAP.md) | — local only |
| Status | [localhost:8000/STATUS.md](http://localhost:8000/STATUS.md) | — local only |
| Public links page (demo-app's own, not this file) | — | [mend-mvp.onrender.com/links](https://mend-mvp.onrender.com/links) |

## Hosted elsewhere (claude.ai, always up, no server needed)

- [Thimble shape options](https://claude.ai/artifact/QxwTAwoqh4GpiYvG5Y5GmF) — the four dome/cone/barrel candidates compared against empathizing's shape
- [Product spec (live artifact)](https://claude.ai/artifact/PRQ4kwizN721tXCAf6ACpt)
- [Workflow diagram](https://claude.ai/artifact/3PmW3kE6ejoq4B8XxS9rH1)
