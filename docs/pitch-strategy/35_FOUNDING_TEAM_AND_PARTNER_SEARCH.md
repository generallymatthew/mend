# Founding Team and Partner Search

Captured 2026-11-27 from a brainstorm conversation about bringing on
partners. Reference notes, not decisions. Equity ranges and role splits
below are typical-startup illustrations from that conversation, not
legal or financial advice, and nothing has been offered to anyone yet.

The conversation used the name "Mend"; the public name is now Thimble
(see the naming note in the repo memory). Outreach copy below should say
Thimble.

Related: [06_HR_BUYER_OUTREACH_STRATEGY.md](06_HR_BUYER_OUTREACH_STRATEGY.md),
[26_SELLING_TO_MANAGERS.md](26_SELLING_TO_MANAGERS.md),
[33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md](33_EVIDENCE_STRATEGY_AND_BUYER_PERSONAS.md).
To-do item t78 tracks the HR follow-up.

---

## The team shape being considered

Three seats:

| Seat | Owns | Why it matters | Typical early equity |
|---|---|---|---|
| Product and systems design (Matt) | Product vision, UX and interaction pacing, conversational state logic, company direction | Originated the IP, built the working prototype, owns the user-trust moat | 50–65% (originator, CEO) |
| Tech lead | Production backend, volatile-memory / confidential-compute architecture, latency, SOC 2 and enterprise security | Removes the "solo non-technical founder" risk and gets through enterprise IT and security review | 20–30% (4-year vest, 1-year cliff) |
| HR specialist (People and GTM) | Buyer narrative, community distribution (Slack groups, Reddit), compliance guardrails, pilot intros | Gets past the vendor reflex in HR communities; turns the product into CFO-ready ROI | 10–20% if full-time co-founder, or 1–3% if part-time advisor |

### Two guardrails before offering anything

- **Full-time versus nights and weekends.** Don't give co-founder-level
  equity (15–25%) to someone keeping their day job indefinitely. If the
  HR contact stays at her startup and helps on the side, structure it as
  a founding advisor role (roughly 1–2%, vesting over 2 years) tied to
  milestones like running community outreach or introducing pilot teams,
  with an option to move into a co-founder role if she goes full-time.
- **Everyone vests, including Matt.** 4-year schedule, 1-year cliff. If
  someone leaves at month four, they leave with nothing, so the company
  doesn't carry dead equity.

### Suggested order

1. **HR specialist first, as a test partner.** Brainstorm call, co-write
   one community post, see whether her voice actually pulls in manager
   testers.
2. **Use that to recruit the tech lead (2–4 weeks later).** "Working
   prototype, live test data, and a sitting SF startup VP of People
   helping with GTM" is a much easier pitch to an engineer.
3. **Run a 2–4 week trial sprint with each person before any paperwork.**
   Work on a concrete deliverable together first.

---

## The HR specialist (SF startup VP of People)

### Why she matters most right now: distribution

Matt got banned the first time he posted in an HR space. Moderators and
members read a UX designer posting there as an outside vendor fishing for
free research. When she posts as a sitting VP of People, she is a peer
sharing a workflow experiment with her own community.

- **Insider credibility.** She knows the shorthand, the compliance
  worries, and the daily problems of startup People leads and frontline
  managers.
- **Access to closed groups.** She is likely already in invite-only
  People Ops communities (examples named: Charter, Resources for Humans,
  PeopleTech Partners, CPOHQ) where cold outreach doesn't work and
  software recommendations actually get made.
- **Framing that lands.** Something like: "I've been advising a designer
  on an off-the-record scratchpad to stop my managers pasting sensitive
  employee issues into personal ChatGPT. Would love 5 other People leads
  or EMs to sanity-check the guardrails."

### How to start without over-committing

Treat her as an informal design partner. She already said she has a lot
of ideas, and Matt has real questions for her, so the questions are the
reason to reconnect. That tests working chemistry before any talk of
equity, titles or contracts.

**Step 1. Low-pressure message.** Draft:

> Subject: Taking you up on bouncing some ideas around
>
> Hey [Name],
>
> Thanks again for the chat last week. Your point about framing this
> around team dynamism and manager leverage instead of "conflict" has
> stuck with me.
>
> You mentioned having a lot of ideas in this space. As I refine the
> prototype and the buyer story, I have 3 or 4 specific questions from
> the People/HR side I'd love your gut reaction on, especially how an HR
> team would measure ROI without ever seeing session transcripts.
>
> No pitch or big ask. Could I grab 20 minutes next week to pick your
> brain?

**Step 2. Use the call to test chemistry and value.**

- Bring concrete things to react to, not abstract questions: a rough
  1-page HR ROI readout (manager hours saved, speed to resolution) or
  the safety floor, and ask her to tear it apart.
- Watch for sharp, practical pushback (how CFOs scrutinize renewals,
  what makes engineering managers actually adopt a tool) versus vague
  big-picture ideas.
- Gauge bandwidth: does she want a side project to advise on a few hours
  a month, or does she want to build something from the ground up?
- Be direct about the distribution problem: "I can build the system, but
  in HR and manager forums I get treated like an outside vendor. Someone
  with your credibility who speaks the language is huge."

**Step 3. End with one small, time-boxed next step.** Not "want to be my
co-founder?" Options:

- Co-write one post for one of her HR or manager communities over the
  next two weeks and see the response.
- Introduce Matt to two other startup People leads for feedback.
- Let 5 of her frontline managers use the prototype off the record for
  two weeks.

Then say plainly: if it clicks and she wants to own the People/GTM side,
Matt is open to a formal advisor or co-founder structure once both can
see how early traction feels. People who are real partners open doors;
this shows whether she follows through before equity or a title changes
hands.

### Questions to ask her

Pick the 3 or 4 closest to what's most uncertain at the time, so it feels
like a peer brainstorm rather than an interview.

**Rollout and usage**

- "If you rolled out a zero-trace prep tool like this, where would you
  draw the line? Push it broadly, or only drop it into high-friction
  moments like 1-on-1s and retros?"

  Working assumption going in: HR would almost certainly not ask people
  to use it before every meeting. It adds friction to an already
  meeting-heavy day, it signals "HR thinks you're about to fight," and
  HR won't put its name on a blanket mandate for an unmonitored tool.
  What HR is more likely to endorse:
  - Use before high-tension moments: performance calibrations, hard
    feedback 1-on-1s, post-mortems after a blown deadline, deadlocked
    cross-team handoffs.
  - A safe alternative to personal AI: "Stop pasting sensitive team
    issues and PIP drafts into ChatGPT on your phone. Use this
    zero-trace tool instead."
  - Manager-triggered: a manager sees two teammates stuck and sends a
    private link so they can agree on a plan before the next sync.

**Budget and purchasing**

- "If a frontline engineering manager wants to expense a $300–500/year
  leadership tool on their L&D stipend or team card, does IT or People
  Ops block it, or does it go unnoticed until 10+ managers are using it?"
- "When you defend software renewals to your CFO, what number keeps a
  tool from getting cut: manager hours saved, lower regrettable
  attrition, or avoided outside employment-counsel fees?"

**Legal and compliance**

- "When you hear 'zero-trace, volatile memory, HR never sees
  transcripts,' does your compliance brain worry about hidden liability,
  or does a hardcoded circuit breaker for harassment and Title VII
  issues satisfy you?"
- "If the tool detects a serious statutory issue and triggers an alert,
  how would you want that handoff to work so it doesn't feel like
  spyware to everyone else?"

**Personal-AI risk and rollout framing**

- "How worried are you about managers pasting PIP drafts and sensitive
  disputes into personal ChatGPT? If you gave them a sanctioned,
  zero-save alternative, would you frame it as data security or as
  manager enablement?"
- "If we gave 5–10 of your newest managers a free browser link with no
  IT setup for 30 days, what would make them actually open it before a
  tough 1-on-1 instead of forgetting it exists?"

**Gauging her interest in partnering**

- "When you look at how People teams run at startups your size, what's
  the biggest daily problem around manager and team friction that nobody
  is building for yet?"

---

## The tech lead

### What Matt wants

Ideally local (Triangle) and someone he has worked with before. He knows
some strong developers but held off reaching out until he felt confident
the app was viable.

Holding off was reasonable: there is one first impression when pitching
a former teammate, and a half-formed idea spends social capital. The
position is different now: a live build in user testing, paying checkout
live, and a potential HR partner on the buyer side. The ask is no longer
"gamble on an idea" but "look at a working system."

### How to approach a former colleague

Keep it low-pressure, technical, and ego-free so they don't feel pushed
to quit their job.

**Lead with the working system, not a pitch.** Draft (personal channel:
text, Signal, or personal email):

> Hey [Name], hope things are going well!
>
> On my own time I've been building an off-the-record workplace tool
> called Thimble (a multi-agent state machine running in volatile memory
> with no stored transcripts). I have a working build deployed with live
> user testing, and I'm talking with an SF startup VP of People on the
> HR and go-to-market side.
>
> I've always respected how you think about backend architecture and
> security. I'd love to buy you a coffee or beer in Durham/Raleigh next
> week. No pitch: I just want to show you how I wired the state machine
> and get your honest read on what it would take to harden it for
> enterprise scale.

**Why this works with former teammates**

- No pressure: the ask is 45 minutes of their engineering brain over
  coffee, not a career change.
- Respects their employer: personal channels and an off-site meeting
  show Matt takes IP and day-job boundaries seriously.
- Lets them opt in: if they see the UX and conversational logic are
  already solved and get interested in the technical problems
  (volatile-memory enclaves, supervisor latency, zero-retention
  pipelines), they'll ask how to get involved.

**If one of them wants in: a nights-and-weekends sprint.** Offer a
4-week side-project sprint before talking about quitting jobs or
splitting equity. Give them one contained infrastructure milestone
(hardening the backend API, or setting up the confidential-memory
pipeline) so both sides can check the working relationship outside a
corporate setting.

### Open question to think through

Of the 2 or 3 developers Matt has worked with, which one has the
strongest instincts for backend security, infrastructure, or AI
pipelines, and would enjoy digging into this over coffee?
