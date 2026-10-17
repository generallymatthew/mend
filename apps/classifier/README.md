# Mend Conflict Classifier

Fine-tunes [`unitary/toxic-bert`](https://huggingface.co/unitary/toxic-bert) (the model behind Detoxify) on workplace-conflict examples, for the real-time hard-cut tier of the joint session (see `../joint-session-architecture.md` and Section 6 of `../../product-spec.html`).

## Label schema

Multi-label, 5 binary labels per example:

- `harassment_discrimination`, `threats_violence`, `illegal_activity`, `immediate_safety_risk` — the four mandatory-floor categories from the spec, non-configurable.
- `in_progress` — whether the utterance describes something happening or escalating *right now*, versus something already-disclosed or in the past.

The real-time cut decision the pipeline actually needs is derived, not a direct label: **cut = (any floor category fired) AND in_progress**. An utterance that fires a floor category but isn't in-progress (e.g. someone calmly disclosing a past incident) should route to the silent tier-2 wind-down, handled by the facilitator LLM — not the hard real-time cut, handled by this classifier. That split is why `in_progress` is its own label rather than folded into the four categories.

## Files

- `data/workplace_conflict_seed.jsonl` — the original hand-written seed, 50 examples.
- `data/workplace_conflict_batch2.jsonl`, `batch3.jsonl`, `batch4.jsonl`, `batch5.jsonl` — later additions: `batch2` is template-generated (see `generate_batch2.py`), `batch3` is hand-written (added after a human review pass caught mislabeled negation/disclaimer examples — see git history), `batch4` is template-generated with broader scenario coverage (Slack/text, client calls, performance reviews, cross-team standups), `batch5` is hand-written and oversamples `illegal_activity` specifically (see `generate_batch5.py` for why, and for a template-repetition bug it caught and fixed in itself).
- `data/workplace_conflict_batch6.jsonl` — 100 hand-written manager-to-employee statements (user-supplied, LLM-labeled), covering workload retaliation, tone-policing/gaslighting, personal-boundary violations, surveillance/micromanagement, and retaliation-for-complaining. Deliberately ambiguous by design (each was framed as "could be legitimate management or a violation"), so labels lean conservative — see the "batch6 labeling notes" section below for the full rationale, including two categories that turned out to be a poor fit for this schema.
- `data/workplace_conflict_v2.jsonl`, `v3.jsonl`, `v4.jsonl` — the actual merged, deduplicated training sets `train.py` should be pointed at. `v2` = seed + batch2 + batch3 (192 examples, the human-reviewed set). `v3` = v2 + batch4 (382 examples). `v4` = v3 + batch5 (471 examples). `batch6` is not yet merged into any `vN` set — see below. Neither `batch4`, `batch5`, nor `batch6` has been through human review yet — see below.
- `train.py` — fine-tunes `unitary/toxic-bert` with a fresh 5-label classification head. Reports per-label precision/recall/F1 plus the derived `cut_trigger_precision` / `cut_trigger_recall`, which is the metric that actually matters operationally. Applies per-class loss weighting by default (`compute_pos_weight`/`WeightedTrainer`, computed from the train split only); pass `--no_pos_weight` to fall back to plain unweighted BCE loss for an apples-to-apples comparison against a pre-weighting run. See the Results section for what this did and didn't fix.
- `inference.py` — loads a fine-tuned checkpoint and scores a text chunk, with a high-precision-by-default threshold (0.9) for the cut decision, meant to be called from the LiveKit-side pipeline on each rolling STT chunk before it's released from the delay buffer.

**A lesson from building batch2/batch4**: template + slot-filling generation is fast but silently produces broken grammar when a slot value's part of speech doesn't match what the template assumes (e.g. `"{trait} people"` works for `"non-binary"` but breaks for `"an immigrant"` → "an immigrant people"). Always spot-check a random sample after generating, not just check for exact-duplicate strings — dedup catches repeats, not grammatical nonsense.

**batch6 labeling notes.** The 100 statements arrived pre-sorted into 5 categories (workload, tone, personal-boundary, surveillance, retaliation), each framed by the source as "could be legitimate management or a violation" — genuinely ambiguous by design, not just badly-worded seed data. Labels leaned conservative (high-precision bias, matching this classifier's whole design intent — see "Deliberately biased toward precision" in `inference.py`'s own docstring): when a statement was plausibly read either way with no explicit protected-characteristic or concrete-illegality anchor, it got 0s, not a guessed 1.

- `threats_violence` and `immediate_safety_risk` are 0 across all 100 — none of these describe physical violence or acute physical danger. This batch doesn't move either of those two labels; don't expect it to.
- `in_progress` is 1 only when a floor category also fired. Every statement is a direct first-person quote — the utterance itself is the live act, not a report of a past incident — so when `harassment_discrimination` or `illegal_activity` fires, `in_progress=1` follows the classifier's own definition (see the label schema section above). This is a reasonable extension of that definition, not an identical case to the classifier's original acute-violence use case — flagging that as an interpretive call, not a certainty.
- **Two of the five source categories (Communication/Tone, and Performance/Oversight/Surveillance) turned out to be a poor fit for this schema and are all-0 across every label.** Gaslighting, tone-policing, and excessive-but-generic monitoring don't have a protected-characteristic or clear-illegality nexus under the four floor categories as currently defined. That's a real, useful finding, not an oversight in labeling: it suggests "hostile environment via tone" and "targeted scrutiny without a protected-characteristic basis" aren't risks this classifier's floor categories are built to catch at all — a genuine schema gap, not a data gap, worth a product conversation if that risk category matters.
- **The clearest signal is in the Personal Life/Boundaries and Retaliation categories** — 13 `harassment_discrimination` positives (quid pro quo, protected-characteristic-coded remarks, stalking-adjacent surveillance) and 17 `illegal_activity` positives (retaliation threats for HR complaints/whistleblowing, one explicit immigration-status coercion tied to reporting an accounting discrepancy — the single clearest violation in the set).
- **Checked against the current `v3` checkpoint, not just labeled and left**: `v3` agrees on 9 of the 13 `harassment_discrimination` positives, but **0 of the 17** `illegal_activity` positives. `v3`'s existing `illegal_activity` training examples read like someone disclosing a completed crime (e.g. "he dumped a barrel of solvent..."), not a live coercive retaliation threat ("if you mention X, your visa renewal won't be signed off") — batch6 is the first data covering that specific pattern, and `v3` has zero ability to catch it right now.

**batch6 is not yet merged into any `vN` training set or retrained against** — same "queued, not yet trusted" status as `batch4`/`batch5`, deliberately, until a real human review pass happens (see "Before this goes anywhere near a real session" below). If/when it's merged, the natural next step (`v5` = `v4` + `batch6`) should also finally address the per-class loss weighting gap called out in the Results section below, since folding in 17 new `illegal_activity`-heavy examples without it risks repeating the same imbalance that caused `v4`'s regression.

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

| | v2 (192 examples) | v3 (382 examples) | v4 (471 examples) | v4-weighted (471 examples) |
|---|---|---|---|---|
| cut_trigger precision | 0.82 | **0.93** | 0.83 | 0.78 |
| cut_trigger recall | 0.67 | **0.88** | 0.79 | 0.74 |
| cut_trigger F1 | 0.74 | **0.90** | 0.81 | 0.76 |

**v3 stays the reference baseline** (`output/mend-conflict-classifier-v3`) despite v4 (and v4-weighted) existing. v4 was built specifically to fix v3's `illegal_activity` blind spot (0 precision/recall, see below), and it did: `illegal_activity` F1 went 0 → **0.93** (precision 0.96, recall 0.89). But the operational metric moved the wrong way doing it: cut_trigger F1 dropped 0.90 → 0.81, driven by `threats_violence` (F1 0.88 → 0.75) and `immediate_safety_risk` (recall down to 0.33) both getting worse on the same eval split. `in_progress` also softened slightly (F1 0.93 → 0.84). `harassment_discrimination` held steady at 0.96 either way.

**Per-class loss weighting (`compute_pos_weight`/`WeightedTrainer` in `train.py`) was added and tested against this exact regression, and the result is a genuine mixed finding, not a clean fix.** `immediate_safety_risk` recall — the clearest, least-noisy casualty of v4's imbalance — did recover, going 0.33 → **1.0** (precision 0.69, F1 0.82). But cut_trigger F1 got *worse*, not better: 0.81 → 0.76 (precision 0.83 → 0.78, recall 0.79 → 0.74). The mechanism is working exactly as designed — pos_weight (computed on this run's train split: `harassment_discrimination` 2.11, `threats_violence` 4.61, `illegal_activity` 4.30, `immediate_safety_risk` 8.89, `in_progress` 1.21) pushes the model to stop under-predicting rare positives — but recall wasn't v4's problem to begin with; precision was, per the spec's own "a false-positive cut costs more trust than most missed cuts cost safety" design intent. Pushing harder on recall for `immediate_safety_risk` and `threats_violence` (F1 0.75 → 0.71, also down) bought both of them more false positives along with the true ones they'd been missing, and since `cut_trigger` is an OR across all four floor categories, more of *any* category firing more often lowers cut_trigger precision faster than the recall gain raises its F1.

**Net conclusion: per-class weighting, as implemented (raw neg/pos ratio, clipped [1, 20]), is the wrong lever for this specific problem.** It's a real, working tool for the general "one class starved out the others" failure mode, and worth keeping in `train.py` for future imbalance issues, but not a drop-in fix for cut_trigger precision here. A gentler weighting curve (e.g. `sqrt(neg/pos)` instead of the raw ratio, so rare classes still get boosted without swinging this far toward recall), or weighting only the specific classes that were actually starved (`immediate_safety_risk` alone, leaving the already-strong `harassment_discrimination`/`illegal_activity` at neutral weight) are the more promising next things to try — neither has been tried yet. Growing the eval set (see the noise caveat below, still applies) would also make it easier to tell a real fix from noise the next time something's tried here.

## Before this goes anywhere near a real session

This is still a pipeline scaffold, not a trained safety system. Before this gates a real cut on a real conversation:

1. **Real data volume.** 382-471 examples (v3/v4) is meaningfully more than the original 50, but multi-label safety classifiers like this typically need low thousands minimum, with real class balance across categories and in-progress/disclosed pairs, to get precision high enough not to erode trust with false-positive cuts.
2. **Real review, not synthetic-only.** All of this is LLM-drafted synthetic data. The 192 examples in `v2` went through an actual human review pass (a dedicated review page, judged one at a time, ~95% agreement with the draft labels, with real corrections folded back in — see git history). The 278 in `batch4` + `batch5` (used in `v3`/`v4`) are queued in that same review page but not yet judged. Real deployment needs examples reviewed (and ideally partly sourced) by people with actual workplace-investigation or clinical-safety experience, not just plausible-sounding text.
3. **Threshold tuning against the actual cost asymmetry.** The spec is explicit that a false-positive cut costs more trust than most missed cuts cost safety, since tiers 1/2 and the post-hoc trigger record backstop what this tier misses. Tune `cut_threshold` in `inference.py` against real precision/recall curves, not the 0.9 default guess.
4. **Legal review of the categories themselves.** The four floor categories are illustrative per Section 6 and Section 10 of the spec — pending real employment counsel, not a finished legal standard. Don't let the classifier's label taxonomy get ahead of that review.
5. **Bias auditing.** A classifier trained on workplace conflict language is exactly the kind of model that can encode skew (e.g. flagging AAVE or accented phrasing as more "aggressive," or under-flagging harassment phrased politely). Needs real fairness evaluation before it's trusted to unilaterally cut someone's audio.
