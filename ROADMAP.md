# Roadmap

Structural, phase-level view — what needs to be true before the next phase starts. For the rolling "what happened recently" log, see `STATUS.md` instead; this file changes rarely, that one changes often. Check a box when the item is actually done and verified, not just attempted. For raw, not-yet-committed ideas (not phase-level work), see `IDEAS.md` instead.

This file now covers only cross-app and repo-level work. Each of the seven
app codenames (see `IDEAS.md`'s "App codenames" section) has its own
phase-level checklist, living in that app's folder:

- [Thimble](apps/thimble/thimble-product-roadmap.md) — solo intake, the
  main conflict-mediation pipeline
- [Suture](apps/suture/suture-product-roadmap.md) — the live
  two-person joint session inside Thimble
- [Seam](apps/seam/seam-product-roadmap.md) — the manager app
- [Splice](apps/splice/splice-product-roadmap.md) — group
  consensus-building as a Zoom plugin
- [Swatch](apps/swatch/swatch-product-roadmap.md) — designer preflight
  collaboration (not yet built)
- [Loom](apps/loom/loom-product-roadmap.md) — pattern-only project retro
  (not yet built)
- [Hem](apps/hem/hem-product-roadmap.md) — cross-platform writing assistant
  (not yet built)

## Positioning principles

Not phase-bound; apply to every phase's feature and pricing decisions.

- **Trust moat over tech moat.** A corporate/HR-suite incumbent (Microsoft, Workday, Slack, Google) cannot credibly build this: their business model runs on compliance/eDiscovery and employer-controlled tenant keys, so employees would rationally assume surveillance. Mend's neutrality (zero-trace, ephemeral memory, no durable transcripts) is an architectural requirement, not branding. Never add a feature that creates a durable, attributable dispute record a manager or IT admin could read (e.g. a PM-tool ticket titled after the dispute) — see Thimble's roadmap (`apps/thimble/thimble-product-roadmap.md`) HR-escalation design for the pattern (anonymized payload only, no transcript either way).
- **Price below the enterprise sales floor, on purpose.** Target an accessible flat tier (e.g. $7k-9k/year per ~100-person org, or ~$10-15 per episodic session) — small enough that a legacy enterprise sales force won't bother chasing it, while still high-margin (near-zero storage cost, fractions of a cent per model turn). Anchor price against the cost of friction (hours lost to conflict, cost of a resignation), not the cost of building the software. Don't propose enterprise-tier pricing or large-deal-size features.
- **"No paper trail" is the feature, not a limitation.** Market the intentional forgetting as the differentiator in a world where every Slack DM and Jira comment is kept forever.

## Phase 0 — Local prototypes (mostly done)

- [x] Real hard-cut classifier (`apps/classifier/`), wired into `suture` (app-specific follow-up items: see Suture's roadmap)
- [x] Real signup/invite backend (`demo-app`), direct and peer-suggested
- [x] Unified local proxy (`run_all.sh` + `Caddyfile`)
- [x] Brand identity applied everywhere (logo, Pink/Evergreen/Honey/Oat, Manrope)

App-specific Phase 0 items (seam, thimble, suture,
etc.) have moved to each app's own roadmap file, linked above.

## Phase 1 — Ready for a real pilot

- [x] GitHub account unsuspended; Render's live deploy also repointed to it (2026-10-21), GitLab no longer load-bearing
- [ ] `trymend.solutions` actually hosting the pitch page
- [ ] Real employment counsel engaged (`docs/pitch-strategy/10_LEGAL_COUNSEL_OUTREACH.md` drafted, not sent)
- [ ] Trigger-category legal review (`product-spec.html` Section 10 — the floor categories are illustrative, not a finished legal standard)
- [ ] Confidential-computing / proof-tier story built out (`product-spec.html` calls this "a genuine, achievable differentiator... once 'provably private' becomes central to the pitch")

## Phase 2 — Go-to-market

Tracked in more detail in `docs/pitch-strategy/`, not duplicated here:

- [ ] HR/buyer outreach (`06_HR_BUYER_OUTREACH_STRATEGY.md`)
- [ ] Pilot cohort selected and testing plan run (`05_USER_TESTING_AND_COHORT_STRATEGY.md`)
- [ ] Pricing validated against a real deal, not just modeled (`02_COMMERCIAL_PRICING_STRATEGY.md`)
