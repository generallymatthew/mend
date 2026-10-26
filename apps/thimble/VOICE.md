# Thimble's voice (TTS)

## The three voices that exist in this codebase

There are only three TTS paths in `server.py`, no others. If someone says
"the voice sounds different," it's one of these three, not a fourth
option that got removed:

1. **macOS `say`, voice `Samantha`** (`synthesize_speech_say`) — the
   fallback, used only when OpenAI isn't configured or its call fails.
   Only works on macOS; Render's container is Linux, so this fallback is a
   silent no-op in production (returns `None`, not an error).
2. **OpenAI TTS, model `tts-1`, voice `alloy`** (`synthesize_speech_openai`)
   — the real default, used whenever `OPENAI_API_KEY` is set and the call
   succeeds. This is the voice Thimble has used for actual testing
   throughout its life, including October 12th.
3. **Deepgram Aura, `aura-asteria-en`** (`synthesize_speech_aura`) — a
   prototype, reachable only via `/api/speak/aura`, not wired into the
   default path. Tried once before and rejected as worse than OpenAI.

Same `say`/OpenAI pattern is duplicated in `apps/suture/server.py` and
`apps/post-session-app/server.py`.

## 2026-10-26 incident: "the voice sounds worse," root cause

Production's `OPENAI_API_KEY` had gone stale (401 "Incorrect API key
provided"). `synthesize_speech()` swallows that failure silently and
falls back to `say`/Samantha locally — so what sounded "different" and
"worse" wasn't a deliberate OpenAI voice at all, it was the Samantha
fallback, triggered by a dead key, with zero visible error anywhere.

This is the **second time** this exact failure mode has happened — see
`STATUS.md`'s 2026-10-?? entry documenting the same stale-key symptom
(there, voice went fully silent instead of falling back, since Render's
Linux container has no `say` binary at all — local dev falls back to
Samantha, production just gets `audio_url: null`).

Rotated the OpenAI key (set to expire in ~180 days from 2026-10-26 —
worth a calendar reminder before then) and updated `apps/thimble/.env`
and Render's Environment tab.

**First rotation didn't take on Render** — Render's own Shell confirmed
`OPENAI_API_KEY` held the correct new value, but OpenAI still rejected it
with "Incorrect API key provided," even though the exact same key string
worked fine from a direct local `curl` call. Root cause never fully
pinned down (most likely a stray character picked up when pasting into
Render's Environment field) — fixed by deleting the field's value
entirely and generating/pasting a second fresh key, which worked
immediately.

**Separately, `ANTHROPIC_API_KEY` had also gone stale on Render**
(independent of the OpenAI issue, discovered while debugging it — the
live UI was returning `server error calling Claude: 401 invalid
x-api-key`). Rotated that key too, same process (new key from
console.anthropic.com, updated `.env` + Render).

**Resolved and verified live, 2026-10-26**: both `/api/message` (Claude
replies) and `/api/speak` (OpenAI `alloy` TTS, confirmed by pulling a
real audio clip straight from `mend-mvp.onrender.com`) work correctly on
production.

## If this happens again

1. Check `GET /api/speak` (or call it directly with a test POST) on the
   live site first — `audio_url: null` means OpenAI failed and (on
   Render) there's no fallback at all.
2. Check Render's Logs tab for the real exception — `synthesize_speech_openai`
   logs the actual OpenAI error body, not just a generic failure.
3. Don't assume a "different-sounding voice" means code changed. The
   `tts-1`/`alloy` config hasn't changed since 2026-09-29 — a bad key
   silently degrading to Samantha (or to nothing, on Linux) is the much
   more likely explanation than a deliberate change.
