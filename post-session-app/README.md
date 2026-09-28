# Mend post-session prototype (local)

A local-only prototype of the post-session follow-up, driven by `../facilitator-post-session-system-prompt.md`. Single-user, in-memory conversation, nothing persisted.

Since this conversation normally starts with context from a joint session that already happened, and this harness doesn't chain to a real run of `../joint-session-app/`, you configure a small scenario first: whether anything escalated (nobody's / this employee's own conduct / the other party's), which category, and optional free-text context. That gets folded into the kickoff message so the facilitator has something real to work from.

## Setup

```bash
cd post-session-app
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../intake-app/.env .env   # reuse the same key, or create a fresh one
```

## Run

```bash
uvicorn server:app --reload --port 8422
```

Open http://localhost:8422, set the scenario, hit Start.

Running this as part of the full walkthrough instead of standalone? Use `../run_all.sh` and open http://localhost:8080/post/ instead (see the repo root `README.md`).

## What to actually test

- **Escalation disclosure comes first, plainly, calmly** — pick "own conduct" or "other party's conduct" escalated and check it doesn't get buried under small talk or soften into ambiguity.
- **Resolution isn't rushed or forced** — try being uncertain, or say the apology from the room doesn't actually land for you now that you're alone; it should take that seriously, not push you toward a tidy "resolved."
- **Skill-building suggestions stay optional and private** — framed as yours to act on, never as something being reported anywhere.
- **"Reopened" is a legitimate outcome** — try coming back and saying a resolution from before didn't actually hold.
