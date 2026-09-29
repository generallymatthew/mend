# Mend: Practice-Session Memory Schema

Problem: repeated practice sessions (e.g. rehearsing a "tough talk" before a real meeting, per [00_LIVE_MEETING_AI_COACH.md](00_LIVE_MEETING_AI_COACH.md)) shouldn't force the user to re-explain their situation from scratch every time. Saving full transcripts is unnecessary, inflates context cost, and violates Mend's zero-trace confidentiality premise.

## The Minimal Context Schema: "Practice State Anchor"

Serialize only the essential factual and psychological parameters into a lightweight, client-side state file (~300-500 tokens / under 2KB of JSON), rather than storing dialogue:

```json
{
  "scenario_metadata": {
    "counterpart_role": "Engineering Lead (Manager / Direct Peer)",
    "relationship_type": "Peer Reviewer / Cross-functional",
    "primary_grievance_category": "Delivery Bottlenecks & Public Ambush"
  },
  "the_north_star": {
    "tangible_objective": "24-hour turnaround SLA on pull requests or instant reassignment",
    "explicit_non_goal": "Extracting an apology for past sprint delays"
  },
  "counterpart_profile": {
    "probable_pressures": "Swamped with architecture refactoring; fears shipping buggy code",
    "primary_defensive_tactics": ["Weaponized process/perfectionism", "Dismissive sarcasm"]
  },
  "user_boundaries": {
    "firm_boundary": "No public call-outs in team-wide Slack or sprint demos",
    "flexible_concession": "Willing to split commits into PRs under 300 lines of diff"
  },
  "practice_analytics": {
    "sessions_completed": 2,
    "last_identified_weakness": "Conceded the SLA timeline too quickly when pushed on code quality",
    "mastered_points": ["Point 1 (Impact on sprint)", "Point 3 (Public ambushes)"]
  }
}
```

## What to Keep vs. What to Discard

| Retained state (~350-500 tokens) | Discarded (zero-trace / ephemeral) |
|---|---|
| The north-star objective: the single concrete agreement the user wants out of the meeting | Raw back-and-forth dialogue — every sentence said during previous practice turns |
| Counterpart pressure model: why the counterpart acts the way they do, to keep the AI roleplayer realistic | Emotional venting & complaints — the messy, raw initial venting from the intake side conversation |
| Concession limits: what the user is and isn't willing to trade | Intermediate Watcher logs: audits and draft rejections from earlier practice rounds |
| Progress delta: 1-2 sentences on the prior session's tactical mistake (e.g. "got defensive on turn 3") | Full audio / screen state: any recording or raw text buffer from prior sessions |

## Re-Initializing the Next Session

When the user returns for session #2 or #3, the system prompt loads this single anchor and opens with targeted coaching:

> "Welcome back. In our last rehearsal, your opening boundary on PR turnaround times was solid, but you dropped your stance when the manager pushed back on code quality. Do you want to re-run that specific pushback moment, or run a full 5-minute mock talk from the top?"

## Architecture & Privacy Implications

- **Storage footprint:** well under $0.0001 per user session to process, since thousands of historical chat tokens are never fed back into the model.
- **Preserving ephemerality:** because the schema contains no raw transcript quotes, names, or corporate secrets, it can be encrypted client-side with a symmetric key held in the user's browser session. Even if inspected, it reveals only tactical conversational strategy, not corporate records.
