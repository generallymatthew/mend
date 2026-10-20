# Live-Meeting AI Coach: Feasibility Notes

Exploration of whether Mend should offer a real-time, in-ear or HUD coach during a live 1:1 with a manager (e.g. a "tough talk" video call), and whether disclosing the AI's presence changes the calculus.

## The Appeal

- **Real-time nervous-system brake:** in high-stakes meetings with an authority figure, adrenaline triggers cognitive freeze or defensiveness. A silent visual cue ("Breathe. Don't defend. Ask for their timeline") can act as an emotional stabilizer.
- **Instant reframing:** if the manager deploys deflection ("You're being overly sensitive about scope"), a live coach can suggest a grounded counter-pivot ("I hear your focus on scope; my concern is predictability on release dates").
- **Boundary tracking:** acts as a memory buffer if the conversation drifts into vague commitments — "You wanted a concrete sign-off SLA. Bring it back to that before wrapping up."
- **Compliance-floor alerting:** if the manager crosses into legally hazardous territory (veiled retaliation, protected-class comments), the AI can flag it silently ("Document this timestamp. Do not agree to unilateral terms live.").

## Why It's Usually a Bad Idea

**1. Divided attention.** People can't parse dense text and stay emotionally attuned at the same time. Eyes darting off-camera reads as disconnection, unpreparedness, or evasiveness. Reading a suggestion introduces unnatural 3-4 second pauses that land as either unprepared or evasive.

**2. Wiretap / surveillance exposure.** Streaming live meeting audio into a third-party tool has real legal exposure:
- Two-party consent laws (California, Massachusetts, etc.) generally require the other party's knowledge before recording or streaming their voice into a transcription service.
- Corporate IT/DLP tooling on a company laptop may flag background audio interception as unauthorized data exfiltration.

**3. Hallucination under fire.** If the model misreads sarcasm, subtext, or company jargon and feeds an aggressive or ungrounded line, reading it aloud unfiltered can cause immediate, irreversible damage to the relationship or the user's standing.

## The Better Compromise: Ambient Telemetry, Not a Script

Never feed the user full sentences to read live — that produces a disjointed, robotic conversation. Instead, build it like a flight instrument:

```
[LIVE HUD DASHBOARD]
┌────────────────────────────────────────────────────────┐
│ TEMPO: [Too Fast - Slow Down 20%]                       │
│ TALK TIME: You (65%) | Boss (35%) -> [PASS THE MIC]     │
│ MOOD: Defensive -> [Pivot to Curiosity]                 │
│ CORE GOAL: Lock PR SLA under 24 hrs [NOT YET MET]       │
└────────────────────────────────────────────────────────┘
```

- **Micro-pacing cues (1-2 words only):** "Pause." "Acknowledge." "Listen."
- **Talk-ratio balance meter:** visual indicator of who is monopolizing the conversation.
- **Pre-baked cheat-sheet anchors:** instead of generating live text, just highlight the relevant bullet from the user's own pre-session cheat sheet based on what the counterpart just said.

In short: AI as a live teleprompter fails. AI as an ambient pacing stabilizer can work.

## Disclosing the AI to the Boss

Telling a manager "I have an AI agent listening to help me argue better" is almost always going to backfire, even though it solves the two-party-consent problem:

- **"I'm being deposed."** The manager assumes a dossier is being assembled for HR or legal, not that the tool is for clarity.
- **"You see this as a battle, not a collaboration."** Framing like "present my argument" signals litigation rather than joint problem-solving, and puts the manager on the defensive before the point is even made.
- **"You lack executive presence."** Needing an algorithmic prompter to communicate can read as an inability to navigate routine professional pressure.
- **"Did IT/Legal approve this?"** Most managers will treat a third-party tool ingesting internal strategy and personnel discussions as a policy violation and shut the call down.

**The one exception — symmetrical, neutral mediation.** An AI agent only works on a live employee/manager call when it is symmetrical, agreed upon by both parties beforehand, and belongs to the process rather than to one side:

> "We've had misaligned expectations on sprint priorities. Would you be open to running a 10-minute structured check-in using an objective turn-taking tool to keep us both focused on operational blockers?"

That framing — a neutral process both people opted into — is the core thesis behind Mend. Even then, peer-to-peer mediation is safer than manager-to-report mediation, because of the vertical power imbalance.

## Recommendation: Keep the AI Asynchronous and Preparatory

1. **Use the AI before the call** — run the situation through the intake prompt to separate emotional venting from the operational ask, and build a "Tough Talk Cheat Sheet."
2. **Show up alone and grounded** — walk in with 2-3 core points on a private notepad, clear boundaries, non-defensive framing.
3. **Preserve authentic presence** — managers respond to someone who can look them in the eye and state their needs calmly, not to someone visibly consulting a third-party scaffold.

See [09_PRACTICE_SESSION_MEMORY_SCHEMA.md](09_PRACTICE_SESSION_MEMORY_SCHEMA.md) for how repeated practice sessions before the real call can stay lightweight without full transcripts.

## The Awkwardness Barrier: Why This Doesn't Stay Top-of-Mind

Real conflict is not a daily, weekly, or even monthly occurrence for most
managers. If the only time a manager touches a tool like this is during an
acute dispute, they forget it exists between incidents — there's no reason
to open it, and no habit loop to bring them back when they actually need it.
To be reached for in a real conflict, Mend has to already be part of the
manager's routine for something they need on a recurring cadence, not
sitting unused waiting for a crisis.

### On-Cycle Touchpoints (staying front-of-mind)

- Bi-weekly 1-on-1 prep and agenda de-biasing.
- Pre-sprint cross-functional handoff and dependency mapping.
- Async tone-check for high-stakes Slack announcements or emails.
- Calibration- and promotion-cycle narrative framing.
- Quarterly blameless retro and post-mortem ingestion.

These are not conflict mediation; they're routine manager maintenance. The
dispute-handling capability (Thimble's case-plan flow, see
`../../apps/manager-app/THIMBLE_MINDSET.md`) rides along as the same tool
the manager already has open for these lower-stakes, higher-frequency tasks.

### Lowering the Awkwardness Barrier Further

- Frame every session as **meeting facilitation**, never as dispute
  mediation — see the dynamic-framing table in `THIMBLE_MINDSET.md`.
- **Solo-first**: zero requirement to invite anyone else before getting
  value.
- **Double opt-in neutral avatars**, defaulting to voice (see
  `11_PRODUCT_ARCHITECTURE_AND_STRATEGY_BLUEPRINT.md` §2, "Double Opt-In
  Shielding").
- Turn-taking timeboxes and blind prioritization during live or async
  planning.
- Automated export of agreed items to Jira or Linear (the Seam, made
  concrete as tickets).

## Calendar-Aware Pre- and Post-Meeting Workflow

A concrete shape for the "on-cycle" idea above: let the AI (Thimble) sit
across the whole arc of a meeting instead of only the live middle, which is
the part most fraught with the wiretap and divided-attention problems
described above.

**Before the meeting:**
- **Calendar scanning** — reads upcoming 1-on-1s and cross-team syncs to
  identify meeting type and attendee roles.
- **Pre-meeting intent calibration** — prompts the manager shortly before
  the meeting to name desired outcomes, non-negotiable boundaries, and any
  decision that actually needs to be made.
- **Stakeholder constraint injection** — surfaces the attendee's known role
  metrics and likely friction points (e.g. reminding the manager of a
  platform's uptime target before a sprint review with that team).
- **Opening rail generation** — 2-3 short framing phrases to anchor the
  session's scope and head off rabbit-holing, handed to the manager before
  the call starts, not read to them live.

**During the meeting:** the ambient HUD described above (tempo, talk-time,
agenda pings, deflection alerts) — pre-baked, not live-generated text.

**After the meeting:**
- **Edge audio processing** — analyzed locally/in-enclave, in volatile
  memory, never as a cloud recording bot.
- **Action-item and SLA extraction** — converts verbal commitments into
  concrete operational items (e.g. "Design submits specs 48 hours prior").
- **Role-anonymized case logging** — updates the manager's own case-state
  anchor (see `THIMBLE_MINDSET.md`'s "case-state anchor" section) with
  progress and next actions; no raw audio or transcript is ever stored.
- **Follow-up communication staging** — pre-drafts a de-biased, neutral
  summary for Slack or email confirming agreed next steps, without
  defensive language.

**Open tension worth tracking:** this calendar-aware, note-taking-adjacent
shape needs to be reconciled against the scope boundary in
`../../apps/manager-app/PHILOSOPHY.md` ("What Mend Is Not" — not a
note-taker or meeting summarizer). The distinction to hold onto: Mend never
produces a record *of the meeting* for later review; everything it
surfaces is either ephemeral in-the-moment pacing help, or a forward-looking
operational commitment (the Seam), never a transcript or minutes.

## Buyer Framing: Would a Manager Pay for This Themselves?

- **Out-of-pocket personal subscription** ($0-15/mo): unlikely — managers
  treat this as an employer responsibility, not something to fund out of
  their own pocket to solve a company problem.
- **Corporate L&D / coaching stipend** ($200-500/yr): high fit — managers
  routinely expense "executive coaching," "leadership development," or
  "productivity" budgets on exactly this kind of private career tool.
- **Discretionary team software card** (departmental expense): moderate-to-
  high fit — managers already expense tactical team utilities that remove
  daily friction.

The moments that actually drive a manager to reach for this tool: acute
dread before an imminent performance conversation or firing; sharp friction
with a peer manager blocking a deliverable; pressure to push back upward
without risking their own standing; and personal composure under pressure,
framed as professional tooling, never as remedial counseling.
