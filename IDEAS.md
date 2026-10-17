# Ideas

A dumping ground for things worth capturing but not worth working on yet. Not a
backlog with commitments, not a roadmap phase — just raw material. When asked
"what's the most interesting next idea," pull from here, not from ROADMAP.md.

Each entry: what it is, where it could plug in, why it's not active yet.
Every entry also names its source file so the original writeup can be found.

---

## Narrative / positioning

### Reframe "professionalism" as human maturity, not human erasure
Core pitch argument: corporate culture uses "be professional" to mean suppress
emotion and act as an interchangeable cog. Suppressed emotion leaks out as
passive-aggression, gossip, and burnout instead of disappearing. Mend's
counter-frame: real professionalism is human maturity — acknowledging
biological limits and stress responses, not erasing them.
- Where it could plug in: pitch deck opener, landing page hero copy, sales narrative.
- Why not active: needs to be distilled to a few lines that survive contact
  with an HR buyer, not the full essay version.

### Corporate-buzzword translation table
A side-by-side table translating corporate euphemisms ("executing an
operational action plan") into plain human language ("figuring out how we
work together without driving each other crazy"). Could be a literal UI
element (tooltip/toggle) or just a style guide for all product copy.
- Where it could plug in: product copy style guide; could also be a fun
  landing-page interactive widget ("corporate-speak to human" translator).
- Why not active: copy work, not urgent before MVP testing finishes.

### "Any AI can make you feel good, do you want to feel good or do you want to solve this" counter to "why not just use ChatGPT"
Direct answer to the sharpest piece of tester feedback so far (six former-colleague
designers): a personal LLM is an echo chamber for one person — it only hears
one side, is tuned to validate, and leaves the user with a self-drafted script
plus 100% of the vulnerability of the real confrontation. Correction worth
keeping: most employees will never voluntarily invite a peer into a joint
session (that's realistically manager-triggered), so the solo intake isn't an
on-ramp to the "real" feature — for most users it IS the product, and this
argument has to land solo, not assume a joint session exists.
- Where it could plug in: landing-page objection-handling copy, designer/
  tester-facing talking points, onboarding copy for the solo flow.
- Why not active: needs distilling into shipped copy; see
  `docs/pitch-strategy/19_PERSONAL_AI_BENCHMARK_AUDIT.md` for the full
  argument plus the research it leans on (not yet source-verified) and a
  runnable benchmark to back it with evidence instead of assertion.

### "No managerial surveillance, no scar tissue" as a trust pillar
Explicit promise: no HR files, no performance review penalties from using
Mend. Friendship isn't the goal — clean functional boundaries without forced
reconciliation is a 100% successful outcome.
- Where it could plug in: trust/privacy section of pitch, onboarding copy
  explaining what Mend does NOT do.
- Why not active: overlaps with existing privacy/confidential-computing
  story already tracked in ROADMAP.md Phase 3; fold in when that's drafted.

---

## Facilitator design

### Social friction as a third, distinct category
Alongside task friction (what's being built) and process friction (how
execution happens), name social friction explicitly: sarcasm, camera-off
freeze-outs, exclusion from casual chatter. Denial of its existence (pretending
only "the work" is discussable) is what lets it fester into backchannel
politics. "Air gaps" (unmonitored venting first) over forced confrontation.
- Where it could plug in: Thimble's classification taxonomy / facilitator
  system prompts, alongside existing task/process friction handling.
- Why not active: would need to check whether `classifier/` or the intake
  prompts already implicitly cover this before adding a formal third category.

### Biological/environmental framing for why people dysregulate in meetings
A causal chain: evolutionary status-threat detection → polyvagal shift
(ventral vagal → sympathetic/dorsal vagal) → audience effect (disagreement in
front of others becomes face-saving, not problem-solving) → environmental
load (poor ventilation, Zoom gaze mechanics, sensory fatigue). Useful as a
"why this isn't a character flaw" explainer for skeptical users or HR buyers.
- Where it could plug in: onboarding/explainer copy, or background material
  for facilitator system prompts to ground tone.
- Why not active: explanatory content, not a feature; lowest urgency of this batch.

### Concrete in-meeting circuit breakers
Specific, teachable tactics: "write, don't speak" (transcribing the other
person's words buys 10-15 seconds and signals engagement), the covert
physiological sigh (double inhale through nose, slow exhale through mouth),
and countering sharp comments with operational questions ("walk me through
the dependency you're worried about") instead of defensiveness.
- Where it could plug in: coaching tips surfaced in `manager-coaching-app` or
  `manager-app`, or as in-session nudges during a live facilitated conversation.
- Why not active: would need UX design for when/how to surface a tip without
  being annoying or patronizing mid-conversation.

### The 4-step constructive collaboration arc
Observable Data → Workflow Impact → Structural Curiosity → Co-Authored SLA.
A structured arc for turning a complaint into a resolvable agreement: cite
verifiable facts without adjectives, describe downstream delivery risk (not
hurt feelings), ask about the other person's constraints, land on explicit
turnaround times/channels instead of a vague "we'll get along" promise.
- Where it could plug in: could become the actual conversation skeleton the
  facilitator steers toward in joint sessions — a concrete structure instead
  of open-ended mediation.
- Why not active: would be a meaningful change to facilitator prompt design;
  needs its own design pass, not a drop-in.

### Self-healing squads framing (Tuckman + Jehn + IKEA effect)
Positioning for why autonomous peer repair matters to performance, not just
wellbeing: teams can't reach "Performing" without passing through "Storming";
task friction signals engagement, not dysfunction; agreements peers negotiate
themselves (not manager-arbitrated) see 80-85% adherence vs. passive
compliance when imposed. Useful for selling to engineering-leadership buyers
specifically (vs. HR).
- Where it could plug in: a leadership/manager-focused pitch variant,
  distinct from the HR-buyer pitch.
- Why not active: `docs/pitch-strategy/` is HR-buyer focused today; this is a
  different buyer persona and would need its own outreach materials.

---

## Hardware / device concept

### "Gimbal" — a physical somatic down-regulation object
A standalone device (or on-screen equivalent) with a morphing geometric form
that acts as a breathing pacer: expands over 4s, holds 1s, contracts over 6s,
guiding down-regulating exhalations. Paired with bilateral ocular pacing (two
focal points moving left-right-left across its perimeter) to interrupt visual
tunnel vision during acute stress. Framed deliberately as tactical cognitive
hardware prep, not wellness/meditation, to land with skeptical knowledge
workers. Deadpan prompting style: "Take 30 seconds to drop the physical
static, or skip straight to the breakdown."
- Where it could plug in: could start as a software-only on-screen widget
  (no new hardware needed) inside `joint-session-app` or the facilitator UI,
  before ever considering an actual physical object.
- Why not active: biggest scope jump in this batch — real industrial-design
  and hardware questions if taken literally; the software-only version is a
  much smaller first bite if this ever gets prioritized.

### Real-time biometric telemetry for detecting dysregulation
Using consumer hardware already in people's hands/desks to detect
physiological arousal: phone IMU (seismocardiography via accelerometer/
gyroscope), camera PPG (heart rate variability via flashlight + camera),
touchscreen dynamics (micro-tremor, tap force, erratic backspacing); webcam
rPPG (contactless pulse via facial color fluctuation), pupillometry/blink
tracking. Explicit zero-trace design constraint: telemetry stays in local
RAM, is purged immediately, and only ever becomes a discreet haptic/UI nudge
— never employer-visible monitoring data.
- Where it could plug in: would pair naturally with the existing
  prosody/tone signal work already validated and wired into the facilitator
  LLM (see ROADMAP.md Phase 1) — this would be a second, vision/touch-based
  signal channel alongside voice.
- Why not active: significant privacy and trust design needed before this is
  even worth prototyping — the "zero-trace" promise has to be real and
  verifiable, not just asserted, especially given Mend's whole pitch rests on
  not being surveillance. Also unclear how much of this consumer hardware
  (rPPG especially) is reliable enough outside a lab setting.

---

## Feature concepts (from `docs/pitch-strategy/`)

### Ambient pacing HUD for live meeting coaching
A non-verbal live dashboard shown during prep/practice sessions: tempo cue
("slow down 20%"), talk-time ratio meter, mood read, core-goal-met status,
plus 1-2 word micro-pacing cues ("Pause." "Acknowledge."). Deliberately not a
live teleprompter/script-reader — that was considered and rejected as unsafe
and awkward.
- Source: `docs/pitch-strategy/00_LIVE_MEETING_AI_COACH.md`
- Where it could plug in: `manager-coaching-app` or the practice/rehearsal
  flow, as a UI overlay during a live or simulated session.
- Why not active: needs its own UI design pass; depends on real-time signal
  inputs (talk-time, tone) that would need to be wired up live, not just
  post-hoc.

### The Watcher — a second supervisor LLM auditing every facilitator draft
A deterministic (temp=0) second model that scores every facilitator reply
against 5 categories (SAFETY_FLOOR, HALLUCINATION, BIAS_ASYMMETRY,
OUT_OF_SCOPE_ADVICE, UNFILTERED_TOXICITY) before it reaches the user.
Non-safety-floor failures trigger a silent regeneration the user never sees.
This is architecturally distinct from — and heavier than — the single-model
`<mend_signal>`/any-of-k-voting approach actually shipped today (see
`STATUS.md`'s safety-floor voting rule).
- Source: `docs/pitch-strategy/03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md`,
  `docs/pitch-strategy/11_PRODUCT_ARCHITECTURE_AND_STRATEGY_BLUEPRINT.md`
- Where it could plug in: a wrapper around all facilitator model calls,
  shared across every app.
- Why not active: real cost/latency tradeoff (doubles inference calls per
  turn); needs a decision on whether current any-of-k voting already covers
  this well enough before adding a second model in the loop.

### PIP Navigator — full feature for employees on a Performance Improvement Plan
A 3-phase module: (1) private intake that triages whether a PIP is genuinely
remediable or an exit runway in disguise; (2) a translator that converts
vague PIP language ("be more collaborative") into concrete, verifiable
counter-proposals to send to the manager; (3) a weekly check-in HUD/evidence
ledger plus a 5-minute roleplay mock-review against an AI "manager" before
each real check-in. Has its own safety-floor carve-outs (no legal advice, no
ingestion of proprietary documents).
- Source: `docs/pitch-strategy/08_PIP_NAVIGATOR_FEATURE.md`
- Where it could plug in: a new standalone app/prototype, similar in shape
  to `manager-coaching-app` but employee-side.
- Why not active: entire feature, unbuilt; would need its own system prompt,
  UI, and legal-carve-out review (PIP navigation brushes against employment
  law) before touching real users.

### Practice State Anchor — compact memory schema for solo rehearsal continuity
A small (~300-500 token, <2KB) client-side JSON schema capturing scenario
metadata, the user's north-star objective, the counterpart's pressure
profile, the user's boundaries, and practice analytics (last weakness), so
repeated "Rehearse" sessions can resume with targeted coaching ("Last time
you dropped your boundary on X — want to re-run that moment?") without
replaying full transcripts.
- Source: `docs/pitch-strategy/09_PRACTICE_SESSION_MEMORY_SCHEMA.md`
- Where it could plug in: any solo practice/rehearsal flow (intake-app's
  voice practice mode, or a future PIP Navigator roleplay). Distinct from
  `manager-app`'s already-built case-state anchor, which serves the
  manager-coaching track, not solo rehearsal.
- Why not active: no solo rehearsal flow currently needs cross-session
  memory; worth revisiting once/if repeated-practice usage shows up in
  real tester behavior.

### Ambient Dual-Track Intake — "Vent" vs. "Mend" doors instead of mode buttons
Replace the current explicit mode-selection buttons at the entry point with
two framed doors: Door A ("Vent" — acute emotional agitation) vs. Door B
("Mend" — operational de-escalation/meeting prep). A softer, metaphor-driven
front door rather than a feature picker.
- Source: `docs/pitch-strategy/11_PRODUCT_ARCHITECTURE_AND_STRATEGY_BLUEPRINT.md`
- Where it could plug in: `intake-app` and `manager-app` landing screens.
- Why not active: a UX experiment, not a functional gap — current explicit
  buttons work; this would need A/B framing to justify the copy/design churn.

### Formalized 5-step pacing protocol with an explicit staging fork
A named conversational structure: Raw Vent → Pressure Gauge Check ("is there
more, or is that the main thing?") → Subtle Incentive Inquiry → Organic
Realization → Actionable Staging Fork, where the fork offers 4 explicit
options (Solo Exit / cheat-sheet summary / 3-minute AI-adversary roleplay /
Peer Invitation). Pieces of this exist informally in the live system
prompts already, but not as this explicit, named, branching structure.
- Source: `docs/pitch-strategy/11_PRODUCT_ARCHITECTURE_AND_STRATEGY_BLUEPRINT.md`
- Where it could plug in: `facilitator-intake-system-prompt.md` — would be a
  rewrite of the existing pacing logic into explicit named stages.
- Why not active: current prompt already does speed-to-value pacing
  (see recent `STATUS.md`/commit history); unclear this formalization buys
  enough over what's already working to justify a prompt rewrite mid-testing.

### Live continuous video-parity guarantee (extends the existing opt-in rule)
Extends the already-shipped one-time "double opt-in" video rule to a live,
continuous guarantee during a session: if either participant's camera drops
for any reason mid-session, BOTH are symmetrically and immediately dropped
to voice+avatar together, with neutral non-blaming framing ("Session
switched to Voice & Avatar mode"), and the facilitator is never told which
transport mode is active.
- Source: `docs/pitch-strategy/12_SYMMETRIC_VIDEO_PARITY_FEATURE.md`
- Where it could plug in: `joint-session-app`/`joint-session-audio`, once
  those are merged (ROADMAP Phase 1).
- Why not active: explicitly flagged in its own source doc as a captured
  idea, not yet designed against the real LiveKit stack; blocked behind the
  Phase 1 audio/video merge anyway.

### Multi-turn rerun of the personal-AI benchmark audit
`intake-app/tests/benchmark_audit.py` is built and has run clean (see
`STATUS.md`): single cold message in, scored by a blind judge. First real
result was NOT what the pitch argument predicted -- raw Claude with no
system prompt outscored both Mend and ChatGPT, because Mend's facilitator
is deliberately paced for multi-turn conversation (ask a grounding question
before delivering) and that reads as "no deliverable" on a one-shot rubric.
Next step: let Mend's conversation run 2-3 turns before scoring, matching
how `conversation_pattern_sweep.py` already tests multi-turn behavior, to
see whether the gap closes once Mend actually reaches its deliverable phase.
- Source: strategy conversation reacting to designer tester feedback, then
  the actual live benchmark run on 2026-10-13.
- Where it could plug in: extend `intake-app/tests/benchmark_audit.py`
  directly -- feed each system's turn-1 reply back as a synthetic follow-up
  and score the final turn instead of turn 1.
- Why not active yet: the single-turn result needs writing up honestly
  first (done, see `docs/pitch-strategy/19_PERSONAL_AI_BENCHMARK_AUDIT.md`'s
  2026-10-13 section) before deciding whether multi-turn is worth the extra
  API cost, and the underlying research citations (CPP stat, Jehn framing)
  still need source verification before any of this goes near a buyer.

### Publish the system prompt with a verifiable attestation
Publish Thimble's real `facilitator-*-system-prompt.md` files publicly for
trust, backed by (a) a SHA-256 manifest checked into the repo, and (b) a
future read-only `/api/v1/attestation` endpoint that hashes the files the
running server actually loaded, so a buyer or employee can verify the
deployed app matches the published prompt.
- Source: `docs/pitch-strategy/17_PROMPT_TRANSPARENCY_AND_ATTESTATION.md`
- Where it could plug in: a new small endpoint on whichever backend serves
  the live facilitator; manifest could live alongside the prompt files now.
- Why not active: open question of which repo mirrors the prompt publicly,
  which is itself blocked on the hosting/remote situation already tracked
  in ROADMAP Phase 3.

---

## Business model

### Remote conflict statistics as cost-of-inaction / credibility backing
A research pass on how workplace conflict actually plays out on fully
remote teams: ~80% of remote knowledge workers report conflict, CPP Inc.'s
2.8 hrs/week baseline drag, the "Silent Cold War" (camera-off, delayed PR
reviews, terse replies), Fundamental Attribution Error filling the
context-vacuum with assumed malice, Jehn's finding that 49-55%+ of
employees blame "ego" while 80%+ of real root causes are structural (KPI
collisions, network siloing), and why formal HR escalation only sees 3-10%
voluntary adoption remotely.
- Where it could plug in: the remote-specific slice of the cost-of-inaction
  case (`07_CULTURAL_POSITIONING_AND_ADOPTION.md`), and reinforces the
  "structural not personal" framing already used for the OSS maintainer
  angle below.
- Why not active: needs distilling into copy; see
  `docs/pitch-strategy/20_REMOTE_CONFLICT_RESEARCH_AND_STATISTICS.md` for
  the full research (citations not yet source-verified).

### Open source maintainer conflict as an adjacent market
A tester-sourced pitch angle: open source projects where a team can't reach
consensus, but the conflict is intellectual (technical disagreement), not
personal — the maintainers often don't know each other well and haven't
worked together before, so they lack the social/emotional-intelligence
tooling to resolve it themselves. Mend fits as an unbiased third party that
facilitates the conversation and drives resolution without taking a side.
- Where it could plug in: same "episodic/informal groups" bucket as the
  roommates/bands/co-founders pivot below — a per-incident "truce ticket"
  model fits an OSS maintainer dispute better than a subscription.
- Why not active: unexplored market, no pilot, and OSS maintainers as a
  buyer segment have no obvious payer (no employer, no HR) — would need its
  own go-to-market thinking distinct from the workplace/HR-buyer pitch.

### Adjacent-market pivots: co-parenting and episodic/informal groups
Two unexplored market variants beyond the core workplace product: (a)
high-conflict co-parenting (court-mandated), priced $12-18/mo split between
parents, with final agreements exported as court-admissible PDFs — a real
departure from the core product's zero-trace, no-transcript model; (b)
episodic/informal groups (roommates, bands, sports teams) via a "truce
ticket" ($10-15 flat per incident) or a group season pass ($29-79/yr).
- Source: `docs/pitch-strategy/02_COMMERCIAL_PRICING_STRATEGY.md`
- Where it could plug in: would be separate product surfaces, not a change
  to the current apps — co-parenting especially implies a different privacy
  model (document retention) than everything else Mend promises.
- Why not active: distraction risk before the core workplace MVP has even
  finished its test phase; the co-parenting variant in particular conflicts
  with Mend's core "no transcript, ever" privacy promise and would need its
  own trust story.

### Full sewing/textile product lexicon for marketing copy
A consistent metaphor set for marketing/UI copy: The Spool (solo intake),
The Loom (the ephemeral joint session), The Snips/Shears (the safety floor),
The Basting Stitch (practice rehearsal), The Pattern (cheat-sheet summary),
Tension Gauge (the Watcher concept above), The Dissolving Suture (the core
value prop — clean resolution, no scar tissue). Not adopted into any shipped
UI copy yet; current apps use plain language.
- Source: `docs/pitch-strategy/04_METAPHORS_AND_PRODUCT_LEXICON.md`
- Where it could plug in: landing page copy, in-app microcopy, the pitch deck.
- Why not active: a cohesive branding decision, not a quick swap — needs to
  be tested against real HR buyers before baking it into shipped copy
  (risk: cute metaphors can read as twee to a skeptical enterprise buyer).

### Aggregate org-level usage dashboard for HR/execs
A reporting view for HR/leadership showing only anonymized aggregate stats
(e.g., "14 peer misalignments resolved this month, ~112 hours of focus
recaptured") — deliberately never per-person — to reinforce adoption without
breaking the confidentiality promise.
- Source: `docs/pitch-strategy/07_CULTURAL_POSITIONING_AND_ADOPTION.md`
- Where it could plug in: a new admin-facing view, backed by aggregation
  over whatever session/outcome data already gets logged.
- Why not active: no real pilot customer yet to design this against (Phase
  3/4 territory); premature before there's HR-side usage to aggregate.

### Cultural-adoption copy kit
Concrete copy drafts for driving internal adoption: an onboarding memo
template, a low-stakes peer-invite message, and a post-session reinforcement
screen ("Alignment reached... saved an estimated 6 hours..."). None of this
copy exists in the shipped apps yet.
- Source: `docs/pitch-strategy/07_CULTURAL_POSITIONING_AND_ADOPTION.md`
- Where it could plug in: onboarding emails and in-app post-session screens,
  once there's a real pilot cohort to send them to.
- Why not active: tied to Phase 4 go-to-market timing — writing this before
  a pilot cohort exists would be guessing at tone with no feedback loop.

---

## Team retro / project post-mortem tool

### Pattern-only project retro — anonymized interviews, no individual call-outs
A separate, standalone tool (not the existing conflict-mediation flow):
after a project/sprint wraps, interview each person on the team separately
and let them be fully honest about what happened ("John didn't review my
PRs in time," "the UX design decisions were late and caused the delay").
The system distills answers across the group into recurring **patterns**
(structural/process causes) and never surfaces individual
names/call-outs in the output. Rationale: naming names in a shared report
makes people vulnerable to blame, which suppresses honesty; stripping
identity out and reporting only patterns is what lets people actually
tell the truth.
- Where it could plug in: new standalone app/prototype, separate from the
  peer-conflict apps (`intake-app`/`joint-session-app`/`manager-app`) —
  this is retro/post-mortem shaped, not conflict-mediation shaped. Could
  reuse the existing LLM-facilitator interview pattern and the
  "anonymized aggregate, never per-person" principle already captured in
  the org-level usage dashboard idea above.
- Why not active: brand new, unscoped concept — no interview flow, no
  distillation/pattern-extraction logic, and no decision yet on how many
  participants are needed before "patterns" stop being traceable back to
  an individual by elimination (a 2-person team can't actually anonymize).

---

## Open design questions

### Disclose safety-floor screening upfront, or only reactively?
Still explicitly unresolved: should Thimble state up front that it's
screening conversations for safety-floor triggers, or only surface that
boundary reactively when something actually crosses it? Current lean is
"disclose upfront, briefly," but it's marked as an open question in its
source doc, not a settled decision.
- Source: `facilitator-persona.md`
- Where it could plug in: whichever `facilitator-*-system-prompt.md` handles
  the first disclosure (currently the intake prompt).
- Why not active: a judgment call worth deciding deliberately rather than
  drifting into by default — flagged here so it doesn't get silently decided
  by whichever way the prompt happens to read today.

### Automatic names-only HR notification on safety-floor trip (competing design)
An alternate, simpler, non-consent escalation design floated early on: when
the safety floor trips, HR gets an email naming only the two parties and
stating that harassment was "potentially detected" — no category, no
severity, no consent flow. This conflicts with the consented, anonymized,
token-based escalation design already written up in `ROADMAP.md` Phase 3.
Not a new idea to build — flagged here so it doesn't get rediscovered and
built by accident instead of the already-decided design.
- Source: `docs/pitch-strategy/03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md`
- Why not active: superseded by the Phase 3 design in `ROADMAP.md`, which
  deliberately chose consent + anonymization over this simpler version.
