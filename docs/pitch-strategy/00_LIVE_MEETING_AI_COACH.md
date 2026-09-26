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
