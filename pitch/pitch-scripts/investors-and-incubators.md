# Pitching Investors & Incubator Partners

Audience cares about: market size, defensibility, unit economics, founder-market fit, traction. Not about feelings — translate everything into operational cost and risk.

## Opening line

> Modern product and engineering squads don't fail from technical incompetence. They fail because unmanaged peer friction quietly bleeds 2.8 hours of focus per worker every week and drives key talent to resign. Today's enterprise tools force a broken choice: file an adversarial HR complaint, or vent into a toxic backchannel.

## The pitch, in order

1. **Pain, quantified.** 2.8 hours/week per employee (CPP Inc.). Replacing one departing mid-level hire costs 1.5x–2x their annual salary once recruiting, the vacancy gap, and ramp-up time are counted (Gallup/SHRM).
2. **The gap.** Enterprise tools are built for surveillance and audit trails — Slack, Teams, Workday. Employees will never be vulnerable inside a tool their employer owns. That's a structural, not a feature, gap.
3. **The product.** Mend: a deterministic, three-stage mediation engine (solo intake, guided turn-taking, decoupled agreement) running in volatile memory, with a non-configurable safety floor that escalates real compliance issues to HR automatically.
4. **The moat.** Independence from enterprise IT/HR control is required for user trust, not optional. A hardcoded safety floor and ephemeral-execution architecture both resist being copied by an incumbent that's built around retention and audit trails.
5. **Unit economics.** Inference cost per resolved conflict is well under a dollar on commercial APIs today. Flat per-seat pricing at $7,000–$9,000/year for a 100-person org clears enterprise procurement thresholds while staying high-margin.
6. **Traction.** Working multi-agent prototype, live user testing underway, benchmarked against raw Claude and a shorter alternative prompt across an 11-scenario suite.
7. **The ask.** State it plainly: pilot introductions, employment counsel access, or capital — whichever actually applies to this conversation.

## Objection: "You're a solo, non-technical founder"

Don't deflect it.

> I built and shipped the full working architecture — the state machine, the safety-floor audit loop, the turn-taking logic — using AI-assisted development, to validate the mechanics with real users fast. That part's proven now. What I need from this program/round is an infrastructure lead to take it through enterprise security review, not someone to build the first version.

Lead with the live product and real test data every time this comes up. Traction answers the credibility question faster than a resume does.

## Objection: "Isn't this just an AI wrapper?"

> No — it's a deterministic state machine with a bounded LLM doing discrete translation tasks, not an open-ended chatbot. An independent Watcher process audits every turn before it reaches the screen. If something steps outside the procedure, the system halts programmatically, not based on the model's judgment in the moment.

## Reframing cheat sheet

| Sounds soft | Reframe as |
|---|---|
| Helping coworkers get along | Preventing sprint-velocity drag and avoidable attrition |
| A private place to vent | A low-friction, bottom-up adoption wedge — no enterprise sales cycle needed to get the first real user |
| Radical privacy | Volatile-memory execution — removes e-discovery/subpoena liability for enterprise legal |
| A gentler alternative to HR | Administrative deflection — HRBPs get hours back |

See [../docs/pitch-strategy/02_COMMERCIAL_PRICING_STRATEGY.md](../docs/pitch-strategy/02_COMMERCIAL_PRICING_STRATEGY.md) for the full pricing/ROI model behind the numbers above.
