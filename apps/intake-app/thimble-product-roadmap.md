# Thimble (intake-app) — Product Roadmap

Thimble is the solo conflict-resolution app overall (intake → joint
session), the main focus of the repo so far. Maps to `intake-app` +
`joint-session-app`/`joint-session-audio` (the live joint-session half of
this pipeline, "Suture," has its own roadmap at
`../joint-session-app/suture-product-roadmap.md`; this file covers the
intake/solo side and the pipeline as a whole).

For shared, cross-app positioning principles (trust moat, pricing floor,
"no paper trail is the feature"), see the root `../../ROADMAP.md`. For raw,
not-yet-committed ideas, see the root `../../IDEAS.md`.

## Phase 0 — Local prototypes (done)

- [x] Intake → joint session → post-session flow, working end-to-end
      locally
- [x] (obsolete, 2026-10-17) The standalone `manager-coaching-app` prototype
      was removed — its path was folded into `intake-app`'s own system
      prompt instead (detected from the conversation itself; see
      `facilitator-intake-system-prompt.md`). The conversation-quality
      question now applies to `intake-app`'s manager-coaching path, not
      tracked as its own item.

## Phase 1 — Test coverage

- [ ] Playwright smoke test for `session.html`
      (`tests/session_smoke_test.py`), mirroring `tests/button_smoke_test.py`'s
      coverage of `index.html`: mobile FAB opens/closes the voice modal
      (button, backdrop click, Escape), top nav doesn't overflow at 375px,
      desktop pane hide/show toggles, "Start over" overflow menu renders
      fully on-screen (regression guard), captions + avatar animation
      active inside the modal.

## Phase 2 — Ready for a real pilot

- [ ] Anonymized HR escalation send (employee-conflict path floor-met, with
      employee consent). Not needed for the current blind-tester phase — no
      real HR is acting on output during testing (see root `STATUS.md`'s
      active-goal note), so this stays a pilot-readiness gate, not
      something to pull forward. Prompt already updated
      (`facilitator-intake-system-prompt.md`) to disclose the floor to the
      employee and ask consent before sending; backend send path not built —
      no email/Slack/webhook integration exists yet. Full design, from a
      2026-10-10 session working through live bugs in the floor-escalation
      flow:
  - Consented send builds an anonymized payload (category + severity +
    timestamp only, no name/session_id/quotes) and mints a random,
    unguessable token mapped server-side to that payload (not to the
    employee's identity or session), with an expiry.
  - An email goes to a configured HR/manager address with a link carrying
    that token.
  - The link opens a **new, separate** conversation, not linked to the
    employee's own session, seeded with a new, smaller system prompt (e.g.
    `facilitator-hr-escalation-system-prompt.md`): states the
    category/severity plainly, answers process questions, and firmly
    redirects any "what's our legal exposure" question to real employment
    counsel. No legal-avenue advice from Thimble in that session, by
    explicit decision.
  - No transcript storage either way, matching existing behavior.
  - Still open, needs a decision before building: email provider
    (SMTP/SendGrid/Gmail API); recipient config (one fixed HR email via env
    var for a single-org MVP, vs. per-customer config); token lifetime and
    whether it's single-use or reusable within that window.

## Open design questions

- Disclose safety-floor screening upfront, or only reactively? Current lean
  is "disclose upfront, briefly," but still marked open in
  `facilitator-persona.md`. Whichever `facilitator-*-system-prompt.md`
  handles the first disclosure (currently the intake prompt) is where this
  lands once decided.
