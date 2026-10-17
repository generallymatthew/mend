#!/usr/bin/env python3
"""
Inference helper for the fine-tuned Mend conflict classifier, meant to be
called from the LiveKit-side pipeline described in
../joint-session-architecture.md: run this on each rolling STT chunk of
the *speaker's* transcript before that chunk is released to the other
party out of the delay buffer.

Deliberately biased toward precision on the cut decision: the threshold
defaults high (0.9) because a false-positive cut costs real trust, and
a missed cut is backstopped by the facilitator LLM's own slower,
fuller-context severity read (tiers 1/2) plus the tamper-evident trigger
record after the fact.

Usage:
    python inference.py --model_dir output/mend-conflict-classifier \\
        --text "some rolling transcript chunk"
"""
import argparse
import json

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

FLOOR_LABELS = [
    "harassment_discrimination",
    "threats_violence",
    "illegal_activity",
    "immediate_safety_risk",
]


class ConflictClassifier:
    def __init__(self, model_dir: str, cut_threshold: float = 0.9):
        with open(f"{model_dir}/labels.json") as f:
            self.labels = json.load(f)
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.eval()
        self.cut_threshold = cut_threshold

    @torch.no_grad()
    def score(self, text: str) -> dict:
        enc = self.tokenizer(text, truncation=True, max_length=128, return_tensors="pt")
        logits = self.model(**enc).logits[0]
        probs = torch.sigmoid(logits).numpy()
        return dict(zip(self.labels, probs.tolist()))

    def should_cut(self, text: str) -> tuple[bool, dict]:
        """Real-time decision: drop this chunk before it reaches the
        other party. High-precision by design -- see module docstring."""
        scores = self.score(text)
        floor_score = max(scores[label] for label in FLOOR_LABELS)
        in_progress_score = scores["in_progress"]
        # Both must independently clear the bar -- a category with no
        # immediacy signal isn't a live cut, it's a tier-2 disclosure for
        # the facilitator LLM to route to a silent wind-down instead.
        cut = floor_score >= self.cut_threshold and in_progress_score >= self.cut_threshold
        return cut, scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", default="output/mend-conflict-classifier")
    ap.add_argument("--text", required=True)
    ap.add_argument("--cut_threshold", type=float, default=0.9)
    args = ap.parse_args()

    clf = ConflictClassifier(args.model_dir, cut_threshold=args.cut_threshold)
    cut, scores = clf.should_cut(args.text)
    print(json.dumps({"text": args.text, "cut": cut, "scores": scores}, indent=2))


if __name__ == "__main__":
    main()
