# Roadmap

Structural, phase-level view — what needs to be true before the next phase starts. For the rolling "what happened recently" log, see `STATUS.md` instead; this file changes rarely, that one changes often. Check a box when the item is actually done and verified, not just attempted. For raw, not-yet-committed ideas (not phase-level work), see `IDEAS.md` instead.

## Phase 0 — Local prototypes (mostly done)

- [x] Intake → joint session → post-session flow, working end-to-end locally
- [x] Real hard-cut classifier (`classifier/`), wired into `joint-session-app`
- [x] Real signup/invite backend (`demo-app`), direct and peer-suggested
- [x] Unified local proxy (`run_all.sh` + `Caddyfile`)
- [x] Brand identity applied everywhere (logo, Pink/Evergreen/Honey/Oat, Manrope)
- [x] `manager-coaching-app` — fifth prototype, manager-side hard-conversation coaching
- [ ] `manager-coaching-app` real conversation-quality test with a live API key (server verified, persona/floor-logic not yet tried against a real model reply)
- [x] `manager-app` — sketched, mocked (`App.dc.html`/`canvas.json`), and the underlying philosophy/workflow/facilitator mindset written up (`PHILOSOPHY.md`/`WORKFLOW.md`/`THIMBLE_MINDSET.md`)
- [x] `manager-app` real backend, wiring `THIMBLE_MINDSET.md` into an actual system prompt the way the other apps' `facilitator-*-system-prompt.md` files do
- [x] `manager-app`: "managing up" translator and the decoupled hand-off into a peer-to-peer session, wired as real actions (not just prompt text telling Thimble to offer them)
- [ ] `intake-app`: Playwright smoke test for `session.html` (`tests/session_smoke_test.py`), mirroring `tests/button_smoke_test.py`'s coverage of `index.html` — mobile FAB opens/closes the voice modal (button, backdrop click, Escape), top nav doesn't overflow at 375px, desktop pane hide/show toggles, "Start over" overflow menu renders fully on-screen (regression guard), captions + avatar animation active inside the modal

## Phase 1 — Real-time audio/video, one voice-driven session

`joint-session-audio/` and `joint-session-app` are still two independently-run prototypes an operator starts by hand under the same code. This phase is the merge.

- [x] Real audio delay buffer (LiveKit + streaming STT + the hard-cut classifier)
- [x] Symmetric video opt-in (parity enforcement, not just UI)
- [x] LiveKit private breakout/side-conversation room (transport only)
- [x] Prosody/tone signal, proof-of-concept validated, wired into the facilitator LLM
- [ ] Facilitator voice for the breakout room (private check-in track is currently inert — no TTS, no live decision logic)
- [ ] Merge `joint-session-audio` and `joint-session-app` into one voice-driven session (STT transcript replacing typed messages, facilitator TTS carrying replies to both employees)
- [ ] Real camera hardware test for video opt-in (parity logic proven, live camera revocation never exercised — this dev environment has no camera)
- [ ] `pitch_flattened` validated against genuine human deadpan/sarcastic speech (TTS can't fake real flat affect; needs a real mic, which this dev environment doesn't have)

## Phase 2 — Classifier trustworthiness

- [x] Per-class loss weighting tried (found: fixes recall, hurts precision — wrong lever for `v4`'s actual regression)
- [ ] Gentler weighting curve, or weight only the one starved class (`immediate_safety_risk`) instead of all five
- [ ] Human review of batches 4/5/6 (378 examples queued in `classifier/data/review_page.html`, not yet judged)
- [ ] Bias audit (no protected-characteristic skew check has been done on any checkpoint yet)
- [ ] Real threshold tuning against an actual precision/recall curve (still the 0.9 default guess)

## Phase 3 — Ready for a real pilot

- [ ] `intake-app`: anonymized HR escalation send (employee-conflict path floor-met, with employee consent). Not needed for the current blind-tester phase — no real HR is acting on output during testing (see `STATUS.md`'s active-goal note), so this stays a Phase 3 gate, not something to pull forward. Prompt already updated (`facilitator-intake-system-prompt.md`) to disclose the floor to the employee and ask consent before sending; backend send path not built — no email/Slack/webhook integration exists yet (confirmed: current code only tells the employee, never contacts HR). Full design, from a 2026-10-10 session working through live bugs in the floor-escalation flow:
  - Consented send builds an anonymized payload (category + severity + timestamp only, no name/session_id/quotes, same as today's spec) and mints a random, unguessable token mapped server-side to that payload (not to the employee's identity or session), with an expiry.
  - An email goes to a configured HR/manager address with a link carrying that token.
  - The link opens a **new, separate** conversation, not linked to the employee's own session, seeded with a new, smaller system prompt (e.g. `facilitator-hr-escalation-system-prompt.md`): states the category/severity plainly, answers process questions, and firmly redirects any "what's our legal exposure" question to real employment counsel, reusing the main prompt's existing hard rule that Thimble never claims something is or isn't legally protected or discoverable. No legal-avenue advice from Thimble in that session, by explicit decision.
  - No transcript storage either way, matching existing behavior.
  - Still open, needs a decision before building: email provider (SMTP/SendGrid/Gmail API); recipient config (one fixed HR email via env var for a single-org MVP, vs. per-customer config); token lifetime and whether it's single-use or reusable within that window.
- [ ] GitHub account unsuspended, or an alternative remote/host chosen
- [ ] `trymend.solutions` actually hosting the pitch page
- [ ] Real employment counsel engaged (`docs/pitch-strategy/10_LEGAL_COUNSEL_OUTREACH.md` drafted, not sent)
- [ ] Trigger-category legal review (`product-spec.html` Section 10 — the floor categories are illustrative, not a finished legal standard)
- [ ] Confidential-computing / proof-tier story built out (`product-spec.html` calls this "a genuine, achievable differentiator... once 'provably private' becomes central to the pitch")

## Phase 4 — Go-to-market

Tracked in more detail in `docs/pitch-strategy/`, not duplicated here:

- [ ] HR/buyer outreach (`06_HR_BUYER_OUTREACH_STRATEGY.md`)
- [ ] Pilot cohort selected and testing plan run (`05_USER_TESTING_AND_COHORT_STRATEGY.md`)
- [ ] Pricing validated against a real deal, not just modeled (`02_COMMERCIAL_PRICING_STRATEGY.md`)
