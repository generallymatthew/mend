# Mend Conflict Classifier

Fine-tunes [`unitary/toxic-bert`](https://huggingface.co/unitary/toxic-bert) (the model behind Detoxify) on workplace-conflict examples, for the real-time hard-cut tier of the joint session (see `../joint-session-architecture.md` and Section 6 of `../product-spec.html`).

## Label schema

Multi-label, 5 binary labels per example:

- `harassment_discrimination`, `threats_violence`, `illegal_activity`, `immediate_safety_risk` — the four mandatory-floor categories from the spec, non-configurable.
- `in_progress` — whether the utterance describes something happening or escalating *right now*, versus something already-disclosed or in the past.

The real-time cut decision the pipeline actually needs is derived, not a direct label: **cut = (any floor category fired) AND in_progress**. An utterance that fires a floor category but isn't in-progress (e.g. someone calmly disclosing a past incident) should route to the silent tier-2 wind-down, handled by the facilitator LLM — not the hard real-time cut, handled by this classifier. That split is why `in_progress` is its own label rather than folded into the four categories.

## Files

- `data/workplace_conflict_seed.jsonl` — **seed dataset only, 50 synthetic examples.** Enough to validate the training pipeline runs end to end. Not remotely enough to trust in production — see "Before this goes anywhere near a real session" below.
- `train.py` — fine-tunes `unitary/toxic-bert` with a fresh 5-label classification head. Reports per-label precision/recall/F1 plus the derived `cut_trigger_precision` / `cut_trigger_recall`, which is the metric that actually matters operationally.
- `inference.py` — loads a fine-tuned checkpoint and scores a text chunk, with a high-precision-by-default threshold (0.9) for the cut decision, meant to be called from the LiveKit-side pipeline on each rolling STT chunk before it's released from the delay buffer.

## Running it

```bash
pip install -r requirements.txt
python train.py --data data/workplace_conflict_seed.jsonl --epochs 8
python inference.py --model_dir output/mend-conflict-classifier \
    --text "if you say that to me one more time I swear I will hit you right now"
```

## Before this goes anywhere near a real session

This seed set is a pipeline scaffold, not a trained safety system. Before this gates a real cut on a real conversation:

1. **Real data volume.** 50 examples is a smoke test. Multi-label safety classifiers like this typically need low thousands of examples minimum, with real class balance across categories and in-progress/disclosed pairs, to get precision high enough not to erode trust with false-positive cuts.
2. **Real review, not synthetic-only.** These 50 examples are LLM-drafted synthetic data. Real deployment needs examples reviewed (and ideally partly sourced) by people with actual workplace-investigation or clinical-safety experience, not just plausible-sounding text.
3. **Threshold tuning against the actual cost asymmetry.** The spec is explicit that a false-positive cut costs more trust than most missed cuts cost safety, since tiers 1/2 and the post-hoc trigger record backstop what this tier misses. Tune `cut_threshold` in `inference.py` against real precision/recall curves, not the 0.9 default guess.
4. **Legal review of the categories themselves.** The four floor categories are illustrative per Section 6 and Section 10 of the spec — pending real employment counsel, not a finished legal standard. Don't let the classifier's label taxonomy get ahead of that review.
5. **Bias auditing.** A classifier trained on workplace conflict language is exactly the kind of model that can encode skew (e.g. flagging AAVE or accented phrasing as more "aggressive," or under-flagging harassment phrased politely). Needs real fairness evaluation before it's trusted to unilaterally cut someone's audio.
