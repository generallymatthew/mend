# Handoff: Simple Agent Presence (circle + mouth)

## Overview
Visual presence for an AI conflict-resolution agent shown in video calls, where it mediates between two people. The agent is a solid green circle with a white oval mouth. It has five states: **Listening, Thinking, Speaking, Empathizing, Calming**. Each state is shown only through mouth size and position, circle scale, motion tempo and a slight shift in the green.

## About the Design Files
`Simple Agent.dc.html` is a **design reference built in HTML**. It is a prototype of the intended look and motion, not production code. Rebuild it in the target codebase with its own framework and patterns (React, SwiftUI, Canvas, Lottie/Rive, etc.). If there's no environment yet, choose what suits the project; a single SVG or canvas component driven by `requestAnimationFrame` is enough. The file opens directly in a browser and needs `support.js` next to it.

## Fidelity
**High-fidelity.** Final colours, geometry, and motion parameters are listed below. Match them exactly.

## Geometry (200 × 200 unit viewBox; scale uniformly)
- **Circle:** centre (100, 100), base radius **80**, radius = 80 × `s` (scale). The circle's cy = 100 + dy × 0.3.
- **Mouth:** a true, symmetric **ellipse** (no curves or asymmetry).
  - Centre x = 100 + `dx`
  - Centre y = 100 + `dy` + 30 × `s` (sits in the lower part of the circle, where a mouth would be on a face)
  - rx = `w` (half-width), ry = `o` / 2 (`o` = full height)
- Mouth fill `#f3f1e8`. No strokes anywhere.

## States: target parameters per frame
`t` = seconds since start. Parameters: `w` mouth half-width, `o` mouth height, `dx`/`dy` offsets, `s` circle scale.

| State | w | o | dx | dy | s | Circle colour |
|---|---|---|---|---|---|---|
| Listening | 28 | 6 | ±7 toward active speaker | nod: `max(0,sin(1.6t))^8 × max(0,sin(0.4t)) × 4` | `1 + 0.012·sin(1.1t)` | `#3f6b5e` |
| Thinking | 12 | 6 | `12·sin(0.8t)` | −5 | 0.97 | `#365c52` |
| Speaking | `28 − 6v` | `6 + 24v` | 0 | 0 | `1 + 0.01v` | `#3f6b5e` |
| Empathizing | 22 | 12 | 0 | `2.5·sin(1.3t)` | 1.025 | `#4e765c` |
| Calming | `24 + 8b` | 6 | 0 | 0 | `0.98 + 0.07b` | `#5c8676` |

- **Speaking `v` (0–1):** in production, use the agent's real TTS output amplitude, normalised and smoothed. The prototype fakes it: `v = |sin(8.5t)| × |sin(3.1t+1)| × (0.55 + 0.45·sin(1.3t)) × (sin(0.7t) > −0.6 ? 1 : 0)`.
- **Calming breath `b` (0–1), 10 s cycle:** inhale 0–4 s `b = (1 − cos(π·p/4))/2`; exhale 4–10 s `b = (1 + cos(π·(p−4)/6))/2`, with `p = t mod 10`.
- **Listening dx:** +7 or −7 toward whoever is currently speaking (the prototype switches on `sin(0.25t) > 0`). Wire it to real speaker detection: left participant = −7, right = +7.

## Smoothing / transitions
Each frame, every param eases toward its target: `cur += (target − cur) × min(1, dt × k)`.
- k = **14** in Speaking (responsive mouth), **4** in all other states.
- Colour eases with k = **2** (per RGB channel).
- Cap dt at 0.05 s. State changes don't need extra tweening; the easing handles them.

## Design tokens
- Circle greens: Listening/Speaking `#3f6b5e`, Thinking `#365c52`, Empathizing `#4e765c`, Calming `#5c8676`
- Mouth: `#f3f1e8`
- Prototype page only (not part of the agent): background `#f1f0ea`, panels `#e9e8e0`, text `#23302b`, font Instrument Sans

## State management
- `state`: one of the five, set by the agent/mediation logic.
- `activeSpeaker`: left | right | none (drives the Listening dx).
- `speechAmplitude`: 0–1 from TTS (drives Speaking).
- The prototype's page (state buttons, auto-cycle every 6 s, five-card grid) is for demonstration only.

## Files
- `Simple Agent.dc.html`: the prototype. Motion logic is in `target()` and `apply()` in the script block.
- `support.js`: runtime needed to open the prototype in a browser.
