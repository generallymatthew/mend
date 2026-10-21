# Manager App: Workflow & Product Design

Design-conversation notes captured 2026-10-09, elaborating on the flow
already summarized in `STATUS.md`. See `PHILOSOPHY.md` for the reasoning
behind these choices and `THIMBLE_MINDSET.md` for the draft system-prompt
material. Nothing here is wired to code yet; `seam` is still a static
mockup (`App.dc.html` / `canvas.json`), not a running backend.

## Who this is for

A people manager who sees a direct report in conflict, either with another
report or with someone on another team, and doesn't have a playbook for
navigating it. Different audience from every other app in this repo, which
all face the employee or joint-session side.

## The core flow

Open a case → unpack what's going on → plan the next step together
(collaborative, not a canned tip list) → act off-app → report back on what
happened, looping back to planning if unresolved.

Two design decisions settled before any mockup:

1. Names of the people involved stay hidden by default (role labels like
   "your report" / "design team lead" instead of real names), since the
   goal is managing the conflict, not building a record on the individuals.
2. The whole interface is one continuous chat thread, not a multi-step form
   wizard. An earlier four-screen stepper-with-progress-dots version was
   explicitly rejected as feeling "administrative" / "enterprise," and
   rebuilt as a single two-pane messaging-app layout (conversation list
   left, one thread right), plus a right-side "plan so far" panel: a
   checklist of agreed steps, each editable with a pencil icon, a note field
   for what happened when a step is marked done, and "+ add a step." That
   panel is the one piece of visible structure in an otherwise unstructured
   conversation.

## Worked example: the step-by-step action plan

A manager opens with an unfiltered dilemma:

> "My junior designer just came to me stressed. A staff engineer on the core
> platform team shot down her mockups in a public Slack channel and called
> the layout unworkable. She's demoralized, but that engineer has a
> reputation for being territorial. How do I step in without starting a
> turf war with their director?"

Thimble's first move is triage, not sympathy: separate impact from intent
(the engineer is probably reacting to tech debt or latency, not malice), and
filter out character labels ("territorial," "toxic") so the manager stays
focused on the operational gap instead of the personality.

Then it builds an asymmetric staging plan, one step at a time rather than a
single bundled checklist:

- **Step 1, the report-alignment 1-on-1.** Meet again with the designer
  first. Clarify the boundary ("I have your back, but the goal is to ship
  this smoothly, not to extract an apology from engineering") and separate
  the technical constraints from how the feedback was delivered.
- **Step 2, the backchannel 1-on-1 with the other party.** Meet the engineer
  alone to hear their side first, leading with curiosity instead of
  accusation ("walk me through the backend blockers you're anticipating").
  Getting them to explain the technical risk out loud tends to disarm
  defensiveness on its own.
- **Step 3, ground rules before any joint meeting.** Get both sides to
  pre-commit to a frame: design reviews focus on user flows, technical
  reviews focus on APIs, and architectural disputes get raised 1-on-1
  rather than in public channels.
- **Step 4, the facilitated joint sync.** Host it as a project kickoff, not
  a grievance hearing.

## Managing up

A second, often-hidden pain point: managers dread reporting team friction to
their own boss, because leadership can read "your team is fighting" as "you
can't manage." Thimble can act as an executive translator, turning a raw
vent into a scripted upward update:

- Raw input: "Carol's team is completely ignoring our requests and her
  senior lead was a jerk to my designer in public."
- Scripted update: "We hit an architectural friction point with Platform
  Engineering on handoff specs. The team initially stalled, but I've aligned
  with their lead on an SLA for design reviews. We're holding a 15-minute
  calibration tomorrow to finalize it so release velocity isn't affected."

## Case-state persistence without breaking anonymity

Unlike the peer-to-peer flow, where ephemerality is essential because both
parties to the conflict are in the room and any persistent log becomes a
weapon for HR dossiers or blame litigation, the manager flow has no
counterpart present. The manager is acting as a case strategist, and real
people-management needs an ongoing, multi-turn plan. That's a deliberate,
narrow exception to "nothing persisted," not an abandonment of it:

1. **Role-based de-identification.** Real names never reach persistent
   state. "Marcus on my team clashing with Dave in Infrastructure" gets
   normalized to something like "Party A: direct report, mid-level product
   designer" / "Party B: cross-functional partner, staff infrastructure
   engineer" before anything is saved.
2. **Case-state anchor instead of raw transcript.** Persist a compact
   structured record, not a chat log:
   - *The tension:* spec misinterpretation and public callouts in the
     engineering channel.
   - *Last action:* 1-on-1 held with the designer; she felt heard on scope,
     agreed to submit specs via ticket templates going forward.
   - *Next action:* 15-minute check-in with the staff engineer on backend
     latency constraints.
3. **Workspace partitioning.** This state lives in the manager's own private
   workspace. HR and company leadership have zero query access to it. Even
   under an audit, there are no names, no transcripts, nothing to pull into
   a formal proceeding.

### Adaptive re-planning example

The manager returns after the engineer 1-on-1:

> "Okay, I met with the engineer. He didn't care about the layout; his
> concern was that the custom components will blow the latency budget. He
> admitted he was too blunt on Slack."

Thimble updates the case state and reframes the next move:

> "Good development: the blocker isn't ego, it's latency. Tell your designer
> engineering is on board with the UX flow but needs standard UI components
> to protect load time. Here's a script to frame that so she doesn't feel
> like engineering won the argument."

## Decoupled hand-off to a peer-to-peer session

Once the manager's prep converges on "both sides actually agree on what the
blocker is, just not each other," Thimble can surface a hand-off:

> "It sounds like both parties agree the handoff specs are the blocker, not
> each other. Want to invite them into a private Mend workspace to work out
> the exact review SLA directly?"

What that hand-off guarantees:

- **The manager's role ends there.** They pass along the link (or Mend
  sends a calendar-friendly nudge); they don't sit in the room, read drafts,
  or get the transcript.
- **Zero context leakage.** The employees' session doesn't inherit the
  manager's notes or framing. They start fresh with their own private
  intake.
- **Radical volatility for the peer session itself.** Even though the
  manager's own case-state anchor persists (per above), the joint session
  between the two employees runs in volatile memory and dissolves once it
  concludes, same as the standalone peer-to-peer flow.
- **Binary status only.** If anything is reported back to the manager at
  all, it's `Resolved` or `Not Resolved`, nothing else.

### The invite, framed as an action plan rather than conflict mediation

The employee-facing side of the hand-off deliberately avoids "conflict"
language (see `PHILOSOPHY.md`'s core reframe):

> **Team alignment: workflow calibration**
>
> Your lead set up a private Mend workspace for Design and Core Platform to
> align on handoff specs and review turnaround times.
>
> Completely confidential. No manager visibility. Used purely to land on an
> agreed way of working going forward.

And the facilitator opens the live session the same way, anchored on the
structural goal rather than on who was upset with whom:

> "Welcome. The goal of this session is straightforward: build a concrete
> action plan for design handoffs that protects UI requirements without
> risking backend latency. Let's define the rules of engagement that make
> that work for both of you."

The deliverable is a concrete working agreement (SLAs, review channels,
escalation rules), not a vague promise to "be nicer." See `PHILOSOPHY.md`
for why that distinction matters.

## Two modes, one engine

| | Peer-to-peer (Mend core) | Manager track (Mend coach) |
|---|---|---|
| User objective | Resolve a direct friction with a colleague | Coach through a third party's friction |
| Participants | Coworker A + Coworker B + facilitator | Manager + AI coach, solo |
| Data lifecycle | Strictly ephemeral, volatile memory only | Role-anonymized case state persists across steps |
| Tone | Neutral mediator: turns, de-biasing, safety floor | Tactical advisor: staging, script drafting |

A manager can spin off a peer-to-peer session at any point once ground rules
are set, bridging the two tracks without ever breaking the ephemerality
guarantee of the peer-to-peer side.
