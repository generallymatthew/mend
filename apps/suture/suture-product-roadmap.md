# Suture — Product Roadmap

Suture is the two-person facilitated conversation itself, inside Thimble —
the live joint session specifically, not the intake step before it. Maps to
`suture` (the current typed-chat prototype) and
`joint-session-audio/` (the real-time audio prototype these items merge
into). Thimble's solo intake half has its own roadmap at
`../thimble/thimble-product-roadmap.md`.

For shared, cross-app positioning principles, see the root
`../../ROADMAP.md`. Per the 2026-10-17 app-concept ranking in
`../../IDEAS.md`, Suture has the weakest adoption pull of the core three
apps (needs a manager to nominate the pair, or two peers to opt in
together) but by far the strongest moat: live, bidirectional,
two-safety-floors-at-once facilitation is the hardest problem in the repo
for a generic assistant to replicate on the fly.

## Phase 1 — Real-time audio/video, one voice-driven session

`joint-session-audio/` and `suture` are still two independently
run prototypes an operator starts by hand under the same code. This phase
is the merge.

- [x] Real audio delay buffer (LiveKit + streaming STT + the hard-cut
      classifier)
- [x] Symmetric video opt-in (parity enforcement, not just UI)
- [x] LiveKit private breakout/side-conversation room (transport only)
- [x] Prosody/tone signal, proof-of-concept validated, wired into the
      facilitator LLM
- [ ] Facilitator voice for the breakout room (private check-in track is
      currently inert — no TTS, no live decision logic)
- [ ] Merge `joint-session-audio` and `suture` into one
      voice-driven session (STT transcript replacing typed messages,
      facilitator TTS carrying replies to both employees)
- [ ] Real camera hardware test for video opt-in (parity logic proven, live
      camera revocation never exercised — this dev environment has no
      camera)
- [ ] `pitch_flattened` validated against genuine human deadpan/sarcastic
      speech (TTS can't fake real flat affect; needs a real mic, which this
      dev environment doesn't have)

## Phase 2 — Classifier trustworthiness

Shared with the rest of the pipeline via `apps/classifier/`, but Suture is
the primary consumer (wired into `suture`'s hard-cut path).

- [x] Per-class loss weighting tried (found: fixes recall, hurts precision —
      wrong lever for `v4`'s actual regression)
- [ ] Gentler weighting curve, or weight only the one starved class
      (`immediate_safety_risk`) instead of all five
- [ ] Human review of batches 4/5/6 (378 examples queued in
      `apps/classifier/data/review_page.html`, not yet judged)
- [ ] Bias audit (no protected-characteristic skew check has been done on
      any checkpoint yet)
- [ ] Real threshold tuning against an actual precision/recall curve (still
      the 0.9 default guess)
