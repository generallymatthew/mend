# Joint Session Architecture

Technical architecture for the digital-only joint session (Section 6 of `product-spec.html`): two employees, one facilitator, real-time trigger monitoring, three response tiers. This is a harder problem than intake (`facilitator-intake-system-prompt.md`) because the facilitator must control what one party's speech actually reaches the other party, in real time, not just decide what to say itself.

## Why this can't sit on a vendor avatar API alone

Tools like Tavus or HeyGen give you a managed pipeline: your text/audio in, avatar video out. That's fine for intake, where the facilitator only ever talks to one person and there's nothing to intercept between two humans. The joint session needs a buffer inserted *between the two humans' audio streams*, with the ability to drop content before it's delivered. That requires owning the transport layer, not renting a black-box one.

## Components

**Transport: self-hosted WebRTC SFU (LiveKit or Daily).** Each joint session is a room with three participants: employee A, employee B, and the facilitator (server-side agent, not a human). The server-side agent needs per-participant publish/subscribe control — the ability to route, delay, or drop any one participant's outbound track independently, and to pull a participant into a private sub-room without the other noticing anything beyond a neutral pause.

**Per-participant pipeline (both directions, both employees):**

```
mic audio → streaming STT → rolling transcript window
                                   │
                                   ├─→ fast real-time classifier (per-chunk, low latency)
                                   │        → gates the delay buffer (see below)
                                   │
                                   └─→ facilitator LLM (full context, both transcripts)
                                            → conversational moves, turn-taking, severity read
                                            → drives facilitator's own TTS + avatar output
```

**The delay buffer (broadcast-delay pattern).** Each employee's outbound audio, on its way to becoming the *other* employee's inbound audio, passes through a short ring buffer (order of ~1-2 seconds, tunable). The fast classifier scores each rolling chunk against the "active, escalating, imminent" bar before the buffered audio is released to the other participant. If it crosses that bar, the chunk is dropped before delivery — the receiving party never gets it. The speaker's own side and the facilitator's own copy of the transcript are unaffected; only what's delivered to the other person is cut. This is the only tier that needs hard real-time gating, and it needs a much higher, narrower threshold than the general floor triggers — a false positive here (cutting a normal exchange) costs real trust, per the spec's own "Real limits, not solved" callout.

**Severity read (LLM-driven, not just the fast classifier).** The fast per-chunk classifier only handles the hard real-time cut. "Rising tension" and "serious, not acute" don't need sub-second gating — they're read by the facilitator LLM working off the fuller rolling transcript and conversational context, same model that's running the session.

## Session state machine

```
ACTIVE
  ├─ facilitator senses rising tension (no trigger) ─→ PAUSED_CHECKIN(participant)
  │     PAUSED_CHECKIN: other participant sees a neutral "one moment" state, no content leak.
  │     Facilitator talks privately to the flagged participant over the same caucus channel
  │     used in intake. That participant decides: resume → ACTIVE, or end → WINDING_DOWN.
  │
  ├─ serious-not-acute content surfaces (floor-tripping, not happening live right now)
  │     ─→ WINDING_DOWN (silent — facilitator does not announce, accuse, or confront)
  │
  ├─ fast classifier fires hard cut (active/escalating/imminent) on a buffered chunk
  │     ─→ that chunk is dropped before delivery, session ─→ WINDING_DOWN
  │
  └─ ordinary end (nothing triggered) ─→ WINDING_DOWN

WINDING_DOWN
  Same routine-sounding close every time, regardless of which path led here — no observable
  difference between an ordinary end and an escalation, by design (Section 6).
  ─→ ENDED

ENDED
  Employees moved to fully separate rooms/sessions (their own individual follow-up,
  Section 8). Only now, apart, does the facilitator tell each person individually
  what was escalated and why, at category level, if anything was.
```

## No-persistence constraint

Everything above operates on ephemeral in-memory streams: STT transcript windows exist only long enough to feed the classifier and the facilitator LLM's context, then are discarded, not written to disk or a database. The one narrow exception is the tamper-evident trigger record (Section 7) — category and timestamp, not transcript content — which is the only thing allowed to outlive the live session.

## Suggested stack

- **Transport:** [LiveKit](https://github.com/livekit/livekit) (self-hosted, or LiveKit Cloud), driven by the [LiveKit Agents](https://docs.livekit.io/agents/) framework — Apache 2.0, Python/Node, built specifically for wiring STT/LLM/TTS into a room it already manages. Gives per-track subscribe/publish control and programmatic breakout routing, which a fully-managed avatar API won't expose.
- **STT:** open-source options exist but need real latency testing before committing:
  - [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-based Whisper, the backend most of the streaming wrappers below build on.
  - [whisper_streaming](https://github.com/wonyx/whisper_streaming) / [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) — streaming wrappers around faster-whisper with voice-activity detection built in.
  - Realistic budget: roughly 500-800ms latency for open-source streaming Whisper setups. That eats directly into the delay-buffer window for the hard-cut tier — may still need a hosted low-latency STT provider (e.g. Deepgram) for that leg specifically, and can afford open-source STT for the facilitator's own general transcript/context needs where sub-second latency matters less.
- **Fast classifier (hard-cut tier only):** [Detoxify](https://github.com/unitaryai/detoxify) (Unitary AI, Apache 2.0) is the closest existing open-source starting point — a BERT-based multi-head model already trained to flag threats, identity-based hate, and obscenity. Caveat: it's trained on Jigsaw's general internet-comment data, not workplace-conflict speech specifically, and the spec's own bar for this tier ("active, escalating, imminent," high precision over recall) is narrower than what Detoxify was tuned for. Treat it as a fine-tuning starting point, not a drop-in, and validate precision hard before trusting it to gate real-time delivery.
- **Facilitator brain:** the same LLM/system-prompt approach as intake, extended with joint-session-specific instructions — now written, see `facilitator-joint-session-system-prompt.md`.
- **TTS + avatar:** can reuse whatever avatar vendor is chosen for intake (e.g. Tavus), since the facilitator's own visual presence doesn't need the low-level transport control the human-to-human legs do. If going fully open-source instead: [MuseTalk](https://github.com/TMElyralab/MuseTalk) and the [TalkingHead](https://github.com/met4citizen/talkinghead) JS class both do real-time lip-synced avatar rendering and show up repeatedly in current self-hosted digital-human stacks, but expect meaningfully more integration work than a managed avatar API.

## Real limits, inherited from the spec

Irreducible latency (STT + classification + the cut itself) means the delay buffer shrinks the interception window, it never removes it. It also adds a small constant lag to the entire conversation, not just risky moments — the same tradeoff real broadcast delay accepts. Budget and tune the buffer length as a deliberate product decision, not an afterthought.

## Not yet designed

- The joint-session facilitator system prompt itself (turn-taking rules, the exact routine close script, how the facilitator narrates the session without ever confirming or denying an escalation live).
- Exact thresholds/prompts for the fast classifier vs. the LLM severity read.
- How the private breakout sub-room is implemented in LiveKit specifically (room composition vs. a second room with re-publish).
