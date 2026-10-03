# Mend: Symmetric Video Parity Feature Concept

Captured from an earlier exploratory code dump (`archive/needs-review/misc/gemini-code-*`), not yet designed against this codebase's actual stack (that dump was React + a WebSocket signaling server + Jest; `joint-session-app`/`joint-session-audio` are vanilla JS + FastAPI + LiveKit). This doc keeps the *idea*; none of the original code is meant to be reused as-is.

## The idea

Extends the existing "Double Opt-In Shielding" video rule (see [11_PRODUCT_ARCHITECTURE_AND_STRATEGY_BLUEPRINT.md](11_PRODUCT_ARCHITECTURE_AND_STRATEGY_BLUEPRINT.md), Section 3) from a one-time intake choice to a **live, continuous guarantee during the session itself**: if either participant's camera drops at any point — a deliberate toggle-off, a hardware failure, a bad connection — both participants are symmetrically and immediately dropped to voice + neutral avatar together. Neither side is ever left on camera alone while the other has gone dark, and neither side is told *why* the room changed mode (just that it did).

Why this matters beyond the original double opt-in: double opt-in only governs how the room *starts*. Without a live parity rule, a participant who agreed to video at the start could end up exposed on camera mid-session after their counterpart silently drops to avatar — the asymmetry (and the inference "they turned their camera off because of something I said") undermines the same psychological-safety goal the opt-in was designed to protect in the first place.

## Mechanics (concept, not final design)

1. **Signaling**: whichever transport the real-time layer ends up using (the dump assumed a generic WebSocket room; `joint-session-audio/` already uses LiveKit, which has its own room/participant event model that should be used instead if this gets built) broadcasts a single event — "a participant's camera went away" — to every participant in the room.
2. **Symmetric teardown**: every client reacts to that broadcast by force-switching its own local video track off and rendering the neutral avatar, regardless of which participant triggered it.
3. **Neutral framing**: the UI shows a plain, non-blaming toast ("Session switched to Voice & Avatar mode.") to everyone — never "Alex turned off their camera."
4. **Facilitator non-intervention**: the facilitator model is never told which transport mode is active and must never comment on cameras, lighting, or the mode switch — it stays focused entirely on the conversation itself. (This instruction already exists, standalone, in the captured dump's system-prompt fragment.)

## Open questions before building this for real

- Whether LiveKit's own participant/track-event hooks are a better fit than a bespoke signaling server (likely yes, given `joint-session-audio/` already depends on LiveKit).
- Whether a dropped camera should be able to re-enable itself automatically once restored, or require both participants to explicitly re-opt-in (probably the latter, to avoid one side being surprised back onto camera).
- Where this sits relative to `joint-session-app`'s still-unmerged audio transport (see `joint-session-architecture.md`) — this is a video-layer concern on top of a session that doesn't have a real-time video layer integrated yet.
