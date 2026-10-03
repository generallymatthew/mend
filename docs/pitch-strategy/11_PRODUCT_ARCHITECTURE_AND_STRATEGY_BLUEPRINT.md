# Mend: Product Architecture, Strategic Framing & Operational Blueprint

## 1. Brand Identity, Manifesto & Taglines

### Core Metaphor & Taglines
* **Heal the rift. Leave no trace.**
* **Like dissolving sutures for team conflict:** Holds relationships together while they heal, then disappears completely without leaving scar tissue, dossiers, or permanent records on an employee's career.
* **Autonomy over surveillance:** Resolving the "missing middle" of everyday workplace friction before it turns into an expensive HR incident or talent attrition.

### The Value Manifesto
* **We value mending relationships over litigating blame:** Assigning fault builds defensive walls; uncovering structural incentives unlocks real solutions.
* **We value peer-to-peer alignment over managerial surveillance:** People can only drop their guard and speak candidly when they know their words can never be weaponized in a performance review.
* **We value durable resolution over fragile truces:** Polite avoidance delays the next flare-up; addressing root operational friction restores true delivery velocity.
* **We value personal agency over forced corporate harmony:** Clearing the air is routine professional hygiene on your own terms, not an HR performance.

---

## 2. The Core Value Proposition: The Dual-Track Framework

Mend resolves the fundamental workplace paradox: **Management wants outcomes without micromanaging, while employees want resolution without surveillance.**

```
Traditional Escalation: Tension ──> HR / Manager ──> Formal Record ──> Career Penalty & Defensiveness
The Mend Model:         Tension ──> Mend Session  ──> Resolution    ──> Zero Trace (Sutures Dissolve)
```

### Track A: The User (Employee Navigating Conflict)
1. **Radical Zero-Trace Career Protection:** Executed inside hardware-isolated confidential enclaves (TEE). No persistent transcripts, manager surveillance, or HR dossiers.
2. **Uncensored Venting & Emotional De-biasing:** A private, zero-judgment space to express raw frustrations, drop performative defenses, and unpack what happened.
3. **Incentive Mapping over Character Flaws:** Reframes conflict from personal malice ("my peer is an idiot") into structural reality ("our roles and KPIs are in direct opposition").
4. **Standalone Solo Utility:** Provides immediate tactical value without requiring the counterpart's consent or presence.
5. **Decoupled Asynchronous Agreement:** Compromises are reviewed and accepted privately away from the live room, preventing performative concession or live social defeat.

### Track B: The Buyer (HR / People Ops / Executive Leadership)
1. **Deflecting the "Missing Middle":** Reclaims 30%–50% of HRBP time and 3–5 hours per week of frontline manager capacity spent arbitrating non-statutory peer squabbles (Slack tone, PR bottlenecks, sprint turf wars).
2. **Stopping the "Focus Leak":** Recaptures the 2.8 hours per employee per week lost to circular avoidance, distraction, and backchannel gossip.
3. **Turnover & Retention Insurance:** Preventing a single mid-level departure (replacement cost: 1.5x–2.0x annual salary) offsets the annual platform license several times over.
4. **Immutable Compliance Safety Floor:** Real-time watcher agents immediately halt private mediation and route straight to HR if Title VII discrimination, sexual harassment, or threats occur.
5. **Elevating Strategic HR:** Shifts People Ops from reactive day-to-day dispute triage to strategic workforce design, leadership coaching, and talent development.

---

## 3. Product Architecture & User Journey

### The Front Door: Ambient Dual-Track Intake
Instead of exposing rigid mode buttons ("Rehearse," "Mend," "Manager Prep"), the interface provides an intuitive fork:
* **Door A ("Vent"):** For acute emotional agitation, cortisol spikes, and the need to be heard without judgment.
* **Door B ("Mend"):** For operational de-escalation, meeting prep, or cross-functional calibration.

### The Pacing Protocol
```
[ Step 1: Raw Vent / Dump ]
            │
            ▼
[ Step 2: Pressure Gauge Check ] ◄── ("Is there more, or is that the main thing?")
            │ (User confirmed finished)
            ▼
[ Step 3: Subtle Incentive Inquiry ] ◄── ("What does their lead get on their case about if it slips?")
            │
            ▼
[ Step 4: The Organic Realization ] ◄── ("Their metric opposes mine.")
            │
            ▼
[ Step 5: Actionable Staging Fork ]
     ├── Option 1: Solo Exit (Catharsis achieved; sutures dissolve)
     ├── Option 2: The Pattern (Generate 1-page "Tough Talk Cheat Sheet")
     ├── Option 3: The Basting Stitch (3-minute low-stakes roleplay against AI adversary)
     └── Option 4: Peer Invitation (Symmetrical turn-taking joint session)
```

### Video vs. Voice-Only: Double Opt-In Shielding
* **Default Mode:** Voice + Neutral Speaker Avatars (lowers autonomic threat response and eliminates facial hypervigilance).
* **Double Opt-In:** Video is unlocked **only** if both participants independently choose video during intake.
* **Zero Coercion:** If one selects voice and the other selects video, the room defaults to voice. Neither participant is informed of the other's preference.
* **Facilitator Invariance:** The AI facilitator is programmatically barred from asking or nudging participants to enable cameras.

---

## 4. Technical Specifications & Safety Architecture

### The Multi-Agent Runtime Loop
```
User Turn Payload (Text + Acoustic Telemetry)
                     │
                     ▼
           [Facilitator LLM Draft]
                     │
                     ▼
        [Deterministic Watcher Agent]
          (Latency: 200–350ms; temp=0.0)
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
     [PASS]                    [FAIL]
  Sent to UI            Self-Correction / Regeneration
                                  │
                                  ▼
                    [SAFETY_FLOOR TRIP] ──► Immediate Session Halt & HR Route
```

### Watcher Audit Rubric
1. `SAFETY_FLOOR`: Non-configurable detection of Title VII discrimination, sexual harassment, physical threats, or illegal retaliation.
2. `HALLUCINATION`: Prevents inventing unstated project details, motives, or deadlines.
3. `BIAS_ASYMMETRY`: Strictly enforces procedural symmetry and prevents taking sides or validating unilateral blame.
4. `OUT_OF_SCOPE_ADVICE`: Blocks clinical diagnostic labels ("gaslighting," "narcissist") and legal counsel.
5. `UNFILTERED_TOXICITY`: Strips raw character attacks and reformulates them into operational needs.

### Lightweight Practice State Anchor (~350–500 Tokens)
To support iterative solo practice without retaining persistent chat logs or ballooning token costs, store only a minimal client-side state schema:
```json
{
  "scenario_metadata": {
    "counterpart_role": "Engineering Lead",
    "relationship_type": "Peer Cross-Functional",
    "primary_grievance_category": "Delivery Bottlenecks & Code Review"
  },
  "the_north_star": {
    "tangible_objective": "24-hour turnaround SLA on pull requests",
    "explicit_non_goal": "Extracting an apology for past sprint delays"
  },
  "counterpart_profile": {
    "probable_pressures": "Accountable for zero production bugs and system uptime",
    "primary_defensive_tactics": ["Process perfectionism", "Scope dismissal"]
  },
  "user_boundaries": {
    "firm_boundary": "No public call-outs in squad Slack channels",
    "flexible_concession": "Willing to break pull requests into smaller diffs"
  },
  "practice_analytics": {
    "sessions_completed": 1,
    "last_weakness": "Conceded the SLA timeline when challenged on edge-case testing"
  }
}
```

---

## 5. Commercial Packaging & Enterprise Pricing

### The Pricing Model (100 FTE Reference)
* **Model:** All-Access Company-Wide Flat Subscription (SSO-integrated).
* **Avoid Seat-Gating:** Per-seat models force employees to ask HR for a license, which destroys privacy and usage.
* **Rate:** **$7.50 / employee / month** ($9,000 / year billed annually).
* **Gross Margins:** Inference turn costs average ~$0.0047 per turn (~$0.25 to $0.40 per complete conflict), delivering >97% gross margins.

### Pitching People Ops Leaders
* **Don't pitch:** "AI therapy" or "mandatory harmony."
* **Do pitch:** "A self-serve operational buffer that deflects 4–6 hours of informal drama per week from HRBPs while maintaining an immutable compliance floor."

---

## 6. Testing Strategy & Validation Framework

### The Asymmetry Solution: 3-Cohort Beta Testing
1. **Cohort A (Roleplay / Adversary):** Single human testers paired with an AI adversary running against realistic scenarios (PR bottlenecks, stolen credit). Tests genuine emotional reaction without scheduling bottlenecks.
2. **Cohort B (Co-Founders & Startup Duos):** Early-stage partners navigating equity, burn, and roadmap alignment. High real stakes, zero corporate bureaucracy.
3. **Cohort C (Organic Coworkers):** Peer coworkers running active, low-to-medium friction disputes through the full caucus-to-joint pipeline.

### ADR Success Metrics
* **Neutrality & Symmetry Score:** Post-session confirmation of mediator impartiality.
* **Decoupled Agreement Rate:** Percentage of users who independently click "Accept" in private.
* **Watcher Interception Rate:** Percentage of drafts regenerated before reaching the UI.
* **14-Day Durability Check:** Verifying that working agreements remain stable in day-to-day delivery.