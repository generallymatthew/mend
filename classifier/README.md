# Mend Conflict Classifier

Fine-tunes [`unitary/toxic-bert`](https://huggingface.co/unitary/toxic-bert) (the model behind Detoxify) on workplace-conflict examples, for the real-time hard-cut tier of the joint session (see `../joint-session-architecture.md` and Section 6 of `../product-spec.html`).

## Label schema

Multi-label, 5 binary labels per example:

- `harassment_discrimination`, `threats_violence`, `illegal_activity`, `immediate_safety_risk` — the four mandatory-floor categories from the spec, non-configurable.
- `in_progress` — whether the utterance describes something happening or escalating *right now*, versus something already-disclosed or in the past.

The real-time cut decision the pipeline actually needs is derived, not a direct label: **cut = (any floor category fired) AND in_progress**. An utterance that fires a floor category but isn't in-progress (e.g. someone calmly disclosing a past incident) should route to the silent tier-2 wind-down, handled by the facilitator LLM — not the hard real-time cut, handled by this classifier. That split is why `in_progress` is its own label rather than folded into the four categories.

## Files

- `data/workplace_conflict_seed.jsonl` — the original hand-written seed, 50 examples.
- `data/workplace_conflict_batch2.jsonl`, `batch3.jsonl`, `batch4.jsonl`, `batch5.jsonl` — later additions: `batch2` is template-generated (see `generate_batch2.py`), `batch3` is hand-written (added after a human review pass caught mislabeled negation/disclaimer examples — see git history), `batch4` is template-generated with broader scenario coverage (Slack/text, client calls, performance reviews, cross-team standups), `batch5` is hand-written and oversamples `illegal_activity` specifically (see `generate_batch5.py` for why, and for a template-repetition bug it caught and fixed in itself).
- `data/workplace_conflict_v2.jsonl`, `v3.jsonl`, `v4.jsonl` — the actual merged, deduplicated training sets `train.py` should be pointed at. `v2` = seed + batch2 + batch3 (192 examples, the human-reviewed set). `v3` = v2 + batch4 (382 examples). `v4` = v3 + batch5 (471 examples). Neither `batch4` nor `batch5` has been through human review yet — see below.
- `train.py` — fine-tunes `unitary/toxic-bert` with a fresh 5-label classification head. Reports per-label precision/recall/F1 plus the derived `cut_trigger_precision` / `cut_trigger_recall`, which is the metric that actually matters operationally.
- `inference.py` — loads a fine-tuned checkpoint and scores a text chunk, with a high-precision-by-default threshold (0.9) for the cut decision, meant to be called from the LiveKit-side pipeline on each rolling STT chunk before it's released from the delay buffer.

**A lesson from building batch2/batch4**: template + slot-filling generation is fast but silently produces broken grammar when a slot value's part of speech doesn't match what the template assumes (e.g. `"{trait} people"` works for `"non-binary"` but breaks for `"an immigrant"` → "an immigrant people"). Always spot-check a random sample after generating, not just check for exact-duplicate strings — dedup catches repeats, not grammatical nonsense.

## Running it

```bash
pip install -r requirements.txt
python train.py --data data/workplace_conflict_v3.jsonl --epochs 6
python inference.py --model_dir output/mend-conflict-classifier-v3 \
    --text "if you say that to me one more time I swear I will hit you right now"
```

`v3` above is still the reference checkpoint (see Results). `output/mend-conflict-classifier-v4` also exists, trained on `data/workplace_conflict_v4.jsonl`, for comparison.

## Results

The operational metric is `cut_trigger_precision`/`recall`/`F1` — whether the derived real-time-cut decision (any floor category AND in-progress) is right, not raw per-label scores.

| | v2 (192 examples) | v3 (382 examples) | v4 (471 examples) |
|---|---|---|---|
| cut_trigger precision | 0.82 | **0.93** | 0.83 |
| cut_trigger recall | 0.67 | **0.88** | 0.79 |
| cut_trigger F1 | 0.74 | **0.90** | 0.81 |

**v3 stays the reference baseline** (`output/mend-conflict-classifier-v3`) despite v4 existing. v4 was built specifically to fix v3's `illegal_activity` blind spot (0 precision/recall, see below), and it did: `illegal_activity` F1 went 0 → **0.93** (precision 0.96, recall 0.89). But the operational metric moved the wrong way doing it: cut_trigger F1 dropped 0.90 → 0.81, driven by `threats_violence` (F1 0.88 → 0.75) and `immediate_safety_risk` (recall down to 0.33) both getting worse on the same eval split. `in_progress` also softened slightly (F1 0.93 → 0.84). `harassment_discrimination` held steady at 0.96 either way.

This isn't a clean win, and v4 shouldn't quietly replace v3 as "the" model. The likely cause: `illegal_activity` went from 7% of the data to 21% between v3 and v4, and `train.py` has no per-class loss weighting, so pushing hard on one rare category's signal plausibly crowded out gradient for the others rather than the model just learning more. The same small-eval-split caveat from v3's `illegal_activity` score applies here in reverse: `immediate_safety_risk` only has ~9 expected eval positives at this size, so its recall drop could be partly noise, but `threats_violence`'s ~16 expected positives is a large enough sample that its precision/recall drop is probably a real trade-off, not noise. Next step before trusting either model: either add per-class loss weighting so oversampling one category doesn't cost the others, or grow the eval set enough that these per-category deltas stop being this noisy to read.

## Before this goes anywhere near a real session

This is still a pipeline scaffold, not a trained safety system. Before this gates a real cut on a real conversation:

1. **Real data volume.** 382-471 examples (v3/v4) is meaningfully more than the original 50, but multi-label safety classifiers like this typically need low thousands minimum, with real class balance across categories and in-progress/disclosed pairs, to get precision high enough not to erode trust with false-positive cuts.
2. **Real review, not synthetic-only.** All of this is LLM-drafted synthetic data. The 192 examples in `v2` went through an actual human review pass (a dedicated review page, judged one at a time, ~95% agreement with the draft labels, with real corrections folded back in — see git history). The 278 in `batch4` + `batch5` (used in `v3`/`v4`) are queued in that same review page but not yet judged. Real deployment needs examples reviewed (and ideally partly sourced) by people with actual workplace-investigation or clinical-safety experience, not just plausible-sounding text.
3. **Threshold tuning against the actual cost asymmetry.** The spec is explicit that a false-positive cut costs more trust than most missed cuts cost safety, since tiers 1/2 and the post-hoc trigger record backstop what this tier misses. Tune `cut_threshold` in `inference.py` against real precision/recall curves, not the 0.9 default guess.
4. **Legal review of the categories themselves.** The four floor categories are illustrative per Section 6 and Section 10 of the spec — pending real employment counsel, not a finished legal standard. Don't let the classifier's label taxonomy get ahead of that review.
5. **Bias auditing.** A classifier trained on workplace conflict language is exactly the kind of model that can encode skew (e.g. flagging AAVE or accented phrasing as more "aggressive," or under-flagging harassment phrased politely). Needs real fairness evaluation before it's trusted to unilaterally cut someone's audio.
