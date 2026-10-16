# Group session app (prototype)

UI option A from the group-session design review: several strangers (e.g. 6
OSS contributors stuck on one issue) join one room, see each other on
video, talk or type, and vote on proposed resolutions.

In-memory, single room, no auth -- a prototype to test the interaction
pattern, not a deployable multi-tenant service.

## What's real

- One shared room, live over WebSocket: every joined tab sees the same
  participant list, chat log, and proposals/votes update instantly.
- Proposals and votes are real state (`server.py`'s `Room`), not canned
  numbers: anyone can add a proposal, anyone can vote yes/no/abstain, the
  tally is computed from actual votes.
- Each tab's own camera tile is a real `getUserMedia` local preview.

## What's not real (yet)

- **No peer-to-peer video.** Other participants' tiles are initials
  placeholders, not their actual camera. There's no signaling server or
  SFU here. Wiring real multi-party video needs a provider (LiveKit or
  Daily), per `../joint-session-architecture.md`'s own reasoning for why
  that transport layer is rented, not built from scratch -- deliberately
  out of scope for this prototype.
- **No speaking detection.** The "speaking" highlight exists in the data
  model (`Participant.speaking` / `/api/speaking`) but nothing currently
  calls it from the client; it's wired for whenever real audio shows up.
- **No persistence, no auth, no room codes.** One room, in memory, lost on
  restart -- same convention as every other app in this repo.

## Run

```
pip install -r requirements.txt
uvicorn server:app --reload --port 8440
```

Open `http://localhost:8440` in several tabs (or on several machines on the
same LAN) to simulate several participants in the same room.
