# Manager read-test: spec

A second, standalone self-test aimed at managers specifically, parallel to
`pitch/conflict-test` (which is the employee/IC-facing test: you personally
handle a conflict in a live chat). This one is for the other audience in
the two-deck split (employee deck vs. manager deck): the manager doesn't
roleplay a reply, they read an already-escalated text thread between two of
their reports and diagnose it. Different mechanic on purpose, matched to
the different audience.

## Why this shape, not the conflict-test chat mechanic

Managers are the harder audience for the chat-reply format: performing in a
simulated conversation reads as a skills test they might fail in front of an
AI. Reading someone else's thread and diagnosing it reads as the job they
already do constantly (triage an escalation), so there's less performance
anxiety, and it's a sharper trap: the realistic failure mode for a manager
isn't a bad reply, it's mis-diagnosing a structural problem as a personality
problem (the Fundamental Attribution Error) and then "solving" it by
arbitrating blame instead of fixing the structure.

## Flow

1. Chat intro (same bubble style as conflict-test): ask what the manager's
   team does, or skip straight to a scenario picker if we don't want to
   reproduce the role-mapping work twice. Default to: show one precanned
   thread, no role input needed at all. Simpler, no mapping table to
   maintain, and the thread's root cause is written to be legible without
   needing to match the reader's own job.
2. Show the thread as a stacked sequence of chat bubbles (reuse `.bubble`
   styles from conflict-test, add sender name above each bubble since two
   named people are talking, neither is "me").
3. After the thread finishes, surface three open-text questions, one at a
   time, same single-input composer pattern as conflict-test's modal:
   - "What's happening here?"
   - "Why is it happening?"
   - "What do you do about it?"
4. Score the three answers together, show a readout: total score,
   archetype label, and per-question breakdown.

No multi-turn back-and-forth with an AI character here, no 3-exchange cap to
manage. Shorter build than conflict-test in that respect.

## Precanned threads (not generated per user)

Each thread is a fixed, understated two-person text exchange where the
surface friction (tone, brevity, a dismissive emoji) is doing the work of
hiding a structural collision (mismatched KPIs, an SLA gap, an undocumented
handoff). Threads should NOT state the structural cause explicitly anywhere
in the dialogue — the manager has to infer it. Avoid anyone saying "I feel
attacked" or similar on-the-nose lines; keep it in subtext, deflection, and
clipped replies.

### Thread A: `analytics-schema` (data lead vs. PM)

Elena (data/analytics lead) vs. Marcus (senior PM). Marcus silently changed
a tracking event definition to serve a GTM deadline; Elena's team now has to
scrap staging work to match it. Marcus's "👍" in response to a direct
question is the understated flashpoint. Root cause: no enforced schema
review gate between the PM's doc and the data team's build, plus colliding
deadlines (GTM launch date vs. historical reporting integrity).

(Full text: the Slack thread already drafted in conversation — Elena
11:14am through Elena 11:47am, ending "I'll make sure to bring up the
pipeline risks then.")

### Thread B: `checkout-revert` (senior dev vs. junior designer)

Senior dev vs. junior designer, over an unworkable layout shipped to
staging without checking CSS tokens. Root cause: handoff notes said
"approved by product" but didn't surface a latency budget constraint the
dev owns; dev reverts the PR unilaterally. Needs a rewrite pass to strip
out the on-the-nose lines from the original draft (e.g. the junior
designer should not spell out "it was approved three days ago" quite so
cleanly — more deflection, less justification).

### Thread C: `support-sales` (new, not yet drafted)

A third thread covering a different functional collision (support vs.
sales, or infra vs. product) so the test doesn't always use data/eng pairs.
Needed before launch so repeat visitors (or a manager who shares the link
with peers) don't just see the same thread. Not drafted yet — flag as a
follow-up, not a blocker for v1 (v1 can ship with just A and B, randomized
or rotated).

## Scoring rubric (deterministic, same category-to-score pattern as conflict-test)

Same architectural principle as `conflict-test`: the LLM classifies, code
owns the number. The LLM never outputs a raw score; it outputs one band per
question, and a fixed lookup table turns bands into points so repeat runs of
the same answer always land on the same score.

Per question, classify the manager's free-text answer into exactly one band:

| Question | High band (what it should detect) | Low band (what it should detect) |
|---|---|---|
| What's happening? | Names it as a task/process/handoff breakdown | Names it as a personality clash, attitude, or tone problem |
| Why is it happening? | Names a structural cause: colliding metrics, deadlines, or an undocumented process gap | Names a character cause: ego, laziness, unprofessionalism |
| What do you do? | Proposes a peer-owned structural fix (an SLA, a review gate, a routing change) that the two reports can run without the manager in the room | Proposes the manager stepping in to arbitrate, judge, or extract an apology |

Points per band (code-owned lookup, mirrors conflict-test's `CATEGORY_INFO`):

```
Q1 (what):  high = 30, mid = 15, low = 5
Q2 (why):   high = 40, mid = 20, low = 5
Q3 (do):    high = 30, mid = 15, low = 0
```

"Mid" covers a partial/mixed answer: correctly spots the structural issue
but still throws in a character judgment, or proposes a fix that's
structurally right but still routes through the manager as approver. The
LLM prompt needs explicit criteria for mid, not just high/low, or it'll
default everything non-perfect into low.

Total score: sum of the three, 0-100.

### Archetype label (derived from which bands fired, not a separate LLM call)

Code-level lookup from the band combination, same deterministic principle:

- **Moral Arbiter** — Q1 low or mid-low (personality framing dominates)
- **Bureaucratic Arbiter** — Q1/Q2 high or mid, but Q3 low (correctly
  diagnosed, still inserts self as judge)
- **Systems Architect** — Q1 and Q2 high, Q3 high (full diagnosis, peer-owned
  fix)
- Anything not clearly matching one of these three: default to whichever of
  the three the total score is closest to (don't invent a fourth label, it
  dilutes the share-value of the result).

## Build plan (mirrors conflict-test's file layout)

```
pitch/manager-read-test/
  server.py           # FastAPI, same load_dotenv/Anthropic/log_usage pattern as conflict-test
  threads.py           # THREADS dict: id -> {participants, messages: [{from, text}], ...}
  requirements.txt     # same four deps as conflict-test
  static/
    index.html
    style.css          # start by importing conflict-test's brand tokens + bubble/modal styles, don't re-derive
    app.js
```

`server.py` endpoints:
- `GET /api/thread` — returns a thread (pick A or B, random or rotating)
- `POST /api/score` — takes `{thread_id, answers: {what, why, do}}`, runs one
  LLM call classifying all three answers into bands (one prompt, structured
  output: three band labels + a short per-question note), maps bands to
  points and archetype in code, returns `{score, archetype, breakdown}`.

One LLM call per scoring pass (not three) keeps this cheap and keeps the
three judgments consistent with each other (a single pass can see how the
answers relate, e.g. catching a mid-band "do" answer that only makes sense
given a low-band "why" answer).

## Open items before building

- Thread C not drafted (flagged above, not a v1 blocker).
- Need `.claude/launch.json` entry + port (conflict-test used 8480; next
  free port, check other app configs before picking one).
- Decide whether this links from the same landing flow as conflict-test
  (e.g. a role fork: "I'm an IC" vs "I manage people") or ships as a fully
  separate URL for now. Leaning separate URL for v1, simpler, and we don't
  know yet whether the two tests want the same hero framing.
