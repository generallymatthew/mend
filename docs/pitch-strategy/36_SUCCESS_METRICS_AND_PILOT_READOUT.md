# Success Metrics & Pilot Readout

Captured 2026-11-27 from a brainstorm on how a company (and we) would know
Thimble is working, given that HR can never read transcripts, see who used
it, or know who is in conflict with whom. Started from a pasted Gemini
conversation proposing a 90-day HR scorecard; this doc keeps what survived
review and records what was rejected and why.

## 1. The rule: count actions, never content

Every metric here is either a count of something a person did (opened it,
finished, copied a plan, came back, renewed) or a one-tap answer the person
chose to give. Nothing is derived from what anyone said.

This rules out several metrics that sound good but break zero-trace:

- **"Structural reframe rate" / "attribution flip"** (share of sessions that
  moved from blaming a person to naming a process gap). Requires classifying
  conversation content and keeping the result.
- **Speed to resolution** (timestamp from intake to agreement). Requires
  linking sessions to a person over time.
- **Theme heatmaps for HR** ("35% of friction is about unclear handoffs").
  Content analysis, and on small teams "de-identified" themes point straight
  at people. If employees believe HR sees themes, they stop being honest and
  adoption collapses. Structural themes belong in Thimble Retro (Loom), which
  already has a minimum-contributor floor built for exactly this, not in
  Thimble Resolve.

Content-derived measures like attribution shift are still fine in controlled
user testing with consenting testers (see
[33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md](33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md) §2),
just never in a customer deployment.

## 2. Why not macro HR metrics

Retention, engagement scores, and HR ticket volume move for a dozen
unrelated reasons (a reorg, a bad quarter, a new manager). Thimble can be
genuinely useful while none of them move in 90 days. Promising them sets up
a pilot to "fail" on noise. Don't put them in a success target.

## 3. The metric set

Strongest first.

### Outcome proxies (closest to "it worked")

1. **"Did you have the conversation?"** Next time someone opens Thimble on
   the same device, ask about their last session: *Had it / Not yet /
   Decided not to.* The real cost of conflict is avoidance, so a hard
   conversation happening sooner is the outcome being sold. The device
   stores only "there was a session on this date"; only the anonymous tally
   leaves the device.
2. **"How did it go?"** Same moment, one tap: *Better than I expected /
   About what I expected / Worse.* Self-reported, but it measures the real
   meeting, not how the app felt.
3. **Renewal and seat growth.** At $20/month per team and $5/employee/month
   company-wide, this is the most honest signal available. A manager who
   keeps paying, or a company that grows from one team to three, needs no
   survey.

### Engagement proxies (in product, no content)

4. **Plan copied or exported.** Tapping "copy" on the opening line or plan
   signals intent to use it. Stronger than session length.
5. **Finished vs. dropped early.** Leaving after 1-2 turns is a bad sign;
   reaching the plan step is a good one. Event counts only.
6. **Return on the same device.** The device sends a "has used this before"
   boolean, nothing else. Unprompted return is the best trust signal and the
   direct answer to "will anyone use it?"
7. **Sharing.** Clicks on a "send Thimble to a colleague" link, or visits
   arriving through one.

### Organization-level (outside the product, cheap)

8. **Manager confidence pulse.** One anonymous question at start and at day
   60: "How prepared do you feel going into a hard conversation?"
9. **HRBP rough count.** "About how many small interpersonal issues reached
   you this month?" Noisy, but free, and HR will want one number of its own.

**If only three:** #1 (did you have the conversation), #6 (return use), #3
(renewal). One shows the outcome, one shows trust, one shows money.

### Caveats

- #1 and #2 have selection bias: people whose meetings went well are more
  likely to come back and answer. Always report response count next to the
  result.
- One team of 8 produces anecdotes, not statistics. Fine for a pilot; don't
  present percentages as if they were significant.
- Build cost: `session.html` already logs a `session_end` analytics event,
  so #4-#6 are small additions. #1 and #2 need device-local storage plus a
  prompt on next open: a small feature, not built yet.

## 4. The pilot readout

Replace the 90-day, six-target HR scorecard with something sized to the
price. A $20/month team pilot doesn't warrant a Finance review; the buyer is
one manager with a card. The readout is a short page:

- How many people used it, how many came back (#6)
- Of those who answered, how many had the conversation, and how it went
  (#1, #2, with response counts)
- Plans copied (#4)
- Safety-floor escalations: count only
- Confidence pulse before/after if it was run (#8)

A heavier scorecard can come later if a company-wide buyer asks for one.
This supersedes the "shifted attribution in Y% of cases" readout line in
[06_HR_BUYER_OUTREACH_STRATEGY.md](06_HR_BUYER_OUTREACH_STRATEGY.md) §5.

## 5. Adoption positioning that came out of the same brainstorm

Two ideas (both the founder's) answer "why would anyone open this?":

- **Meeting prep.** Every hard conversation is a meeting first. People don't
  wake up wanting conflict resolution; they dread a 2pm 1:1. Pitched as prep
  for hard meetings, Thimble carries no stigma, and managers become the core
  users. Seam's Meeting Strategy already does this, so it's a positioning
  change, not new build work.
  - Guardrail: "prep for a 1:1 with an underperforming report" can turn
    Thimble into a tool for building a case against an IC. The prep flow has
    to ask the manager whether the underperformance comes from the setup
    (unclear expectations, overload, conflicting priorities). That question
    is also the difference from asking ChatGPT. See
    [30_FOUNDER_MANIFESTO_AND_CORE_PHILOSOPHY.md](30_FOUNDER_MANIFESTO_AND_CORE_PHILOSOPHY.md).
- **Shadow AI.** HR's reason to promote it that has nothing to do with
  conflict: "stop pasting work situations into personal AI accounts; use
  this instead." It also gives IT and Legal a risk they already worry about
  (see [33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md](33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md) §1).

### Rollout copy: keep it accurate

Gemini's draft HR message overclaimed. What's true today:

- **OK:** "saves no transcripts," "doesn't report back to us," "no account
  needed." Conversations are cleared on tab close and after 30 minutes idle
  (fixed 2026-11-18).
- **Not OK:** "saves nothing" (Seam keeps meeting titles, goals, and strategy
  text as metadata), "nothing leaves" (text passes through the model
  provider), "zero prompts leaked to public AI" (unmeasurable).
- Say "use this on any device," not "use your phone": HR telling people to
  put work data on personal phones will worry IT.
- Avoid resilience framing ("tested resilience over polite silence"). The
  problem is institutional, not people coping badly.

## 6. Statistics from the source conversation: don't cite unverified

- "Ombuds offices see 80%+ voluntary usage": either trivially true (all
  ombuds visits are voluntary) or misleading (not 80% of employees). Don't use.
- "HRBPs lose 30-50% of bandwidth refereeing," "managers spend 3-5
  hrs/week," "BetterUp/Lyra lifted utilization 3x-5x": unsourced. Verify or drop.
- CPP Inc. (2008), roughly 2.8 hours per employee per week spent on
  conflict: real and citable (see
  [20_REMOTE_CONFLICT_RESEARCH_AND_STATISTICS.md](20_REMOTE_CONFLICT_RESEARCH_AND_STATISTICS.md)).

## Status

Working notes, 2026-11-27. Metrics #1, #2, #4, #6, #7 are not built. Next
step is unchanged from doc 06: one warm intro and one real team, not a more
detailed scorecard.
