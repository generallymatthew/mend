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
  without           ┌───┴────┐
  diagnosing)        ▼        ▼
                 [Deleted] [Email HR]
                 Zero       Names only,
                 trace      no content
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

`SAFETY_FLOOR` is the single exception to the zero-trace guarantee described above, and it is deliberately minimal:

- The session halts immediately. No further turns are generated.
- The conversation is deleted. No transcript, summary, or context is written anywhere — the zero-trace guarantee holds even for the violation itself.
- HR receives a names-only email notice: that harassment (or another safety-floor category) was potentially detected between the two named parties, with no conversation content, quotes, or context attached.
- Mend keeps no data and takes no further role. HR runs its own independent investigation from there — Mend is a notifier, not an investigator.

## Unit Economics & Cost Analysis (100 conflict pairs / 10,000 turns)

- Intake side conversation (40 turns) + joint session (20 turns) + decoupled agreement (40 turns) = 100 turns per pair.
- Total LLM turn cost (Facilitator + Watcher): ~$0.0047/turn.
- Total cost for 100 full pairs: ~$47.00-$60.00 total spend.
- Gross margin on the software license exceeds 98%.
