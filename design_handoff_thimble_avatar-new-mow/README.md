# Handoff: Thimble avatar (live-call states)

## Overview
Thimble is the animated avatar shown during a Mend live voice session. It's a pink circle with a single cream mouth. It changes shape and moves to show six states: idle, listening, thinking, speaking, muted and paused. While listening or speaking, the outline "wobbles" into a rounded hexagon driven by audio level.

## About the design files
The files here are **design references**. `thimble-avatar.js` is a working, dependency-free reference implementation that shows the exact intended look and motion. Recreate it in the target codebase's environment (React, Vue, SwiftUI, Lottie/Rive, etc.) using its own patterns; don't drop it in unchanged unless it fits. `demo.html` runs it standalone: open it in a browser, switch states, and optionally drive it with your microphone.

## Fidelity
**High-fidelity.** Colors, timings, shape math and state behavior are final.

## Files
- `thimble-avatar.js` — reference implementation (`new ThimbleAvatar(host, {size, facets})`, `.setState()`, `.setLevel()`, `.destroy()`)
- `demo.html` — interactive demo of all states
- `reference/Listening Options.dc.html` — the design exploration canvas. **Turn 5 (top section) is the approved set**; the earlier turns are rejected explorations. It opens in a browser with `reference/support.js` beside it.

## Anatomy
- **Body**: a filled shape, `#F4849C`, sized to the container. The outline comes from a `clip-path: polygon()` with 120 points (see Shape below).
- **Mouth**: a cream (`#F5F0E8`) ellipse. It is horizontally centered at `left: 50%` and its bottom edge sits 24% above the body's bottom. Width and height are percentages of the avatar's size.
- No eyes, no ears, no outline strokes, no halos or radiating rings in any state.

## Shape: rounded-hexagon wobble
The outline blends between a circle and a **rounded-corner polygon**:
- `facets` = 6 (hexagon).
- Polygon radius at angle θ: `cos(seg/2) / cos(((θ − φ) mod seg) − seg/2)`, where `seg = 2π / N`.
- Corners are rounded with a box filter: average 13 samples across ±0.42·seg.
- Final radius: `r = 50% · (1 − depth · (1 − smoothed)) · jitter`, where
  - `depth = geo · min(1, 0.55 + level · 0.6)`
  - `jitter = 1 + 0.025 · geo · level · sin(N·θ + 5t)` (a small ripple on the sides)
- Rotation: `φ = t · spin + 0.15 · sin(1.7t)`. Spin is 0.35 rad/s, or 0.12 while thinking.
- `geo` (0 = circle, 1 = full polygon) eases toward its target at 12% per frame, so the shape always morphs smoothly and never snaps.

## States

| State | Color | Shape (`geo` target) | Breathing period | Face motion | Mouth (w × h, % of size) | Extra |
|---|---|---|---|---|---|---|
| idle | `#F4849C` | 0 (circle) | 4.5 s | none | 30 × 6 | — |
| listening | `#F4849C` | 1 while mic level > 0.08, otherwise 0 | 3 s | **slow continuous nod**, 2.6 s cycle, down by up to 4% of size | 34 × 4 | No head tilt |
| thinking | `#F4849C` | 0.6, slow spin | 3 s | **head tilt**: rotate −10° ± 2° (sin 1.2t), origin 50% 40% | 12 × 7, shifted to `left: 58%` ("hmm") | — |
| speaking | `#F4849C` | 0.8, driven by output level | 2.2 s | none | (26 + 6L) × (3 + 14L), opens with each syllable | — |
| muted | `#F4849C` at 50% opacity | 0 | none (still) | none | 26 × 3 | — |
| paused | `#A9A39A` (warm grey) | 0 | none (frozen) | none | 28 × 4 | — |

Notes:
- **One color** for every active state. Don't add per-state hues; only paused turns grey.
- **Breathing**: `scale = 1 + 0.0175 · (1 − cos(2πt / period))`, a peak of +3.5%.
- **Listening vs. silence**: the nod runs the whole time the avatar is listening. The wobble only appears while the user is actually making sound, so silence reads as calm and speech reads as "taking it in".

## Audio level input
`setLevel(0..1)`, called every frame:
- **Listening**: microphone RMS. The demo uses `min(1, rms × 6)` from an AnalyserNode with fftSize 1024.
- **Speaking**: RMS of the TTS audio as it plays, so the mouth and wobble follow the actual speech.
- Smoothing: 30% per frame for listening, 45% for speaking.

## Transitions
- Background color: 0.6 s ease. Opacity (muted): 0.4 s.
- Mouth size and position: 0.3 s, or 70 ms while speaking so it can track syllables. Horizontal shift (thinking): 0.5 s.
- Shape: eased per frame via `geo` (see above).

## Tokens
- Pink `#F4849C`
- Cream `#F5F0E8`
- Paused grey `#A9A39A`
- Call background (context) `#1B3A32`

## Accessibility
- Under `prefers-reduced-motion`, keep the state changes (mouth shape, color, opacity) but turn off breathing, wobble and nod.
- Show the state as text next to the avatar as well, e.g. the call's name tag: "listening", "thinking…", "speaking".
