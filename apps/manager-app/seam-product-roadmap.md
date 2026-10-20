# Seam (manager-app) — Product Roadmap

Seam is the manager app: solo coaching/practice for a manager preparing for
or rehearsing a hard conversation with a direct report, or a
case-management space for a manager working through conflict between two
members of their team. Product-facing name "Seam" as of 2026-10-17; the
in-app persona/AI the manager talks to is still "Thimble" (see
`PHILOSOPHY.md` and `THIMBLE_MINDSET.md` in this folder).

Per the 2026-10-17 app-concept ranking in `../../IDEAS.md`, Seam ranks #1 of
the seven app codenames: real buyer with budget (manager/L&D training
spend), no invite-friction problem (solo, manager-initiated for their own
benefit), solid moat from the same outcome-tuning as Thimble/Suture.

**2026-10-19 pitch session**: see
`../../docs/pitch-strategy/24_SEAM_PRODUCT_PITCH_AND_ADOPTION_STRATEGY.md`
for an idea-stage (not yet committed to the phases below) proposal to make
Seam the primary product, with Thimble/Suture/Loom embedded as scoped
manager-facing features and a three-tier manager-cascade distribution
model (skip-level → manager → employee) replacing single-tier pilot
rollout.

For shared, cross-app positioning principles, see the root
`../../ROADMAP.md`. Before adding any feature here, check it against the
scope boundary in `PHILOSOPHY.md`'s "What Mend is not" list (not a
note-taker, not a productivity tracker, not a tone nanny, not an
administrative copilot) — several of the Phase 2 items below are exactly
the kind of feature that needs that check first.

## Phase 0 — Local prototype (done)

- [x] Sketched, mocked (`App.dc.html`/`canvas.json`), and the underlying
      philosophy/workflow/facilitator mindset written up
      (`PHILOSOPHY.md`/`WORKFLOW.md`/`THIMBLE_MINDSET.md`)
- [x] Real backend, wiring `THIMBLE_MINDSET.md` into an actual system
      prompt the way the other apps' `facilitator-*-system-prompt.md`
      files do (`facilitator-case-plan-system-prompt.md`)
- [x] "Managing up" translator and the decoupled hand-off into a peer-to-
      peer Suture session, wired as real actions (not just prompt text
      telling Thimble to offer them)
- [x] Core thesis, moat-vs-ChatGPT/Copilot framing, commercial pricing
      model, and self-actualization scope boundary written up (2026-10-19
      pitch-strategy session): see
      `../../docs/pitch-strategy/00_LIVE_MEETING_AI_COACH.md`,
      `../../docs/pitch-strategy/02_COMMERCIAL_PRICING_STRATEGY.md`,
      `../../docs/pitch-strategy/03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md`,
      and this folder's `PHILOSOPHY.md`

## Phase 1 — On-cycle retention (not yet built)

The core open problem identified 2026-10-19: real conflict is not a daily,
weekly, or even monthly occurrence for most managers, so a tool that's only
useful during an acute dispute gets forgotten between incidents. Seam needs
a reason to already be open before the conflict happens. See
`../../docs/pitch-strategy/00_LIVE_MEETING_AI_COACH.md`'s "Awkwardness
Barrier" and "On-Cycle Touchpoints" sections for the full writeup.

- [ ] Bi-weekly 1-on-1 prep and agenda de-biasing
- [ ] Pre-sprint cross-functional handoff and dependency mapping
- [ ] Async tone-check for high-stakes Slack announcements or emails
- [ ] Calibration- and promotion-cycle narrative framing
- [ ] Quarterly blameless retro and post-mortem ingestion

## Phase 2 — Calendar-aware pre/post-meeting workflow (not yet built, needs scope check)

Speculative, from the same 2026-10-19 session. Each item needs to be
checked against `PHILOSOPHY.md`'s "What Mend is not" boundary before being
committed to — the risk flagged there is this workflow drifting into a
meeting-note-taker/summarizer, which is explicitly out of scope.

- [ ] Calendar scanning — read upcoming 1-on-1s and cross-team syncs to
      identify meeting type and attendee roles
- [ ] Pre-meeting intent calibration — prompt the manager shortly before a
      meeting to name desired outcomes, boundaries, and decisions needed
- [ ] Stakeholder constraint injection — surface attendees' known role
      metrics and likely friction points
- [ ] Opening rail generation — 2-3 short framing phrases handed to the
      manager before the call, not read to them live
- [ ] Live ambient HUD during the meeting (tempo, talk-time, agenda pings,
      deflection alerts) — pre-baked cues only, never live-generated text
      read aloud (see the "live-meeting AI coach" feasibility analysis for
      why a live teleprompter fails)
- [ ] Edge audio processing (local/in-enclave, volatile memory, never a
      cloud recording bot) for action-item and SLA extraction
- [ ] **RE-SCOPE NEEDED (2026-10-19)**: ~~Role-anonymized case logging
      into the existing case-state anchor (`cases.db`)... no raw audio or
      transcript ever stored~~ — anonymization and transcript-exclusion
      are not sufficient. The existence of a queryable record that a
      conflict involving a specific employee happened, when, and what
      category, is itself the trust problem, independent of content.
      Employees expect a disappearing conversation (same norm as a
      manager informally discussing them with their own manager) but
      would be rightly angry about a persistent log, even anonymized. See
      `../../docs/pitch-strategy/24_SEAM_PRODUCT_PITCH_AND_ADOPTION_STRATEGY.md`
      §7-8 for the resolution: **never retain the conversation, only ever
      the resulting action item** ("talk to employee X about Y" — the
      same action-plan output Suture already produces), encrypted at
      rest and decrypted only transiently inside an isolated/enclave
      process for a single inference call, never logged or human-legible
      to anyone including Mend's own staff. Still not decided: server-
      side (encrypted, enclave-mediated) vs. client/device-side-only
      storage — a real engineering tradeoff, not yet resolved.
- [ ] Follow-up communication staging — pre-drafted, de-biased summary for
      Slack/email

## Phase 3 — Go-to-market

- [ ] Validate L&D/coaching-stipend buyer path
      ($200-500/yr line item) against a real deal, not just modeled — see
      `../../docs/pitch-strategy/02_COMMERCIAL_PRICING_STRATEGY.md`
- [ ] Pitch-test the moat-vs-ChatGPT/Copilot framing
      (`../../docs/pitch-strategy/03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md`)
      with real managers, not just reasoned from first principles
