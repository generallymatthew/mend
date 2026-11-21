# Thimble Retro — Product Roadmap

**Renamed 2026-11-21** (codename `Loom` stays as the directory/internal name; dated entries below predate the rename and keep using the old name, as the historical record of what was actually built at the time).

Loom is a pattern-only project retro tool: after a project/sprint wraps, it
interviews each team member separately, lets them be fully honest about
what happened, and distills answers across the group into recurring
structural/process patterns — never individual names or call-outs. The
rationale: naming names in a shared report makes people vulnerable to
blame, which suppresses honesty; stripping identity out and reporting only
patterns is what lets people actually tell the truth.

Full writeup: `../../IDEAS.md`'s "Pattern-only project retro" section.

Note: "Loom" is also used elsewhere in this repo as a sewing/textile
metaphor for the ephemeral runtime enclave (see
`../../docs/pitch-strategy/04_METAPHORS_AND_PRODUCT_LEXICON.md`'s "The
Loom" entry) — that's a different, unrelated use of the same word and isn't
this app.

Per the 2026-10-17 app-concept ranking in `../../IDEAS.md`, Loom ranks #4 of
seven: real recurring pull (every team does retros; "retros surface
complaints but never fix the structural cause" is a known failure mode),
good differentiated mechanism (private interviews distilled into structural
patterns, e.g. "team's overworked, that's why PRs slip" — not anonymization
of blame, root-cause diagnosis), but furthest from built of the ranked apps
and lower-stakes pain than the top three.

## Phase 0 — Concept

- [x] Scope the interview flow: what Loom asks each team member,
      separately, after a project/sprint wraps (`apps/facilitator-loom-intake-system-prompt.md`)
- [x] Per-person interview prototype, text only, local (`server.py` +
      `static/index.html`), browser-pane verified end to end
- [x] Build the distillation/pattern-extraction logic
      (`apps/facilitator-loom-distillation-system-prompt.md` +
      `server.py`'s `/api/distill`): reads every confirmed contributor's
      findings for a sprint, only reports a pattern corroborated by at
      least 2 independent contributors (substance match, not matching
      wording), drops uncorroborated singletons entirely rather than
      softening them. Browser-pane verified with 4 simulated interviews:
      correctly merged 3 differently-worded review-bottleneck complaints
      into one structural pattern, correctly excluded two singleton
      positive findings (standups, deploys) from "what's working" since
      neither had a second corroborating contributor.
- [x] Decide the minimum team size before "patterns" stop being traceable
      back to an individual by elimination — set to 4 (`LOOM_MIN_CONTRIBUTORS`
      env var), not the more obvious-looking 3: with only 3, a 2-of-3
      corroborated pattern can often be narrowed to "the one who didn't
      say it" by elimination. `/api/distill` refuses to run below this
      floor (409, states how many more are needed) rather than silently
      producing a report anyway. Still a first conservative default, not
      a validated number — real org team-size distribution and
      re-identification by writing style are both untested.
- [x] Per-person confirmation gate added to intake (Phase 3 of
      `facilitator-loom-intake-system-prompt.md`): nothing is recorded
      into a sprint's contributor pool until the person has seen a plain-
      language readback of their own findings and given an explicit,
      specific-to-that-readback yes (`confirmed: true` in the signal) —
      not just reaching the end of the conversation. They can drop, reword,
      or add findings before confirming, as many rounds as needed.
- [x] Decide output format (2026-11-21): aggregated pattern report only,
      emailed to whoever initiated the sprint's retro, nothing persisted
      server-side. Considered and rejected a Seam-style durable
      `plan_steps` table (Seam's case plan is meant to be revisited over
      weeks, which is a different job): Thimble Retro's one job is
      helping people be honest without fear of blame, not being a
      system of record for engineering process. Email reuses the
      existing `smtplib` pattern from `../thimble-resolve/digest.py` and
      `../thimble-resolve/feedback_alert.py` -- no new infrastructure.
      Where the team's org keeps that report after (Jira, Confluence,
      nowhere) is out of scope, same as a scrum master's notes today.
      Not yet built: capturing the initiator's email at `/api/start`,
      and the actual send step.
- [ ] Decide whether the live group session (not yet built -- see
      `../../system diagrams/spring-retro-flow.html`) produces anything
      beyond the pattern report, e.g. a decisions/action-items list the
      team lands on together during the call. No mechanism for this
      exists yet; the distillation step only extracts structural
      patterns (what's wrong/working), not commitments going forward.
