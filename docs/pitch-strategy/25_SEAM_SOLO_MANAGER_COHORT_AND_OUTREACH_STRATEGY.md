# Seam: Solo-Manager Cohort and Outreach Strategy

Companion to [05_USER_TESTING_AND_COHORT_STRATEGY.md](05_USER_TESTING_AND_COHORT_STRATEGY.md), which is scoped to Thimble/Suture (two-person conflict pairs). Seam's core surfaces (Meeting Strategy, Tone-check, solo case prep) are single-user: one manager, no counterpart to recruit, no asymmetry problem. This doc covers what Seam actually needs instead: finding managers, and selling into the right budget line. Idea-stage, not yet run — see `seam-product-roadmap.md` Phase 3.

## 1. Why this isn't a pairs problem

05's whole design exists to solve "Person A is easy to recruit, Person B is where conversion fails" (05:5). Seam doesn't have a Person B for most of its MVP surface:

- **Meeting Strategy** — one manager, one meeting goal, no counterpart.
- **Tone-check** — one manager, one draft message, no counterpart.
- **Thimble-in-Seam** (manager's own conflict processing) — same solo treatment as standalone Thimble.

**Suture-in-Seam** is the exception — it still needs two reports — but the invite-friction problem is already solved by being manager-initiated (`24_SEAM_PRODUCT_PITCH_AND_ADOPTION_STRATEGY.md` §3), not something this cohort plan needs to re-solve.

So the open problem isn't "how do we get two strangers into a room," it's "how do we find managers at all, and get them to actually open the app a second time" — a recruitment-and-retention problem, not a matching problem.

## 2. Two separate things to find: testers and buyers

These are different people and need different outreach, even though a buyer can self-nominate as a tester.

- **Testers** — individual managers who'll use Seam and give feedback. Volume matters more than title. A pilot needs maybe 10-20 managers using it for 2-4 weeks, not a signed contract.
- **Buyers** — the skip-level/director or the L&D/people-ops person who controls a coaching-stipend line (`02_COMMERCIAL_PRICING_STRATEGY.md` §"Individual-Manager Buyer Economics": $200-500/yr per manager, out of an existing stipend, not a personal subscription). One buyer conversation, if it lands, can produce many testers at once via the three-tier cascade (`24_...` §2.2) — land the skip-level, they push Seam to their managers.

Chasing buyers first is probably the higher-leverage move: one skip-level yes gets a whole team of testers in one motion, instead of recruiting each manager individually.

## 3. Where to find managers (tester channel)

- **Manager-specific practitioner communities** — same move as 06's HR-community approach (`06_HR_BUYER_OUTREACH_STRATEGY.md` §2A), but aimed at manager-facing communities instead of HR ones: First Round's manager Slack communities, Lenny's Newsletter community, EM (engineering manager) Slacks (Rands Leadership Slack, EM365), r/ExperiencedDevs / r/managers. Run the same practitioner-inquiry framing, never a cold product link:
  > "Question for managers: what's your go-to move when two people on your team are in a quiet conflict that hasn't blown up yet? Building something to help managers think through tough conversations before they happen — would love 15 minutes with a few people who manage a team day to day."
- **First-line managers inside a company already landed for the all-hands Thimble tier** — if a company ever buys the company-wide tier (`02_COMMERCIAL_PRICING_STRATEGY.md`), every manager inside it is a warm Seam tester with zero additional outreach cost.
- **New/first-time managers specifically** — highest-pain segment (least practiced at hard conversations), likely most receptive to a coaching tool, worth a dedicated outreach angle distinct from the skip-level/cascade path (which assumes an existing, confident manager recommending downward).

## 4. Where to find buyers (stipend/cascade channel)

- **L&D and people-ops leads who already own a coaching-stipend budget line** — warmer than general HR cold outreach because they already buy manager-training tools, so the category isn't a hard sell. Same communities as 06 (Charter, PeopleTech Partners, Hacking HR), but the ask is narrower and easier to say yes to than 06's HR-safety-floor pitch:
  > "We built a manager-coaching tool that sits inside an existing L&D stipend line ($200-500/yr/manager) instead of needing a new procurement line. Would a 10-minute look be useful before your next stipend-renewal cycle?"
- **Skip-levels/directors directly** (the primary cascade entry point per `24_...` §2.2) — pitch is self-interest, not altruism: "your reports' management skill is your own performance metric." Reuse 13's design-partner framing (`13_PITCHING_MEND_TO_ENTERPRISE_HR.md` §3 Stage 4) but scoped down from a 15-25 person squad pilot to a single skip-level's direct reports (typically 3-8 managers) — smaller ask, faster yes.

## 5. Evaluation metrics (Seam-specific, not 05's pair metrics)

05's metrics (symmetry score, decoupled agreement rate, watcher interception rate) are built for two-person mediation and mostly don't apply here. Seam needs its own:

- **Re-open rate** — does a manager who used Meeting Strategy or Tone-check once come back for a second, unprompted use within 2 weeks? This is the real signal for whether Seam escapes the "only useful during an acute dispute" problem (`seam-product-roadmap.md` Phase 1 framing).
- **Artifact usefulness** — for Meeting Strategy, did the manager report actually using the written strategy artifact in the meeting (not just generating it)?
- **Tone-check acceptance rate** — fraction of suggested rewrites the manager actually sends as-is or close to it, vs. ignored.
- **Cascade conversion** — for the skip-level-entry pilots specifically: of N managers a skip-level pushes Seam to, how many actually try it. Tests whether the self-interest framing in `24_...` §2.2 actually survives contact with real managers, not just reasoned from first principles.

## 6. What this doesn't cover

- Legal/safety-floor stress-testing — still gated on `22_SOLO_THREAT_FLOOR_AND_TURN_SCORING.md` per `24_...` §5, applies to Seam same as Thimble.
- Pricing validation against a real deal — tracked separately, `ROADMAP.md` Phase 2 and `seam-product-roadmap.md` Phase 3.
- The growth-vs-crisis segment fork (`24_...` §4) — outreach copy for the two segments will likely need to differ, not yet drafted.
