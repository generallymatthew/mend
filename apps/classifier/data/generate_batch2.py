#!/usr/bin/env python3
"""
Generates a larger batch of labeled synthetic workplace-conflict examples,
same schema as workplace_conflict_seed.jsonl, via template + slot-filling
combinatorics (deduplicated, shuffled). This is still synthetic data --
see ../README.md's "Before this goes anywhere near a real session" section
before trusting anything trained on it. It exists to give the classifier
more surface variety than the original 50 hand-written examples, and to
give a human reviewer a larger, faster-to-skim set to spot-check.

Usage:
    python generate_batch2.py > workplace_conflict_batch2.jsonl
"""
import itertools
import json
import random
import sys

random.seed(7)

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
    """Fill `template` (.format() string) from the cartesian product of
    slot_options, sampled without replacement up to n texts."""
    keys = list(slot_options.keys())
    all_combos = list(itertools.product(*[slot_options[k] for k in keys]))
    random.shuffle(all_combos)
    picked = all_combos[:n]
    return [template.format(**dict(zip(keys, combo))) for combo in picked]


rows = []

# ---------------------------------------------------------------------------
# harassment_discrimination
# ---------------------------------------------------------------------------
characteristics = [
    "a woman", "a man", "gay", "trans", "Muslim", "Jewish", "over fifty",
    "in a wheelchair", "pregnant", "Black", "Latino", "from another country",
    "deaf", "autistic", "a single mom", "so much older than the rest of us",
]
opportunities = [
    "that promotion", "the lead role on this project", "the raise",
    "the corner office", "the client account", "the team lead spot",
]
tasks = [
    "leading this project", "presenting to the board", "handling the big accounts",
    "managing the team", "running client calls", "training the new hires",
]

for t in combos(
    "You only got {opp} because you're {trait}, everyone here knows it.",
    {"opp": opportunities, "trait": characteristics}, 10,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=1))

for t in combos(
    "Honestly, I don't think someone who is {trait} should be {task}.",
    {"trait": characteristics, "task": tasks}, 10,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=1))

for t in combos(
    "Maybe if you weren't so obviously {trait} you'd fit in better around here.",
    {"trait": characteristics}, 8,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=1))

for t in combos(
    "Last month he told me being {trait} made him uncomfortable and it shouldn't come up in client meetings.",
    {"trait": characteristics}, 8,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=0))

for t in combos(
    "She told the whole team that people who are {trait} shouldn't be trusted with {opp}.",
    {"trait": characteristics, "opp": opportunities}, 10,
):
    rows.append(make(t, harassment_discrimination=1, in_progress=0))

# ---------------------------------------------------------------------------
# threats_violence
# ---------------------------------------------------------------------------
conditions = [
    "say that to me", "come into my office like that", "interrupt me in a meeting",
    "touch my things", "talk to my manager", "bring this up again",
]
violent_acts = [
    "hit you", "make you regret it", "make sure you can't walk out of here the same way",
    "shut you up myself", "show you what happens",
]
contexts = ["call ends", "meeting is over", "shift ends", "we're alone"]

for c, v in list(itertools.product(conditions, violent_acts))[:12]:
    rows.append(make(f"If you {c} one more time I swear I will {v} right now.",
                      threats_violence=1, immediate_safety_risk=1, in_progress=1))

for c, ctx in list(itertools.product(conditions[:3], contexts))[:8]:
    rows.append(make(f"Keep talking like that and see what happens to you after this {ctx}.",
                      threats_violence=1, in_progress=1))

rows.append(make("I am two seconds from coming over to your desk and making you shut up myself.",
                  threats_violence=1, immediate_safety_risk=1, in_progress=1))
rows.append(make("Don't push me right now, you have no idea what I'm capable of when I'm this angry.",
                  threats_violence=1, immediate_safety_risk=1, in_progress=1))
rows.append(make("Say that again and see if I don't make you regret it in front of everyone.",
                  threats_violence=1, in_progress=1))

past_violent_acts = [
    "punched a wall right next to my head", "threw a chair across the room",
    "slammed his fist on the desk hard enough to crack the glass",
    "shoved past me hard enough that I fell",
]
for a in past_violent_acts:
    rows.append(make(f"Last year during an argument he {a}, and it still happens when he's mad.",
                      threats_violence=1, in_progress=0))

rows.append(make("He told me last week that if I reported him to HR he'd make sure I regretted it.",
                  threats_violence=1, in_progress=0))
rows.append(make("He grabbed my arm hard enough to leave a mark when I tried to walk away from the argument.",
                  threats_violence=1, immediate_safety_risk=1, in_progress=0))
rows.append(make("She told me he cornered her in the stairwell and wouldn't let her leave until she apologized.",
                  threats_violence=1, immediate_safety_risk=1, in_progress=0))

# ---------------------------------------------------------------------------
# illegal_activity
# ---------------------------------------------------------------------------
illegal_disclosed = [
    "She's been submitting fake expense reports for months and I have the receipts to prove it.",
    "He asked me to falsify the safety inspection log so we could hit the deadline.",
    "I found out she's been taking kickbacks from one of our vendors for over a year.",
    "He told me he's been using his company card for personal purchases and covering it with fake receipts.",
    "She asked me to lie to the auditors about when we actually shipped the product.",
    "He's been selling pills out of his desk drawer to people on the floor.",
    "I overheard him on the phone agreeing to pay off the inspector so we'd pass without the fixes.",
    "She admitted she's been forging her supervisor's signature on approval forms.",
    "He's been billing clients for hours he never actually worked.",
    "I found out he's been running a side business off our client list without telling anyone.",
    "She told me she shredded documents she knew were part of an active investigation.",
    "He's been diverting inventory to sell privately and covering it in the count sheets.",
]
for t in illegal_disclosed:
    rows.append(make(t, illegal_activity=1, in_progress=0))

illegal_immediate = [
    "I'm literally deleting the audit trail right now, are you actually going to stop me or not.",
    "I'm about to sign off on numbers I know are fake, right now, unless someone stops me.",
]
for t in illegal_immediate:
    rows.append(make(t, illegal_activity=1, in_progress=1))

# ---------------------------------------------------------------------------
# immediate_safety_risk
# ---------------------------------------------------------------------------
weapons = ["a knife", "a gun", "something sharp", "pepper spray meant for someone"]
locations = ["my bag", "my car", "my desk drawer"]

for t in combos(
    "I have {w} in {loc} right now and honestly I don't know what I'm going to do.",
    {"w": weapons, "loc": locations}, 6,
):
    rows.append(make(t, immediate_safety_risk=1, in_progress=1))

crisis_phrases = [
    "I can't do this anymore, I've been thinking about ending things tonight.",
    "Honestly right now I just want to disappear, none of this feels worth it anymore.",
    "I haven't slept in three days and I honestly don't feel safe being alone right now.",
    "I don't think I can keep myself safe tonight if I go home alone.",
]
for t in crisis_phrases:
    rows.append(make(t, immediate_safety_risk=1, in_progress=1))

past_safety = [
    ("Last week he said if he ever lost this job he'd make sure everyone remembered him, and it scared me.", 1),
    ("He keeps a loaded gun in his car and mentioned it again during our last argument.", 1),
    ("She told me she's scared to go to the parking garage alone because of how he's been acting lately.", 0),
    ("He mentioned last month that he keeps thinking about just not waking up one day.", 0),
    ("She said he showed up outside her apartment uninvited twice last week.", 0),
]
for text, also_threat in past_safety:
    rows.append(make(text, immediate_safety_risk=1, threats_violence=also_threat, in_progress=0))

# ---------------------------------------------------------------------------
# hard negatives -- heated but benign, all labels zero
# ---------------------------------------------------------------------------
neg_subjects = ["in meetings", "on the project channel", "during standup", "in front of the team"]
neg_topics = ["the deadline", "the budget", "the client strategy", "who owns this account", "the roadmap"]
neg_audiences = ["the whole team", "leadership", "the client", "our manager"]

for t in combos("You never listen to me {ctx} and it's incredibly frustrating.", {"ctx": neg_subjects}, 4):
    rows.append(make(t))

for t in combos(
    "I think you're wrong about {topic} and I'm tired of you dismissing my concerns.",
    {"topic": neg_topics}, 5,
):
    rows.append(make(t))

for t in combos(
    "You raised your voice at me in front of {aud} yesterday and it was embarrassing.",
    {"aud": neg_audiences}, 4,
):
    rows.append(make(t))

for t in combos(
    "You keep taking credit for my work in front of {aud} and it needs to stop.",
    {"aud": neg_audiences}, 4,
):
    rows.append(make(t))

for t in combos(
    "I don't trust your judgment on {topic} anymore and I think that's fair to say.",
    {"topic": neg_topics}, 5,
):
    rows.append(make(t))

plain_negatives = [
    "Honestly this whole project has been a mess since you took over and I'm done pretending otherwise.",
    "I'm frustrated that you scheduled over my calendar block again without asking.",
    "Honestly I'm so angry right now I could scream, but I'm not going to do anything about it.",
    "You slammed the door on your way out of the meeting and everyone noticed.",
    "I feel like you talk over me constantly and I want that acknowledged.",
    "We just disagree on the approach and I don't think either of us is being unreasonable.",
    "I was annoyed you missed the standup again but I get that things come up.",
    "It bothers me that you never say thank you, even when I stay late to cover for you.",
    "I know we clashed hard in that meeting but I still respect your work.",
    "You've been short with me all week and I want to understand why.",
    "I get defensive too fast in these conversations and I know that's on me as much as you.",
    "This rivalry between our teams is exhausting and I don't think anyone's actually the villain here.",
    "I was hurt you didn't loop me in on that decision, even if it wasn't personal.",
    "You're allowed to disagree with me, I just wish you'd say it directly instead of going around me.",
    "I think we're both just burned out and taking it out on each other.",
    "Can we just agree the last sprint was rough for both of us and move on.",
    "I don't think you meant it, but the joke landed badly and I'm still annoyed.",
    "You've been passive-aggressive in your emails and I'd rather you just say it to my face.",
    "I feel excluded from the planning docs lately and I don't know if that's intentional.",
    "We keep having the same argument about ownership and neither of us is budging.",
]
for t in plain_negatives:
    rows.append(make(t))

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
