# Ideas

A dumping ground for things worth capturing but not worth working on yet. Not a
backlog with commitments, not a roadmap phase — just raw material. When asked
"what's the most interesting next idea," pull from here, not from ROADMAP.md.

Each entry: what it is, where it could plug in, why it's not active yet.
Every entry also names its source file so the original writeup can be found.

---

## App names

Moved to the top-level `README.md` ("App names" section) — these are shipped,
working names now, not raw ideas. `Swatch`, `Loom`, and `Hem` are still
unbuilt-idea concepts; their full writeups are below under their own
headings.

---

## Architecture cleanup

### Consolidate Spool into Seam as one app
`apps/spool` and `apps/seam` currently run as two separate backend processes
in production (`deploy/start.sh`): Spool serves the root landing/chooser page
(`/`), Seam serves the actual manager tool (`/seam/`, renamed from the
stale `/manager/` path on 2026-10-28). Not intentional — Seam is meant to
be the one app name for the manager-facing product. Spool should be
folded into Seam (one FastAPI app, one deploy process) instead of staying
a separate service.
- Source: found while testing the live site 2026-10-28 — `LINKS.md` still
  labels the root URL "Spool," which is accurate today but reflects the
  split that shouldn't exist.
- Where it could plug in: `apps/seam/server.py` absorbing Spool's routes;
  `deploy/start.sh`, `render.yaml`, `Caddyfile`/`render.Caddyfile`, and
  `LINKS.md` would all need updating to drop the separate `spool` process.
- Why not active: not yet scheduled — flagged here so it's captured before
  the testing phase, not lost.

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

### Community-as-leverage mechanism (never stated as copy)
Helping people resolve conflict builds a sense of community within a
workplace, and that community is itself leverage when bargaining with
management. Today, team-vs-team friction is frequently a deliberate release
valve — it keeps conflict running between employees instead of between
employees and management, which protects management from a unified
workforce. A tool that actually resolves interpersonal and inter-team
conflict removes that release valve: people stop burning energy fighting
each other and start noticing the actual source of institutional
dysfunction. This is the mechanism behind "find solidarity" in
[[project_mend_core_philosophy]] (memory) — not just a value statement, but
how the employee version builds real bargaining power over time, team by
team, without ever being pitched as an organizing tool. Deliberately never
stated in copy, no pitch deck, no landing page — implied entirely by the
seriousness of the no-trace promise and Thimble's employee's-best-interests
POV.
- Source: `MARKET_STRATEGY.md` (2026-10-24 strategy note, folded in here)
- Where it could plug in: nowhere in visible copy — this stays purely
  behavioral, in how Thimble responds, not in how the product is described.
- Why not active: not a feature, a worldview constraint on how existing
  features behave; flagged here so it isn't rediscovered and accidentally
  turned into a marketing angle.

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
- Where it could plug in: coaching tips surfaced in `thimble`'s
  manager-coaching path or `seam`, or as in-session nudges during a
  live facilitated conversation.
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
  (no new hardware needed) inside `suture` or the facilitator UI,
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
- Where it could plug in: `thimble`'s manager-coaching path or the
  practice/rehearsal flow, as a UI overlay during a live or simulated
  session.
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
  to `thimble`'s solo rehearsal mechanics but employee-side.
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
- Where it could plug in: any solo practice/rehearsal flow (thimble's
  voice practice mode, or a future PIP Navigator roleplay). Distinct from
  `seam`'s already-built case-state anchor, which serves the
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
- Where it could plug in: `thimble` and `seam` landing screens.
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
- Where it could plug in: `suture`/`joint-session-audio`, once
  those are merged (ROADMAP Phase 1).
- Why not active: explicitly flagged in its own source doc as a captured
  idea, not yet designed against the real LiveKit stack; blocked behind the
  Phase 1 audio/video merge anyway.

### Multi-turn rerun of the personal-AI benchmark audit
`thimble/tests/benchmark_audit.py` is built and has run clean (see
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
- Where it could plug in: extend `thimble/tests/benchmark_audit.py`
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

### Standing self-advocacy advice: raises and presenting your own work
Every employee using the tool should always be able to get advice on how to
ask for a raise and how to show their value when presenting — a standing
capability, not a one-off feature request. Consistent with the product's
broader worldview (see [[project_mend_core_philosophy]], memory): helping
people advocate for themselves individually feeds the same muscle as
advocating for themselves collectively.
- Source: `MARKET_STRATEGY.md` (2026-10-24 strategy note, folded in here)
- Where it could plug in: Thimble's standing system-prompt capabilities,
  available any time, not gated behind an active conflict session.
- Why not active: not yet scoped as a concrete feature, just a standing
  intent to carry into whichever prompt/feature work touches this.

### Audio-only rehearsal feedback (watch me present and critique delivery)
Floated idea: Mend listens to a rehearsal presentation and gives feedback on
delivery — pace, filler words, tone, pauses, confidence. Deliberately
audio-only, not video: most people present from their own computer anyway,
so the eye-contact/body-language signal video would add is already weak
(webcam angle, glare, half a face), and audio-only is a smaller build with a
smaller privacy footprint (process and return feedback, no need to keep the
recording).
- Source: `MARKET_STRATEGY.md` (2026-10-24 strategy note, folded in here)
- Where it could plug in: a rehearsal/practice mode alongside the standing
  self-advocacy advice above, or Seam's manager-rehearsal path.
- Why not active: today's video mode (Tavus) is outbound only — the avatar
  speaking to the user, not inbound analysis of the user's own
  camera/screen. Doing this for real means a new capture + multimodal
  review pipeline with its own privacy design, not a toggle on what
  exists. Parked, not committed.

### Legal/rights decoder — plain-English handbook, PIP, and NDA translation + statutory circuit breaker
Two parts: (1) translate obscure handbook language, ambiguous PIP wording, or
NDA/non-compete clauses into plain English, off the record; (2) a breaker
that flags when an issue crosses from routine interpersonal friction into a
labor-rights question (Title VII, retaliation, misclassification,
constructive dismissal) and surfaces the user's actual options — document
privately, know your rights — before they say anything further.
- Source: user-floated idea, 2026-10-28.
- Where it could plug in: PIP Navigator's translator phase (above) is the
  closest existing shape, but PIP Navigator's own carve-out says "no legal
  advice" — this idea runs straight into that boundary and would need its
  own legal-review pass before touching real users, likely harder than PIP
  Navigator's own carve-out review.
- Why not active: unscoped; the safety-floor/no-legal-advice boundary this
  would need to operate inside hasn't been designed yet.

### Meeting HUD — persistent on-screen tactical cheat sheet during a live external meeting
A HUD surfacing the techniques already in "Concrete in-meeting circuit
breakers" (write-don't-speak, physiological sigh, operational questions) as
glanceable on-screen tripwires during a real meeting happening outside Mend,
not a prep/practice session.
- Source: user-floated idea, 2026-10-28.
- Where it could plug in: tension with two existing ideas needs resolving
  first, not built independently — distinct from the "Ambient pacing HUD"
  above, which is explicitly prep/practice-only and deliberately avoids
  being a live-meeting overlay, and close enough to the rejected "live
  in-ear coaching during a real meeting" idea (see Ideation section) that
  the same objections (divided attention, consent/recording concerns, reads
  as adversarial if the other party learns about it) likely apply even
  without an AI feeding live lines.
- Why not active: unscoped; needs the pacing-HUD/rejected-coaching tension
  resolved before it's buildable.

### Unblockable communication scripts — pre-drafted boundary-setting formulas
A small library of ready-made phrasings for common boundary situations:
scope defense ("if we pull Project A into this sprint, Project B's delivery
date moves two weeks — which trade-off would leadership prefer?") and async
insulation ("I'll post a bulleted dependency update daily at 9:30 so you have
visibility without breaking focus time"). Concrete scripts, not just
technique advice.
- Source: user-floated idea, 2026-10-28.
- Where it could plug in: pairs with the standing self-advocacy advice idea
  above and the Basting Stitch rehearsal flow (see STATUS.md / project
  memory) — a scripts library the rehearsal flow could pull from.
- Why not active: unscoped; no script library exists yet, no decision on
  how many/which situations to cover first.

### Reframe regulation tools as cognitive performance equipment, not wellness
Positioning note, not a feature: pitch the somatic down-regulation tools
(physiological sigh, Gimbal) as tactical cognitive-performance equipment —
"when your heart rate spikes, your prefrontal cortex drops offline and your
peripheral vision narrows, so you lose your leverage" — rather than
wellness/mindfulness language.
- Source: user-floated idea, 2026-10-28.
- Where it could plug in: copy/positioning for the Gimbal device idea and
  the in-meeting circuit breakers idea above, not a new feature.
- Why not active: copy direction only; needs to be applied consistently
  wherever regulation tools are described, not a one-off rewrite.

---

## Business model

### Manager-to-team invite as Thimble's distribution and credibility path
Managers already using Seam can invite their own team to Thimble, so the
first thing an employee hears about Thimble is "my manager actually found
this useful and wants me to have it," not a cold, slightly cringe-inducing
self-serve pitch for an AI conflict tool. Solves two problems at once: the
adoption-credibility gap Thimble has on its own (nobody wants to be the
first person at a company to use something like this), and gives Seam
managers a concrete reason to keep paying attention to Mend between actual
conflict episodes.
- Source: user idea, 2026-10-30, raised right after the Seam-first
  marketing-site work landed — explicit framing was "a really good way to
  get around the cringe factor and give Thimble some credibility because
  their managers are actively asking them to use it because they
  themselves found it useful."
- Where it could plug in: a Seam dashboard/admin feature (invite flow,
  probably post-session or from a settings area); marketing copy on
  index.html/seam-story.html once built ("invite your team" as a listed
  manager benefit); ties into the existing "two products, one engine"
  subsidy idea below, since this is the other product's actual bridge
  from manager to employee.
- Why not active: pricing/mechanics explicitly deferred by the user
  ("we can figure out pricing later") — no invite flow exists in
  `apps/seam` yet, and it's not clear whether it's a free team-wide
  unlock, a per-seat add-on, or something else.

### Two products, one engine — institution-facing tool funds the consumer tool
The business-model framing behind the EPLI/EAP distribution work: an
institution-facing tool (satisfies what an insurer/broker/EAP vendor wants
to see — documented reporting mechanism, safety-floor escalation, risk-
control credit eligibility) and a consumer tool (employee + manager
versions of the same engine), where the employee version is the core
product and can subsidize the manager version so access isn't gated by who
pays. Full writeup, comparables, and channel analysis moved to
`docs/pitch-strategy/28_GTM_EPLI_EAP_AND_ADJACENT_DISTRIBUTION.md`.
- Source: `MARKET_STRATEGY.md` (2026-10-24 strategy note, superseded by
  doc 28 above — kept here only as an index pointer)
- Why not active: subsidy mechanics (flat % of revenue into a manager-
  access pool vs. per-seat matching vs. something else) still unresolved;
  see doc 28's open questions.

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

### Pattern-only project retro — anonymized interviews, no individual call-outs (codename: Loom)
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
  peer-conflict apps (`thimble`/`suture`/`seam`) —
  this is retro/post-mortem shaped, not conflict-mediation shaped. Could
  reuse the existing LLM-facilitator interview pattern and the
  "anonymized aggregate, never per-person" principle already captured in
  the org-level usage dashboard idea above.
- Why not active: brand new, unscoped concept — no interview flow, no
  distillation/pattern-extraction logic, and no decision yet on how many
  participants are needed before "patterns" stop being traceable back to
  an individual by elimination (a 2-person team can't actually anonymize).

---

## New adjacent tool concepts (2026-10-17)

### Swatch — preflight collaboration for designers who don't know each other
Not conflict resolution — preflight. Two (or more) designers who haven't
worked together before get paired on a shared design problem, and Thimble
runs a structured process with two equal goals: (1) the two people's
working relationship gets better, (2) the design objective actually gets
finished. Same "structural, not personal" spirit as the rest of Mend,
applied before friction exists instead of after.

The workflow (named "The Workflow" in the design artifact), six steps,
built to also scale past two people:

1. **Warm-up** (~2 min). Talk through the shared goal together, then a
   couple of questions: how do you like to receive feedback, how do you
   work collaboratively in general.
2. **Heads-down solo work**. Each designer works alone. Time box scales
   with how big the problem is, not a fixed default.
3. **Thimble-facilitated presenting**. Each designer presents their work
   to the others. Thimble assigns the presenting order up front instead of
   implicit back-and-forth. While someone's presenting, others can flag "I
   have a question" without interrupting — the queue holds order (who's
   first, second), not just presence, and Thimble calls on them in that
   order. At group scale, Thimble still manages one ordered queue across
   everyone, not a free-for-all.
4. **Thimble keeps the presenter talking**. Not a goal in itself — if the
   question queue from step 3 is empty when the presenter finishes,
   Thimble asks problem-relevant questions so the designer keeps thinking
   out loud instead of the round ending on silence. Hard constraint:
   Thimble only ever asks the presenter, never calls on a specific
   listener by name — forcing someone to produce a question is
   overstepping, and at group scale silence from 4 people isn't the same
   signal as silence from 1.
5. **Consensus**. Voting, or each person marking what they liked across
   the presented work — a reaction signal, not necessarily a single
   winner. At group scale this is aggregation (which element got the most
   marks), not just a side-by-side list of two opinions.
6. **Repeat**, building on what step 5 produced (loops back to step 2).
   Next round's solo work starts from the converged direction, not a blank
   goal — each pass refines the last one instead of re-litigating it. Loop
   ends when either the goal is achieved, or the group runs out of time
   and the session pauses to continue later at the same point, not from
   scratch.

Open questions, still unresolved: does step 5's "liked" output a ranked
winner, a merged direction, or just a heatmap of reactions for humans to
decide from; and who calls "goal achieved" — the group by vote, or does it
need to clear some threshold on its own.

Platform decision: the whole workflow runs over a real video call
(Zoom/Teams/Slack-style) that already owns screen share — Swatch doesn't
build its own video or screen-share UI, same architecture call already
made for Splice below. Zoom was picked first because of its Apps SDK;
Teams needs heavier Azure AD auth, Slack has no in-call panel SDK so it
only fits async pieces. Decided direction: single-driver v0, not full
realtime multiplayer sync, as the first build target.

Mockups exist as a Claude Artifact, not yet built: a canvas comparing this
shape against two rejected alternatives (a plain parallel-sprint flow, a
continuous-check-in flow), a zoomed-in mock of Thimble's solo-brainstorm
prompts, and four app-screen UI mockups (warm-up, solo work, presenting,
consensus). One correction still pending in that artifact: the presenting
screen currently mocks up its own fake screen-share panel, which is wrong
now that the real call already handles screen share — needs to become a
companion-overlay layout (order list + question queue only).
- Where it could plug in: standalone app/prototype, separate from the
  conflict-mediation apps. Likely shares infrastructure with Splice below
  (`splice/`'s room/WebSocket backend, Zoom Apps SDK companion
  panel pattern) rather than a from-scratch build, since both are
  companion-panel-over-a-real-call shapes — though Swatch's trust model is
  the opposite of Splice's: two people building a working relationship
  needs encouragement/warmth framing, not neutral group-vote mechanics.
- Why not active: workflow spec and UI mockups exist only in a private
  design artifact, not yet exported into this repo; no code written.

### Splice — consensus-builder for loose groups, as a Zoom plugin
Small/loose groups of strangers (reference case: open-source maintainers
stuck on one GitHub issue) stuck at an impasse, meeting live, with nothing
confidential between them — the opposite trust model from the two-person
conflict-mediation apps, where privacy between the two parties is the whole
point. Splice's job is driving a group to an explicit, visible group
decision (a vote), not protecting anyone's privacy from anyone else in the
room. This is a meaningfully different product shape from Thimble/Suture, not
just a group-sized version of it: no safety floor, no side-conversation
firewall, no confidential intake — those are Thimble/Suture-specific and
deliberately left out of Splice's facilitator prompt.

First build pass is done, as `splice/` (prototype, in-memory
only, no persistence):
- A shared room: participants, group chat, proposals, and per-proposal
  voting (yes/no/abstain), broadcast live over WebSocket to everyone in
  the room.
- Thimble sits visibly inside the group as a named participant, not a
  silent backend process — asks the next useful question, names implicit
  proposals out loud, nudges toward a vote when discussion stalls, stays
  neutral on substance (never argues for one proposal over another), and
  never declares a vote "decided" — only reports where the count stands.
  System prompt: `facilitator-group-session-system-prompt.md`.
- Onboarding: Thimble states the session's goal (the pinned issue) and
  asks the participant's preferred way of taking part — video+mic or
  text-only — before they enter the room.
- Self-serve controls: mute mic, turn off video, leave the session.
  Explicitly not a facilitator-removes-others feature — each person only
  controls themselves.
- Architecture decision, after initially misreading the ask as "build a
  video-call app": Splice does NOT build or own video/audio at all. Zoom
  is the entire transport layer; Splice is a companion panel that runs
  alongside a real Zoom meeting (via the Zoom Apps SDK) and only owns
  chat, proposals, voting, and Thimble. Two front ends exist today for
  this reason: `static/index.html` (a standalone video-first mockup, used
  to validate the UI before the Zoom-panel pivot) and
  `static/zoom-panel.html` (the real target shape — no video grid, no
  media controls, calls `zoomSdk.getUserContext()` to auto-join a real
  Zoom participant by name).
- Verified live (browser-pane testing): join → onboarding → room → chat →
  proposal → vote → mute/camera/leave all work end to end on
  `index.html`. `zoom-panel.html`'s non-Zoom fallback path (manual name
  entry, used when the SDK isn't present) also renders correctly through
  onboarding and into the room.
- Known open bug: in `zoom-panel.html`'s own tab, `POST /api/message`
  succeeds server-side but the message never renders back locally — the
  browser console shows a WebSocket reconnect loop. Not yet root-caused;
  not yet confirmed whether it's a real bug in that page's
  `connectSocket()` or a browser-pane sandbox artifact. See `STATUS.md`
  2026-10-16 entry.
- Blocked on the user, not yet attempted: testing the actual in-Zoom path
  needs a Zoom Marketplace developer account and a registered Zoom App
  (Client ID) to get a Client ID, plus HTTPS hosting (Zoom Apps refuse
  plain-HTTP localhost) — likely via a tunnel (ngrok or similar) until
  real hosting exists.
- Where it could plug in: standalone Zoom app/plugin, `splice/`
  in the shipped codebase.
- Why partially active: core group room + Thimble + voting is built and
  browser-verified; the Zoom-native integration itself (the actual point
  of "as a Zoom plugin") is unverified beyond the local fallback path,
  gated on developer-account setup only the user can do.

### Hem — cross-platform writing assistant for calm communication
A desktop app you can invoke from any other app (highlight text, bring it
in) that helps you write or rewrite a message so it makes your point without
causing conflict, regardless of the platform you're sending it from.
- Where it could plug in: standalone desktop utility (OS-level hotkey/
  highlight capture), separate from the conflict-mediation apps; could reuse
  facilitator tone/framing logic from the existing system prompts.
- Why not active: brand new, unscoped — no OS-level text-capture mechanism
  built, and open question on which platforms/OS to target first.

---

## App concept strength ranking (2026-10-17)

Ranked the seven app codenames (see "App codenames" above) by concept
strength, in this priority order: market pull (real buyer + budget) first,
then defensibility/moat, then mechanism novelty, then build feasibility.
Moat is judged on fit to the actual target outcome (emotional de-escalation
+ walking away equipped with a strategy, plus the safety floor) — not on
one-shot LLM benchmark output quality, which undersells this (see the
`19_PERSONAL_AI_BENCHMARK_AUDIT.md` single-turn result and its known
limitation, written up in the "Multi-turn rerun" entry above).

**Family note, not a merge**: Suture and Splice both sit in the same
category — Mend facilitating a live, real-time session that drives toward
a deliverable, rather than solo prep (Thimble/Seam) or async distillation
(Loom). They are NOT the same engine at different headcounts (see the
Splice entry above for why — opposite trust model, confirmed deliberate
and already partially built that way). The real split within the family is
trust model and output shape: Suture is private, two-party, and resolves
into an action plan; Splice is public, group-scale, and resolves into a
visible group decision/vote. Swatch is a third variant in this same live-
facilitation family, with yet another trust model (warmth/encouragement
between two people building a working relationship, not conflict
resolution and not neutral group voting).

1. **Seam** — real buyer with budget (manager/L&D training spend), no
   invite-friction problem (solo, manager-initiated for their own benefit),
   solid moat from the same outcome-tuning as Thimble/Suture.
2. **Thimble** — soft buyer economics (individual employee, no budget line),
   but decent moat (tuned for the regulate-then-equip arc + safety floor,
   not raw output quality), already built and tester-validated, feeds
   everything downstream.
3. **Suture** — weakest pull of the core three: needs a manager to nominate
   the pair, or two peers to opt in together, which most people won't do
   unprompted. But by far the strongest moat and most novel mechanism — live,
   bidirectional, two-safety-floors-at-once facilitation is a much harder
   problem than solo intake and the hardest for a generic assistant to
   replicate on the fly.
4. **Loom** — real recurring pull (every team does retros; "retros surface
   complaints but never fix the structural cause" is a known failure mode),
   good differentiated mechanism (private interviews distilled into
   structural patterns, e.g. "team's overworked, that's why PRs slip" — not
   anonymization of blame, root-cause diagnosis). Furthest from built
   (brand new interview/distillation flow) and lower-stakes pain than the
   top three.
5. **Swatch** — facilitated design critique/collaboration session (not
   passive Figma-style comments). Narrower, lower-stakes buyer (design
   leads, not broad org pain), moat is borrowed from Suture's facilitation
   tuning but unproven in this domain, real platform risk (Figma could ship
   this natively).
6. **Splice** — Zoom-plugin consensus-builder for loose groups. No clear
   named/budgeted buyer, thin moat, competes directly with where Zoom/Otter/
   Read AI are already investing their own live-meeting AI features.
7. **Hem** — cross-platform "don't sound like an ass" writing assistant.
   Broadest surface appeal but essentially no defensible position: every
   major platform (Grammarly, Gmail, Slack) already ships tone/rewrite AI
   natively, and the OS-level text-capture engineering lift is unrelated to
   anything already in this repo.

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
