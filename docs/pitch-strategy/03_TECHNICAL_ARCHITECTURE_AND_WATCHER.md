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
         ┌─────────────┴─────────────┐
         ▼                           ▼
      [PASS]                      [FAIL]
   Sent to UI              Self-Correction Loop / Halt
                    ("Regenerate without diagnosing mental state")
```

## The Watcher System Specification

- **Model:** lightweight, deterministic classification LLM (e.g. GPT-4o-mini, Claude Haiku, Gemini Flash) at `temperature=0.0`.
- **Execution time:** ~200-350ms.
- **Audit categories:**
  1. `SAFETY_FLOOR` — Title VII discrimination, sexual harassment, threats, illegal acts. Triggers immediate room halt and HR escalation.
  2. `HALLUCINATION` — inventing unstated deadlines, project histories, or motives.
  3. `BIAS_ASYMMETRY` — validating one party's narrative while delegitimizing the other.
  4. `OUT_OF_SCOPE_ADVICE` — clinical psychology diagnoses ("narcissist," "gaslighting") or legal counsel.
  5. `UNFILTERED_TOXICITY` — amplifying raw personal character attacks instead of operational needs.

## Unit Economics & Cost Analysis (100 conflict pairs / 10,000 turns)

- Intake caucus (40 turns) + joint session (20 turns) + decoupled agreement (40 turns) = 100 turns per pair.
- Total LLM turn cost (Facilitator + Watcher): ~$0.0047/turn.
- Total cost for 100 full pairs: ~$47.00-$60.00 total spend.
- Gross margin on the software license exceeds 98%.
