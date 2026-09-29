# Mend: Legal Counsel Outreach (Pre-Pilot Review)

Outreach template for finding employment/tech-liability counsel ahead of the user-testing pilot, per `product-spec.html`'s own repeated "not legal advice, needs real employment counsel before this ships" caveats (Section 6's trigger definitions, Section 10's open legal/compliance items).

## Initial outreach email

**Subject:** Inquiry: Pre-Launch Regulatory & Product Review for AI Conflict Facilitator (Mend)

> Hi [Name/Title],
>
> I am the founder of Mend, an early-stage startup developing an autonomous, digital-only dispute facilitator for workplace teams. The platform uses symmetrical turn-taking and a private side-conversation structure to help coworkers de-escalate day-to-day friction before it reaches HR.
>
> Because our system operates as an informal peer tool with zero persistent conversation storage (volatile in-memory execution), we are seeking targeted, limited-scope legal counsel prior to our user-testing pilot. Specifically, we want to ensure our architecture and user agreements avoid inadvertent liability for our company and the employers deploying it.
>
> I have attached a concrete 1-page scoping memo detailing our technical posture and the four specific legal questions we need reviewed. We are seeking an efficient, fixed-scope review or an initial consultation.
>
> Could you let me know if your [clinic / practice] has bandwidth for this type of engagement, or if you can recommend a colleague specializing in labor/employment and tech liability?
>
> Best regards,
> [Your Name]
> Founder, Mend
> [Your Phone Number] | [Your Email] | [Website/Link if applicable]

## 1-page scoping memo

**Entity:** Mend
**Stage:** Pre-Seed / Pre-User Pilot
**Matter:** Product Liability, Employment Law Intersections, and Terms of Service (ToS) Review

### 1. Executive summary & product architecture

Mend is an automated conflict facilitation web application. It provides:
- **Solo intake side conversation:** a private space where an employee deconstructs a workplace issue with an AI agent.
- **Symmetrical joint room:** a guided digital session enforcing turn-taking and reframing hostile phrasing into operational proposals.
- **Decoupled agreement:** solutions are accepted or rejected asynchronously in private.
- **Ephemerality:** transcripts are processed in volatile runtime memory and are not stored in durable databases.
- **Safety circuit breaker:** a secondary classifier monitors conversation turns in real time. If severe misconduct is detected, the session halts immediately.

### 2. Primary legal questions & scope of engagement

**A. Employer "constructive notice" & Title VII liability**
- Context: under *Faragher/Ellerth* doctrines, employers have an affirmative defense against certain harassment claims if reasonable reporting channels exist.
- Inquiry: does an employee disclosing harassment, discrimination, or retaliation within Mend's software create a legal risk of "constructive notice" against the employer?
- Deliverable: review and refine disclaimer language for user onboarding ensuring Mend cannot be construed as a formal statutory reporting channel.

**B. Evidentiary discovery & ADR settlement privilege**
- Context: Federal Rule of Evidence 408 and state Alternative Dispute Resolution (ADR) statutes protect compromise negotiations from civil admissibility.
- Inquiry: does Mend's turn-taking and decoupled agreement qualify under standard mediation/settlement negotiation privileges? In the event of subsequent third-party litigation between employees, how should our Terms of Service address subpoena resistance given our zero-trace technical design?

**C. Regulatory boundaries: unauthorized practice of law (UPL) & therapy**
- Context: the system reframes disputes into objective, forward-looking operational agreements (e.g. SLA timelines, communication boundaries).
- Inquiry: confirm our safety-classifier guardrails sufficiently prevent crossing statutory lines into unlicensed legal advice or clinical mental health counseling.

**D. Non-configurable safety floor & tort liability**
- Context: Mend implements an automated circuit breaker halting sessions upon detection of violence, sexual harassment, or statutory violations.
- Inquiry: by implementing an automated safety filter, does Mend assume a common-law duty to rescue or third-party monitoring liability if a user circumvents the filter? What limitation-of-liability clauses best protect Mend from claims arising from failed mediation or subsequent workplace termination?

### 3. Key deliverables requested

1. A redline/markup of Mend's standard User Intake Disclaimer and Enterprise Terms of Service limitation-of-liability sections.
2. A 30-45 minute consultation reviewing the findings and confirming our trigger taxonomy.

*(Memo ends here as provided -- item 2 above was mid-sentence in the source paste; confirm the full scope of the second deliverable before sending.)*

## Status

Not yet sent. Cross-reference against `../../product-spec.html`'s own Section 10 ("Legal & compliance — open items") and Section 6's trigger-definition caveats before finalizing — the four questions above overlap directly with what that section already flags as needing real counsel.
