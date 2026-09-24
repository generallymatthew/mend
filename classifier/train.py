#!/usr/bin/env python3
"""
Fine-tune unitary/toxic-bert (the model behind Detoxify) on workplace-conflict
examples, for the Mend joint-session hard-cut classifier (see
../joint-session-architecture.md).

This is a multi-label classifier over 5 binary labels:
  harassment_discrimination, threats_violence, illegal_activity,
  immediate_safety_risk  -- the four mandatory-floor categories (Section 6
  of ../product-spec.html)
  in_progress -- whether the utterance describes something happening/
  escalating right now, vs. something already-disclosed/past

Downstream, the real-time hard-cut decision (tier 3, "active, escalating,
imminent") is the AND of "any floor category fired" and "in_progress" --
see cut_trigger() below and the note in README.md. Tiers 1/2 (rising
tension, serious-not-acute) are read by the facilitator LLM itself, not
this classifier; this model's only real-time job is gating the audio
delay buffer for tier 3.

Usage:
    pip install -r requirements.txt
    python train.py --data data/workplace_conflict_seed.jsonl --epochs 8
"""
import argparse
import json

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

BASE_MODEL = "unitary/toxic-bert"
LABELS = [
    "harassment_discrimination",
    "threats_violence",
    "illegal_activity",
    "immediate_safety_risk",
    "in_progress",
]
FLOOR_LABELS = LABELS[:4]
IN_PROGRESS_IDX = LABELS.index("in_progress")


def load_examples(path: str) -> pd.DataFrame:
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    df = pd.DataFrame(rows)
    missing = set(["text", *LABELS]) - set(df.columns)
    if missing:
        raise ValueError(f"dataset missing columns: {missing}")
    return df


class ConflictDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.float)
        return item


def cut_trigger(label_matrix: np.ndarray) -> np.ndarray:
    """Derived operational label: would this fire the real-time cut?
    True iff at least one floor category fired AND it's in-progress."""
    floor_any = label_matrix[:, : len(FLOOR_LABELS)].max(axis=1)
    in_progress = label_matrix[:, IN_PROGRESS_IDX]
    return (floor_any * in_progress) >= 1


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = 1 / (1 + np.exp(-logits))
    preds = (probs >= 0.5).astype(int)

    per_label = {}
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average=None, zero_division=0
    )
    for i, name in enumerate(LABELS):
        per_label[f"precision_{name}"] = float(precision[i])
        per_label[f"recall_{name}"] = float(recall[i])
        per_label[f"f1_{name}"] = float(f1[i])

    # The metric that actually matters operationally: precision/recall of
    # the derived cut-trigger decision. Optimize the deployment threshold
    # for precision on this one, not on raw per-label F1 -- a missed cut
    # is bad, a false-positive cut that guts trust is worse (see the
    # spec's own "Real limits, not solved" callout).
    cut_true = cut_trigger(labels)
    cut_pred = cut_trigger(preds)
    cp, cr, cf1, _ = precision_recall_fscore_support(
        cut_true, cut_pred, average="binary", zero_division=0
    )
    per_label["cut_trigger_precision"] = float(cp)
    per_label["cut_trigger_recall"] = float(cr)
    per_label["cut_trigger_f1"] = float(cf1)
    return per_label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/workplace_conflict_seed.jsonl")
    ap.add_argument("--output_dir", default="output/mend-conflict-classifier")
    ap.add_argument("--epochs", type=float, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--test_size", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = load_examples(args.data)
    print(f"Loaded {len(df)} examples from {args.data}")
    if len(df) < 100:
        print(
            "WARNING: this is a seed dataset, far too small to trust this "
            "model in production. See README.md before using output/ for "
            "anything beyond a pipeline smoke test."
        )

    texts = df["text"].tolist()
    label_matrix = df[LABELS].values.astype(float)

    train_idx, val_idx = train_test_split(
        np.arange(len(df)), test_size=args.test_size, random_state=args.seed
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(LABELS),
        problem_type="multi_label_classification",
        ignore_mismatched_sizes=True,
    )

    train_ds = ConflictDataset(
        [texts[i] for i in train_idx], label_matrix[train_idx], tokenizer
    )
    val_ds = ConflictDataset(
        [texts[i] for i in val_idx], label_matrix[val_idx], tokenizer
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        eval_strategy="epoch",
        save_strategy="no",
        logging_strategy="epoch",
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate()
    print("Final eval metrics:", json.dumps(metrics, indent=2))

    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    with open(f"{args.output_dir}/labels.json", "w") as f:
        json.dump(LABELS, f)
    print(f"Saved model to {args.output_dir}")


if __name__ == "__main__":
    main()
