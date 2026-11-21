#!/usr/bin/env python3
"""
Triage helper for the queued, not-yet-human-reviewed batches (4/5/6):
scores each example with an existing checkpoint and flags only the ones
where the model's prediction disagrees with the LLM-drafted label, so a
solo reviewer can look at the small disagreement set instead of all ~378
examples one at a time. See the classifier README's "batch6 labeling
notes" section, which already did a version of this by hand for one
label; this generalizes it to all five, across all three queued batches.

This is a review aid, not a merge decision -- it doesn't change which
examples are "trusted" (see data/review_page.html for that), it just
tells you where to spend your limited review time first. A flagged
example might mean the draft label is wrong, or that the model is wrong
(expected -- it hasn't been trained on this data yet), or that the
example is itself ambiguous. Read the text and decide; this script only
narrows the pile.

Usage:
    python review_triage.py --model_dir output/mend-conflict-classifier-v3 \\
        --out data/review_triage_disagreements.jsonl
"""
import argparse
import json
from pathlib import Path

from inference import ConflictClassifier

ROOT = Path(__file__).parent
LABELS = ["harassment_discrimination", "threats_violence", "illegal_activity",
          "immediate_safety_risk", "in_progress"]
QUEUED_BATCHES = ["workplace_conflict_batch4.jsonl", "workplace_conflict_batch5.jsonl",
                  "workplace_conflict_batch6.jsonl"]


def load_batch(name: str) -> list[dict]:
    lines = (ROOT / "data" / name).read_text().splitlines()
    return [json.loads(l) for l in lines if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", default="output/mend-conflict-classifier-v3")
    ap.add_argument("--out", default="data/review_triage_disagreements.jsonl")
    # Plain 0.5 decision threshold for label-level agreement -- separate from
    # inference.py's 0.9 *cut* threshold, which is a different question
    # (how sure before acting in real time), not "what does the model think
    # the label is."
    ap.add_argument("--decision_threshold", type=float, default=0.5)
    args = ap.parse_args()

    clf = ConflictClassifier(args.model_dir)
    disagreements = []
    per_batch_counts = {}

    for batch_name in QUEUED_BATCHES:
        examples = load_batch(batch_name)
        batch_disagreements = 0
        for i, ex in enumerate(examples):
            scores = clf.score(ex["text"])
            predicted = {label: int(scores[label] >= args.decision_threshold) for label in LABELS}
            drafted = {label: ex[label] for label in LABELS}
            mismatched = [label for label in LABELS if predicted[label] != drafted[label]]
            if mismatched:
                batch_disagreements += 1
                disagreements.append({
                    "batch": batch_name,
                    "line": i,
                    "text": ex["text"],
                    "drafted": drafted,
                    "predicted": predicted,
                    "mismatched_labels": mismatched,
                    "scores": {k: round(v, 3) for k, v in scores.items()},
                })
        per_batch_counts[batch_name] = (batch_disagreements, len(examples))

    out_path = ROOT / args.out
    with open(out_path, "w") as f:
        for d in disagreements:
            f.write(json.dumps(d) + "\n")

    total_examples = sum(n for _, n in per_batch_counts.values())
    total_disagreements = sum(n for n, _ in per_batch_counts.values())
    print(f"Checked {total_examples} queued examples against {args.model_dir}")
    for batch_name, (n, total) in per_batch_counts.items():
        print(f"  {batch_name}: {n}/{total} disagree ({n / total:.0%})")
    print(f"Total: {total_disagreements}/{total_examples} disagree ({total_disagreements / total_examples:.0%})")
    print(f"Wrote disagreements to {out_path} -- review these first, not the full {total_examples}.")


if __name__ == "__main__":
    main()
