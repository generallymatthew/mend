# Mend: GTM Strategy — EPLI, EAP, and Adjacent Institution-Facing Distribution

Working notes on using insurance- and benefits-industry channels to distribute Mend, fund the free consumer tool, and do it without compromising the zero-trace promise. See [[project_epli_distribution_route]] and [[project_mend_moat_strategy]] (memory) for the decisions already made; this doc is the business-model writeup of that reasoning plus the EAP/adjacent-channel extension.

## The underlying model: two products, one engine

Same facilitation engine, two front doors, aimed at two different buyers:

1. **Institution-facing tool** (this doc's subject). Built to satisfy what an insurer, broker, or benefits vendor wants to see — a documented harassment-reporting mechanism, a safety-floor escalation path, risk-control credit eligibility — without compromising the employee's actual interests. The safety floor is the only place a record is ever created, and it fires the same way regardless of who's paying for the seat. See `STATUS.md` / `ROADMAP.md` for where that's built.
2. **Consumer tool**, employee-facing and manager-facing versions of the same engine (see [[project_naming_structure]]: Seam is the app, Thimble is the in-app persona). The employee version is the core product — all conflict, not just harassment — and can subsidize the manager version so access isn't gated by who can pay. Subsidy mechanics are still TBD.

**The hard constraint that makes this work**: any carrier/broker/vendor credit must be flat for having the control in place, not scaled to incident rate or usage volume. A variable credit (fewer reported incidents → bigger discount → employer has a reason to keep renewing) creates a financial incentive to undercount harassment, which breaks the entire trust premise the product depends on. This is the one term to check in any deal. See [[project_safety_floor_voting_rule]] for how the only record-creating event is structured so this holds regardless of channel.

This is the business-model expression of [[project_mend_core_philosophy]] (the problem is institutional dysfunction, not people): build the thing institutions will pay for, and use it to fund the thing that actually serves the people inside those institutions.

## Channel 1 — EPLI (Employment Practices Liability Insurance)

Decided 2026-10-24 as a live direction (see [[project_epli_distribution_route]]). Positioning: Mend as a qualifying risk-control for EPLI underwriters, the same way a fire alarm lowers a homeowner's premium, or a documented harassment hotline/EAP already earns credits with carriers like Chubb, Hiscox, Travelers, and Beazley.

**Why zero-trace survives this**: HR already pays for Mend today. The only record ever created is the safety-floor escalation trigger, which fires identically no matter who's downstream of it. Routing a premium credit through an insurer doesn't add new data collection or change when records get created — it just gives the employer a second reason to buy something they'd buy anyway.

**Comparables** (no carrier publicly advertises a specific credit for a named third-party tool — those deals are negotiated case-by-case through a broker, not published on a rate card):

- **Hiscox Risk Academy** ships free with every Hiscox EPLI policy — training modules on harassment prevention, discrimination, hiring practices. The clearest public example of a carrier bundling prevention tooling directly into a policy rather than crediting an external vendor.
- **Vault Platform** (now part of Diligent) and **AllVoices** are the closest product comparables to Mend's EPLI-facing side: confidential misconduct reporting, AI-assisted triage/investigation workflow, sold to enterprises. Neither publicly confirms an insurer premium-credit partnership.
- **Workshield** — another enterprise misconduct-management platform worth a look as a comparable.
- **Spot** — AI-assisted incident-reporting chatbot, also worth checking for how it frames itself to brokers.

**Next step**: a broker conversation (Marsh, HUB, Gallagher, or a regional EPLI broker) is still the fastest way to learn what risk-control credit language carriers currently recognize, before spending more time on comparables or legal review.

## How EPLI vendor inclusion actually works (researched 2026-10-25)

There is no single "EPLI certification" to pursue — no exam, no accreditation body, no public standard. What exists is carrier-by-carrier, and each carrier's program works differently:

- **Chubb** runs the most concrete, documented model: its Employment Practices Liability Loss Prevention Program maintains a directory of **120+ pre-approved employment services vendors** (employment law firms, HR/risk-management consulting firms, labor-economist statistical firms). Policyholders who use a listed vendor for preventive services get **reimbursed 50% of the cost, up to 10% of their EPL premium**. Source: Chubb's own EPL Loss Prevention Program overview (PDF) and its [EPL Consultant Directory](https://www.chubb.com/us-en/business-insurance/epl-consultant-directory.html) page. Critically, **the inclusion process for a new vendor isn't published anywhere public** — the directory page only describes the program from the customer's side (download an Excel list of approved vendors); there's no vendor-facing "apply here" form or stated criteria. Getting onto that list is a relationship managed internally by Chubb's EPL/risk-engineering team.
- **Travelers** leans more toward carrier-built-and-owned tooling rather than crediting external vendors: Risk Management Plus+ Online (their own training/content portal) and an EPL Help Line staffed by an outside law firm (Jackson Lewis, same firm Chubb's hotline uses). No public evidence of a comparable external-vendor reimbursement program.
- **Hiscox** bundles its own Risk Academy training free with every policy — again carrier-built, not third-party-credited.
- No equivalent public documentation was found yet for AIG, CNA, Hartford, Beazley, or Zurich's EPL programs; worth a follow-up pass once a broker conversation is scheduled, rather than more open-web searching (these programs aren't well indexed).

**What this means practically**: there's no self-serve application to fill out. The real path is a business-development motion, not a compliance checklist:

1. **Talk to an EPLI broker first, not a carrier directly.** Brokers (Marsh, HUB, Gallagher, Lockton, or a regional EPLI specialist) already have relationships with each carrier's risk-control/loss-prevention team and know which carriers currently run a vendor-reimbursement program like Chubb's versus which build everything in-house. Ask specifically: *"Which of your EPLI markets maintain a pre-approved vendor directory with a reimbursement credit, and who runs that program?"*
2. **Ask to see the actual vendor directory** (e.g. Chubb's downloadable Excel list) through a broker or an existing Chubb EPL policyholder contact, to see what a real listing looks like — what's named, how vendors are categorized, whether software tools (vs. law firms/consultants) appear at all today.
3. **Prepare a one-page "qualifying control" pitch** before any carrier conversation: what Mend does, how it maps to EPL policy coverage (documented harassment-reporting mechanism + non-configurable safety-floor escalation), and the proposed credit structure — flat, not scaled to incident rate (see the hard constraint above). Carriers and brokers will ask for this before any program conversation goes further.
4. **Get real employment counsel involved before claiming "approved" or "qualifying" anywhere.** This is already flagged in `ROADMAP.md` Phase 1 ("Real employment counsel engaged") — any language implying insurer endorsement needs legal review first, separate from the GTM motion itself.

**A separate, genuinely certifiable track worth distinguishing from the above**: state-mandated harassment-training laws (e.g. California SB 1343) have real, auditable vendor/trainer requirements — interactive content (not passive video), trainer-led or trainer-supported, written questions answered within 2 business days, records retained 2+ years. This isn't an insurance credit and doesn't touch EPLI at all, but it's a concrete, checklist-style compliance bar Mend could pursue independently (faster and more self-serve than any carrier relationship) if it wants to market a training-adjacent surface as "SB 1343-compliant." Worth scoping as its own smaller workstream, not conflated with the EPLI carrier-relationship track above.

## Channel 2 — EAP (Employee Assistance Programs)

Not yet explored in prior sessions — new as of this doc. EAPs are a structurally different but adjacent opportunity:

- Almost every mid-size-and-up employer already pays for an EAP (ComPsych, Lyra Health, Spring Health, LifeWorks/TELUS Health, Optum, Magellan are the major vendors), usually bundled into the benefits package and bought through the same broker relationship as EPLI.
- **The gap Mend fills**: EAPs are built for individual counseling and referral (therapy, legal/financial consults, substance-abuse resources) — not real-time peer-to-peer conflict mediation. There's no EAP product today that sits between "do nothing" and "file an HR complaint." That's the same "missing middle" Mend already targets (see [01_EXECUTIVE_SUMMARY.md](01_EXECUTIVE_SUMMARY.md)), just reached through a different buyer.
- **The chronic EAP problem Mend's model is actually suited to solve**: EAP utilization industry-wide is notoriously low (commonly cited in the 5-10% range), largely because employees don't trust that "confidential" counseling-line intake is actually private from the employer. Mend's zero-trace architecture is a real answer to that trust gap, not just positioning — the same no-trace design that makes the consumer tool work can make the pitch to an EAP vendor concrete rather than aspirational.
- **Two ways in**: (a) white-label / API-licensed module sold *to* an EAP vendor, who resells it as part of their existing benefits package; or (b) sold *alongside* an EAP as a complementary point solution, with EAP as the warm handoff path for cases that need a licensed counselor rather than peer mediation. (a) has better distribution leverage (one vendor deal reaches many employers); (b) is easier to pilot without a vendor partnership first.
- **Open question**: whether an EAP vendor would treat Mend as a competitive overlap (counseling adjacent) or a complementary module (different job entirely). Needs a direct conversation with an EAP vendor's product or partnerships team, not just inference from their marketing copy.

## Channel 3 — other adjacent institution-facing distribution

Flagged as worth scoping, not yet researched in depth:

- **PEOs (Professional Employer Organizations)** — ADP TotalSource, Insperity, Justworks, Rippling PEO. A PEO sells bundled HR/benefits/compliance to many small employers at once, so one PEO partnership has outsized distribution leverage for exactly the SMB segment [02_COMMERCIAL_PRICING_STRATEGY.md](02_COMMERCIAL_PRICING_STRATEGY.md)'s pricing already targets.
- **The broker channel itself as a single conversation covering multiple lines** — the same broker (Marsh, HUB, Gallagher, Lockton) that places EPLI for an employer often also places their EAP and wellness benefits. One broker relationship could plausibly open both the EPLI and EAP routes rather than needing two separate pitches.
- **HR/benefits SaaS platforms** with a benefits marketplace or app-store model (Rippling, Gusto, Lattice, Culture Amp) — distribution via listing rather than underwriting credit.
- **State-mandated harassment-training/reporting compliance budgets** (e.g. CA SB 1343, NY) — a compliance line item that already exists in many employers' budgets independent of EPLI or EAP, worth checking whether Mend's documented-mechanism angle qualifies.

None of these are committed directions — they're parked here so they don't get rediscovered from scratch later.

## Open questions

- Subsidy mechanics: flat percentage of EPLI/EAP/employee revenue into a manager-access pool, per-seat matching, or something else? (Carried over from the original strategy note, still unresolved.)
- Does an EAP vendor see Mend as competing or complementary? Needs a real conversation, not an inference.
- Which single broker conversation most efficiently tests both the EPLI and EAP angles at once?
- How much of the "two products, one mission" framing (institution-facing funds consumer-facing) ever becomes visible in any pitch material, versus staying purely internal strategy? Current lean: stays internal — see [[project_mend_core_philosophy]] on why the underlying worldview is deliberately never stated as copy.
