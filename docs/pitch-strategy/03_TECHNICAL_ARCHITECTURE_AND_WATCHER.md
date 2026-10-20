# Mend: Technical Architecture & The Watcher Engine

## Runtime Privacy: Hardware Enclave Ephemerality

Mend never "records and deletes" — it never persists conversation data in the first place.

- **Confidential computing (TEE):** sessions execute strictly within hardware-isolated confidential enclaves in volatile memory.
- **Client-side state:** ongoing practice or intake metadata is stored client-side in a minimal (~350-500 token) encrypted schema, avoiding server-side dossier creation. See [09_PRACTICE_SESSION_MEMORY_SCHEMA.md](09_PRACTICE_SESSION_MEMORY_SCHEMA.md).

## Multi-Agent Orchestration Loop

```
User Input ──► [Facilitator LLM (Drafts Action/Advice)]
                       │
                       ▼
              [Supervisor / Watcher Agent]  ◄── Evaluates against Media Literacy / ADR Rubric
                       │
       ┌───────────────┼───────────────┐
       ▼                ▼               ▼
 [MINOR FAIL]     [SAFETY_FLOOR]      [PASS]
 Self-Correct       Halt session    Sent to UI
 ("Regenerate           │
  without      ┌────────┼────────┐
  diagnosing)  ▼        ▼         ▼
        [Never recorded] [Email HR] [Tell parties]
        Session ends in     Names     "Escalated to
        volatile memory,    only      HR," no detail
        nothing persisted
                         │
                         ▼
               HR runs own investigation
               (Mend has no further role)
```

## The Watcher System Specification

- **Model:** lightweight, deterministic classification LLM (e.g. GPT-4o-mini, Claude Haiku, Gemini Flash) at `temperature=0.0`.
- **Execution time:** ~200-350ms.
- **Audit categories:**
  1. `SAFETY_FLOOR` — Title VII discrimination, sexual harassment, threats, illegal acts. Triggers immediate room halt and HR escalation (see below).
  2. `HALLUCINATION` — inventing unstated deadlines, project histories, or motives.
  3. `BIAS_ASYMMETRY` — validating one party's narrative while delegitimizing the other.
  4. `OUT_OF_SCOPE_ADVICE` — clinical psychology diagnoses ("narcissist," "gaslighting") or legal counsel.
  5. `UNFILTERED_TOXICITY` — amplifying raw personal character attacks instead of operational needs.

Categories 2-5 are handled by the self-correction loop: the Facilitator regenerates its draft and the user never sees the failed attempt. `SAFETY_FLOOR` is the only category that does not loop back — it halts the session outright.

## Safety Floor Escalation

`SAFETY_FLOOR` does not break the zero-trace guarantee described above — the escalation is deliberately minimal and content-free:

- The session halts immediately. No further turns are generated.
- Nothing is deleted, because nothing was ever recorded: the session simply ends inside the volatile-memory enclave, and no transcript, summary, or context was ever written anywhere — the same zero-trace guarantee that applies to every other session, not a special case for the violation.
- HR receives a names-only email notice: that harassment (or another safety-floor category) was potentially detected between the two named parties, with no conversation content, quotes, or context attached.
- Each party is separately told that the conversation was escalated to HR for potential harassment — not what was said, just that it happened.
- Mend keeps no data and takes no further role. HR runs its own independent investigation from there — Mend is a notifier, not an investigator.

## Moat vs. Generic LLM Tools (ChatGPT, Copilot, Slack/Teams AI)

Captured 2026-10-19. The question worth returning to whenever scoping a new
feature: what does Mend do that a generic chatbot or an in-app enterprise AI
assistant structurally cannot, not just "do it with better prompts"?

1. **The enterprise panopticon problem.** Copilot, Slack AI, Teams AI, and
   Google Duet are built for enterprise indexing and executive discovery:
   every query, draft, and prompt is stored, searchable, and
   subpoena-ready. Employees will never type a raw, unvarnished grievance
   into Microsoft Copilot, because doing so creates a corporate paper trail
   HR can audit. Mend's hardware-enforced ephemerality (the TEE / Loom
   architecture above) is a structural guarantee those tools cannot offer
   without abandoning their own business model (enterprise search and
   retention).
2. **Decoupled Watcher vs. sycophancy loop.** Consumer LLMs are RLHF-tuned
   to be agreeable; venting about an unfair coworker tends to get validated
   back ("that does sound toxic"), fueling righteous indignation and
   escalatory draft messages. Mend's Facilitator/Watcher split (see the
   runtime loop above) exists specifically to intercept and regenerate a
   draft that validates a character attack instead of pointing at the
   structural pressure underneath — this is `BIAS_ASYMMETRY` and
   `UNFILTERED_TOXICITY` in the audit rubric, not a prompt-level
   instruction a generic assistant could just copy, since nothing audits
   the generic assistant's own output before it's shown.
3. **The structural attribution engine vs. pop psychology.** A generic
   assistant will readily hand back amateur diagnostic labels ("sounds like
   narcissism," "that's gaslighting") because it pattern-matches to
   internet pop psychology. Mend is anchored in Jehn's conflict taxonomy and
   the fundamental attribution error (see `PHILOSOPHY.md` in
   `../../apps/manager-app/`) and is built to systematically translate
   personal-character framing into its operational primitives: colliding
   KPIs, broken handoffs, bandwidth panic, undefined SLAs. `OUT_OF_SCOPE_ADVICE`
   in the Watcher rubric is what blocks the diagnostic-label failure mode.
4. **Asymmetric pacing (the Spool) vs. immediate prescriptions.** A generic
   assistant, handed a messy situation, tends to jump straight to a 5-step
   checklist or a ready-to-send email, before the user has finished
   processing what happened. Mend's pacing protocol (raw vent, then a
   pressure-gauge check for whether there's more, only then incentive
   inquiry and a plan) is a deliberate concession to the fact that a
   flooded nervous system can't evaluate trade-offs yet — see the triadic
   threat response discussion above in `PHILOSOPHY.md`.
5. **Realistic pushback (the Basting Stitch) vs. compliant roleplay.** A
   generic assistant playing the "other side" in a rehearsal tends to
   concede too easily, giving false confidence. The rehearsal sandbox is
   calibrated to push back using the counterpart's actual role constraints
   until the user's ask is framed in objective operational terms.
6. **Decoupled asynchronous consent (the Seam) vs. live concession.** A
   generic assistant mediating a live three-way chat has no mechanism for
   letting each side accept terms privately; Mend's handoff pattern
   collects each party's agreement independently, so neither side is
   forced into a face-losing concession in front of an audience.

## Unit Economics & Cost Analysis (100 conflict pairs / 10,000 turns)

- Intake side conversation (40 turns) + joint session (20 turns) + decoupled agreement (40 turns) = 100 turns per pair.
- Total LLM turn cost (Facilitator + Watcher): ~$0.0047/turn.
- Total cost for 100 full pairs: ~$47.00-$60.00 total spend.
- Gross margin on the software license exceeds 98%.
