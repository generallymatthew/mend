# Hem — Product Roadmap

Hem is a cross-platform desktop writing assistant: invoke it from any other
app (highlight text, bring it in) and it helps you write or rewrite a
message so it makes your point without causing conflict, regardless of
which app you're sending it from.

No code exists yet — this folder is a placeholder. Full writeup:
`../../IDEAS.md`'s "Hem — cross-platform writing assistant for calm
communication" section.

Note: "Hem" is also used elsewhere in this repo as a sewing/textile
metaphor for boundaries and scope-setting (see
`../../docs/pitch-strategy/04_METAPHORS_AND_PRODUCT_LEXICON.md`'s "The Hem"
entry) — that's a different, unrelated use of the same word and isn't this
app.

Per the 2026-10-17 app-concept ranking in `../../IDEAS.md`, Hem ranks #7 of
seven, last: broadest surface appeal but essentially no defensible
position — every major platform (Grammarly, Gmail, Slack) already ships
tone/rewrite AI natively, and the OS-level text-capture engineering lift is
unrelated to anything already built in this repo.

## Phase 0 — Concept, not yet built

- [ ] Decide which platform to target first for OS-level text capture
      (hotkey/highlight capture) — no mechanism built yet, open question on
      macOS vs. Windows vs. both
- [ ] Scope how much of the existing facilitator tone/framing logic from
      `facilitator-persona.md` and the other system prompts can be reused
      here, vs. needing its own prompt built for single-message rewriting
      rather than multi-turn conversation
- [ ] Re-evaluate whether this is worth building at all before investing
      further, given the #7 ranking and the crowded competitive field
      (Grammarly, Gmail Smart Compose, Slack's own AI) — this is the
      weakest-moat concept of the seven and the one most likely to get
      cut rather than scheduled
