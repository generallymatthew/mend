# Status

Updated at natural checkpoints (a completed, verified piece of work), not on every commit. Meant to let anyone — including you, switching between your two Claude accounts on this same machine — pick the project back up cold, without depending on any one conversation's chat history. See `README.md` for what the project actually is.

**Last updated:** 2026-09-29

## Where things stand

Core facilitator flow (intake → joint session → post-session) works end-to-end as local FastAPI prototypes, real API keys required. `demo-app`'s signup/invite flow is real (access code + crypto-shredded invites), not a simulation. `joint-session-audio/` is a separate, newer prototype proving the real audio delay buffer + video opt-in over LiveKit — not yet merged into `joint-session-app`'s conversational logic. The brand (logo, Pink/Evergreen/Honey/Oat, Manrope) is now canonical everywhere.

GitHub (`github.com/generallymatthew/mend`) is **suspended** — blocks push/pull/Pages until resolved (check `git ls-remote origin HEAD` before assuming it's fixed). Local commits + the Google Drive git-bundle backup (`.git/hooks/post-commit`) are unaffected and are the durable copy right now.

## Recently completed

- Brand rebrand: new logo/color kit applied across all 5 apps, `product-spec.html`, `launchpad.html`, and `Mend Pitch/`'s full design system + both animated videos (chrome only, character illustrations left untouched on purpose). Real contrast bugs found and fixed (white text was illegible on Pink/Honey fills in several places).
- "Below-floor coaching" principle: codified in `product-spec.html` (harmful-but-not-illegal patterns like gaslighting get private coaching, never reach a manager/HR) and wired into `facilitator-joint-session-system-prompt.md` + `facilitator-post-session-system-prompt.md` + both apps' `server.py`. Live-verified against a running server, including a real bug fix (the facilitator wasn't flagging a pattern it had already handled live — fixed via an explicit prompt instruction).
- `joint-session-audio/`: real audio delay buffer (LiveKit + streaming STT + the real hard-cut classifier) and symmetric video opt-in, both live-tested. Found and fixed a real LiveKit Agents subprocess-timeout bug along the way.
- classifier `batch6`: 100 hand-labeled manager-statement examples, checked against the live v3 model (surfaced that v3 currently has 0% recall on live coercive-retaliation phrasing).
- `demo-app`'s real signup/invite backend + `run_all.sh`/`Caddyfile` unified local proxy, both verified.
- Legal counsel outreach template saved to `docs/pitch-strategy/10_LEGAL_COUNSEL_OUTREACH.md` — drafted, not sent.

## Open / next up

- **Classifier per-class loss weighting** — `train.py` has no per-class loss weighting, which is why `v4` regressed `cut_trigger` F1 despite fixing `illegal_activity` (see `classifier/README.md`'s Results section). Fully self-testable, no human review needed to make progress here.
- **Human review of classifier batches 4/5/6** — 378 examples queued in `classifier/data/review_page.html`, not yet judged by a person.
- **`intake-app`/`post-session-app` rate limiting + proxy-path fixes** — committed but not live-tested against a running server the way most other changes this session were.
- **`product-spec.html`'s Mermaid diagrams** — still on their own old color config, not part of the brand rebrand pass.
- **GitHub Pages hosting for `trymend.solutions`** — designed, blocked entirely on the account suspension above.
- **Real camera hardware test for video opt-in** — the parity *logic* is proven (`joint-session-audio/tests/test_video_parity.py`), but the actual LiveKit video-subscription-revocation path has never been exercised with a live camera (this dev environment has none).
- **Peer-suggested invite mechanism** — specced in `product-spec.html` a while back, never built.
- **LiveKit private caucus/breakout room** — `joint-session-architecture.md` still marks this "not yet designed."
