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

- [ ] Bi-weekly 1-on-1 prep and agenda de-biasing — **superseded 2026-10-20
      by "Meeting Strategy" below, scoped wider than just 1-on-1s**
- [ ] Pre-sprint cross-functional handoff and dependency mapping
- [ ] Async tone-check for high-stakes Slack announcements or emails —
      **scoped 2026-10-20, see below**
- [ ] Calibration- and promotion-cycle narrative framing
- [ ] Quarterly blameless retro and post-mortem ingestion

### 2026-10-20 MVP cut: four features scoped for the current build

Out of the Phase 1/2 lists plus the bundle ideas in
`../../docs/pitch-strategy/24_SEAM_PRODUCT_PITCH_AND_ADOPTION_STRATEGY.md`,
four features were picked as the MVP to actually build next, each scoped
through a Q&A pass with the user. This section is the build spec; a
parallel chat is doing UI/visual design against this same spec, so keep it
current as scope changes rather than letting the two drift.

**1. Meeting Strategy** (renamed from "1-on-1 prep and agenda de-biasing")
- Explicitly **not** a task list or productivity tool. Works at the level
  of meeting strategy, not meeting tactics: a manager names a goal for a
  meeting (team cohesion, delivering hard news, a pep talk, addressing a
  known team issue, planning a team-building exercise, or anything else),
  and Thimble helps them figure out how to actually achieve it.
- Scope: **any meeting a manager runs**, not just 1-on-1s (team meetings,
  all-hands, whatever has a goal) — deliberately wider than the original
  Phase 1 item.
- Interaction: fully open-ended chat, no preset goal picklist — the
  manager describes the meeting and goal in their own words, Thimble asks
  questions to build the approach (same three-beat-adjacent facilitation
  style as the case-plan flow, but tuned for forward-looking strategy
  rather than conflict diagnosis).
- Output: a written strategy / talking points artifact the manager can
  glance at before or during the meeting — not just the chat transcript.
- Output **persists** so the manager can reopen and re-read past
  strategies (unlike the raw chat, which stays ephemeral, same treatment
  as case conversations).
- Standalone entry point: **not** nested inside the existing case system
  (no conflict case required to use this).
- No enforced recurrence/reminders in this version — manager opens it
  whenever they want; bi-weekly scheduling/notifications explicitly out of
  scope for now.
- Build shape (mirrors the existing case-plan pattern in `server.py`):
  - New system prompt file, `../facilitator-meeting-strategy-system-prompt.md`
    (sibling to `facilitator-case-plan-system-prompt.md`), tuned for
    strategy coaching rather than conflict mediation.
  - New table `meeting_sessions` (id, title, goal_summary, strategy_text,
    created_at, updated_at) in `cases.db` — same persistence pattern as
    `cases`, but without conflict-specific fields (no tension_summary,
    floor_triggered, handoff).
  - New routes: `POST /api/meeting-sessions`, `POST
    /api/meeting-sessions/{id}/messages`, `GET
    /api/meeting-sessions/{id}` — same shape as the existing case routes.
  - The back-and-forth chat itself stays in-memory only (same
    `CONVERSATIONS` pattern already used for cases); only the final
    strategy text gets written to the DB.

**2. Action-item-only persistence (conflict-case continuity)** — already
built, no new work needed. `plan_steps` already persists server-side,
plaintext, survives a restart; the raw conversation (`CONVERSATIONS`)
stays in-memory only and is lost on restart. That's already the "never
retain the conversation, only the resulting action item" split from
`../../docs/pitch-strategy/24_SEAM_PRODUCT_PITCH_AND_ADOPTION_STRATEGY.md`
§7-8 — confirmed as the intended MVP design (server DB, plaintext, defer
enclave encryption to later). Not tied to Meeting Strategy's action items;
this is specifically about conflict-case plan steps.

**3. Suture handoff — real two-person test** — no known code gap, the
`/api/cases/{case_id}/handoff` route already exists. Needs a real dry run
(two browsers, two roles) to find what actually breaks before trusting it
for a pilot. Not scheduled yet; the user will run this themselves once
ready, not before.

**4. Tone-check** — in progress as of 2026-10-20.
- Deliberately **not** deficit-flagging ("this sounds harsh"). Instead
  checks whether a draft message reads as coming from someone emotionally
  regulated, secure, and competent — positive-signal framing, not a list
  of flaws.
- Input: manager pastes a draft (email/Slack message/etc.) into Seam.
  Photo/screenshot input considered and explicitly rejected for MVP (extra
  OCR/vision build cost for little gain over paste, since drafts already
  exist as text before sending) — revisit only if real usage shows paste
  friction.
- Output: feedback **and** a suggested rewrite (not feedback-only).
- Stateless: no persistence, no case/session tie-in, one-shot request/response.
- Build shape:
  - New system prompt file, `../facilitator-tone-check-system-prompt.md`.
  - New route `POST /api/tone-check`, takes raw draft text, returns
    `{feedback, rewrite}`. No DB write at all.

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
- [ ] Run the solo-manager tester/buyer outreach plan (not 05's pairs-based
      plan — Seam's MVP surface is solo) — see
      `../../docs/pitch-strategy/25_SEAM_SOLO_MANAGER_COHORT_AND_OUTREACH_STRATEGY.md`
