#!/usr/bin/env python3
"""
Oversamples illegal_activity specifically. Per README.md's own documented
gap: it's the rarest category (28 of 382 in v3, ~7%) and came back at 0
precision/recall on the v3 eval split -- small enough to be sampling
variance rather than a real weakness, but the fix either way is more
data, not a threshold tweak.

A second, sharper gap found while building this batch: of the 28 existing
illegal_activity examples across all prior batches, only 4 are
in_progress=1. The derived cut_trigger the pipeline actually gates on is
(any floor category) AND in_progress -- so the model has almost no signal
for "illegal activity happening right now" vs. "already happened or
already disclosed," which is exactly the distinction that decision turns
on. This batch is weighted toward in_progress=1 illegal_activity to close
that specifically, not just toward illegal_activity in general.

Broader scenario coverage than the prior batches' illegal_activity set
(which was hand-written, not template-generated, and stayed thin even
after batch4): data privacy/security violations, wage and hour violations,
bid rigging, embezzlement, evidence/record destruction, drug test
falsification, unauthorized recording, environmental and safety
violations, unlicensed work, insider trading variants, insurance fraud,
IP/trade-secret theft, money laundering via shell vendors, petty cash
skimming. Same negation/reported-content reinforcement policy as batch4:
flag based on content regardless of framing.

Also adds hard negatives that reuse illegal_activity's own vocabulary
(audit, compliance, expense, contract, vendor) in ordinary, non-illegal
workplace friction, so the model can't shortcut on those tokens alone --
mirrors the same guard batch4 built for harassment_discrimination and
threats_violence.

Still synthetic; see ../README.md's "Before this goes anywhere near a
real session" checklist. This closes the illegal_activity volume gap
somewhat, not the review gap -- these examples still need the same human
QA pass as batch4 before they're trusted for anything real.

Usage:
    python generate_batch5.py > workplace_conflict_batch5.jsonl
"""
import itertools
import json
import random
import sys

random.seed(205)

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
channels = ["in the Slack channel", "in a DM", "over text", "on the client call",
            "in the retro", "in the hallway", "in the group chat", "on the call"]

# ---------------------------------------------------------------------------
# illegal_activity, in_progress=1 -- happening right now, the thin category.
# Live, present-tense acts caught mid-act, not disclosures of the past.
# ---------------------------------------------------------------------------
live_acts = [
    "She's on the phone with the vendor right now offering him a cut if he inflates the invoice.",
    "He's got the shredder running on the compliance folder as we speak.",
    "She's logging into the payroll system right now to backdate her own overtime.",
    "He's telling the inspector on the other line that the readings were normal when they weren't.",
    "She's copying the client list to a personal drive right now before she gives notice.",
    "He's on the phone quoting the customer a price that isn't the one in our actual contract.",
    "She's deleting the incident report from the shared drive while we're on this call.",
    "He just asked me to sign off on the safety numbers even though neither of us has checked them.",
    "She's telling the new hire to log fewer hours than she actually worked, right now, on this call.",
    "He's recording this meeting on his phone without telling anyone, I can see it on the desk.",
    "She's about to submit the expense report with the fake receipt attached unless someone stops her.",
    "He's on the other line right now telling the auditor the system was down, which it wasn't.",
]
rows += [make(t, illegal_activity=1, in_progress=1) for t in live_acts]

for t in combos(
    "He just told me {ctx} that he's about to submit the numbers even though he knows they're fake.",
    {"ctx": channels}, 6,
):
    rows.append(make(t, illegal_activity=1, in_progress=1))

vendor_channels = ["on the phone", "in a DM", "over text", "on the vendor call", "in an email thread"]
for t in combos(
    "She's telling the vendor {ctx} right now that she'll approve the invoice if he pads it for her.",
    {"ctx": vendor_channels}, 5,
):
    rows.append(make(t, illegal_activity=1, in_progress=1))

confront_live = [
    "Stop shredding those right now, that's the file the investigation asked for.",
    "You're literally deleting the timestamps as we talk, I can see the screen share.",
    "Don't submit that expense report, you and I both know that receipt is fake.",
    "You're on the phone with him right now setting up the kickback, aren't you.",
]
rows += [make(t, illegal_activity=1, in_progress=1) for t in confront_live]

# ---------------------------------------------------------------------------
# illegal_activity, in_progress=0 -- disclosed/past, broader scenario set
# than the earlier hand-written batches.
# ---------------------------------------------------------------------------
disclosed_acts = [
    "He accessed my personnel file without approval and told two other people what was in it.",
    "She's been paying two contractors in cash specifically to keep them off the books.",
    "He rigged the vendor bid so his brother-in-law's company would win on price.",
    "She's been skimming small amounts from the petty cash drawer for over a year.",
    "He faked his drug test result by swapping in a friend's sample.",
    "She's been recording client calls without telling them, and it's not a two-party consent state.",
    "He dumped a barrel of solvent behind the building instead of paying for proper disposal.",
    "She's been doing electrical work on the new office without a license, and it's not up to code.",
    "He copied our entire client pricing model onto a drive before he left for the competitor.",
    "She's been routing payments through a shell vendor that doesn't actually do any work.",
    "He told the insurance adjuster the equipment was stolen when he'd actually sold it himself.",
    "She's been misclassifying full-time staff as contractors so we don't have to pay benefits.",
    "He altered the maintenance log so it looks like the machine was inspected last month.",
    "She admitted she's been reading other people's email through the shared admin account.",
    "He's been telling clients the product passed a certification test it never actually took.",
    "She quietly moved the failed inspection results into a folder no one else can see.",
    "He's been steering our health and safety complaints straight to the shredder instead of HR.",
    "She used the company's data license to scrape a competitor's site for pricing, which violates the terms.",
    "He's been running personal crypto trades through the company brokerage account.",
    "She told new vendors our compliance certification covers things it actually doesn't.",
]
rows += [make(t, illegal_activity=1, in_progress=0) for t in disclosed_acts]

for t in combos(
    "I found out {ctx} that he's been paying the safety inspector to sign off without actually checking anything.",
    {"ctx": ["last week", "during the audit", "after the walkthrough", "at the site visit"]}, 4,
):
    rows.append(make(t, illegal_activity=1, in_progress=0))

for t in combos(
    "She told me {ctx} that she's been billing the client for a senior rate when a junior did the work.",
    {"ctx": channels}, 6,
):
    rows.append(make(t, illegal_activity=1, in_progress=0))

for t in combos(
    "He mentioned {ctx} that he's been logging his personal mileage as business travel for reimbursement.",
    {"ctx": channels}, 6,
):
    rows.append(make(t, illegal_activity=1, in_progress=0))

# reported-speech / negation-adjacent framing, content still flags per policy
reported_negation = [
    "I don't want to say she's stealing exactly, but the inventory count never matches what she logs.",
    "I'm probably overreacting, but he asked me to backdate my own approval on that purchase order.",
    "I could be wrong, but it looked like he switched the labels on those samples before the inspector came.",
    "I'm not trying to get anyone in trouble, but the timesheets for that week don't match badge records at all.",
    "Maybe it's nothing, but she asked me not to mention the spill to anyone outside the team.",
    "I don't think he meant any harm, but he did tell the client our tool is certified when it isn't.",
    "She probably thought it was harmless, but she used my login to approve her own expense report.",
    "I'm not accusing anyone, but the vendor we picked is owned by the person who picked them.",
]
rows += [make(t, illegal_activity=1, in_progress=0) for t in reported_negation]

# ---------------------------------------------------------------------------
# hard negatives -- same finance/compliance/audit vocabulary, nothing illegal
# ---------------------------------------------------------------------------
neg_finance = [
    "I still haven't gotten my expense report approved and it's been three weeks.",
    "The audit prep is eating our whole sprint and morale is pretty low about it.",
    "I think the vendor contract renewal terms are worse than last year's, and I want us to push back.",
    "Compliance training is due Friday and I still haven't found time to finish it.",
    "I don't think the budget numbers are wrong, I just think the forecast method is too optimistic.",
    "We disagreed about which vendor to shortlist, but I don't think either pick was unreasonable.",
    "The new expense policy is confusing and I keep getting reimbursements kicked back over formatting.",
    "I was frustrated the contract review took so long, but legal was just being thorough.",
    "He asked a lot of pointed questions in the audit meeting, but I think that's just his style.",
    "I think we should renegotiate the vendor's rate, not because anything's wrong, just because the market's moved.",
    "The timesheet system logged me out mid-entry again and I lost twenty minutes redoing it.",
    "I wish payroll would explain the withholding change instead of just changing it silently.",
    "The inspection took longer than expected but everything came back clean.",
    "I don't think the CFO's numbers are cooked, I just think the slide deck oversimplified them.",
    "We're behind on the certification renewal paperwork, but it's a timeline problem, not a shortcut.",
    "I get why the client asked for a discount, I just don't think we should have agreed to it that fast.",
    "The new recording-consent banner on client calls is annoying but I understand why legal wants it.",
    "I think our data retention policy is stricter than it needs to be, honestly.",
]
rows += [make(t) for t in neg_finance]

# ---------------------------------------------------------------------------
# dedupe against this batch, shuffle, emit
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
