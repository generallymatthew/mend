# Mend joint session prototype (local, you play both employees)

A local-only prototype of the joint session, driven by `../facilitator-joint-session-system-prompt.md`. You play both Employee A and Employee B yourself, switching hats, so you can test the facilitator's behavior without needing a second real person. Single-user, in-memory conversation, nothing persisted.

## What this tests, and what it doesn't

This validates the facilitator's own conversational logic: does it manage turn-taking sensibly, does the routine close read identically whether or not something got flagged, does it actually pause and check in privately when tension rises, does it stay calm and non-confrontational when something serious surfaces.

It does **not** implement the real hard-cut mechanism from `../joint-session-architecture.md` — the audio delay buffer and fast classifier that would physically stop a live threat from reaching the other person. That's a real-time audio engineering problem a text harness can't exercise. This only tests what the facilitator itself decides to say.

When the signal panel shows `session_state: "paused_checkin"`, the facilitator's reply is a private aside to whichever employee is named in `checkin_target`. In a real deployment the other employee would never see that message. This harness shows it to you anyway (marked "(private aside)") since you're the only person testing — but it's worth checking that the facilitator actually behaves as if the other person can't hear it.

## Setup

```bash
cd joint-session-app
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../intake-app/.env .env   # reuse the same key, or create a fresh .env with your own
```

## Run

```bash
uvicorn server:app --reload --port 8421
```

Open http://localhost:8421. Type as Employee A or Employee B in their respective boxes — the facilitator responds after every single turn, same as it would in a real session managing the room.
