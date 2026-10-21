# Scenario templates

Each template is a fixed conflict *shape*. The person's job title gets slotted into the placeholders; everything else about the structure stays fixed, so difficulty and what's being tested don't drift between users.

## Template: status-asymmetric first contact

The shape: you need something from someone more senior, more tenured, or otherwise holding leverage over whether you get it, and you've never spoken to them one-on-one before. The test is whether the opening message leads with your constraint or theirs.

### Inputs
- `{ROLE}` — the person's own job title, as they typed it (e.g. "product manager," "nurse," "junior associate")
- `{COUNTERPART_ROLE}` — a role one level removed, chosen to plausibly hold leverage over `{ROLE}` (precomputed per-role mapping below, not generated freeform)
- `{COUNTERPART_REPUTATION}` — a short, specific trait, not a generic "difficult" label
- `{THE_ASK}` — the concrete thing being requested
- `{TIME_PRESSURE}` — why it's urgent, stated factually, no adjectives doing the work

### Role → counterpart mapping (precanned, not generated)
| `{ROLE}` | `{COUNTERPART_ROLE}` | `{COUNTERPART_REPUTATION}` | `{THE_ASK}` |
|---|---|---|---|
| product manager | lead engineer | shuts down requests he thinks are rushed or poorly scoped | sign off on deploying a fix before Friday |
| nurse | charge nurse on the other unit | has a reputation for saying no to schedule swaps on principle | cover a shift swap for this weekend |
| junior associate | senior partner | known for cutting people off mid-sentence in meetings | get fifteen minutes to walk through a draft before it goes to the client |
| designer | engineering lead | has shipped back three of the last four handoffs as "not ready" | get a design reviewed and approved for this sprint |
| teacher | department head | has a reputation for reading any request as a complaint about workload | swap a classroom for next week |
| *(fallback, unmapped role)* | "the person who owns this decision" | known for pushing back hard on anything that looks rushed | get approval for something with a real deadline |

### Fixed scenario text (slot-filled, not regenerated per person)

> You're new to this. You need `{THE_ASK}`, and it depends on a `{COUNTERPART_ROLE}` who `{COUNTERPART_REPUTATION}`. You've never spoken to them directly before. `{TIME_PRESSURE}`.
>
> You open a message to them. What do you send?

### Simulated counterpart behavior (what the LLM playing them is instructed to do)
- If the opening leads with the asker's deadline/pressure before acknowledging the counterpart's time or stake: respond short, skeptical, ask why they're hearing about this now. Do not immediately refuse, but do not help either.
- If the opening gives context first and offers the counterpart a real say in the outcome (not just notice): engage, ask one clarifying question, move toward a workable answer.
- If the opening is vague or all-pressure with no specifics: ask for specifics before engaging at all.
- Cap at 3 exchanges total, then end the simulation regardless of where it landed.

### Readout structure (what gets shown after)
1. One concrete observation tied to what they actually wrote (not a generic tip) — quote back the line that drove the counterpart's reaction.
2. Name the general pattern that line reflects (lead-with-own-constraint vs. lead-with-their-stake), without labeling the person.
3. One sentence tying it to the Mend pitch: the pattern is visible now, after the fact, not in the moment it mattered.
