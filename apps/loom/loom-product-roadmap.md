# Loom — Product Roadmap

Loom is a pattern-only project retro tool: after a project/sprint wraps, it
interviews each team member separately, lets them be fully honest about
what happened, and distills answers across the group into recurring
structural/process patterns — never individual names or call-outs. The
rationale: naming names in a shared report makes people vulnerable to
blame, which suppresses honesty; stripping identity out and reporting only
patterns is what lets people actually tell the truth.

No code exists yet — this folder is a placeholder. Full writeup:
`../../IDEAS.md`'s "Pattern-only project retro" section.

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

## Phase 0 — Concept, not yet built

- [ ] Scope the interview flow: what Loom asks each team member,
      separately, after a project/sprint wraps
- [ ] Build the distillation/pattern-extraction logic (reuse the existing
      LLM-facilitator interview pattern and the "anonymized aggregate,
      never per-person" principle already used elsewhere in this repo's
      org-level usage dashboard idea)
- [ ] Decide the minimum team size before "patterns" stop being traceable
      back to an individual by elimination — a 2-person team can't
      actually anonymize, so this needs a real floor before launch, not
      just a style guideline
- [ ] Decide output format: aggregated pattern report only, or also a
      private per-person reflection back to the individual who gave it
