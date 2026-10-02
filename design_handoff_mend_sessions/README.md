# Handoff: Mend — Intake, Joint Session & Thimble Avatar

## Overview
Mend is a private, AI-assisted workplace conflict resolution app. The AI persona is **Thimble** (named for the sewing tool that protects you while you mend). This package covers:
1. **Intake screen** — one person talks to Thimble in one of three modes (Talk it through / Rehearse / For managers), in a call-style layout.
2. **Joint session** — Thimble mediates between two employees, including private side conversations ("caucus") where one person can't hear.
3. **Thimble avatar** — a faceless pink shape with four animated states: listening, thinking, talking, empathizing.

## About the Design Files
The `.dc.html` files are **design references built in HTML** — prototypes that show intended look and behaviour, not production code. Recreate them in the target codebase's environment (React, React Native, SwiftUI, etc.) using its established patterns. If there is no codebase yet, pick the most suitable framework (React + CSS/Tailwind works well; the avatar is plain DOM + CSS transforms + requestAnimationFrame).

To view them, open any `.dc.html` in a browser from this folder (they load `support.js` and `mend-brand-kit/` relatively). Logic lives in the `<script data-dc-script>` block at the bottom of each file; `renderVals()` is the equivalent of a React render's derived values.

## Fidelity
**High-fidelity.** Colors, type, spacing, copy and animation behaviour are final-intent. AI responses and conversation content are placeholders.

## Brand principles that drive the design
- **No eyes, no camera.** Thimble is here to listen and advise, not to see or judge you. There is no camera option; the user is represented by a voice-only circle.
- **No recording iconography.** Never use red/pink blinking dots or "REC" patterns. Privacy is signalled with a lock icon: "Private. Nothing is recorded."
- **Impartiality.** In joint sessions Thimble stays centred; participant tiles are equal size and symmetric. Thimble leans toward whoever is speaking.
- **Only talking reaches past the shape.** Listening, thinking and empathizing animations stay inside the avatar's silhouette. Talking ripples outward (it's Thimble's voice).
- **Two circles.** The logo is two overlapping circles. User = honey circle, Thimble = pink circle; the honey blend in "empathizing" echoes the logo overlap.

## Design Tokens
| Token | Value | Use |
|---|---|---|
| Pink | `#F3829A` | Thimble, logo, "Leave session"/"End live" |
| Evergreen | `#17372E` | Ink, primary buttons, active controls |
| Deep evergreen | `#0F2620` | Dark overlay pills (at `B3` = 70% alpha) |
| Honey | `#E9B949` | User circle, private/caucus banner & outlines |
| Oat | `#F6F1E7` | Page background, mouth colour, user tile bg |
| Sage | `#A9C4B4` | Other participant's circle (joint session; not in core palette) |
| White | `#FFFFFF` | Video stage, inputs; frame at `#FFFFFF80` |

Borders: `#17372E1A` (10%), `#17372E14` (8%), `#17372E26` (15%) for inputs, `#17372E33` inset for inactive controls.

- **Font:** Manrope 400/500/600/700. Labels/eyebrows: JetBrains Mono 11–12px, uppercase, letter-spacing .12em, opacity .6.
- **Type:** brand 18/700; mode title 16/700 lh1.3; mode sub 13.5/400 lh1.4; subtitles clamp(17px,1.6vw,21px)/500 lh1.45; chat bubbles 14.5 lh1.55; tile labels 12/600.
- **Radii:** frame 24px, stage 18px, mode cards 14px, tiles 14px, pills/inputs/buttons 999px, bubbles 14px (4px on the speaker's corner).
- **Spacing:** page padding 24px / clamp(16px,3vw,44px); section gap 16–20px; frame padding 12px; overlay insets 14–16px.
- **Control buttons:** 52×52 circles. Active = evergreen bg + oat icon. Inactive = white bg + evergreen icon + inset 1px `#17372E33`. Primary pill buttons 52px tall, padding 0 22px, 15/700.

## Screens

### 1. Intake (`Mend Intake.dc.html`)
**Layout (top → bottom), max-width 1400px:**
- **Header:** Mend mark (pink SVG, 20px tall) + "Mend" 18/700. Right: pill `#17372E0D` bg, lock icon + "Private. Nothing is recorded." 13/500.
- **Mode cards:** grid `repeat(auto-fit,minmax(220px,1fr))`, gap 10. Selected card: evergreen bg, oat text. Unselected: white, 1px `#17372E1F`.
  - Talk it through — "Tell Thimble what happened, in your own words"
  - Rehearse — "Practice the hard conversation before you have it"
  - For managers — "Get advice on a hard conversation with someone you manage" (one manager getting advice about a direct report, not a joint session)
- **Call frame** (`#FFFFFF80`, border, radius 24, min-height calc(100vh − 200px)):
  - **Stage** (white, radius 18, flex:1, avatar centred with 110px bottom padding):
    - Top-left (live only): "Live · mm:ss" pill, deep evergreen 70%, mono 12px. No dot.
    - Top-right (live only, prototype/demo aid): state picker chips. Omit in production.
    - Bottom-left: label pill "Thimble" (700) + state ("Listening…", "Thinking", "Talking", "Empathizing").
    - Subtitles: plain evergreen text, no background, centred, max 720px, left 16 / right = tile width + 32, bottom 60px.
    - Bottom-right user tile: width clamp(150px,18vw,260px), 16:10, oat bg, 1px border, no shadow. Honey avatar (64px) centred, "You" 12/600 at bottom-left, crossed mic next to it when muted.
  - Optional transcript panel (hidden by default; toggled): 360px, oat bg, "THIS SESSION ONLY" + "Start over", chat bubbles (You = evergreen right, Thimble = white left).
  - **Bottom bar:** Voice / Text segmented toggle (left) + controls (right): Mute, Subtitles, Transcript, Go live / End live (evergreen → pink while live). No text input in voice mode.

**Voice / Text toggle:** segmented pill, `#17372E0D` track, 4px padding; active tab evergreen bg + oat text, 13/700, padding 8px 16px. Choosing Text replaces the call frame with the chat interface (and ends a live call if one is running). The conversation log is shared between both views.

**Text mode (chat interface):** inside the same frame, a white panel (radius 18):
- Header (padding 12×16, bottom border): small Thimble avatar (44px, same animated states), "Thimble" 15/700, status 12.5px at .6 opacity ("Here to listen. Private, nothing is recorded." / "Thinking…" / "Replying…"). Right: Voice/Text toggle + "Start over" outline pill.
- Thread: centred column, max-width 720px, gap 14. Thimble bubbles oat `#F6F1E7`, left, 4px bottom-left corner; user bubbles evergreen with oat text, right, 4px bottom-right corner. 15.5px / lh 1.6, padding 12×16, radius 16, max-width 80%. Sender label above each (11.5/600, .55 opacity). While Thimble is thinking, show a typing bubble with three 7px dots (`dot` keyframe, .2s stagger).
- Composer (top border): max-width 720, white, 1px `#17372E26`, radius 18; 2-row textarea + 44px evergreen "Send" (radius 12). Hint below: "Enter to send · Shift+Enter for a new line" 12px .55 opacity. Enter sends, Shift+Enter adds a new line. Thread auto-scrolls to the bottom.

**Mode welcome copy:** see the `MODES` object in the file. Keep the "Talk it through" message verbatim (client-provided). It explains the HR-escalation exceptions (harassment/discrimination on a protected characteristic, threats/violence, illegal activity, immediate safety risk).

### 2. Joint session (`Mend Joint Session.dc.html`)
- Header: logo + "Mend" + "Joint session with Sam" (opacity .6); privacy pill.
- Stage: Thimble centred (size min(innerHeight−520, innerWidth×.28, 360), min 140). Subtitles **directly under Thimble** with speaker line above ("Sam", "You", "Thimble · to Sam", "Thimble · to both"). Bottom row grid `clamp(150px,20vw,260px) 1fr clamp(150px,20vw,260px)`: Sam tile (sage) left, You tile (honey) right, empty middle. Subtitles must never sit between the two people.
- Bottom bar: "Type to the room…" input + Send; Mute, Subtitles, Ask for a pause; "Leave session" (pink).
- **Caucus (private) states:**
  - Thimble with Sam (from your view): honey banner top-centre "Thimble is talking privately with Sam. You can't hear this." Thimble fades to 35%, no subtitles, your tile at 40% opacity with lock + "Can't hear right now". Thimble label "With Sam".
  - Thimble with you: banner "Private with you. Sam can't hear this." Sam's tile dimmed with the lock note; your tile gets a honey border; stage gets inset 3px honey outline + `#E9B9490F` tint.
- Prototype loops a scripted exchange (`SCENES` array). Pause button freezes it. Sending text shows it as your subtitle → Thimble thinks → asks Sam. Replace with real session logic.

### 3. Thimble states reference (`Thimble States.dc.html`)
The four states side by side with descriptions. Use as the animation spec.

## Thimble avatar spec (`function avatar(st, s, refs, col, label, dir)`)
Pink circle (`col`), oat mouth, no eyes. `s` = size in px. The body layer has `overflow:hidden`; everything except talking ripples stays inside it.

| State | Body | Mouth | Extra |
|---|---|---|---|
| **Listening** | Egg shape `50% 50% 47% 53% / 58% 58% 42% 42%`, leans `rotate(-10deg) translate(2%,1%)` toward the speaker (`dir` ±1 mirrors it) | **Closed**: pill .11s × .028s at top 60% | Live wobble (below), nods |
| **Thinking** | `blob` keyframes 4s: border-radius morph + scale .92–.95 + ±3° | Replaced by **3 pulsing dots** (.045s, gap .04s, `dot` 1.2s staggered .2s) | — |
| **Talking** | Round, `bob` .8s | **Oval** (`border-radius:50%`) .19s × .12s, `talk` .7s scaleY .3→1 alternate | Two ripples outward (`ripple` 1.6s, .8s offset), the only thing outside the shape |
| **Empathizing** | Softer bottom `…/62% 62% 38% 38%`, `nod` 2.8s (translateY 6→11%, scaleY .88→.8, no widening) | Soft smile: bottom border arc .22s × .1s, stroke .028s | Honey circle (80% size, at −38%/30%) blends in with `mix-blend-mode:multiply` at .85 opacity |

Transitions between states: border-radius .6s, mouth .35–.45s, lean .7s `cubic-bezier(.3,1.4,.5,1)`.

**Active listening (per-frame, requestAnimationFrame):**
- Mic level L (0–1): RMS of `AnalyserNode` time-domain data ×6, smoothed (attack .5, release .12). Only with mic permission during live; otherwise simulated during listening only.
- Wobble: border-radius corners oscillate with sines (periods 240/330/290ms), amplitude `5 + L×16`%. The side facing the speaker flattens by `L×14`% (ear turning in).
- Tilt: extra `rotate(−L×7°·dir) translateX(L×3%·dir)`.
- Nods: a double nod (620ms, `|sin(2πp)|×(1−.45p)` → translateY 5%, scaleY −5%) when the speaker pauses (L drops below .15) and every 1.7s of continuous speech.

**User circle:** same function with `col = #E9B949`, 64px. Talking state while the user's level > .12 (hysteresis off < .06), listening otherwise.

**Keyframes** (copy from the `<style>` in any file): `breathe`, `ripple`, `blob`, `bob`, `nod`, `talk`, `dot`, `blink`.

## State (intake)
`ui` (voice | text), `mode` (talk | practice | manager), `draft`, `thinking`, `log` per mode, `stage` (text-mode avatar state), `live`, `callState`, `auto` (demo cycling), `secs`, `muted`, `captions` (default **on**), `transcript` (default **off**), `youTalk`.

## Assets
- `mend-brand-kit/logo/` — Mend mark SVGs (pink/evergreen/oat) and app icons.
- `mend-brand-kit/colors.css`, `colors.json`, `README.md` — brand tokens and usage.
- Icons are inline SVG strokes (mic, subtitles, transcript, pause, lock), 2–2.2px stroke, round caps. Swap for the codebase's icon set if equivalent.

## Files
- `Mend Intake.dc.html` — intake / 1:1 call screen, with Voice / Text (chat) toggle
- `Mend Joint Session.dc.html` — joint mediation + caucus
- `Thimble States.dc.html` — avatar state reference
- `support.js` — runtime needed only to open the prototypes
- `mend-brand-kit/` — logo and tokens
