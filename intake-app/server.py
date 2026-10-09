#!/usr/bin/env python3
"""
Local prototype of the Mend intake conversation: text + voice-memo input,
text replies from the facilitator, driven by ../facilitator-intake-system-prompt.md.

Single-user, in-memory conversation state -- this is a prototype to test the
persona and flow, not a deployable multi-tenant service. No audio or text is
persisted to disk; conversation history lives only in this process's memory
and is lost on restart, consistent with the "nothing recorded" principle in
../product-spec.html.

Run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...   # your own key, set in your shell/.env, never pasted into chat
    uvicorn server:app --reload --port 8420
"""
import asyncio
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import websockets
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.oauth2.service_account import Credentials as GoogleCredentials
import gspread

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-intake-system-prompt.md"
MODEL = "claude-sonnet-5"
AUDIO_DIR = Path(tempfile.mkdtemp(prefix="mend-intake-audio-"))
VOICE = "Samantha"  # a built-in macOS voice, used only if OPENAI_API_KEY isn't set; see `say -v ?`

# Optional higher-quality voice via OpenAI TTS. Falls back to macOS `say`
# above if OPENAI_API_KEY isn't set, or if the OpenAI call fails.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_TTS_VOICE = os.environ.get("OPENAI_TTS_VOICE", "alloy")
# tts-1, not gpt-4o-mini-tts: measured ~2x faster for the same text (2.64s vs
# 4.97s in a real timing test) with this prototype's voice-latency complaint
# in mind. Less expressive/steerable than gpt-4o-mini-tts, a real tradeoff,
# not a strict improvement -- override with OPENAI_TTS_MODEL if the more
# natural voice matters more than speed for what you're testing.
OPENAI_TTS_MODEL = os.environ.get("OPENAI_TTS_MODEL", "tts-1")

# Optional streaming STT via Deepgram, replacing the local-Whisper VAD/partial
# pipeline (/api/voice/partial, the client's maybeSendPartial/getFinalTranscript)
# with a server-relayed WebSocket to Deepgram's own live transcription, which
# does endpointing (knowing when a turn ended) server-side instead of the
# client's own fixed-silence-timer VAD. Scoped in STATUS.md as the next real
# lever on voice latency: local Whisper's per-call overhead (1.7-3.4s on this
# machine, regardless of clip length) and the VAD silence-wait are the two
# biggest remaining serial stages in a voice turn, and both go away at once
# with this. Absent DEEPGRAM_API_KEY, /ws/voice refuses the connection and the
# frontend falls back to the existing local-Whisper path entirely -- this is
# additive, not a replacement, so a tester without a Deepgram key still gets
# a working (just slower) voice path.
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

# Prototype: Deepgram Aura TTS as a 3rd-party alternative to the OpenAI/`say`
# chain above, running in parallel for side-by-side testing -- not wired into
# the default synthesize_speech() path, so existing behavior is untouched.
# Reuses DEEPGRAM_API_KEY (already required for streaming STT), one fewer
# vendor key than the current OpenAI+macOS setup.
#
# aura-asteria-en (Aura-1), not aura-2-asteria-en -- measured live, same
# text, direct Deepgram calls: Aura-1 ~0.25s total (~0.2s to first byte),
# Aura-2 ~2.0s total (~0.3-0.4s to first byte) -- Aura-2's trailing
# generation time (not connection/TTFB) is the gap, confirmed live as
# "felt so slow after transcription" once this was wired into a real voice
# turn. Aura-1 is also ~8x faster than the existing OpenAI tts-1 path.
AURA_TTS_MODEL = os.environ.get("AURA_TTS_MODEL", "aura-asteria-en")

# Optional video-avatar mode (Tavus Conversational Video Interface). All four
# must be set -- see README.md's "Optional: video avatar" section for how to
# get them. Absent any of them, the app just runs text/voice-memo only, same
# as before.
TAVUS_API_KEY = os.environ.get("TAVUS_API_KEY")
TAVUS_PAL_ID = os.environ.get("TAVUS_PAL_ID")
LLM_SHIM_SECRET = os.environ.get("LLM_SHIM_SECRET")
VIDEO_ENABLED = bool(TAVUS_API_KEY and TAVUS_PAL_ID and LLM_SHIM_SECRET)

app = FastAPI()
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

# --- Rate limiting --------------------------------------------------------
# A free/public pilot with no request limit on endpoints that call a paid
# LLM API (or Tavus video minutes) is an open invitation to run up the bill.
# Simple in-memory fixed-window limiter per client IP -- no new dependency,
# consistent with every other app's in-memory-only state.
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
_rate_hits: dict[str, list[float]] = {}
# /api/voice/partial calls local Whisper only -- never a paid API, exactly
# what this limiter exists to protect -- and is deliberately chatty by
# design (fires every ~1-2s of new audio during live listening, see
# static/index.html's maybeSendPartial). Counting it against the same
# budget as /api/message's real Claude calls meant a single long voice turn
# could burn the whole window on its own free, local partial traffic and
# then get the actual paid reply call rejected with 429 right after --
# confirmed live: a turn's partials ate the budget, then /api/message came
# back 429 and Thimble never replied at all.
RATE_LIMIT_EXEMPT_PATHS = {
    "/api/voice/partial", "/api/survey", "/api/analytics",
    # Sentence-streamed TTS (see static/index.html's queueSentence) fires
    # one /api/speak call per sentence instead of one per reply, so a
    # multi-paragraph reply burns through the shared budget fast and gets
    # its later sentences 429'd -- the text stream is unaffected (separate
    # endpoint), so this surfaced as "the text looks right but the voice
    # just doesn't say the last paragraph," with no visible error, since a
    # failed /api/speak call is silently skipped (see queueSentence's catch).
    "/api/speak", "/api/speak/aura",
}
# /api/audio/<filename> just serves an mp3/m4a this process already
# generated and has sitting on disk -- zero marginal cost, same free-local
# reasoning as /api/voice/partial above, but it's a dynamic per-file path so
# the exact-match set above never matched it. Sentence-streamed TTS (see
# static/index.html's queueSentence) now fetches several of these per
# reply instead of one, so it hit the shared budget fast enough to get a
# real audio clip 429'd mid-reply -- confirmed live.
RATE_LIMIT_EXEMPT_PREFIXES = ("/api/audio/",)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    path = request.url.path
    exempt = path in RATE_LIMIT_EXEMPT_PATHS or path.startswith(RATE_LIMIT_EXEMPT_PREFIXES)
    if (path.startswith("/api/") or path.startswith("/chat/")) and not exempt:
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        hits = [t for t in _rate_hits.get(ip, []) if now - t < RATE_LIMIT_WINDOW]
        if len(hits) >= RATE_LIMIT_MAX:
            return JSONResponse({"error": "too many requests -- slow down and try again shortly"}, status_code=429)
        hits.append(now)
        _rate_hits[ip] = hits
    return await call_next(request)


# A fresh httpx.post() opens a new connection (full TCP+TLS handshake)
# every single call -- fine for one TTS call per reply, but now that
# sentence-streamed TTS fires several /api/speak calls per reply (see
# static/index.html's queueSentence), that handshake cost was paid again
# and again. Measured live: a 16-char and a 224-char call both took
# ~1.3-2s, barely different despite 14x the text -- almost entirely fixed
# per-request overhead, not synthesis time. A persistent client reuses the
# same keep-alive connection across calls instead.
#
# timeout=8, not 30: a real sentence-length call has never measured above
# ~3s even at its worst in this session's own timing logs, so a call still
# running past 8s is already hung, not just slow -- confirmed live, one
# call sat for the full 30s before falling back to macOS `say`, directly
# causing one of this turn's reported "took a long time" waits. Failing
# fast here means a stuck OpenAI call costs 8s and a `say` fallback instead
# of 30s and a `say` fallback -- same eventual outcome, much shorter stall.
_openai_http_client = httpx.Client(timeout=8)


def synthesize_speech_openai(text: str) -> str | None:
    """Speaks `text` with OpenAI's TTS, saves the returned mp3, and returns
    a URL path to fetch it. Returns None on any failure so the caller falls
    back to macOS `say`."""
    try:
        resp = _openai_http_client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": OPENAI_TTS_MODEL, "voice": OPENAI_TTS_VOICE, "input": text},
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        # Deployed audio_url:null with no explanation anywhere (confirmed
        # live on Render -- every /api/speak call came back audio_url:null,
        # no TTS, intro never played) was undiagnosable from the outside:
        # this swallowed the real reason (bad/missing key, quota, network)
        # and the macOS `say` fallback below is a silent no-op on Linux, so
        # the failure had zero visible trace anywhere. stdout-only, same as
        # the other timing diagnostics -- visible via Render's Logs tab.
        body = getattr(e, "response", None)
        print(f"[synthesize_speech_openai] failed: {e!r}" + (f" body={body.text[:300]!r}" if body is not None else ""), flush=True)
        return None
    file_id = uuid.uuid4().hex
    mp3_path = AUDIO_DIR / f"{file_id}.mp3"
    mp3_path.write_bytes(resp.content)
    return f"/api/audio/{file_id}.mp3"


def synthesize_speech_say(text: str) -> str | None:
    """Speaks `text` with macOS's built-in `say`, converts to .m4a (broad
    browser support), and returns a URL path to fetch it. Returns None
    (and lets the caller fall back to text-only) if `say`/`afconvert`
    aren't available -- e.g. running this on non-macOS."""
    file_id = uuid.uuid4().hex
    aiff_path = AUDIO_DIR / f"{file_id}.aiff"
    m4a_path = AUDIO_DIR / f"{file_id}.m4a"
    try:
        subprocess.run(["say", "-v", VOICE, "-o", str(aiff_path), text], check=True, capture_output=True)
        subprocess.run(
            ["afconvert", str(aiff_path), str(m4a_path), "-f", "m4af", "-d", "aac"],
            check=True, capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    finally:
        aiff_path.unlink(missing_ok=True)
    return f"/api/audio/{file_id}.m4a"


def synthesize_speech(text: str) -> str | None:
    if not text:
        return None
    if OPENAI_API_KEY:
        url = synthesize_speech_openai(text)
        if url:
            return url
    return synthesize_speech_say(text)


def synthesize_speech_aura(text: str) -> str | None:
    """Prototype: speaks `text` with Deepgram's Aura TTS, saves the returned
    mp3, and returns a URL path to fetch it. Returns None on any failure --
    not wired into synthesize_speech()'s fallback chain, so a failure here
    never touches the default voice path. Parallel path for comparison only,
    reached via /api/speak/aura."""
    if not DEEPGRAM_API_KEY:
        return None
    try:
        resp = _openai_http_client.post(
            "https://api.deepgram.com/v1/speak",
            params={"model": AURA_TTS_MODEL, "encoding": "mp3"},
            headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
            json={"text": text},
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        body = getattr(e, "response", None)
        print(f"[synthesize_speech_aura] failed: {e!r}" + (f" body={body.text[:300]!r}" if body is not None else ""), flush=True)
        return None
    file_id = uuid.uuid4().hex
    mp3_path = AUDIO_DIR / f"{file_id}.mp3"
    mp3_path.write_bytes(resp.content)
    return f"/api/audio/{file_id}.mp3"

_whisper_model = None
# "small.en"/"base.en" are noticeably slower on CPU than this needs to be for
# a live back-and-forth conversation, especially on weaker hardware (no
# GPU/Neural Engine acceleration path exists for faster-whisper on Intel
# Macs) -- "tiny.en" trades real accuracy for a much snappier turnaround.
# Measured on an Intel i5-8210Y (dual-core, no GPU): base.en ~5.2s, tiny.en
# ~2.2s for the same ~9.5s clip, real transcript quality held up in that
# test but this is a genuine tradeoff, not a free win -- override via .env
# if you want base/small/medium's accuracy back and don't mind the wait.
WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL", "tiny.en")
# CTranslate2's own default (cpu_threads=0, its own heuristic) measured
# meaningfully slower here than just handing it every logical core
# (base.en: 5.16s default vs 3.58s at cpu_threads=4) -- unlike the model-size
# tradeoff above, this one's free, no accuracy cost, just using the hardware
# that's actually available.
WHISPER_CPU_THREADS = int(os.environ.get("WHISPER_CPU_THREADS", str(os.cpu_count() or 4)))
# faster-whisper's own default (beam_size=5) explores 5 hypotheses per step;
# tiny.en is small enough that greedy decoding (beam_size=1) is a real
# turnaround win -- measured 2.9s avg vs 2.0s avg (beam=5 vs beam=1) on the
# same ~9.5s clip, same transcript both times in that test. Free to override
# if a harder clip shows quality issues at beam=1.
WHISPER_BEAM_SIZE = int(os.environ.get("WHISPER_BEAM_SIZE", "1"))


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            WHISPER_MODEL_NAME, device="cpu", compute_type="int8", cpu_threads=WHISPER_CPU_THREADS,
        )
    return _whisper_model


def transcribe_file(path: str) -> str:
    """Synchronous, CPU-bound -- always call via run_in_threadpool from a
    route handler, never directly, same reason as facilitator_reply() below."""
    t0 = time.monotonic()
    model_already_loaded = _whisper_model is not None
    model = get_whisper()
    t1 = time.monotonic()
    segments, info = model.transcribe(path, beam_size=WHISPER_BEAM_SIZE)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    t2 = time.monotonic()
    # Real timing, not a guess -- "transcription is slow" reports so far
    # have mostly turned out to be something else entirely (mislabeled
    # status text, a mid-request server restart). This settles it either
    # way next time: if transcribe_s is itself large relative to
    # audio_duration_s, that's genuinely this old CPU being the bottleneck;
    # if it's small, the slowness is happening somewhere else again.
    print(
        f"[transcribe_file] model_load_s={t1 - t0:.2f} (already_loaded={model_already_loaded}) "
        f"transcribe_s={t2 - t1:.2f} audio_duration_s={getattr(info, 'duration', None)} "
        f"beam_size={WHISPER_BEAM_SIZE} cpu_threads={WHISPER_CPU_THREADS} model={WHISPER_MODEL_NAME}"
    )
    return text


def load_system_prompt() -> str:
    text = SYSTEM_PROMPT_FILE.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {SYSTEM_PROMPT_FILE}")
    return match.group(1)


SYSTEM_PROMPT = load_system_prompt()
# Claude's own prompt caching needs the system prompt as a content block with
# an explicit cache_control breakpoint, not a plain string -- without this,
# every single turn reprocesses the whole ~8k-token system prompt from
# scratch before generating a single token of reply, which is the real gap
# behind "the response I get back from Claude directly is much faster than
# Thimble's" (reported live). A plain top-level system string is never
# cached, no matter how many turns reuse the identical text. With this, only
# the first turn in a conversation pays full cost; every later turn reuses
# the cached prefix (5min TTL, refreshed on each hit) and only has to
# process the new message on top of it.
SYSTEM_PROMPT_BLOCKS = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]

# In-memory conversation state -- a prototype, not a persistence layer.
# Keyed by session_id so independent conversations (e.g. several
# self-consistency "judge" calls fired concurrently for an ambiguous
# safety-floor case, see tests/voting_rule_prototype.py) don't share state
# and race each other. The real frontend (static/index.html) never sends a
# session_id, so every one of its requests lands on DEFAULT_SESSION_ID --
# this is additive, not a behavior change, for the single-user app itself.
# Each session's own conversation is still a single list a client can race
# against ITSELF (e.g. /api/reset mid-in-flight-reply, a known separate
# issue -- see STATUS.md); this only isolates DIFFERENT sessions from each
# other, it doesn't add per-session locking.
DEFAULT_SESSION_ID = "default"
conversations: dict[str, list[dict]] = {}


def get_conversation(session_id: str | None) -> list[dict]:
    return conversations.setdefault(session_id or DEFAULT_SESSION_ID, [])


def strip_signal(reply_text: str) -> tuple[str, str | None]:
    """Separate the visible reply from the <mend_signal> control block."""
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    signal = match.group(1).strip() if match else None
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    return visible, signal


def facilitator_reply(conversation: list[dict], synthesize: bool = False) -> dict:
    """Synchronous, blocking network call (client.messages.create) -- always
    call via run_in_threadpool from a route handler, never directly. uvicorn
    runs a single-threaded asyncio event loop by default; calling this
    straight from an `async def` handler blocks that whole event loop for
    the call's full duration, which means every other request -- including
    totally unrelated ones, from any user -- stalls or hangs until Anthropic
    responds. A slow or stuck Claude call used to be able to freeze the
    entire app, not just the one request waiting on it; confirmed live (a
    single request queued behind a stuck call long enough to make a plain
    `GET /` take 9s instead of its normal <0.2s).

    Takes the specific session's conversation list explicitly (from
    get_conversation(session_id)) rather than reading a module global, so
    independent sessions never touch each other's list -- see
    `conversations`'s own comment above for why that matters.

    Assumes the latest turn just appended to `conversation` is the user's.
    On any failure, rolls that turn back off so conversation always ends on
    an assistant turn (or is empty) -- Anthropic's API rejects consecutive
    same-role turns, so a dangling unanswered user turn would break the
    next real call once a key is set.

    `synthesize=False` by default: TTS alone measured ~12-14s for a typical
    reply (OpenAI call, scales with text length), on top of ~5-6s for the
    Claude call itself and, for voice input, ~6-8s of Whisper transcription
    -- all previously bundled into one blocking request the UI showed as a
    single misleading "transcribing..." label the whole time, real total
    ~30s. Callers now get reply text back fast and fetch audio separately
    via POST /api/speak, so the UI can show the reply ~15-20s sooner and
    label the remaining wait accurately. Pass synthesize=True to keep the
    old one-shot behavior (unused today, kept for e.g. a non-interactive
    caller that has no second round trip available)."""
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set in this shell)", "signal": None}
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            system=SYSTEM_PROMPT_BLOCKS,
            messages=conversation,
        )
    except Exception as e:
        conversation.pop()
        return {"reply": f"(server error calling Claude: {e})", "signal": None}
    raw = "".join(block.text for block in response.content if block.type == "text")
    if not raw:
        conversation.pop()
        return {
            "reply": f"(server error: no text in response, stop_reason={response.stop_reason} -- "
                     f"likely ran out of max_tokens mid-thinking; try again or raise the limit)",
            "signal": None,
        }
    visible, signal = strip_signal(raw)
    conversation.append({"role": "assistant", "content": raw})
    return {"reply": visible, "signal": signal, "audio_url": synthesize_speech(visible) if synthesize else None}


def parse_mend_signal(raw_signal: str | None) -> dict:
    """Parses the JSON object inside a reply's <mend_signal> block (already
    extracted by strip_signal). Tolerates a null/malformed one rather than
    raising -- a single off turn's signal failing to parse shouldn't crash
    the request that's just trying to read floor_triggered off it."""
    if not raw_signal:
        return {}
    try:
        return json.loads(raw_signal)
    except (json.JSONDecodeError, TypeError):
        return {}


def floor_met(signal: dict) -> bool:
    return bool(signal.get("floor_triggered")) or signal.get("screen_result") == "floor_met"


def floor_uncertain(signal: dict) -> bool:
    return signal.get("screen_result") == "uncertain"


# --- Screening-timing diagnostic log --------------------------------------
# Logs ONLY the <mend_signal> state fields per turn -- never the message
# text itself, matching this file's existing "no conversation text"
# boundary (see ANALYTICS_FILE's own comment above) even though real
# disclosures are exactly what this field screens. Exists to answer "which
# turn did screen_result actually change on" after a live report that a
# harassment disclosure wasn't flagged until several turns in.
SCREEN_LOG_FILE = ROOT / "screen_signal_log.jsonl"


def log_screen_signal(session_id: str, turn: int, signal: dict, note: str | None = None) -> None:
    record = {
        "ts": time.time(),
        "session_id": session_id,
        "turn": turn,
        "track": signal.get("track"),
        "phase": signal.get("phase"),
        "screen_result": signal.get("screen_result"),
        "floor_triggered": signal.get("floor_triggered"),
        "note": note,
    }
    with SCREEN_LOG_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")


def vote_flags(signal: dict) -> bool:
    """Whether one vote in the any-of-k ensemble counts as "this might be a
    problem." Deliberately broader than floor_met() alone -- an extra vote
    is judging the exact same genuinely-ambiguous input the primary call
    already couldn't confidently clear, so it will itself mostly land on
    "uncertain" too, not jump straight to a hard floor_met commitment.
    Requiring extra votes to hit floor_met before counting (an earlier,
    wrong version of this) meant the ensemble almost never fired for the
    exact cases it exists for -- confirmed directly: 10 clean single-turn
    samples of a known-ambiguous case came back ~1 floor_met, ~8 uncertain,
    0 confidently cleared, so demanding floor_met from EXTRA votes was
    requiring something the data shows barely happens even once, let alone
    twice. "uncertain" IS the signal worth amplifying here, consistent with
    the already-decided any-flag-counts design (see
    memory/project_safety_floor_voting_rule.md) -- this just applies that
    same philosophy to the real 3-way signal instead of a false binary."""
    return floor_met(signal) or floor_uncertain(signal)


# --- Self-consistency voting on the safety floor -------------------------
# Prototyped in tests/voting_rule_prototype.py against a real ambiguous
# case: majority vote across k independent samples CONVERGES on whichever
# answer already dominates, which actively suppresses a rare-but-real
# floor case as k grows -- the wrong direction for a safety check where a
# missed real disclosure is worse than a false alarm. An any-of-k (OR)
# rule does the opposite, amplifying the rare signal instead (measured
# there: 20% -> 48% caught at k=3, -> 80% at k=7). VOTE_K below is total
# votes, primary call included -- VOTE_K=3 means the primary plus 2 extra
# throwaway samples. See memory/project_safety_floor_voting_rule.md (or
# its MEMORY.md pointer) for the full writeup of why OR, not majority.
#
# Only fires when the primary call's own signal says `screen_result:
# "uncertain"` (see that field's own instructions in the mandatory-floor
# section) -- NOT merely "didn't already meet the floor." An earlier
# version of this gated on the latter, which fires on nearly every turn of
# an ordinary conversation (screen_result is null/cleared the vast
# majority of the time; floor_met turns are rare by design), running
# VOTE_K-1 extra Claude calls on turns that were never ambiguous in the
# first place -- caught live, not by design: a real run showed it firing
# on essentially every message. "uncertain" is the facilitator's own
# explicit, narrow signal that THIS specific turn sits in the genuine
# middle, which is the only case this feature exists for.
VOTE_K = int(os.environ.get("VOTE_K", "3"))


def _judge_floor_only(conversation_snapshot: list[dict]) -> dict:
    """One throwaway independent sample for the any-of-k vote below -- same
    model call facilitator_reply makes, but only the floor fields from its
    own <mend_signal> matter; the generated reply text is discarded, and
    `conversation_snapshot` is never mutated or shared with any real
    session's own conversation list (each call site passes its own copy).
    Any failure here just counts as "no flag," not an error -- a transient
    failure on one of several throwaway judge calls shouldn't distort or
    crash a feature whose whole point is tolerating disagreement across
    samples; see VOTE_K's own comment for why "no flag" is the safe default
    for a single failed vote rather than, say, retrying it."""
    if client is None:
        return {}
    try:
        response = client.messages.create(
            model=MODEL, max_tokens=8192, system=SYSTEM_PROMPT_BLOCKS, messages=conversation_snapshot,
        )
        raw = "".join(block.text for block in response.content if block.type == "text")
    except Exception as e:
        print(f"[vote] throwaway judge call failed (counts as no-flag): {e!r}", flush=True)
        return {}
    _, signal = strip_signal(raw)
    return parse_mend_signal(signal)


async def maybe_override_via_voting(conversation: list[dict], snapshot: list[dict], result: dict) -> dict:
    """Runs after the primary facilitator_reply() call for a turn. Only
    does anything when the primary's own signal says `screen_result:
    "uncertain"` -- see VOTE_K's own comment for why that's the gate, not
    "didn't already meet the floor." Every other turn (the vast majority)
    returns `result` unchanged with zero extra calls. When it does fire:
    VOTE_K-1 throwaway judge calls, genuinely concurrently (asyncio.gather
    over run_in_threadpool, not a sequential loop -- the whole point is
    this doesn't make the person wait k times as long), against `snapshot`
    (the conversation as it stood right before the primary call ran, so
    every vote -- primary included -- judges the identical input).

    If any extra vote flags it, the primary's already-generated reply is
    superseded: per the system prompt's own "never silently" rule, the
    person must still be told plainly, so this doesn't just flip the
    signal and leave the primary's ordinary-conversation reply standing --
    it discards that reply, appends a system note telling the facilitator
    plainly what was just determined, and gets a fresh reply, letting the
    facilitator's OWN escalation-disclosure instructions (already in the
    system prompt) produce the actual words, rather than hand-writing
    canned override text here. The synthetic note is prefixed with "(" the
    same way /api/start's own kickoff turn is, so /api/history's existing
    stripping logic already hides it from any reconstructed transcript --
    not a new convention, reusing one already in this file.

    Scope: only wired into /api/message today, not /api/message/stream --
    overriding a reply that's already mid-stream to the client is a harder
    problem (discarding partially-shown text) than this prototype needed
    to solve to answer the "does any-of-k work" question."""
    primary_signal = parse_mend_signal(result.get("signal"))
    if not floor_uncertain(primary_signal) or VOTE_K <= 1 or client is None:
        return result

    print(f"[vote] primary call marked screen_result=uncertain -- firing {VOTE_K - 1} extra votes", flush=True)
    extra_signals = await asyncio.gather(
        *[run_in_threadpool(_judge_floor_only, list(snapshot)) for _ in range(VOTE_K - 1)]
    )
    flagged = next((s for s in extra_signals if vote_flags(s)), None)
    if not flagged:
        print("[vote] no extra vote flagged it -- primary's reply stands", flush=True)
        return result

    category = flagged.get("floor_triggered") or "unspecified"
    print(
        f"[vote] OVERRIDE: primary call missed a floor hit that an extra vote caught "
        f"(category={category!r}, {1 + len(extra_signals)} total votes, {sum(1 for s in extra_signals if vote_flags(s))} flagged)",
        flush=True,
    )
    conversation.pop()  # discard the primary's own now-superseded reply
    conversation.append({
        "role": "user",
        "content": (
            "(System note, not from the person you're talking to: a safety-floor review "
            f"just determined this conversation meets the mandatory floor (category: "
            f"{category}). Your next turn must be the required floor-escalation "
            "disclosure, exactly as your own instructions describe it -- plainly, "
            "calmly, right now.)"
        ),
    })
    return await run_in_threadpool(facilitator_reply, conversation)


# --- Video-avatar mode (Tavus) -------------------------------------------
# The video call's transcript lives entirely in Tavus's own conversation, not
# in `conversation` above -- Tavus re-sends the running history to the shim
# below on every turn, so this process stays stateless for that path except
# for the one thing the UI still needs: the latest mend_signal, so the
# existing "ready for joint session" banner keeps working in video mode too.
video_conversation_id: str | None = None
latest_video_signal: str | None = None


@app.get("/api/video/enabled")
async def video_enabled():
    return {"enabled": VIDEO_ENABLED}


@app.get("/api/voice/config")
async def voice_config():
    """Tells the frontend whether /ws/voice (Deepgram streaming) is usable,
    so it can pick that path over the local-Whisper VAD/partial pipeline
    without hardcoding the choice client-side."""
    return {"deepgram": bool(DEEPGRAM_API_KEY)}


@app.post("/api/video/start")
async def video_start():
    global video_conversation_id, latest_video_signal
    if not VIDEO_ENABLED:
        return JSONResponse({"error": "video mode isn't configured -- see README.md"}, status_code=400)
    latest_video_signal = None
    async with httpx.AsyncClient() as http:
        try:
            resp = await http.post(
                "https://tavusapi.com/v2/conversations",
                headers={"x-api-key": TAVUS_API_KEY},
                json={"pal_id": TAVUS_PAL_ID, "conversation_name": "Mend intake"},
                timeout=30,
            )
        except httpx.HTTPError as e:
            return JSONResponse({"error": f"couldn't reach Tavus: {e}"}, status_code=502)
    if resp.status_code >= 400:
        return JSONResponse({"error": f"Tavus error {resp.status_code}: {resp.text}"}, status_code=502)
    data = resp.json()
    video_conversation_id = data.get("conversation_id")
    return {"conversation_url": data.get("conversation_url")}


@app.post("/api/video/end")
async def video_end():
    global video_conversation_id
    if video_conversation_id and TAVUS_API_KEY:
        async with httpx.AsyncClient() as http:
            try:
                await http.post(
                    f"https://tavusapi.com/v2/conversations/{video_conversation_id}/end",
                    headers={"x-api-key": TAVUS_API_KEY},
                    timeout=15,
                )
            except httpx.HTTPError:
                pass  # best-effort cleanup; the conversation will also time out on its own
        video_conversation_id = None
    return {"ok": True}


@app.get("/api/video/signal")
async def video_signal():
    return {"signal": latest_video_signal}


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def stream_facilitator_reply(messages: list[dict]):
    """OpenAI-chat-completions-shaped SSE stream for Tavus's custom_llm layer.
    Tavus speaks whatever text this yields, so the <mend_signal> control
    block must never reach it -- it's held back and parsed out instead,
    same job strip_signal() does for the text/voice-memo path above."""
    global latest_video_signal
    chat_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    def chunk(delta: dict, finish_reason: str | None = None) -> str:
        return _sse({
            "id": chat_id, "object": "chat.completion.chunk", "created": created,
            "model": MODEL, "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        })

    yield chunk({"role": "assistant"})

    if client is None:
        yield chunk({"content": "Video mode is on, but ANTHROPIC_API_KEY isn't set on the server."})
        yield chunk({}, finish_reason="stop")
        yield "data: [DONE]\n\n"
        return

    marker = "<mend_signal>"
    full_text = ""
    flushed_len = 0
    signal_started = False

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            system=SYSTEM_PROMPT_BLOCKS,
            messages=[m for m in messages if m.get("role") in ("user", "assistant")],
        ) as stream:
            for delta in stream.text_stream:
                full_text += delta
                if signal_started:
                    continue
                tag_at = full_text.find(marker, flushed_len)
                if tag_at != -1:
                    if tag_at > flushed_len:
                        yield chunk({"content": full_text[flushed_len:tag_at]})
                    flushed_len = tag_at
                    signal_started = True
                    continue
                safe_len = max(flushed_len, len(full_text) - (len(marker) - 1))
                if safe_len > flushed_len:
                    yield chunk({"content": full_text[flushed_len:safe_len]})
                    flushed_len = safe_len
            # The loop above always withholds the last len(marker)-1 chars
            # (in case they're the start of <mend_signal>) -- for a reply
            # that never actually contains the marker, that tail never
            # gets flushed by anything above once the stream ends, and was
            # silently lost: every such reply was missing its last ~12
            # characters, confirmed live as replies cutting off mid-word.
            if not signal_started and len(full_text) > flushed_len:
                yield chunk({"content": full_text[flushed_len:]})
                flushed_len = len(full_text)
    except Exception as e:
        yield chunk({"content": f"(server error calling Claude: {e})"})
        yield chunk({}, finish_reason="stop")
        yield "data: [DONE]\n\n"
        return

    match = re.search(r"<mend_signal>(.*?)</mend_signal>", full_text, re.S)
    latest_video_signal = match.group(1).strip() if match else None

    yield chunk({}, finish_reason="stop")
    yield "data: [DONE]\n\n"


@app.post("/chat/completions")
async def llm_chat_completions(request: Request):
    auth = request.headers.get("authorization", "")
    if not LLM_SHIM_SECRET or auth != f"Bearer {LLM_SHIM_SECRET}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await request.json()
    messages = payload.get("messages", [])
    return StreamingResponse(stream_facilitator_reply(messages), media_type="text/event-stream")


TEST_SHORT_INTRO = os.environ.get("TEST_SHORT_INTRO", "").lower() in ("1", "true", "yes")


@app.get("/api/history")
async def get_history(session_id: str | None = None):
    """`conversation` lives server-side and survives a reload; the
    transcript panel / chat view are pure client-side DOM state and don't.
    Without this, a reload partway through a session showed a blank,
    silent screen -- indistinguishable from the app just being broken,
    even though resuming instead of restarting is the intended behavior
    once /api/start no-ops on a non-empty conversation. Strips the
    synthetic kickoff turn (always a parenthesized stage direction, never
    something the employee/manager actually said) and each reply's
    <mend_signal> block -- only ever reconstructs what was already shown."""
    turns = []
    for msg in get_conversation(session_id):
        if msg["role"] == "user" and msg["content"].startswith("("):
            continue
        if msg["role"] == "assistant":
            visible, _ = strip_signal(msg["content"])
            if visible:
                turns.append({"role": "assistant", "text": visible})
        else:
            turns.append({"role": "user", "text": msg["content"]})
    return {"turns": turns}


@app.post("/api/start")
async def start(payload: dict = None):
    # No mode param anymore -- there's no frontend mode selector (Talk it
    # through / Rehearse / For managers) to read one from. Which track
    # applies (employee conflict vs. manager coaching) and whether someone
    # wants to skip straight to rehearsal are now both things the facilitator
    # itself figures out from the conversation, per its own system prompt's
    # "Which track applies" section -- not pre-declared here.
    payload = payload or {}
    conversation = get_conversation(payload.get("session_id"))
    if not conversation:
        kickoff = "(Someone just opened the app. Begin the conversation now with your opening line.)"
        if TEST_SHORT_INTRO:
            kickoff += (
                " (Testing note, not from the user: keep this opening to one short sentence, "
                "skip the usual disclosures, so this is fast to click through repeatedly.)"
            )
        conversation.append({"role": "user", "content": kickoff})
        return await run_in_threadpool(facilitator_reply, conversation)
    return {"reply": None, "signal": None}


@app.post("/api/message")
async def post_message(payload: dict):
    text = payload.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)
    session_id = payload.get("session_id") or DEFAULT_SESSION_ID
    conversation = get_conversation(session_id)
    conversation.append({"role": "user", "content": text})
    turn = sum(1 for m in conversation if m["role"] == "user")
    snapshot = list(conversation)  # before the primary call appends its own reply -- see maybe_override_via_voting
    result = await run_in_threadpool(facilitator_reply, conversation)
    log_screen_signal(session_id, turn, parse_mend_signal(result.get("signal")))
    final = await maybe_override_via_voting(conversation, snapshot, result)
    if final is not result:
        log_screen_signal(session_id, turn, parse_mend_signal(final.get("signal")), note="overridden_by_vote")
    return final


def stream_message_reply(conversation: list[dict], session_id: str, turn: int):
    """SSE stream of the facilitator's reply for /api/message/stream -- same
    job as facilitator_reply() above, but yields visible text incrementally
    instead of returning it all at once, so the frontend can show Thimble's
    reply appearing as it's generated instead of the whole ~5-6s Claude call
    passing in silence (reported live: "transcription was fine but the
    thinking took 6sec"). A sync generator passed straight to
    StreamingResponse, same as stream_facilitator_reply() below already does
    for the Tavus path -- Starlette iterates it via its own threadpool
    wrapper, so this doesn't block the event loop the way a raw blocking
    call from an async def handler would (see facilitator_reply's own
    docstring for why that distinction matters here).

    Reuses stream_facilitator_reply's own marker-withholding logic (buffer
    until certain text isn't the start of <mend_signal>) rather than
    reinventing it, just shaped as {"text": ...} chunks for this app's own
    frontend instead of the OpenAI chunk format Tavus needs."""
    if client is None:
        conversation.pop()
        yield _sse({"text": "(server error: ANTHROPIC_API_KEY is not set in this shell)"})
        yield _sse({"done": True, "signal": None})
        return
    marker = "<mend_signal>"
    full_text = ""
    flushed_len = 0
    signal_started = False
    t0 = time.time()
    t_first_token = None
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            system=SYSTEM_PROMPT_BLOCKS,
            messages=conversation,
        ) as stream:
            for delta in stream.text_stream:
                if t_first_token is None:
                    t_first_token = time.time()
                full_text += delta
                if signal_started:
                    continue
                tag_at = full_text.find(marker, flushed_len)
                if tag_at != -1:
                    if tag_at > flushed_len:
                        yield _sse({"text": full_text[flushed_len:tag_at]})
                    flushed_len = tag_at
                    signal_started = True
                    continue
                safe_len = max(flushed_len, len(full_text) - (len(marker) - 1))
                if safe_len > flushed_len:
                    yield _sse({"text": full_text[flushed_len:safe_len]})
                    flushed_len = safe_len
            # The loop above always withholds the last len(marker)-1 chars
            # (in case they're the start of <mend_signal>) -- for a reply
            # that never actually contains the marker, that tail never
            # gets flushed by anything above once the stream ends, and was
            # silently lost: every such reply was missing its last ~12
            # characters, confirmed live as replies cutting off mid-word
            # ("messages keep getting cut off... thimble's thought is not
            # finished").
            if not signal_started and len(full_text) > flushed_len:
                yield _sse({"text": full_text[flushed_len:]})
                flushed_len = len(full_text)
            # Diagnostic only (reported live: "still took a long time" after
            # prompt caching was added) -- logs to stdout, not sent to the
            # client, so it's visible via `preview_logs`/the terminal without
            # changing anything the frontend sees. Confirms or rules out a
            # cache miss as the actual cause of a given slow turn.
            final = stream.get_final_message()
            u = final.usage
            print(
                f"[timing] /api/message/stream: first_token={t_first_token - t0:.2f}s "
                f"total={time.time() - t0:.2f}s cache_read={getattr(u, 'cache_read_input_tokens', None)} "
                f"cache_creation={getattr(u, 'cache_creation_input_tokens', None)} input={u.input_tokens}",
                flush=True,
            )
    except Exception as e:
        conversation.pop()
        yield _sse({"error": f"server error calling Claude: {e}"})
        return
    if not full_text:
        conversation.pop()
        yield _sse({"error": "server error: no text in response"})
        return
    # visible text is already fully delivered via the "text" deltas above
    # (the marker-withholding loop never streams the <mend_signal> block
    # itself) -- only the parsed signal still needs to reach the frontend.
    _, signal = strip_signal(full_text)
    conversation.append({"role": "assistant", "content": full_text})
    log_screen_signal(session_id, turn, parse_mend_signal(signal))
    yield _sse({"done": True, "signal": signal})


@app.post("/api/message/stream")
async def post_message_stream(payload: dict):
    text = payload.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)
    session_id = payload.get("session_id") or DEFAULT_SESSION_ID
    conversation = get_conversation(session_id)
    conversation.append({"role": "user", "content": text})
    turn = sum(1 for m in conversation if m["role"] == "user")
    return StreamingResponse(stream_message_reply(conversation, session_id, turn), media_type="text/event-stream")


DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?encoding=linear16&channels=1&model=nova-2"
    "&interim_results=true&smart_format=true"
    # endpointing=500 (Deepgram's own default-ish quick setting) reported
    # live as "really fast but it keeps interrupting me" -- the same
    # failure shape the local-Whisper VAD path already hit and fixed once
    # (see VAD_SILENCE_MS's own history: 500ms cut people off mid-sentence
    # repeatedly before landing on 1400ms as the real fix, not just a
    # tuning tweak). Matching that same tuned value here instead of
    # re-discovering it from scratch -- Deepgram's silence-to-speech_final
    # window is the direct equivalent of VAD_SILENCE_MS, same tradeoff.
    #
    # utterance_end_ms was written up as a rare backstop for when
    # speech_final doesn't fire on a clean word boundary -- turned out to
    # be backwards. Checked directly against the real API (a short reply
    # and a long one, both watched frame by frame over the real websocket):
    # speech_final never came back true in either case, not once. This
    # backstop is the thing actually ending every single turn, not a rare
    # fallback -- which meant real turn-end latency was gated on THIS
    # number the whole time, not endpointing, and reported live as "doesn't
    # seem to know I've finished talking" was really this 2500ms silence
    # requirement on every turn, felt worse on short replies since there's
    # less talking beforehand to offset the same wait. Lowered to 1300ms,
    # same real-silence-after-speech tradeoff VAD_SILENCE_MS already went
    # through and landed near (1100ms) -- if this starts cutting people off
    # mid-sentence, that's the signal to raise it back up, not evidence the
    # whole approach is wrong.
    "&endpointing=1400&utterance_end_ms=1300&vad_events=true"
)


@app.websocket("/ws/voice")
async def ws_voice(websocket: WebSocket):
    """Relays the browser's raw PCM16 mic stream straight through to
    Deepgram's live streaming API and forwards Deepgram's transcript/
    utterance events back as JSON -- replaces the local-Whisper
    partial-transcription round trip (/api/voice/partial) and the client's
    own fixed-silence VAD entirely when this path is active: Deepgram does
    endpointing (knowing when a turn ended) server-side from the real audio
    stream, not from a client-side timer guessing at silence. See
    DEEPGRAM_API_KEY's own comment for why this is additive, not a
    replacement, for anyone running without a Deepgram key.

    Client protocol: connects with ?sample_rate=<hz> (the browser mic's own
    native rate -- resampling client-side isn't needed, Deepgram takes any
    rate you tell it), then sends raw Int16 PCM frames as binary WebSocket
    messages (little-endian, mono) for the duration of one listening
    session, and a close frame to end it. Server sends back
    {"type": "transcript", "text": ..., "is_final": bool, "speech_final": bool}
    per Deepgram result, and {"type": "utterance_end"} when Deepgram's own
    VAD detects the turn ended with no further speech."""
    await websocket.accept()
    if not DEEPGRAM_API_KEY:
        await websocket.close(code=1008, reason="Deepgram isn't configured on this server")
        return
    sample_rate = websocket.query_params.get("sample_rate", "16000")
    url = f"{DEEPGRAM_URL}&sample_rate={sample_rate}"

    try:
        async with websockets.connect(url, additional_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}) as dg:
            async def browser_to_deepgram():
                try:
                    while True:
                        chunk = await websocket.receive_bytes()
                        await dg.send(chunk)
                except WebSocketDisconnect:
                    pass
                finally:
                    try:
                        await dg.send(json.dumps({"type": "CloseStream"}))
                    except websockets.exceptions.ConnectionClosed:
                        pass

            async def deepgram_to_browser():
                async for raw in dg:
                    msg = json.loads(raw)
                    msg_type = msg.get("type")
                    if msg_type == "Results":
                        alt = msg.get("channel", {}).get("alternatives", [{}])[0]
                        text = alt.get("transcript", "")
                        if not text:
                            continue
                        await websocket.send_json({
                            "type": "transcript",
                            "text": text,
                            "is_final": bool(msg.get("is_final")),
                            "speech_final": bool(msg.get("speech_final")),
                        })
                    elif msg_type == "UtteranceEnd":
                        await websocket.send_json({"type": "utterance_end"})

            await asyncio.gather(browser_to_deepgram(), deepgram_to_browser())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except (RuntimeError, WebSocketDisconnect):
            pass  # already closed -- different Starlette versions raise different things here


@app.post("/api/voice/partial")
async def post_voice_partial(file: UploadFile):
    """Live preview only, called repeatedly while the employee is still
    talking (see static/index.html's partial-capture loop) -- re-transcribes
    whatever's been said so far in the current turn so the transcript panel
    can show real words appearing during speech, not just after it stops.
    Never touches `conversation`; a bad or empty result here just means no
    preview update, never an error the employee sees."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        tmp.write(await file.read())
        tmp.flush()
        try:
            transcript = await run_in_threadpool(transcribe_file, tmp.name)
        except Exception:
            # Same "a bad result here just means no preview update" contract
            # the docstring above already promises -- transcribe_file can
            # raise (not just return empty), e.g. av.error.EOFError on a
            # clip too short/empty to even decode (confirmed live from a
            # push-to-talk quick-tap), and this call site had nothing
            # catching that, so the exception reached the client as an
            # unhandled 500 instead of just skipping this one preview.
            return {"partial": ""}
    return {"partial": transcript}


@app.post("/api/voice")
async def post_voice(file: UploadFile):
    """Transcription only -- does NOT touch `conversation` or call the
    facilitator. Used to bundle both in one request, with the frontend's
    status line stuck on "transcribing..." for the whole thing -- real
    transcription is a couple seconds on this hardware, but the Claude
    call after it can run much longer, so "transcribing" was silently
    mislabeling most of the actual wait. The caller now gets the
    transcript back fast and POSTs it to /api/message itself (the exact
    same path text input already takes), so the UI can show "you said
    this" immediately and then accurately switch to "thinking..." for the
    part that's actually thinking. Mirrors the same split already done
    for TTS (see facilitator_reply's docstring)."""
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=True) as tmp:
        body = await file.read()
        tmp.write(body)
        tmp.flush()
        print(f"[post_voice] uploaded clip: {len(body)} bytes")
        try:
            transcript = await run_in_threadpool(transcribe_file, tmp.name)
        except Exception:
            # transcribe_file can raise, not just return empty -- a clip too
            # short/empty to even decode (av.error.EOFError) reached the
            # client as an unhandled 500/HTML error page instead of the
            # JSON error shape getFinalTranscript() already expects and
            # handles gracefully (see its own "couldn't transcribe audio"
            # path below) -- confirmed live from a push-to-talk quick-tap,
            # reported as "Unexpected token 'I', 'Internal S'... is not
            # valid JSON" (the frontend trying to JSON.parse that HTML page).
            transcript = ""
    if not transcript:
        return JSONResponse({"error": "couldn't transcribe audio"}, status_code=400)
    return {"transcript": transcript}


@app.post("/api/speak")
async def speak(payload: dict):
    """Second round trip for a reply's audio -- see facilitator_reply's
    docstring for why this is split out. Stateless: just synthesizes
    whatever text is handed to it, no coupling to `conversation`."""
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty text"}, status_code=400)
    t0 = time.time()
    url = await run_in_threadpool(synthesize_speech, text)
    # Diagnostic only (reported live: still slow after prompt caching and
    # sentence-streamed TTS both landed) -- stdout only, see stream_message_reply's
    # own timing log for the matching Claude-side half of this.
    print(f"[timing] /api/speak: {time.time() - t0:.2f}s for {len(text)} chars: {text[:60]!r}", flush=True)
    return {"audio_url": url}


@app.post("/api/speak/aura")
async def speak_aura(payload: dict):
    """Prototype twin of /api/speak, routed to Deepgram Aura instead of the
    default OpenAI/`say` chain -- for side-by-side comparison. Existing
    callers of /api/speak are unaffected."""
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty text"}, status_code=400)
    t0 = time.time()
    url = await run_in_threadpool(synthesize_speech_aura, text)
    print(f"[timing] /api/speak/aura: {time.time() - t0:.2f}s for {len(text)} chars: {text[:60]!r}", flush=True)
    return {"audio_url": url}


@app.post("/api/reset")
async def reset(payload: dict = None):
    payload = payload or {}
    get_conversation(payload.get("session_id")).clear()
    # Audio files aren't namespaced per session (random uuid filenames,
    # see synthesize_speech) -- clearing them here is harmless for the real
    # single-session frontend (the only caller that ever uses synthesize
    # audio), but would be a real cross-session hazard for anyone resetting
    # one session while another's audio is still in flight. Not a concern
    # for the text-only concurrent-session use case this was built for
    # (self-consistency voting never calls synthesize=True), but worth
    # fixing properly before audio is ever used across concurrent sessions.
    for pattern in ("*.m4a", "*.mp3"):
        for f in AUDIO_DIR.glob(pattern):
            f.unlink(missing_ok=True)
    return {"ok": True}


# Post-session feedback -- deliberately the one thing this app persists
# outside process memory. Everything else here follows "nothing is
# recorded" (see the module docstring and the header's own privacy pill):
# conversation content/audio only ever live in memory. A survey response
# isn't session content, it's the tester volunteering feedback about the
# product through a separate page (static/survey.html), with no
# conversation text attached -- the whole point is to actually be able to
# read it back later. The real durable store is a Google Sheet (Render's
# own container disk is ephemeral -- see the git history around this
# comment for the stdout-logging stopgap that predated this); SURVEY_FILE
# and the stdout print below are now just a local-dev/fallback safety net
# for whenever Sheets access isn't configured or a single write fails.
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
SURVEY_FILE = ROOT / "survey_responses.jsonl"
VALID_ISSUES = {"voice", "audio", "captions", "other", "none"}
# Every single-choice survey question (everything except overall_rating, nps,
# issues, and the two free-text fields) validates the same way: null or one
# of a fixed option set. Declared once here instead of a hand-written if/else
# per field, both in this file and in static/survey.html's own radio names.
SURVEY_RADIO_FIELDS = {
    "felt_fair": {"yes", "somewhat", "no"},
    "felt_safe": {"yes", "somewhat", "no"},
    "trusted_privacy": {"yes", "somewhat", "no"},
    "sided": {"neutral", "me", "other", "clear"},
    "understood_situation": {"well", "mostly", "poorly"},
    "changed_approach": {"clarified", "changed_mind", "no_difference"},
    "readiness": {"more", "same", "less"},
    "comparison": {"better", "same", "worse", "na"},
    "would_reuse": {"yes", "maybe", "no"},
    "emotional_shift": {"calmer", "same", "worse"},
    "thimble_relation": {"tool", "presence", "comforting_presence", "person"},
    "thimble_comforting": {"yes", "somewhat", "no"},
    "granted_authority": {"yes", "somewhat", "no", "not_sure"},
}

_sheet = None
_sheet_init_failed = False


def get_survey_sheet():
    """Returns the first worksheet of GOOGLE_SHEET_ID, authenticated via a
    service account whose JSON key lives in GOOGLE_SERVICE_ACCOUNT_JSON (the
    whole key file's contents, not a path -- Render's env vars and this
    app's own .env are the only places this credential should ever live,
    never committed to the repo or pasted into chat). Returns None, logging
    why, if either env var is unset or auth fails -- a survey submission
    still succeeds either way, falling back to SURVEY_FILE/stdout below.

    One-time setup, done once in Google Cloud Console / Sheets, not here:
    enable the Sheets API, create a service account, generate a JSON key,
    create (or reuse) a Sheet with a header row matching the columns
    appended below, and share that Sheet with the service account's own
    client_email as an Editor. Then set GOOGLE_SHEET_ID (the id segment of
    the Sheet's URL) and GOOGLE_SERVICE_ACCOUNT_JSON (the raw key file
    contents, as a single-line value) as env vars, both locally (.env) and
    in Render's dashboard.
    """
    global _sheet, _sheet_init_failed
    if _sheet is not None or _sheet_init_failed:
        return _sheet
    if not GOOGLE_SHEET_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        _sheet_init_failed = True
        return None
    try:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = GoogleCredentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        _sheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID).sheet1
    except Exception as e:
        print(f"[survey] Google Sheets auth/open failed, falling back to local log: {e}", flush=True)
        _sheet_init_failed = True
        return None
    return _sheet


@app.post("/api/survey")
async def submit_survey(request: Request):
    data = await request.json()
    rating = data.get("overall_rating")
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return JSONResponse({"error": "overall_rating must be an integer 1-5"}, status_code=400)
    radios = {}
    for field, valid_values in SURVEY_RADIO_FIELDS.items():
        value = data.get(field)
        if value not in valid_values and value is not None:
            return JSONResponse({"error": f"invalid {field} value"}, status_code=400)
        radios[field] = value
    nps = data.get("nps")
    if nps is not None and (not isinstance(nps, int) or not (0 <= nps <= 10)):
        return JSONResponse({"error": "nps must be an integer 0-10"}, status_code=400)
    ai_comfort_general = data.get("ai_comfort_general")
    if ai_comfort_general is not None and (not isinstance(ai_comfort_general, int) or not (1 <= ai_comfort_general <= 5)):
        return JSONResponse({"error": "ai_comfort_general must be an integer 1-5"}, status_code=400)
    issues = data.get("issues") or []
    if not isinstance(issues, list) or not all(i in VALID_ISSUES for i in issues):
        return JSONResponse({"error": "invalid issues value"}, status_code=400)
    # Generous caps, not unbounded -- this is open free text from an
    # unauthenticated page.
    standout_moment = str(data.get("standout_moment") or "")[:2000]
    trust_improvement = str(data.get("trust_improvement") or "")[:2000]
    authority_source = str(data.get("authority_source") or "")[:2000]
    comments = str(data.get("comments") or "")[:4000]
    record = {
        "ts": time.time(),
        "overall_rating": rating,
        **radios,
        "nps": nps,
        "ai_comfort_general": ai_comfort_general,
        "issues": issues,
        "standout_moment": standout_moment,
        "trust_improvement": trust_improvement,
        "authority_source": authority_source,
        "comments": comments,
    }
    sheet = get_survey_sheet()
    if sheet is not None:
        try:
            # gspread's append_row is a blocking HTTP call -- same
            # threadpool-offload reasoning as every other blocking call in
            # this file (see transcribe_file/facilitator_reply), so it
            # doesn't freeze the single-threaded event loop for every other
            # concurrent request while it runs. Column order here must match
            # the Sheet's own header row -- see README.md's survey setup
            # section.
            await run_in_threadpool(
                sheet.append_row,
                [
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(record["ts"])) + " UTC",
                    rating,
                    radios["felt_fair"] or "",
                    radios["felt_safe"] or "",
                    radios["trusted_privacy"] or "",
                    radios["sided"] or "",
                    radios["understood_situation"] or "",
                    radios["changed_approach"] or "",
                    radios["readiness"] or "",
                    radios["comparison"] or "",
                    radios["would_reuse"] or "",
                    nps if nps is not None else "",
                    radios["emotional_shift"] or "",
                    radios["thimble_relation"] or "",
                    radios["thimble_comforting"] or "",
                    radios["granted_authority"] or "",
                    authority_source,
                    ai_comfort_general if ai_comfort_general is not None else "",
                    standout_moment,
                    trust_improvement,
                    ", ".join(issues),
                    comments,
                ],
            )
        except Exception as e:
            # A real write failure (quota, revoked share, transient network
            # error) shouldn't lose the response -- it still lands in the
            # fallback log below.
            print(f"[survey] Sheets append failed, response saved to local log only: {e}", flush=True)
    with SURVEY_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[survey] {json.dumps(record)}", flush=True)
    return {"ok": True}


# Usage analytics -- same "nothing is recorded" boundary as everything else
# in this file: no conversation text, no audio, no IP tied to a record.
# session_id is a random uuid4 the client mints fresh per page load (never
# derived from anything identifying), so this answers "how many turns did a
# session have", "text or voice", "did anyone interrupt" in aggregate without
# ever carrying what was actually said.
ANALYTICS_FILE = ROOT / "analytics_events.jsonl"
VALID_ANALYTICS_EVENTS = {"session_start", "turn", "interrupt", "session_end"}
VALID_ANALYTICS_MODES = {"text", "voice"}
_events_sheet = None
_events_sheet_init_failed = False


def get_events_sheet():
    """Same spreadsheet as get_survey_sheet, a separate 'events' worksheet
    so the two don't interleave. Created on first use if the sheet doesn't
    already have one. Returns None, logging why, on any auth/access failure
    -- an analytics event still succeeds either way, falling back to
    ANALYTICS_FILE/stdout below, same contract as the survey path."""
    global _events_sheet, _events_sheet_init_failed
    if _events_sheet is not None or _events_sheet_init_failed:
        return _events_sheet
    if not GOOGLE_SHEET_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        _events_sheet_init_failed = True
        return None
    try:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = GoogleCredentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        spreadsheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID)
        try:
            _events_sheet = spreadsheet.worksheet("events")
        except gspread.WorksheetNotFound:
            _events_sheet = spreadsheet.add_worksheet(title="events", rows=1000, cols=6)
            _events_sheet.append_row(["timestamp_utc", "session_id", "event", "mode", "turn"])
    except Exception as e:
        print(f"[analytics] Google Sheets auth/open failed, falling back to local log: {e}", flush=True)
        _events_sheet_init_failed = True
        return None
    return _events_sheet


@app.post("/api/analytics")
async def submit_analytics_event(request: Request):
    data = await request.json()
    event = data.get("event")
    if event not in VALID_ANALYTICS_EVENTS:
        return JSONResponse({"error": "invalid event"}, status_code=400)
    session_id = str(data.get("session_id") or "")[:64]
    if not session_id:
        return JSONResponse({"error": "missing session_id"}, status_code=400)
    mode = data.get("mode")
    if mode is not None and mode not in VALID_ANALYTICS_MODES:
        return JSONResponse({"error": "invalid mode"}, status_code=400)
    turn = data.get("turn")
    if turn is not None and not isinstance(turn, int):
        return JSONResponse({"error": "invalid turn"}, status_code=400)
    record = {"ts": time.time(), "session_id": session_id, "event": event, "mode": mode, "turn": turn}
    sheet = get_events_sheet()
    if sheet is not None:
        try:
            await run_in_threadpool(
                sheet.append_row,
                [
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(record["ts"])) + " UTC",
                    session_id,
                    event,
                    mode or "",
                    turn if turn is not None else "",
                ],
            )
        except Exception as e:
            print(f"[analytics] Sheets append failed, event saved to local log only: {e}", flush=True)
    with ANALYTICS_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return {"ok": True}


@app.get("/survey")
async def survey_page():
    return FileResponse(ROOT / "static" / "survey.html")


@app.get("/voice-live")
async def voice_live_page():
    # Served at a root-level path, not under /static, for the same reason
    # index() below is: static/voice-transcript-live.html's own apiPath()
    # derives BASE_PATH from location.pathname, which only resolves to the
    # real API routes (e.g. /api/start, not /static/voice-live/api/start)
    # when the page itself loads from a root-level path like this one.
    return FileResponse(ROOT / "static" / "voice-transcript-live.html")


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    path = AUDIO_DIR / filename
    if ".." in filename or not path.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    media_type = "audio/mpeg" if path.suffix == ".mp3" else "audio/mp4"
    return FileResponse(path, media_type=media_type)


@app.on_event("startup")
async def preload_whisper():
    # Loads (and on first run, downloads) the model now, during startup, so
    # the first voice message of a session isn't the one that eats this cost
    # -- that's what made live mode feel stuck on "transcribing..." before.
    get_whisper()


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


# No explicit Cache-Control on index.html/static/* meant browsers were
# applying their own heuristic freshness lifetime and sometimes serving a
# stale cached copy on an ordinary reload without even revalidating with
# the server -- confirmed live more than once this session (a page-load
# behavior fix silently not taking effect; a browser tab caught directly
# serving JS from before a fix had landed, a hard refresh needed to see
# it). During active development this app changes every few minutes, so
# unlike a stable production asset, no caching at all is the right default
# here -- a reload should always reflect whatever's actually on disk.
@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store"
    return response
