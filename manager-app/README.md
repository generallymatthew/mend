# manager-app (product name: Loom)

The product-facing name for this app is **Loom**, from "weaving" teams back into a working relationship rather than just mediating a one-off dispute. The directory and file names stay `manager-app` throughout the codebase; only the UI (page title, sidebar brand lockup, help copy) shows "Loom."

A conflict-case manager for people managers, not employees. A manager opens a case about a direct report in conflict (with a peer, with someone on another team, or with another direct report), talks it through with Thimble as one continuous chat, and keeps a running plan of agreed next steps. See `STATUS.md`'s "New product idea sketched and mocked: `manager-app`" entry for the original design writeup, and the docs below for the fuller reasoning:

- `PHILOSOPHY.md`: the product philosophy, conflict as task/process/relationship, why task conflict mutates into personal conflict, why peer-led resolution outlasts managerial arbitration, and the core reframe (action plan, not "conflict resolution").
- `WORKFLOW.md`: the concrete manager-facing flow, the step-by-step action-plan pattern, case-state persistence without breaking anonymity, and the decoupled hand-off into a peer-to-peer session.
- `THIMBLE_MINDSET.md`: the design-conversation notes this app's facilitator persona is drawn from. The actual running prompt is `../facilitator-case-plan-system-prompt.md`, which integrates this with `PHILOSOPHY.md` and `WORKFLOW.md`.
- `App.dc.html` / `canvas.json`: the original UI mockup, authored as a Claude Artifact (Design canvas). The real frontend is `static/index.html`, which implements the same two-pane chat layout plus the right-side "plan so far" panel. The mockup is kept for reference; its live editable version is at https://claude.ai/artifact/8HrMPhjifgqAUiKVzPHx2L, and it won't render standalone (it references `./support.js`, a runtime only the Artifact page provides).

## What's real here

A working FastAPI backend plus a plain HTML/JS frontend, single-user, local-only, no build step, same pattern as this repo's other small apps (`../intake-app`, `../manager-coaching-app`). Text only, no voice.

Persistence is deliberately narrow, matching `WORKFLOW.md`'s anonymity design: each case's SQLite record holds only a role-anonymized state anchor (`tension_summary` / `last_action` / `next_action`, written by the facilitator itself via its `<mend_signal>` block) and the plan steps, never a transcript and never a name. The actual conversation text lives only in the running server process's memory and is lost on restart; reopening a case after a restart re-seeds a fresh conversation from the stored anchor and plan instead of replaying old messages, so Thimble still picks the case back up without needing the exact prior wording.

Verified live against the real Claude API: creating a case, getting the opening line ("What's going on?"), a multi-turn conversation that correctly built up `tension_summary` while never storing a name, and plan-step add/toggle/note all round-tripped correctly. Caught and fixed one real bug this way: an early version of the system prompt let the facilitator's own reply text echo back a name the manager had used ("what did Marcus's feedback look like"), even though the persisted anchor was already correctly role-based. The prompt now says explicitly this applies to every reply, not just what gets saved, and a retest confirmed it holds.

One of `WORKFLOW.md`'s remaining pieces is wired in as a real action, not just prompt text:

- **Peer-session hand-off.** The facilitator sets `handoff_ready: true` in its `<mend_signal>` block on the turn it actually offers the hand-off (see `facilitator-case-plan-system-prompt.md`), which surfaces a "Start peer session" banner. Clicking it hits `POST /api/cases/{id}/handoff`, which mints a `joint-session-app` room code and returns two role links (`?code=...&role=a` / `role=b`) -- the same link pattern `joint-session-app` already uses for manual pairing. No case context crosses over: the two employees land in a brand-new joint session with zero knowledge of the manager's notes, matching `WORKFLOW.md`'s "zero context leakage" guarantee. The code is idempotent per case (stored as `handoff_code`), so reopening the case or the banner shows the same links rather than minting a new room. `joint-session-app` must be running (`JOINT_SESSION_BASE_URL` env var, defaults to `http://localhost:8421`) for the links to resolve; this app doesn't start it for you.

Not yet built: anything that reports the peer session's binary resolved/not-resolved status back to the manager's case -- `joint-session-app` has no mechanism today to notify anything on completion, so that's still a manual follow-up conversation, not wired automatically.

The "managing up" translator (`WORKFLOW.md`'s executive-update scripting) stays purely conversational, no dedicated button: the facilitator prompt's own "Managing up, on request" section already tells Thimble to produce the scripted update when the manager asks for it in chat, which needs no app-level wiring to work.

## Setup

```bash
cd manager-app
python3.11 -m venv .venv   # or any Python 3.10-3.12
source .venv/bin/activate
pip install -r requirements.txt
```

You need your own Anthropic API key (from console.anthropic.com). Create a file called `.env` in this directory (it's git-ignored, never commit it or paste it anywhere else) containing:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
uvicorn server:app --reload --port 8426
```

Open http://localhost:8426 in a browser. Click the `+` next to "Cases" to start a new one; Thimble opens with "What's going on?"

`cases.db` (SQLite, git-ignored) is created in this directory on first run.
