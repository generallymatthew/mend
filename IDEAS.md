# Ideas

A dumping ground for things worth capturing but not worth working on yet. Not a
backlog with commitments, not a roadmap phase — just raw material. When asked
"what's the most interesting next idea," pull from here, not from ROADMAP.md.

Each entry: what it is, where it could plug in, why it's not active yet.
Every entry also names its source file so the original writeup can be found.

---

## Process: how to know if Thimble's conflict-management approach is actually right

Raised directly by the user (not a feature idea): he has no formal ADR/
mediation credentials, is building Thimble's conflict logic off instinct
plus an LLM that's structurally biased to agree with whatever theory he
proposes, and wants a real check on whether the approach is sound rather
than just self-reinforcing.

What his instincts have already gotten right, cross-checked against actual
ADR/psych literature:
- People reject the "conflict" label and want an operational plan or
  communication buffer, not to admit they need "remediation" — matches how
  defensiveness works in dispute resolution.
- Peer-negotiated agreements stick better than management-imposed ones
  (Self-Determination Theory, Deci & Ryan) — supports keeping Thimble
  peer-owned rather than authority-driven.
- Venting has to happen before problem-solving — an emotionally flooded
  person can't negotiate rationally yet. Matches the existing split between
  solo intake (Spool) and forward-looking alignment (Weft).

Where gut-feel + an agreeable AI breaks down, specifically:
- **Single-hammer trap**: an early insight ("conflict = competing KPIs")
  got agreed with and then over-applied to every case, when real friction
  is often bandwidth panic, status defense, or style mismatch instead.
- **Clean-plan delusion**: product-designer instinct wants tidy 3-step
  flowcharts; real conflict is messy, and forcing it into an SLA-shaped plan
  makes users feel invalidated.
- **Sycophancy blind spot**: the hard technical job isn't being agreeable,
  it's being a fair mirror that can tell the user an uncomfortable truth
  without triggering defensiveness — directly related to
  [[feedback_interrogate_dont_placate]] in memory.

Three concrete ways to actually test this instead of asking an LLM if the
idea sounds good:
1. **Real-friction transcript audit** — run 10-15 real, unfiltered
   messages/scenarios from actual past tension (old jobs, trusted peers,
   anonymized retros) through Thimble and judge the output with brutal
   candor: does it sound like a patronizing HR bot forcing a generic
   explanation, or like a grounded wingman giving the right two sentences?
2. **End-of-session gut check with real users** — skip "did you like this"
   and ask: did it feel like it was on your side vs. policing you; did it
   tell you what you wanted to hear vs. help you see what was actually
   going on; would you bring the next awkward Slack/meeting here first?
3. **Anchor to established frameworks** — check Thimble's turns against
   Principled Negotiation (separate people from problem, focus on
   interests not positions), Attribution Theory / Fundamental Attribution
   Error (does it catch the user assuming the other person is just evil),
   and Nonviolent Communication (isolate observable facts before drafting
   requests, rather than passing judgment).
- Source: conversation 2026-11-03, pasted user writeup (unnamed, framed as
  "how do I know I'm building Thimble right").
- Where it could plug in: not a code change — this is a standing test
  protocol to run against the coaching prompts and the overall product
  direction periodically, especially before locking in any new Thimble
  "insight" the way the KPI-hammer one got overapplied.
- Why not active: no actual real-friction transcripts have been run
  through Thimble yet under this protocol — flagged here so the three
  tests get run deliberately rather than substituting more gut-check
  conversations with an agreeable model.

---

## Thimble presence and personality

### Homepage speaks as Thimble in first person, not as marketing copy about it
Instead of a third-person brochure page explaining what Mend/Thimble is,
the landing page itself talks directly to the visitor as Thimble, in its
own voice, replacing standard marketing sections with first-person copy:
- Above the fold: Thimble introduces itself directly ("I'm Thimble... I
  don't lecture... nothing you say here ever gets logged"), followed by a
  single input box and a few quick-prompt chips (e.g. "A message I want to
  send without blowing things up").
- "Why I Exist" replaces "About Us": frames conflict as an operational
  pile-up between people under opposing pressures, and positions itself as
  "the fourth option" beyond swallow-it / vent / escalate-to-HR.
- "Whose Side I'm On" replaces "Our Values": explicit "yours, not your
  company's" framing, using the thimble-as-finger-shield metaphor.
- "How the Privacy Works" replaces "Security & Compliance": explains
  zero-persistent-memory sessions in plain first-person language, with the
  one named exception being a "strict legal floor for active threats and
  overt abuse."
- Closing CTA: no signup/corporate email required, just drop the draft.

**Flag**: the user noted the most recent actual homepage tells the story
from the manager's POV, which is a different narrator/audience than
"Thimble talking directly to an employee venting" above — these two
framings are in tension and would need to be reconciled (or deliberately
kept as two different entry points) rather than assumed compatible.
- Source: conversation 2026-11-03, pasted user writeup (unnamed).
- Where it could plug in: whichever file renders the root marketing page
  (`apps/spool` per the "Consolidate Spool into Seam" entry above, or
  wherever the current manager-POV homepage copy lives).
- Why not active: homepage copy, not written; also unresolved against the
  current manager-POV homepage, per the flag above.

### Living avatar with Reading/Thinking/Talking states, two-pane chat layout with transcript
A proposal to make Thimble more visually present during actual chat
sessions (not just the landing page), via a two-pane layout:
- **Left pane**: Thimble's avatar occupies the main visual space and
  animates through three states — Reading/Listening (grounded, relaxed,
  "I'm holding space"), Thinking/Deliberating (warmer palette, slight
  tilt, pensive pursed mouth, breathing slows), and Talking/Articulating
  (rose bloom, body undulates with speech cadence, mouth articulates with
  streaming text). A live, low-contrast speech bubble shows words as they
  stream.
- **Right pane**: a persistent chronological transcript. As Thimble
  finishes a sentence, it "docks" into this transcript. When Thimble
  identifies a concrete tactical ask (a script/message to send), it gets
  pulled out into a separate "Framed Artifact Box" with a one-click "Copy
  Clean Script" button, rather than staying buried in a chat bubble.
- A rough HTML/canvas prototype was included in the writeup (state machine
  driving a radial-gradient dome shape, mouth-cavity ellipse sized by
  state, timed sequence reading -> thinking -> talking -> docking to
  transcript).

**Flag — check against [[feedback_no_polygon_ripple]]**: the writeup
describes "harmonic acoustic ripples" tracing along the dome's outer rim
in the Reading state. That memory says the user specifically rejected a
faceted/polygonal clip-path "ear-ripple" effect and wants organic blurred
glow pulses instead, not faceted ripples — this detail should be checked
against that rejection before building, not assumed to be a new, different
ripple.

This also connects to the existing [[project_thimble_expressive_lab]]
work (anticipation/backchannel/squash/mirroring prototype, squash strength
confirmed at 50%) and [[project_thimble_voice_fragility]] (voice engine
duplicated across 5 files, breaks easily) — a three-state avatar visible
during ordinary text chat, not just the voice/expressive-lab prototype
page, would mean whatever state logic exists needs to be surfaced in the
main chat UI too, not just the lab page.
- Source: conversation 2026-11-03, pasted user writeup (unnamed),
  including an HTML/canvas prototype snippet.
- Where it could plug in: Seam's main chat interface; would likely share
  (or need to be reconciled with) whatever avatar/animation code already
  exists from the expressive lab work.
- Why not active: per [[feedback_design_review_before_building]], this
  needs mockup/design review before any real UI file gets touched — not
  yet reviewed as options, so nothing should be built from this directly
  yet.

---

## Funding: grant-funded local inference hardware

Idea floated 2026-11-03: apply for non-dilutive grants to buy a dedicated
local-inference machine, instead of (or alongside) paying per-token for a
commercial LLM API. Rationale and specifics below are speculative, not
researched/verified by Claude — capture only, not a recommendation to act on
without checking current grant terms and hardware pricing.

**Grant angle**: foundations focused on digital rights / privacy / public
infrastructure (named: NLnet Foundation, Prototype Fund, Mozilla Open
Source Support, Sovereign Tech Fund) reportedly fund open hardware and
localized software stacks, and would be pitched on a "zero-trace,
air-gapped, open-weight mediation engine" framing — directly reinforces
[[project_mend_moat_strategy]]'s zero-trace promise, but see
[[project_zero_trace_gap_prototype]]: that promise doesn't fully hold yet
even in the current cloud-based prototype, so any grant narrative built on
it would need that gap closed first or stated honestly. Unrestricted
micro-grant programs (Awesome Foundation, 1517 Fund Medici Project,
Emergent Ventures) were also named as options with no capex restrictions.
Corporate cloud credit programs (Google Cloud, AWS Activate, Azure) were
flagged as NOT fitting this — they only give compute credits, never cash
for hardware.

**Customization upside of owning the hardware**: could fine-tune (LoRA/SFT)
an open-weight base model (Qwen 2.5 32B/72B, Llama 3.3 70B) so ADR rules
and de-biasing logic live in the weights instead of a long system prompt,
run the Facilitator and the deterministic Watcher locally with no API rate
limits, and get a genuinely air-gapped enclave with no external network
dependency.

**Hardware/cost reality check**: a 70B-class model needs ~40-48GB memory
bandwidth (dual used RTX 3090 rig ~$2,200-2,600, or Apple Silicon Mac
Studio 96-128GB unified RAM ~$3,600-4,800); anything smaller (8B-14B on a
single 16GB GPU) was flagged as more prone to sycophancy and hallucination
for nuanced mediation. One such machine handles only 1-2 concurrent users
smoothly; concurrent load beyond that queues up without a request
scheduler or more machines. Breakeven estimate given: roughly 3,000-5,000
completed disputes vs. pure per-token API cost (~$0.47/100-turn cycle) to
justify a ~$3,000 machine on cost grounds alone.

**Staged approach suggested**: use API credits (e.g. Anthropic/Google
startup credit tiers) to finish prompt/schema tuning with early users
first, then apply for hardware-specific grants once the design is
validated, then package the fine-tuned model + state machine as a
self-hostable Docker/vLLM image for the open-source community.
- Source: conversation 2026-11-03, pasted user writeup (unnamed).
- Where it could plug in: infrastructure/deploy decisions, not product
  code — would sit alongside whatever `deploy/start.sh` / `render.yaml`
  setup exists once (if) a local-inference path is pursued; also connects
  to [[project_epli_distribution_route]] and the broader moat strategy as
  a cost/credibility lever.
- Why not active: no grant applications written, no hardware purchased —
  this is unvetted early-stage financial/strategic speculation generated by
  an LLM in response to a one-line prompt, not something Claude verified
  (pricing, grant eligibility, and token/dispute cost estimates above
  should all be re-checked before being relied on). Flagged here so it
  isn't lost, and so it doesn't get acted on without that verification.

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

## Working relationship compact (human-first coworker norms)

A set of coworker "operating norms" research-backed in structure (Jehn's
task/process/relationship conflict split, Deci & Ryan's self-determination
theory on peer-authored vs. imposed rules, Fundamental Attribution Error in
async text channels) but explicitly reframed away from the standard
corporate version of the same mechanics. First pass used the normal
"SLAs/channels/escalation" framing and the user flagged it as building
"efficient worker bees" rather than something for the employee's own
benefit — the correction matters more than the content: the same three
pillars (structural empathy, operational boundaries, de-stigmatized
redress) only count as on-brand for Mend if they're framed as protective
equipment for the person (the right to feel what you feel, the right to
log off without eggshell-walking, the right to flag friction without it
becoming an HR event), not as productivity infrastructure that happens to
also make people feel nice. Directly reinforces
[[project_mend_core_philosophy]] (institutions not people) and
[[feedback_no_eq_term]]'s instinct that soft HR language undersells what
this actually does.

Includes a ready peer-to-peer kickoff script ("Default to Grace" / "Protect
Our Sanity" / "Pebble in the Shoe") written in first-person, human voice —
closer to how Thimble itself might talk than how an HR document would.
- Source: conversation 2026-11-10 (pasted chat, unnamed), full summary in
  `summerizing-conversations.md`'s template, applied ad hoc to this chat.
- Where it could plug in: could become actual onboarding/kickoff copy
  surfaced inside Seam or Thimble (e.g. a "start this working relationship
  off right" prompt a manager or peer can send), or could inform the
  "Why I Exist" / "Whose Side I'm On" homepage copy already proposed under
  "Thimble presence and personality" above — same worker-protective framing
  problem, same fix.
- Why not active: never asked for as a feature — this was pure discussion/
  framing work, no product surface decided, no copy drafted for a specific
  screen yet. The two next steps floated (customize for a specific
  cross-functional dynamic; tie into Spool's reassurance copy) were offered
  but not accepted by the user.

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
- Supporting evidence (not yet source-verified, needs citation check before
  using in external-facing copy): organizational psychology research backs
  the claim that masking has a real output cost, not just a wellbeing cost.
  Gross's emotion-regulation work shows expressive suppression taxes
  prefrontal/working-memory resources, which collapses "integrative
  complexity" (holding competing perspectives, trade-offs) into rigid,
  checklist-style thinking. Kahn's 1990 "psychological presence" framework
  and Amabile's creativity research tie genuine emotional engagement
  directly to divergent thinking and discretionary creative effort; Gross
  also connects suppression to reduced empathic accuracy and worse reading
  of others' nonverbal cues. Grandey's surface-acting research adds that
  counterparts detect the physiological "flatness" of forced suppression,
  which erodes trust rather than protecting it. Net argument for the pitch:
  masking doesn't just cost the employee, it visibly degrades the nuance,
  creativity, and empathy of the work itself, which gives "professionalism
  as human maturity" a performance argument, not just a wellbeing one.

### ADR (Alternative Dispute Resolution) framework research — Thimble's model vs. named mediation styles
Background research (2026-11-11) mapping Thimble's actual behavior against the
established mediation frameworks, to sanity-check scope and borrow credible
language for the pitch.

Four named ADR models, mediator's role vs. what "success" looks like:
- **Facilitative** (classic Fisher & Ury / *Getting to Yes*): mediator is a
  neutral process manager only, no opinion on outcome, draws out each side's
  real interests (not stated positions) so they can find a mutually workable
  option. Broadest default model (HR mediation, community mediation, divorce
  mediation).
- **Evaluative**: mediator (often a retired judge/expert) gives an opinion on
  likely legal/financial outcome to push parties toward realistic settlement.
  Trades neutrality for expertise. Needs a real external baseline (a court
  outcome) to work — common in commercial/legal/insurance disputes, doesn't
  map to workplace interpersonal conflict.
- **Transformative** (Bush & Folger, *The Promise of Mediation*, 1994):
  settlement isn't the goal, "empowerment and recognition" is — mediator
  reflects back without steering, success = both people feel heard and
  capable, agreement is a side effect not the target.
- **Narrative** (Winslade & Monk, drawing on narrative therapy): reframes a
  dispute as two incompatible stories each party is living in, and helps them
  author a new shared story. Technique: "externalize the problem" (name the
  conflict as a separate entity — "the tension between you two" — rather than
  a trait of either person), so both parties fight the problem instead of
  each other.

Fairness has two distinct components in ADR theory, worth keeping separate in
any pitch copy:
- **Procedural fairness** (Tyler): did the process treat both sides equally,
  did each person get heard, understand what was happening. People judge an
  outcome as fair mostly by *how* they were treated, not by who technically
  won.
- **Substantive fairness**: is the outcome fair on the merits, anchored to
  objective criteria (market rate, precedent, comparable cases) rather than
  whoever negotiated harder.
- Gap: classic mediation theory mostly assumes symmetric power between two
  individuals. Workplace disputes usually aren't symmetric (manager vs.
  report, tenured vs. new hire). A process can be procedurally fair and still
  produce an inequitable result if the power asymmetry is never named, just
  smoothed over.

How this maps onto Thimble: closest to **facilitative + narrative** — it stays
neutral on who's "right" (facilitative) and surfaces structural pressure as a
reframe of why someone is resisting, which is a narrative-style move
(see [[project_structural_misalignment_reframe]]). It is deliberately not
evaluative (no verdicts, matches the zero-blame philosophy in
[[project_mend_core_philosophy]]) and not quite transformative (the point is
a workable message, not emotional recognition as the end goal). The
pitch-relevant insight: most ADR process design optimizes for procedural
fairness but leaves structural/power asymmetry unaddressed. Naming the real
institutional constraint (what Thimble already does) is a form of substantive
fairness that classic facilitative mediation leaves to chance.
- Where it could plug in: positioning/credibility section of the pitch (gives
  Mend's approach academic grounding instead of sounding invented), possibly
  informs how "fairness" gets defined in product copy.
- Why not active: pure background research, no copy drafted, not yet decided
  whether referencing named ADR frameworks helps or just adds jargon for a
  buyer who doesn't care about mediation theory.

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

## Thimble for proactive collaboration, not just conflict (2026-11-10)

### Collaboration/negotiation/conflict as one continuum, applied upfront instead of reactively
Framing: collaboration, negotiation, and conflict are the same underlying
dynamic (interdependent parties, colliding constraints) differentiated mainly
by nervous-system state — regulated people treat colliding constraints as a
shared puzzle (collaboration/negotiation), dysregulated people treat them as
personal threat (conflict). Follows directly from
[[project_structural_misalignment_reframe]] (memory): structural pressure is
the one thing Thimble surfaces, before and after open conflict, not a
separate "collaboration mode" vs. "conflict mode."

Implication: the same dispute-resolution arc Thimble already runs reactively
(private intake → surface constraints → joint framing → co-authored
deliverable → decoupled async consent) works just as well run proactively, at
a project/sprint kickoff, before any friction exists — producing a team
working agreement (SLAs, review turnaround, escalation path) instead of a
conflict resolution. Rationale for doing it upfront: nervous systems aren't
already flooded, so it's easier than doing the same work after conflict hits.

### Team feedback harvester — synthesize a whole squad's private feedback into shared, depersonalized themes
Extends the existing solo-intake → deflective-reframing → synthesis pipeline
from two people to a whole team. Each member gives Thimble raw, private
feedback (including character-level venting); Thimble strips labels/attacks
in real time and extracts the underlying operational friction; outputs are
anonymized (writing-style/fingerprint stripped, not just names) and grouped
into shared structural themes ("release-readiness tension between
Product/Design wanting fast iteration and Platform protecting stability")
rather than per-person call-outs; raw inputs are purged after synthesis, same
zero-trace posture as the rest of Mend. Final output is a team "Seam"
artifact — concrete working agreements — pushed to retro/wiki/backlog, not a
vague culture report.
- Why this over a normal 360/retro survey: traditional anonymous surveys
  either produce toothless praise (social risk) or unfiltered toxic venting
  (paranoia/witch-hunts); routing everything through Thimble's reframing step
  before synthesis avoids both failure modes.

### Gut-to-heuristic translator — specific to design critique
A narrower sub-case of the same reframing mechanic, aimed at the specific
failure mode where designers struggle to be honest without being negative.
Reviewer dumps their raw, unfiltered gut reaction to Thimble privately
("I hate this design"); Thimble doesn't tone-police, it asks why — 1-2 short
probing turns — until the gut reaction resolves into an objective design
heuristic (cognitive load, visual hierarchy, progressive disclosure, etc.),
then hands back a reframed version the reviewer can actually send. The
designer being reviewed never hears "I hate this"; they get a concrete,
outward-focused question about the artifact instead of a verdict on their
competence.
- Source: conversation 2026-11-10, user-initiated pasted brainstorm
  ("Talk to me about how collaboration negotiation and conflict are
  similar" → team feedback harvester → design-critique variant).
- Where it could plug in: the team feedback harvester would be closest in
  shape to [[project_oss_maintainer_use_case]]'s sibling idea "Loom" (pattern-
  only project retro, anonymized, no individual call-outs) above — likely the
  same app/engine rather than a fourth standalone tool; the design-critique
  variant could be a Swatch-specific reframing step (Swatch already runs
  structured peer design sessions, see "Swatch" above) rather than new
  infrastructure. The upfront-agreement framing is a system-prompt framing
  change, not new code — would extend whichever prompt handles Thimble's
  kickoff/handoff coaching, not add a new flow.
- Why not active: entirely conceptual, no prompts written, no decision on
  whether this is a new feature of Loom, a new mode of Swatch, or a fourth
  thing. Open question raised but not answered in the source conversation:
  should team-wide harvesting run as an async per-sprint check-in, or a
  periodic (quarterly/milestone) 360-style ritual — per
  [[feedback_interrogate_dont_placate]], worth asking the user directly
  rather than assuming either answer.

---

## Suture/Loom convergence + real-time audio decision (2026-11-11)

### Suture and Loom are one intake engine, parameterized by context
Resolves the open question left at the end of the 2026-11-10 entry above
(team feedback harvester vs. a Swatch mode vs. a fourth thing). Conclusion:
intake's job is the same regardless of context — (1) triage: is this safe
to run in the declared format, or does it need to escalate/reclassify
(harassment screening is conflict's version of this; a retro or critique
intake needs the same ability to catch something more serious hiding
under a lower-stakes label), and (2) help the person frame their real
reaction authentically. The actual obstacle is the same across conflict,
retro, and critique: stating a true reaction to someone/something in
front of them carries social cost that makes people flatten or withhold
it (fear of retaliation, fear of blame landing on a teammate, fear of
hurting the designer's feelings) — not anonymity for its own sake.

What varies by context (conflict/retro/critique/etc.) is the question set
and the escalation triggers, not the mechanism. The declared mode, picked
by whoever creates the session link ("not sure" as a fallback), is a soft
starting hypothesis that steers the first questions, not a locked
category — intake should be able to reclassify mid-flow if what it's
hearing doesn't fit the declared mode.

Does NOT overturn the "family note, not a merge" distinction above between
Suture/Splice/Swatch's live-session trust models (two-party private
resolution vs. public group vote vs. warmth-building collaboration) — what
a live session resolves into still forks by context. This is specifically
about the *intake* step underneath all of them being one shared mechanism.

### Seam case model: case = recurring arc, a session is an event inside it
A Suture session (or a retro/critique session, once those exist) should
not create a new Seam case by default. A case is the ongoing arc — a
specific conflicting pair, or "Team X's sprint retros," or a design team's
critique cadence — and each live session is an event logged against that
case, contributing to its running plan/pattern log the same way plan
steps accumulate today. New case only for a genuinely new arc (different
people, different team, different stated goal), not one case per session,
which would lose the cross-session pattern that Loom-style synthesis
exists for in the first place.
- Schema implication, not yet built: `cases` currently assumes one
  continuous plan; would need a way to tag which session/sprint each plan
  step or pattern came from to support multiple sessions per case.

### Real-time layer: audio through Thimble, video is bring-your-own (decided 2026-11-11)
Considered and rejected: embedding Suture/group sessions as a panel
inside Zoom/Teams/Slack, the pattern Splice already uses for Zoom.
Rejected for two reasons: (1) it's not one build — Zoom Apps SDK, Teams
meeting extensions, and Slack (which has no real equivalent; its Calls
API registers third-party call providers, it doesn't let you embed a UI
inside a Huddle) are three incompatible integration surfaces, each its
own dev-account/certification effort; (2) for conflict mode specifically,
running inside the employer's Zoom/Teams tenant undermines the zero-
trace/neutral-party promise the trust model depends on (admin-controlled
cloud recording, retention policy, legal hold).

Decided instead: Thimble owns the full two-way audio channel itself,
maturing the existing `joint-session-audio` LiveKit + streaming-STT +
hard-cut-classifier prototype (not yet integrated with `suture/`'s
conversational logic). This also solves a problem embedding couldn't:
Thimble speaking/interjecting live has nowhere to go if it isn't actually
in the audio path. Video is explicitly NOT owned by Mend for now —
participants may keep their own Zoom/Teams/whatever open, muted, just to
see each other's faces. Two known frictions with that workaround, not
blockers: A/V sync drift (video and audio ride two independent
transports with their own jitter/buffering) and echo/double-audio if
someone forgets to mute their video tool's mic. Applies to conflict mode
now; the same owned-audio approach is the default starting point for
retro/critique sessions too, rather than reopening the platform-embedding
question per mode.

---

## Open design questions

### Safety-floor tone must branch on whether the user already knew it was harassment
When the safety floor trips, the underlying mechanics don't change — same
classifier, same halt, same Victim Agency Gate offering report-to-HR /
export-locally / flush-memory. But the user arrives in one of two very
different mental states, and Thimble's tone needs to match which one it is,
not use one generic script for both:

- **User already knows it's harassment**: they came in consciously seeking
  self-defense, documentation, or a safe escalation path, scared mainly of
  retaliation. The Agency Gate lands as an expected protective service —
  it confirms their diagnosis and hands them the safety container they were
  looking for. Thimble's role here is a documentation/reporting bridge; risk
  of alienating them is low since they already expect formal boundaries.
  Gate tone: "Here is the factual brief of what happened. You choose if it
  goes anywhere."
- **User thinks it's routine friction** (e.g. "my manager's being unfair
  about my schedule, I just need a script to get them off my back"):
  tripping the safety floor is a disorienting revelation — they came in
  thinking it was a personality clash or their own communication problem,
  and the system is telling them it's actually a statutory violation.
  Thimble's role here is an objective reality mirror catching an invisible
  boundary violation. Risk of alienation is high: if it sounds like an
  alarmist HR cop, the user may panic, feel surveilled, and backpedal
  ("wait no, don't report anything"). Gate tone needs to be calmer and more
  reassuring: name the violation without inducing panic, emphasize nothing
  has been sent yet and they have full control, before presenting choices.

Framing implication: if Thimble is ever positioned/marketed as an
"anonymous harassment tip line," it only catches people in the first
bucket — the junior engineer who thinks a manager conditioning PR approval
on personal calls is "just tech culture" will never open a harassment
hotline. Framing it as a routine communication/sanity-check tool with an
integrated safety floor is what catches both, since the second bucket only
ever shows up by venting about something else first.
- Source: conversation 2026-11-03, pasted user writeup framed as "what's
  the difference between someone describing something and not knowing it
  was harassment vs. already knowing."
- Where it could plug in: whichever prompt renders the Victim Agency Gate
  copy when the safety floor trips (ties directly into the "disclose
  upfront vs. reactively" open question right below, and into the overall
  Phase 3 consented/anonymized escalation design in `ROADMAP.md`) — would
  need the classifier or surrounding context to carry some signal of which
  bucket the user is in, not just that the floor tripped.
- Why not active: tone/copy branch not yet written — flagged here so the
  two-bucket distinction doesn't get flattened into one generic halt
  message when this gets built.
- **Status (2026-11-03): built.** Added a tone branch to the floor
  disclosure in `facilitator-intake-system-prompt.md` (employee-conflict
  path), right after the "order matters" paragraph: reads whether the
  employee's own opening framing already treated this as mistreatment vs.
  routine friction, and delivers the (unchanged) disclosure + choice
  plainly in the first case, more slowly and reassuringly in the second.
  Not yet tested against real transcripts.

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

### Thimble reflection pattern: ask for their read, offer one concrete scenario, then follow their lead
A specific conversational move for how Thimble should respond when a user is
stuck or venting without a clear diagnosis yet (e.g. "my coworker just shut
down on me"). Instead of guessing the cause or interrogating with multiple
questions, Thimble does two things in one short reply: asks the user for
their own read on what happened, then offers exactly one concrete, grounded
hypothesis to react to ("Usually when someone shuts down like that, it's
less about the work and more that they're underwater and triaging badly.
Does that ring true, or is something else driving this?"). The user then
either confirms it or corrects it, and Thimble's next line branches off
whichever one they gave — no flattery ("trust your gut"), no multi-question
menu, no claim to already know the answer.
- Why one hypothesis and not a menu: a single testable guess is something a
  brain can push against (confirm or correct); a multiple-choice list makes
  an already-agitated user do analysis work instead of reacting.
- Why ask for their read first: treats the user as the one with ground
  truth, not someone to be diagnosed — this is the "mirror, not lecture"
  posture generally wanted for Thimble.
- Both branches (confirmed or corrected) should land on a concrete next
  action in the same reply, not just validate the read and stop.
- Source: conversation 2026-11-03, pasted user writeup titled "The
  Two-Sentence Move."
- Where it could plug in: whichever Thimble coaching prompt handles the
  "user describes a stuck/frustrating interaction, cause unclear" case —
  likely the same family as the Phase 1 coaching fork
  (`facilitator-coaching-system-prompt.md` or similar, per recent commit
  "fork Phase 1 between framing help and understanding why").
- Why not active: this is a reusable response pattern/heuristic, not yet
  written into any system prompt — flagged here so it can be deliberately
  incorporated rather than reinvented ad hoc.
- **Status (2026-11-03): built.** Added as its own guidance paragraph in
  `facilitator-manager-coaching-system-prompt.md` Phase 1, right where the
  manager picks the "help me understand why" branch: ask for the manager's
  own read first, then offer exactly one concrete hypothesis, then branch
  on confirm/correct. Only written into the manager-coaching prompt so far,
  not into the employee-conflict path's beat 2 (which already has its own,
  slightly different, driver-guessing mechanic in
  `facilitator-case-plan-system-prompt.md`). Not yet tested against real
  transcripts.

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
