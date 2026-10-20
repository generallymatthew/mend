# Splice (group-session-app) — Product Roadmap

Splice is a consensus-builder for loose groups stuck at an impasse, meeting
live, with nothing confidential between them (reference case: open-source
maintainers stuck on one GitHub issue) — the opposite trust model from the
two-person conflict-mediation apps (Thimble/Suture), where privacy between
the two parties is the whole point. Splice drives a group to an explicit,
visible group decision (a vote), not privacy from the rest of the room: no
safety floor, no side-conversation firewall, no confidential intake —
those are Thimble/Suture-specific and deliberately left out of Splice's
facilitator prompt.

Per the 2026-10-17 app-concept ranking in `../../IDEAS.md`, Splice ranks #6
of seven: no clear named/budgeted buyer, thin moat, competes directly with
where Zoom/Otter/Read AI are already investing their own live-meeting AI
features.

Architecture decision already made: Splice does **not** build or own
video/audio at all. Zoom is the entire transport layer; Splice is a
companion panel that runs alongside a real Zoom meeting (via the Zoom Apps
SDK) and only owns chat, proposals, voting, and Thimble (here acting as a
visible, named participant in the room, not a silent backend process).

## Phase 0 — Local prototype (done, browser-verified)

- [x] Shared room: participants, group chat, proposals, and per-proposal
      voting (yes/no/abstain), broadcast live over WebSocket
- [x] Thimble as a visible named participant: asks the next useful
      question, names implicit proposals out loud, nudges toward a vote
      when discussion stalls, stays neutral on substance, never declares a
      vote "decided" (only reports where the count stands) — system
      prompt: `../facilitator-group-session-system-prompt.md`
- [x] Onboarding: Thimble states the session's goal (the pinned issue) and
      asks the participant's preferred way of taking part (video+mic or
      text-only) before they enter the room
- [x] Self-serve controls: mute mic, turn off video, leave the session
      (each person only controls themselves, no facilitator-removes-others
      feature)
- [x] Two front ends: `static/index.html` (standalone video-first mockup,
      used to validate UI before the Zoom-panel pivot) and
      `static/zoom-panel.html` (real target shape — no video grid, no media
      controls, calls `zoomSdk.getUserContext()` to auto-join a real Zoom
      participant by name)
- [x] Verified live end to end on `index.html`: join → onboarding → room →
      chat → proposal → vote → mute/camera/leave
- [x] `zoom-panel.html`'s non-Zoom fallback path (manual name entry, used
      when the SDK isn't present) verified through onboarding and into the
      room

## Phase 1 — Fix known bugs

- [ ] `zoom-panel.html`'s own tab: `POST /api/message` succeeds server-side
      but the message never renders back locally — browser console shows a
      WebSocket reconnect loop. Not yet root-caused; not yet confirmed
      whether it's a real bug in that page's `connectSocket()` or a
      browser-pane sandbox artifact. See root `STATUS.md`'s 2026-10-16
      entry.

## Phase 2 — Real Zoom-native integration (blocked on the user)

- [ ] Zoom Marketplace developer account + registered Zoom App (Client ID)
- [ ] HTTPS hosting for the panel (Zoom Apps refuse plain-HTTP localhost) —
      likely a tunnel (ngrok or similar) until real hosting exists
- [ ] Testing the actual in-Zoom path once the above are available — this
      is the actual point of "as a Zoom plugin," currently unverified
      beyond the local fallback path

## Shared infrastructure note

Swatch (`../swatch/swatch-product-roadmap.md`) likely shares
`group-session-app/`'s room/WebSocket backend and Zoom Apps SDK companion
panel pattern rather than a from-scratch build, since both are
companion-panel-over-a-real-call shapes — though Swatch's trust model is
the opposite of Splice's (encouragement/warmth between two people, not
neutral group-vote mechanics).
