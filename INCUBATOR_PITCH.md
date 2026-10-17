# Incubator Pitch Script

Draft application answers and talking points for incubator/accelerator submissions (CED GRO, Launch Chapel Hill, American Underground, etc.). See [FUNDING.md](FUNDING.md) for the submission calendar. See [docs/pitch-strategy/](docs/pitch-strategy/) for the deeper strategy docs this draws from, especially [01_EXECUTIVE_SUMMARY.md](docs/pitch-strategy/01_EXECUTIVE_SUMMARY.md) and [04_METAPHORS_AND_PRODUCT_LEXICON.md](docs/pitch-strategy/04_METAPHORS_AND_PRODUCT_LEXICON.md). For investor- and HR-specific variants, see [pitch-scripts/](pitch-scripts/).

**Tagline:** Heal the rift. Leave no trace.

## 1. Company name, URL, one-line description

- **Name:** Mend
- **URL:** https://mend.work (or current live demo link)
- **One-line:** Mend is an autonomous, confidential peer-resolution protocol that resolves everyday workplace friction before it reaches HR, running in volatile memory with zero persistent transcripts.

## 2. The problem

The average employee loses 2.8 hours a week to unresolved workplace friction (CPP Inc.). Today's tools force a broken choice:

1. Vent to peers or in backchannels — releases nothing systemic, drags teammates into the toxicity.
2. Escalate to HR or a manager — high-friction, adversarial, risks being tagged "difficult" for something that was just a communication breakdown.

Most routine friction (missed PR reviews, blunt Slack tone, sprint-priority conflicts) sits unresolved in this "missing middle." It drains focus, damages morale, and drives otherwise-avoidable attrition — replacing a departing mid-level employee costs 1.5x to 2x their annual salary once recruiting, lost productivity during the vacancy, and ramp-up time are counted (Gallup/SHRM benchmark).

## 3. The solution

Mend runs a three-stage mediation flow:

1. **Solo intake (the Spool).** One person vents privately, Mend separates emotion from the operational root cause, and they can leave with an actionable script even if the other person never joins.
2. **Guided turn-taking (the Warp & Weft).** If both consent, Mend enforces symmetrical, asynchronous dialogue — no live social pressure, no performative truce.
3. **Decoupled agreement (the Seam).** Working agreements are reviewed and accepted separately, away from the pressure of the live room.

Like a dissolving suture, Mend holds the relationship together while it heals, then disappears — no persistent transcripts, no manager surveillance, no career penalties.

An independent supervisor process (the Watcher) audits every turn in milliseconds and enforces a non-configurable safety floor: any sign of Title VII harassment, discrimination, or a physical threat halts the session and routes it straight to HR.

## 4. Why this is defensible, not just "an AI wrapper"

- **Trust requires independence.** Employees won't be vulnerable inside a tool HR or IT controls. Being a neutral third party is an architectural requirement, not a marketing angle.
- **Deterministic safety floor.** The Watcher's triggers are hardcoded, not a prompt a customer can configure away — this is the thing that lets a cautious HR buyer say yes.
- **Unit economics support a flat, low-touch price.** Inference cost per resolved conflict is well under a dollar on commercial APIs today; margins stay high enough to price at $7,000–$9,000/year per 100-person org, below the radar that triggers procurement friction.

## 5. Current traction and validation stage

- Functional multi-agent prototype live and in active user testing.
- Core turn-taking, safety-floor triggers, and the Watcher audit loop are built and benchmarked against raw Claude and an alternative shorter prompt ("CF") across an 11-scenario test suite — see `intake-app/tests/`.
- Next milestone: a time-boxed 50–100 pair pilot, measuring agreement durability at 14 days and whether real pairs reach a decoupled agreement at all, before approaching enterprise design partners.

## 6. Why this incubator, and the ask

Adapt per program, but the core ask is usually:

1. **Employment counsel access** — stress-test the safety-floor trigger taxonomy with a labor law mentor so the Title VII/harassment boundary is airtight before any enterprise pilot.
2. **Design partner introductions** — 3–5 pilot teams (20–100 person engineering/product orgs) willing to run the 30-day pilot described in [docs/pitch-strategy/13_PITCHING_MEND_TO_ENTERPRISE_HR.md](docs/pitch-strategy/13_PITCHING_MEND_TO_ENTERPRISE_HR.md).
3. **Peer network** — other regional B2B/SaaS founders navigating a solo, non-engineer founding path.

## 7. Handling the solo, non-technical-founder question

Don't dodge it. Answer directly:

> "I built and shipped this working architecture myself — the state machine, the turn-taking logic, the Watcher safety audit — using AI-assisted development, to prove the workflow and get it in front of real testers fast. The mechanics are validated now. I'm using this program's network to find an infrastructure/backend lead to take it through enterprise security and compliance review, not to get someone to build the first version for me."

Lead every conversation with the live product and real user data, not the job title. "Product designer and systems architect who shipped an autonomous dispute-mediation engine currently in live testing" lands differently than "UX designer with an idea."

## 8. Reframing table (for application copy)

| Sounds soft | What it actually is |
|---|---|
| Helping coworkers get along | Preventing sprint-velocity drag and avoidable attrition |
| An off-the-record place to vent | A bottom-up adoption wedge — no enterprise sales cycle required to get the first user |
| Radical privacy so people aren't scared | Volatile-memory execution that removes e-discovery/subpoena liability for enterprise legal teams |
| A gentler alternative to HR | Administrative deflection — HRBPs recover hours currently spent as informal arbiters |

## 9. Open line for a cold outreach / warm intro email

> We've built an autonomous, confidential peer-resolution protocol that defuses everyday workplace friction before it reaches HR, running entirely in volatile memory with zero persistent transcripts. We're running early pilots now and refining the safety-floor architecture with [incubator]'s network in mind — would you be open to a short look at how we handle adoption friction in zero-retention enterprise tooling?
