# Mend joint session prototype (local, two real participants)

A local-only prototype of the joint session, driven by `../facilitator-joint-session-system-prompt.md`. Two separate people connect as Employee A and Employee B over a WebSocket, each only ever seeing what their role should see. In-memory conversation, nothing persisted.

Opening both role links yourself, in two tabs or two browser profiles, still covers solo testing exactly like the old single-user version did — there's no separate "solo mode," it's just this same flow from two windows instead of one.

## What this tests, and what it doesn't

This validates the facilitator's own conversational logic: does it manage turn-taking sensibly, does the routine close read identically whether or not something got flagged, does it actually pause and check in privately when tension rises, does it stay calm and non-confrontational when something serious surfaces.

It does **not** implement the real *audio* hard-cut mechanism from `../joint-session-architecture.md` — the delay buffer that would physically hold back a live audio stream. That's a real-time audio engineering problem a text harness can't exercise. It does now run the real *decision* behind that mechanism (see "The hard-cut classifier" below) — employee-to-employee messages are mutually visible, same as a real joint session, unless that classifier flags one as an active, escalating threat, in which case it's withheld from the other participant entirely, same as the private check-in is.

When the signal panel shows `session_state: "paused_checkin"`, the facilitator's reply is a private aside to whichever employee is named in `checkin_target`. The server actually enforces this now: the other participant's browser only ever receives a neutral "one moment" status, never the content, and their composer is disabled until the check-in resolves. Worth testing directly with two people: does the paused side genuinely learn nothing, and does the room resume without any recap once it's over.

## The room layout and turn-taking

The screen is a small "stage" — Employee A, the Facilitator, Employee B, left to right — above the scrolling transcript, not just a flat chat log. Each turn highlights whoever just spoke, and dims whichever side currently can't speak.

Two separate things gate who can send, both enforced server-side (not just hidden in the UI):
- **The private check-in** (`session_state: "paused_checkin"`) — unchanged from above, fully locks the room to `checkin_target`. The non-addressed side's stage collapses to one neutral overlay covering all three tiles, not a partially-dimmed 3-tile view — showing *which* tile is dimmed would itself leak who's being checked in on, the same class of leak the private-content fix closed last round.
- **General turn-taking** (`next_speaker`, new field in `<mend_signal>`) — the facilitator can hand the floor to one specific person (a direct question, "let's hear from B now") the rest of the time too, not just during a check-in. Unlike the check-in, this is ordinary, visible facilitation — both sides see whose turn it is, same as a mediator turning to address someone. Defaults to `"either"` (floor open, same as before this existed).

A `thinking` status also now covers the several real seconds a Claude API call takes — both composers disable and the facilitator tile pulses, instead of the room just looking idle.

## The hard-cut classifier

Every employee message (outside a private check-in — there's nothing to protect there, the other party already gets nothing) is scored by `../classifier/inference.py`'s `ConflictClassifier`, loaded once at startup against the `mend-conflict-classifier-v3` checkpoint. **v3, not v4** — v4 fixed a real gap (`illegal_activity`) but regressed the metric that actually matters here, `cut_trigger` F1 (0.90 → 0.81); see `../classifier/README.md`'s Results section and commit `314e6c2`.

If it scores a message as cut-worthy: that message is withheld from the other participant entirely (their screen shows nothing — no placeholder, no notice, matching the requirement that a clean end and an escalating one look identical from their side), the facilitator is told a cut just happened (the same `external_cut_reported` hook `facilitator-joint-session-system-prompt.md` already defines), and it moves straight to the routine close. The sender's own screen, and the facilitator's own transcript, are unaffected — only delivery to the other side is cut.

**This is not a validated safety system.** `../classifier/README.md`'s own "Before this goes anywhere near a real session" section applies in full here: small, largely-synthetic training data, an unvalidated 0.9 threshold, no bias audit. Treat a cut firing (or not firing) in testing as exactly that — the current checkpoint's behavior, not a guarantee. If `torch`/`transformers` aren't installed or the checkpoint is missing, this feature just silently disables (`CLASSIFIER_MODEL` stays `None`) and every message is treated as a non-cut, same as before this existed.

`CLASSIFIER_CUT_THRESHOLD` in `.env` overrides the 0.9 default for local testing (e.g. to reliably trigger a cut with milder test phrasing) — this is a testing convenience, not a substitute for the real threshold tuning `classifier/README.md` calls for.

## Prosody proof-of-concept (not live-wired)

`../joint-session-audio/prosody.py` computes tone flags (`pitch_elevated`, `pitch_flattened`, `pace_elevated`, etc.) per audio segment, but that app and this one are still disconnected -- nothing here actually receives them yet (see `../joint-session-audio/README.md`'s "Prosody / tone signal"). Before building that real bridge, `poc_prosody_in_prompt.py` tests the *idea* directly against the real facilitator system prompt and the real model: does annotating a transcript line with prosody.py's actual flag vocabulary change how the facilitator reads it? Not a live integration, just a controlled side-by-side -- same conversation, same everything, branching into two variants that differ in exactly one line's annotation, one real API call per variant.

Run it (costs a few cents in real API calls, not automated):
```bash
python poc_prosody_in_prompt.py
```

Two scenarios, two different findings:
- **A textually-loaded line** ("Fine, whatever you say.", after being told an omission "wasn't intentional") -- text alone already reads as passive-aggressive; the facilitator paused for a check-in either way. The tone-annotated variant committed to `severity_tier: "rising_tension"` explicitly where the baseline run left it `null` despite still pausing -- a real but narrower difference, and this phrase was too textually loaded to cleanly isolate what tone alone adds.
- **A textually-neutral line** ("Sure, I can take care of that too.", agreeing to take on extra work) -- the words carry no negative signal at all. Baseline: the facilitator treated it as an ordinary, untroubled response (`session_state: null`, no pause) and moved on. Tone-annotated (`pitch_flattened`, `pace_slowed`): the facilitator paused for a private check-in (`severity_tier: "rising_tension"`), reading it as someone possibly agreeing under strain rather than freely -- exactly the system prompt's own "Power imbalance" guidance ("if they seem to be going along with something under pressure... that's itself a signal for the rising-tension pause"), triggered here by tone alone, since the text gave it nothing to go on.

**Real, and worth taking seriously, but not a rigorous validation**: two scenarios, one run each -- LLM outputs have real sampling variance (re-running scenario 1 once during this testing gave a different baseline result the second time). This proves the concept has genuine signal, not that these exact numbers/behaviors are reproducible at scale. Enough to justify the real integration work, not enough to skip validating that integration once built.

```bash
cd joint-session-app
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes torch + transformers for the classifier below -- a real, sizable one-time download
cp ../intake-app/.env .env   # reuse the same key, or create a fresh .env with your own
```

## Run

```bash
uvicorn server:app --reload --port 8421
```

Open http://localhost:8421 — it generates a session code and shows you two links, one per role:

    http://localhost:8421/?code=xxxxx&role=a
    http://localhost:8421/?code=xxxxx&role=b

Send the Employee B link to whoever's testing that role (a second person, or your own second tab/profile). The facilitator won't open the session until both roles are connected — the first person to join sees a "waiting for the other participant" state. Each side only ever sees its own composer and whatever the facilitator/other participant sends it; the facilitator responds after every turn, same as before.

Running this as part of the full walkthrough instead of standalone? Use `../run_all.sh` and swap `localhost:8421` for `localhost:8080/joint` in the two role links above — the post-session banner link only resolves correctly when browsed that way (see the repo root `README.md`).

## Voice

Replies are spoken aloud using macOS's built-in `say` (voice `Samantha`) by default — noticeably robotic. For a much better-sounding voice, add an OpenAI key to `.env`:

```
OPENAI_API_KEY=sk-...
```

`synthesize_speech` then tries OpenAI's TTS (`gpt-4o-mini-tts`) first and only falls back to `say` if that call fails, same pattern as `../intake-app`. Pick a different voice with `OPENAI_TTS_VOICE` in `.env` (default `alloy`; also available: `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`, `verse`, `marin`, `cedar`).
