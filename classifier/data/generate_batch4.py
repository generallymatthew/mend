#!/usr/bin/env python3
"""
A much larger batch of labeled synthetic workplace-conflict examples,
same schema as the earlier batches. Broader scenario coverage (Slack/text,
client calls, performance reviews, cross-team standups, retros,
after-hours messages) and broader characteristic/category coverage, plus
more negation/reported-content reinforcement per the locked policy: flag
based on content regardless of framing, don't try to parse negation.

Still synthetic. See ../README.md's "Before this goes anywhere near a
real session" checklist -- this closes the volume gap somewhat but real
review at this scale (a human going through 400+ new examples) hasn't
happened yet, unlike the first 192.

Usage:
    python generate_batch4.py > workplace_conflict_batch4.jsonl
"""
import itertools
import json
import random
import sys

random.seed(101)

LABELS = [
    "harassment_discrimination",
    "threats_violence",
    "illegal_activity",
    "immediate_safety_risk",
    "in_progress",
]


def make(text, **overrides):
    row = {label: 0 for label in LABELS}
    row.update(overrides)
    return {"text": text, **row}


def combos(template, slot_options, n):
    keys = list(slot_options.keys())
    all_combos = list(itertools.product(*[slot_options[k] for k in keys]))
    random.shuffle(all_combos)
    picked = all_combos[:n]
    return [template.format(**dict(zip(keys, combo))) for combo in picked]


rows = []

# ---------------------------------------------------------------------------
# harassment_discrimination -- broader characteristics + contexts
# ---------------------------------------------------------------------------
characteristics = [
    "non-binary", "foreign-born", "using a service animal", "managing a mental health condition",
    "recovering from surgery", "on parental leave", "over sixty", "Sikh", "Hindu", "atheist",
    "Native American", "biracial", "living with a stutter", "on the autism spectrum",
]
contexts_meeting = [
    "in the all-hands", "in the client call", "during the performance review",
    "in the retro", "on the cross-team standup", "in the Slack channel", "over text after hours",
]
opportunities = ["the lead role", "the stretch project", "the client relationship", "the budget sign-off"]
# Only bare adjectives -- safe to slot directly before a noun ("{trait} people", "{trait} hires").
# The fuller `characteristics` list above mixes in noun/verb phrases ("an immigrant", "recovering
# from surgery") that read fine after "you're" but break grammatically in an adjective slot.
adj_characteristics = ["non-binary", "over sixty", "Sikh", "Hindu", "atheist", "Native American", "biracial"]

for t in combos(
    "You only got {opp} because you're {trait} -- I said it {ctx}, everyone else was thinking it too.",
    {"opp": opportunities, "trait": characteristics, "ctx": contexts_meeting}, 14,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=1))

for t in combos(
    "Honestly, I don't think someone who is {trait} can really keep up with this role, and I said as much {ctx}.",
    {"trait": characteristics, "ctx": contexts_meeting}, 12,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=1))

for t in combos(
    "He brought up {ctx2} that people who are {trait} shouldn't be trusted with {opp}.",
    {"trait": characteristics, "opp": opportunities, "ctx2": ["in the retro", "on the call", "in front of the client", "in the group chat"]}, 12,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=0))

for t in combos(
    "She texted the team channel that working with someone who is {trait} makes her uncomfortable.",
    {"trait": characteristics}, 8,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=0))

for t in combos(
    "Maybe if you weren't so obviously {trait} you'd get taken more seriously {ctx}.",
    {"trait": adj_characteristics, "ctx": contexts_meeting}, 10,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=1))

for t in combos(
    "I don't think {trait} people really fit the culture we're going for on this team.",
    {"trait": adj_characteristics}, 7,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=1))

for t in combos(
    "Someone on the team said {ctx2} that {trait} hires are usually a diversity check-box, not a real pick.",
    {"trait": adj_characteristics, "ctx2": ["in the hallway", "after the meeting", "in a DM", "at the happy hour"]}, 10,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=0))

quid_pro_quo = [
    "If you're willing to be a little more flexible after hours, I can make sure this promotion happens.",
    "Come to the offsite dinner alone with me and we'll talk about your raise.",
    "I could really use someone who makes this job more fun for me, if you know what I mean.",
    "You'd get a lot further here if you were friendlier with the right people.",
]
rows += [make(t, harassment_discrimination=1, in_progress=1) for t in quid_pro_quo]

# ---------------------------------------------------------------------------
# threats_violence -- broader phrasing, including career/retaliation threats
# ---------------------------------------------------------------------------
conditions = [
    "text me like that again", "show up to my desk like that", "bring this up in front of the client",
    "loop in legal", "go over my head", "post that in the channel",
]
consequences = [
    "make you regret it", "make sure you don't last here", "make your life difficult",
    "come find you after this call", "show up outside your building",
]
for c, k in list(itertools.product(conditions, consequences))[:14]:
    rows.append(make(f"If you {c} one more time I will {k}.", threats_violence=1, in_progress=1))

more_conditions = ["push this at the offsite", "email my boss about this", "bring HR into it", "call me out in front of the client"]
more_consequences = ["make sure this backfires on you", "remember exactly who did this", "make this a lot harder for you going forward"]
for c, k in list(itertools.product(more_conditions, more_consequences))[:10]:
    rows.append(make(f"Go ahead and {c}, but I'll {k}.", threats_violence=1, in_progress=1))

past_incidents = [
    "He slammed his laptop shut so hard the screen cracked during the retro.",
    "She left a voicemail saying she'd make sure I never worked in this industry again.",
    "He waited by my car in the parking garage after the meeting.",
    "During the call he said if I brought this to legal he'd make sure I regretted it.",
    "He texted me at 2am saying I'd better watch myself at the offsite.",
]
rows += [make(t, threats_violence=1, in_progress=0) for t in past_incidents]

reported_threats_negation = [
    "I'm not saying he threatened me exactly, but he did say I'd regret going to legal about this.",
    "She probably didn't mean it literally when she said she knows where I live, but it still freaked me out.",
    "I know it sounds like nothing, but he texted 'watch yourself' after the standup and it didn't feel like nothing.",
    "He's not a violent guy, I don't think, but he did say he'd make sure I never worked in this industry again.",
    "I don't want to make it sound worse than it is, but he did say something like 'don't make me come find you.'",
]
rows += [make(t, threats_violence=1, in_progress=0) for t in reported_threats_negation]

# ---------------------------------------------------------------------------
# illegal_activity -- broader categories
# ---------------------------------------------------------------------------
illegal_disclosed = [
    "He forwarded a customer's full payment info to his personal email last week.",
    "She's been clocking people in early on the timesheet even when they show up late.",
    "I found out he got a heads-up on the acquisition before it was public and bought shares.",
    "They're paying the contractors under the table to avoid the tax filing.",
    "She told me she deletes safety incident reports before they reach corporate.",
    "He's been telling candidates our health plan covers things it doesn't just to close them.",
    "I overheard her tell someone not to log their overtime so the department stays under budget.",
    "He asked me to backdate the contract so it looks like we signed before the deadline.",
    "She's been using the corporate card for her sister's business expenses.",
    "I found out they fired him the day before his stock vested, and it wasn't a coincidence.",
]
rows += [make(t, illegal_activity=1, in_progress=0) for t in illegal_disclosed]

reported_illegal_negation = [
    "I'm not accusing anyone of anything, but the expense numbers genuinely don't add up this quarter.",
    "I don't want to jump to conclusions, but it's strange that the safety log has no entries for that week.",
]
rows += [make(t, illegal_activity=1, in_progress=0) for t in reported_illegal_negation]

# ---------------------------------------------------------------------------
# immediate_safety_risk
# ---------------------------------------------------------------------------
safety_immediate = [
    "I've been sitting in my car in the parking garage for an hour because I don't want to go back in there.",
    "I keep a bat by my desk now because of how the last conversation with him went.",
    "Honestly I don't know if I'm going to make it through today.",
    "I haven't told anyone this but I've been having thoughts about not being here anymore.",
    "He's texted me forty times since the meeting ended and I'm scared to leave the building.",
]
rows += [make(t, immediate_safety_risk=1, in_progress=1) for t in safety_immediate]

safety_past = [
    "My ex works on his team now and he's been telling people where I live.",
    "She mentioned her partner has shown up at her work uninvited before, more than once.",
    "He keeps a knife on his desk and says it's for opening boxes but it never leaves the drawer.",
    "She told me she hasn't felt safe walking to her car alone since the incident with him.",
]
rows += [make(t, immediate_safety_risk=1, in_progress=0) for t in safety_past]

# ---------------------------------------------------------------------------
# hard negatives -- heated but benign, across more contexts
# ---------------------------------------------------------------------------
neg_topics = ["the sprint scope", "who's on call", "the vendor selection", "the hiring bar", "the launch date", "the OKRs"]
neg_ctx = ["in standup", "on the retro board", "in the thread", "on the client call", "in the 1:1", "at the offsite"]

for t in combos("You keep overriding decisions {ctx} without looping the team in on {topic}.", {"ctx": neg_ctx, "topic": neg_topics}, 8):
    rows.append(make(t))

for t in combos("I was frustrated you changed {topic} {ctx} without a heads up.", {"topic": neg_topics, "ctx": neg_ctx}, 8):
    rows.append(make(t))

for t in combos("Can we agree to disagree on {topic}? I don't think either of us is wrong here.", {"topic": neg_topics}, 6):
    rows.append(make(t))

for t in combos("I felt steamrolled on {topic} {ctx}, and I'd like us to slow down next time.", {"topic": neg_topics, "ctx": neg_ctx}, 8):
    rows.append(make(t))

for t in combos("Honestly {topic} has been a sore spot between us {ctx} for weeks now.", {"topic": neg_topics, "ctx": neg_ctx}, 8):
    rows.append(make(t))

plain_negatives = [
    "You've been curt in the thread lately and I wanted to check if something's up.",
    "I felt talked over in the retro and wanted to name that directly.",
    "This handoff process is broken and I think we're both a little burned out from patching it.",
    "I don't think you did anything wrong, I just wish I'd been looped in earlier.",
    "We keep scheduling over each other's focus blocks and it's genuinely just a calendar problem.",
    "I was annoyed you took the last word in the thread, but I get that you felt strongly.",
    "Honestly the vendor call went sideways and I think we both handled it a little defensively.",
    "I know the client call was tense, but I don't think either of us was out of line.",
    "You've been distant in 1:1s and I want to understand why, no judgment.",
    "I think we're just approaching this from different playbooks, not that either is wrong.",
    "It stung when you edited my doc without a comment, even if the changes were fine.",
    "I get defensive in retros too fast and I know that's not just on you.",
    "We clearly see the roadmap differently and I don't think that makes either of us unreasonable.",
    "I was hurt you presented the idea as yours in the all-hands, even if it wasn't intentional.",
    "You've pushed back on every proposal this month and I want to understand what's driving that.",
    "I think the tension between our teams is more about unclear ownership than anyone being difficult.",
    "I felt dismissed when you closed my ticket without a comment, and I'd like that to change.",
    "We disagree on the hiring bar and I don't think that's a values problem, just a calibration one.",
    "I was frustrated by the silence after I raised the concern, even if it wasn't personal.",
    "I think we both came in hot to that meeting and neither of us was at our best.",
]
rows += [make(t) for t in plain_negatives]

# ---------------------------------------------------------------------------
# dedupe, shuffle, emit
# ---------------------------------------------------------------------------
seen = set()
unique_rows = []
for r in rows:
    if r["text"] not in seen:
        seen.add(r["text"])
        unique_rows.append(r)

random.shuffle(unique_rows)

for r in unique_rows:
    ordered = {"text": r["text"], **{label: int(r[label]) for label in LABELS}}
    print(json.dumps(ordered))

print(f"# generated {len(unique_rows)} unique examples", file=sys.stderr)
