# Swatch — Product Roadmap

Swatch is preflight collaboration for designers who don't know each other
yet — not conflict resolution. Two (or more) designers who haven't worked
together before get paired on a shared design problem, and Thimble runs a
structured process with two equal goals: the working relationship gets
better, and the design objective actually gets finished. Same
"structural, not personal" spirit as the rest of Mend, applied before
friction exists instead of after.

No code exists yet — this folder is a placeholder until "The Workflow" is
exported out of its design artifact into a real prototype. Full writeup:
`../../IDEAS.md`'s "Swatch — preflight collaboration for designers who
don't know each other" section.

Per the 2026-10-17 app-concept ranking in `../../IDEAS.md`, Swatch ranks #5
of seven: narrower, lower-stakes buyer (design leads, not broad org pain),
moat borrowed from Suture's facilitation tuning but unproven in this
domain, real platform risk (Figma could ship this natively).

## Phase 0 — Design, not yet built

- [x] "The Workflow" six-step process designed (warm-up, solo work,
      facilitated presenting with an ordered question queue, keep-presenter-
      talking fallback, consensus/reaction aggregation, repeat-from-
      converged-direction loop)
- [x] Platform decision: runs as a companion panel over a real video call
      (Zoom first, via the Apps SDK) — Swatch does not build its own video
      or screen-share UI, same architecture call as Splice
      (`../group-session-app/splice-product-roadmap.md`)
- [x] Single-driver v0 (not full realtime multiplayer sync) decided as the
      first build target
- [ ] Export the Claude Artifact mockups (workflow canvas vs. two rejected
      alternatives, solo-brainstorm prompt mock, four app-screen UI
      mockups) into this repo
- [ ] Fix the pending correction in those mockups: the presenting screen
      currently mocks its own fake screen-share panel, which is wrong now
      that a real call already handles screen share — needs to become a
      companion-overlay layout (order list + question queue only)

## Phase 1 — First build pass

- [ ] Stand up the companion-panel shape, likely reusing
      `../group-session-app/`'s room/WebSocket backend and Zoom Apps SDK
      pattern rather than building from scratch (see Splice's roadmap "Shared
      infrastructure note") — trust model is the opposite of Splice's
      (encouragement/warmth between two people, not neutral group-vote
      mechanics), so the facilitator prompt needs its own tuning, not a
      copy of `facilitator-group-session-system-prompt.md`
- [ ] Resolve open design question: does the consensus step output a ranked
      winner, a merged direction, or just a heatmap of reactions for humans
      to decide from
- [ ] Resolve open design question: who calls "goal achieved" — the group
      by vote, or does it need to clear some threshold on its own
