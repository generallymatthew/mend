# Evidence Strategy, Market Precedent & Buyer Personas

Captured 2026-11-17 from a brainstorm on proving the core investor-facing
claim behind Mend: that employees will voluntarily leave personal ChatGPT/
Gemini accounts for a purpose-built, zero-trace tool once the surveillance
risk is removed. No third-party market study exists on this yet (no product
like Mend operates at scale), so the proof has to be built in two layers:
macro telemetry on why today's tools fail, plus Mend's own pilot data.

## 1. Macro evidence already available (why corporate AI loses today)

Existing 2026 enterprise security research, cited as directional support
(**not yet source-verified against the primary reports** — confirm before
using a specific figure in an external deck or one-pager):

- Personal accounts dominate workplace AI use: cited ~47% of workplace AI
  conversations run on personal accounts (LayerX/Netskope telemetry), and
  ~88% of office workers admit sharing work information with public AI
  tools (PagerDuty).
- Bans don't work: cited 41-46% of employees route around AI bans when they
  need help in the moment (UpGuard / Software AG).
- Why handing out ChatGPT Enterprise or Copilot doesn't fix it: those tools
  ship with admin logs, compliance APIs, and 30-90 day retention windows
  for eDiscovery. Employees understand intuitively that typing "my VP is
  setting me up to fail" into an SSO-logged corporate bot creates a
  permanent, discoverable paper trail.

## 2. Pilot evidence Mend needs to generate (proving the switch)

Three experiments, runnable with 30-50 testers over roughly two weeks,
since no one has studied a zero-retention "third option" at scale yet.

**Experiment A — A/B preference & trust survey.** Before or after a tester
runs a real high-stakes scenario (an unfair PIP, a hostile Slack message)
through Mend, ask two forced-choice questions:
1. "Where would you paste this today?" (Company Copilot/Slack AI / personal
   ChatGPT or Gemini on my phone / nowhere — I wouldn't use AI)
2. "If your company gave you a zero-login, volatile-memory tool with a
   legal non-recording warranty, which would you use instead?"

Target investor-slide stat: "X% of testers who currently use personal
ChatGPT for work disputes said they'd switch to Mend because it leaves
zero personal chat history to subpoena and doesn't just validate their
anger."

**Experiment B — Blind side-by-side output test.** Run ~10 real workplace
friction prompts through both personal ChatGPT/Claude and Mend, strip the
labels, and have 20-30 professionals vote on which response they'd trust
to protect their job. Hypothesis to test: personal AI tends to validate
anger ("that sounds toxic, here's an assertive email") in a way that gets
people fired or PIP'd, while Mend should de-escalate and isolate the
counterpart's hidden constraint instead.

**Experiment C — Real-world voluntary usage ("cold traffic" funnel).** The
strongest proof isn't a survey, it's unprompted behavior: post a zero-login
link where people are actively venting (e.g. r/careerguidance, Blind,
Fishbowl, r/experienceddevs — subject to each community's self-promotion
rules) and track completion rate (did they finish the intake without
bouncing) and attribution shift (did framing move from "my coworker is a
jerk" to "we have a broken handoff/SLA").

## 3. Market precedent: "paving the cowpaths" / enterprise harm reduction

The pattern this fits: when a ban fails because it's blocking a real human
need, the organization stops fighting the behavior and ships a sanctioned,
zero-friction alternative that satisfies the same need without the toxic
downside. Historical precedents at scale, used as supporting evidence that
this is a known, proven adoption pattern rather than a novel bet:

- **Password managers vs. sticky notes / reused passwords** — IT banned
  writing passwords down, employees kept doing it anyway because
  memorizing 50 credentials is impossible; enterprise password managers
  won adoption because autofill was faster than a sticky note, not because
  of the ban.
- **Organizational Ombuds offices vs. backchannel gossip and litigation** —
  voluntary HR mediation historically stalls at 3-10% adoption because of
  fear of retaliation and a permanent record; independent, zero-record
  Ombuds offices (firewalled from HR) see 80%+ voluntary walk-in usage once
  surveillance is removed, with ~95% of cases resolved informally per 2024
  International Ombuds Association data. **This is the closest structural
  analogue to Mend and the strongest precedent to cite.**
- **Slack/Teams vs. shadow SMS/WhatsApp** — workers texted sensitive files
  over personal SMS because corporate email was too slow; Slack/Teams won
  by being fast and mobile like texting, but inside a secured perimeter.
- **Safe-harbor bug bounty programs (e.g. HackerOne) vs. unauthorized
  probing** — legal threats drove vulnerability discovery underground;
  sanctioned bounty programs turned a liability into protection.
- **Non-alcoholic "dry bars" / daytime offsites vs. open-bar liability** —
  banning social decompression outright felt punitive; a safe substitute
  preserved the bonding without the legal exposure.

Pitch framing ("1Password playbook for workplace AI"): the unstoppable
habit is employees pasting PIPs and manager disputes into personal AI; the
hidden trap is that personal AI leaves permanent, subpoena-ready records on
unsecured devices; the safe harbor is Mend, structured like a password
manager's private vault or an Ombuds office — company funds the seat pool,
blind tokens and volatile memory mean only the employee holds the keys.

This sits alongside, but should not replace, the "Four Undeniable Truths"
opener and the password-manager core analogy already locked in at
[32_HR_AND_INVESTOR_PITCH_STRATEGY.md](32_HR_AND_INVESTOR_PITCH_STRATEGY.md)
— that doc's §4 covers the same 1Password analogy at the product level;
this section is the supporting evidence and the wider precedent list.

## 4. Brand stance: blunt, pro-worker, openly distrustful of corporations

The positioning decided in this conversation: Mend does not soften its
language to flatter the corporate buyer. The stance, stated plainly rather
than as a reversal/aphorism:

- Mend is built for the worker, not for HR. HR exists to manage corporate
  risk; that's a different job than protecting the person caught in a bad
  PIP or a turf war.
- Mend doesn't trust corporations to protect employee honesty, so that
  trust requirement is engineered out rather than promised — see the
  headless architecture in
  [03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md](03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md#headless-enterprise-architecture-no-portal-no-accounts-email-only).
- The commercial argument to a buyer is explicit, not disguised as
  altruism: covering the employee's back ends up covering the company's
  back too (fewer leaks onto personal AI, fewer undocumented disputes that
  turn into litigation), and that alignment is presented as a byproduct,
  not the reason Mend was built.
- To a sharp HR/Legal buyer, the pitch leans into this rather than away
  from it: a tool that visibly protects the worker is the only kind a
  worker will actually use honestly, and only honest use produces the risk
  reduction a company is paying for. A tool built to flatter HR first
  would get the same silent boycott that keeps formal mediation stuck at
  3-10% adoption.

## 5. Buyer persona: which department actually pays

Breakdown of likely purchasers by budget access, motivation, and blocker.

| Department | Likelihood to pay | Budget line | Why they buy | Blocker |
|---|---|---|---|---|
| **HR / People Ops** (primary buyer, fastest path at 50-250 FTEs) | High | EAP/behavioral health or People Ops/retention budget, ~flat annual license | Deflects routine peer-conflict refereeing off HRBPs; reduces avoidable turnover | Traditional/control-oriented HR wants surveillance, not a tool that visibly withholds data from them; only buyers who think in terms of outcomes over control convert |
| **Legal / Risk / CFO** (highest-leverage buyer, best fit 250+ FTEs) | High | EPLI risk-mitigation premium credit, deductible relief, or legal defense reserve | One wrongful-termination or retaliation suit costs far more than the license; zero-trace volatile memory means no subpoena discovery landmine, and the safety floor (see Watcher doc) preserves the employer's Faragher/Ellerth affirmative defense | Slower to reach directly; best approached via an EPLI broker or employment counsel introduction — see [28_GTM_EPLI_EAP_AND_ADJACENT_DISTRIBUTION.md](28_GTM_EPLI_EAP_AND_ADJACENT_DISTRIBUTION.md) and [31_EPLI_BROKER_ONE_PAGER_AND_OUTREACH.md](31_EPLI_BROKER_ONE_PAGER_AND_OUTREACH.md) |
| **Frontline engineering/product leads** (bottom-up wedge) | Medium-high | Discretionary L&D/coaching stipend or team software card | Zero-procurement-friction entry point; keeps sprints unblocked | Small initial check size; a wedge into the larger HR/Legal contract, not the main revenue path |
| **IT / InfoSec** | Low as a buyer, but a required sign-off | Shadow AI / data-loss-prevention budget | IT holds real budget but rarely originates a purchase for a workplace-dynamics tool; its reflex is visibility and audit logs, which is the opposite of what Mend offers | Brought in by HR or Legal to approve, not to initiate; wins their sign-off quickly because there's no SSO integration, no database, and no internal network access required — see headless architecture doc |

**Cleanest enterprise motion:** a joint HR + Legal/Risk sale, with IT
rubber-stamping security because there's nothing for IT to integrate or
secure. HR sponsors it to stop PIPs and disputes leaking onto personal
phones and to get out of playing referee; Legal/CFO approves the budget
because preventing a single six-figure employment claim (or capturing an
EPLI premium credit) pays for the whole license; IT signs off in minutes
because the architecture has no attack surface to review.

## Status

Working notes from a 2026-11-17 brainstorm. Macro statistics in §1 and the
EPLI/precedent figures are illustrative and **not yet checked against
primary sources** — same caveat as
[32_HR_AND_INVESTOR_PITCH_STRATEGY.md](32_HR_AND_INVESTOR_PITCH_STRATEGY.md).
Confirm before citing a specific number to an investor or buyer.
