# Swatch — Product Roadmap

Swatch covers two related things under one app, distinguished mainly by
headcount, per the 2026-11-18 decision in `../../IDEAS.md`'s "Swatch
design-crit workflow resolved" entry: **preflight collaboration** (two or
more designers who don't know each other yet, paired on a shared design
problem before friction exists) and **design critique** (reviewers giving
honest feedback on a specific artifact). Both run on the same two-phase
shape — a private intake pass per person, then a live group session — not
conflict resolution in either case. Same "structural, not personal" spirit
as the rest of Mend.

Per the 2026-10-17 app-concept ranking in `../../IDEAS.md`, Swatch ranks #5
of seven: narrower, lower-stakes buyer (design leads, not broad org pain),
moat borrowed from Suture's facilitation tuning but unproven in this
domain, real platform risk (Figma could ship this natively).

## Phase 0 — Design

- [x] "The Workflow" six-step live-session process designed (warm-up, solo
      work, facilitated presenting with an ordered question queue,
      keep-presenter-talking fallback, consensus/reaction aggregation,
      repeat-from-converged-direction loop)
- [x] **Platform decision superseded (2026-11-18):** no longer a companion
      panel over Zoom via the Apps SDK. Matches the 2026-11-11
      "Real-time layer" decision in `../../IDEAS.md` (Suture/Loom
      convergence entry) instead — Thimble owns the live audio channel
      directly (maturing `../joint-session-audio`'s LiveKit prototype, same
      as Suture), video is explicitly bring-your-own (Zoom/Teams/whatever,
      muted, just to see faces). Rejected the Apps-SDK/companion-panel
      route for the same two reasons Suture's decision gave: it's three
      incompatible per-platform integration surfaces, not one build, and
      Thimble speaking/interjecting live has nowhere to go if it isn't
      actually in the audio path.
- [x] Single-driver v0 (not full realtime multiplayer sync) decided as the
      first build target for the live session
- [x] **Design-crit workflow resolved (2026-11-18)**, full writeup in
      `../../IDEAS.md`: async, one-off per artifact (not a recurring
      cadence like Loom's retro). Two channels with different attribution
      rules — (1) private gut-reaction-to-heuristic reframing, reusing
      Loom's intake engine but posted **attributed**, not anonymized/pooled
      (a crit's value depends on following up with the actual person; no
      corroboration floor, a single reviewer's catch is often the most
      valuable thing in a crit); (2) an anonymous clarification relay (not
      yet built) letting anyone route a follow-up question through Thimble
      privately, answered from the real reframing transcript or relayed to
      the original commenter, answers posted publicly to the whole group.
      Deniability for (2) needs a genuine baseline rate of Thimble's own
      self-initiated questions plus normalized phrasing — flagged as a real
      open engineering problem, not a solved default.
- [ ] Export the Claude Artifact mockups for "The Workflow" (workflow
      canvas vs. two rejected alternatives, solo-brainstorm prompt mock,
      four app-screen UI mockups) into this repo
- [ ] Fix the pending correction in those mockups: the presenting screen
      currently mocks its own fake screen-share panel, which was wrong even
      under the old companion-panel plan and is more clearly wrong now —
      video (including any screen share) is entirely bring-your-own, this
      app's UI should only ever show the order list + question queue +
      audio controls

## Phase 1 — First build pass

- [x] **Design-crit intake built** (`server.py`, `static/index.html`,
      `../facilitator-swatch-intake-system-prompt.md`), modeled directly on
      `../loom/server.py`'s shape. One reviewer, one artifact, one private
      session: raw reaction → probed toward a design heuristic → read back
      → confirmed → recorded **attributed** via `GET /api/notes`. No
      distillation step, no contributor floor — each note stands alone.
      Verified live against the real Anthropic API in-browser: "I hate this
      checkout flow, it's cluttered" correctly resolved (one probing turn)
      into "four CTAs competing for attention, no clear visual hierarchy
      pointing to the primary action," read back verbatim, only recorded
      after an explicit confirming yes to that exact wording, correctly
      attributed to the reviewer's name in the notes view. No console
      errors. Text only, no voice, in-memory only (see `README.md`).
- [x] **Anonymous clarification relay built (2026-11-21)** (`server.py`'s
      `handle_live_ask`/`find_grounding_transcript`/`build_relay_turn`,
      the `ws_private` message type on the live WebSocket, the new "Ask
      Thimble privately" box in `static/index.html`'s live-session view,
      the relay section added to `../facilitator-swatch-live-system-
      prompt.md`). Rescoped from Phase 0's framing before building: a
      forced baseline rate of self-initiated questions would fight the
      house style (every other facilitator prompt explicitly avoids
      manufactured turns), and phrasing alone can't hide a relay's
      specificity either. Built for **plausible deniability, not
      statistical indistinguishability** — Thimble answers a privately
      submitted question directly when the asking reviewer's own private
      intake transcript grounds a real answer, or poses it to the note's
      author otherwise, either way posting to the whole room in its own
      voice with no "a question came in" framing. The timing correlation
      (a question lands right after someone privately asked something) is
      an acknowledged, documented limit, not something this build claims
      to solve. Verified live against the real Anthropic API in-browser:
      Jordan's confirmed note ("checkout/promo/save/back-to-cart all
      styled identically") was on the floor; a private question from
      "Sam" asking whether Jordan meant the promo field specifically or
      the whole button row got answered directly and correctly from
      Jordan's grounding transcript, posted to the room with no mention of
      Sam or of a private channel. No console errors.
- [x] **Live crit-side group session built, text-first (2026-11-20)**
      (`server.py`'s `LiveSession`/`/ws/live/{artifact}/{participant_name}`,
      `static/index.html`'s "Live crit session" view,
      `../facilitator-swatch-live-system-prompt.md`). Any number of named
      participants join a room keyed by artifact name; once anyone sends
      `start`, Thimble presents each of that artifact's confirmed notes in
      turn (reviewer name, note, heuristic) and opens the floor before
      advancing. Same incremental scope cut Suture itself took before real
      LiveKit audio became a separate follow-on: no audio, no TTS, no
      turn-taking classifier yet — text broadcast to everyone in the room.
      Verified live against the real Anthropic API in-browser: joined,
      started, the confirmed "CTA competes with search bar" note was
      presented attributed with its heuristic, a reply from "Sam" broadcast
      and got a facilitator follow-up. No console errors (besides a stale
      connection error from before `websockets` was added to
      `requirements.txt` — confirmed harmless, see commit).
      **Still needed before this is the real thing:** real audio (reuse
      `../joint-session-audio`'s LiveKit prototype and Suture's
      `speak_in_room`/facilitator-speak pattern, per the Phase 0 platform
      decision) instead of Splice's companion-panel/Zoom-Apps-SDK
      infrastructure, and the preflight-collaboration side's full six-step
      "Workflow" (warm-up, solo work, consensus/reaction aggregation) —
      this build only covers the crit side's "present notes, discuss" shape.
- [ ] Resolve open design question: does the consensus step (preflight
      collaboration side) output a ranked winner, a merged direction, or
      just a heatmap of reactions for humans to decide from
- [ ] Resolve open design question: who calls "goal achieved" in the live
      session — the group by vote, or does it need to clear some threshold
      on its own
