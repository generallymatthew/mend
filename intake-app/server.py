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
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import httpx
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

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


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/") or request.url.path.startswith("/chat/"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        hits = [t for t in _rate_hits.get(ip, []) if now - t < RATE_LIMIT_WINDOW]
        if len(hits) >= RATE_LIMIT_MAX:
            return JSONResponse({"error": "too many requests -- slow down and try again shortly"}, status_code=429)
        hits.append(now)
        _rate_hits[ip] = hits
    return await call_next(request)


def synthesize_speech_openai(text: str) -> str | None:
    """Speaks `text` with OpenAI's TTS, saves the returned mp3, and returns
    a URL path to fetch it. Returns None on any failure so the caller falls
    back to macOS `say`."""
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": OPENAI_TTS_MODEL, "voice": OPENAI_TTS_VOICE, "input": text},
            timeout=30,
        )
        resp.raise_for_status()
    except httpx.HTTPError:
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


def load_system_prompt() -> str:
    text = SYSTEM_PROMPT_FILE.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {SYSTEM_PROMPT_FILE}")
    return match.group(1)


SYSTEM_PROMPT = load_system_prompt()

# In-memory conversation state -- a prototype, not a persistence layer.
conversation: list[dict] = []
session_mode = "talk"  # "talk" (normal side conversation) or "practice" (rehearsal only, see /api/start)


def strip_signal(reply_text: str) -> tuple[str, str | None]:
    """Separate the visible reply from the <mend_signal> control block."""
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    signal = match.group(1).strip() if match else None
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    return visible, signal


def facilitator_reply(synthesize: bool = False) -> dict:
    """Assumes the latest turn just appended to `conversation` is the user's.
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
            system=SYSTEM_PROMPT,
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
            system=SYSTEM_PROMPT,
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


@app.post("/api/start")
async def start(payload: dict = None):
    global session_mode
    if not conversation:
        session_mode = (payload or {}).get("mode", "talk")
        if session_mode == "practice":
            kickoff = (
                "(The employee just opened the app in Practice mode: they want to rehearse a hard "
                "conversation with you playing the other person, before actually having it for real. "
                "This is not the standard intake side conversation -- skip the phase-by-phase intake flow "
                "entirely. Begin now by briefly asking who they need to talk to and what the "
                "situation is, just enough for you to play a realistic version of that person, then "
                "move into the rehearsal itself per your own instructions on practicing the "
                "conversation (roleplay). Stay in coaching/rehearsal mode for this whole session "
                "unless the employee explicitly says they also want to open a real case or request a "
                "joint session, in which case shift into the normal intake flow. Keep floor screening "
                "active as always.)"
            )
        else:
            kickoff = "(The employee just opened the app. Begin the conversation now with your opening line.)"
        if TEST_SHORT_INTRO:
            kickoff += (
                " (Testing note, not from the employee: keep this opening to one short sentence, "
                "skip the usual disclosures, so this is fast to click through repeatedly.)"
            )
        conversation.append({"role": "user", "content": kickoff})
        return facilitator_reply()
    return {"reply": None, "signal": None}


@app.post("/api/message")
async def post_message(payload: dict):
    text = payload.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)
    conversation.append({"role": "user", "content": text})
    return facilitator_reply()


@app.post("/api/voice/partial")
async def post_voice_partial(file: UploadFile):
    """Live preview only, called repeatedly while the employee is still
    talking (see static/index.html's partial-capture loop) -- re-transcribes
    whatever's been said so far in the current turn so the UI can show real
    words appearing during speech, not just after it stops. Never touches
    `conversation`; a bad or empty result here just means no preview update,
    never an error the employee sees."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        tmp.write(await file.read())
        tmp.flush()
        segments, _ = get_whisper().transcribe(tmp.name, beam_size=WHISPER_BEAM_SIZE)
        transcript = " ".join(seg.text.strip() for seg in segments).strip()
    return {"partial": transcript}


@app.post("/api/voice")
async def post_voice(file: UploadFile):
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=True) as tmp:
        tmp.write(await file.read())
        tmp.flush()
        segments, _ = get_whisper().transcribe(tmp.name, beam_size=WHISPER_BEAM_SIZE)
        transcript = " ".join(seg.text.strip() for seg in segments).strip()
    if not transcript:
        return JSONResponse({"error": "couldn't transcribe audio"}, status_code=400)
    conversation.append({"role": "user", "content": transcript})
    result = facilitator_reply()
    result["transcript"] = transcript
    return result


@app.post("/api/speak")
async def speak(payload: dict):
    """Second round trip for a reply's audio -- see facilitator_reply's
    docstring for why this is split out. Stateless: just synthesizes
    whatever text is handed to it, no coupling to `conversation`."""
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty text"}, status_code=400)
    return {"audio_url": synthesize_speech(text)}


@app.post("/api/reset")
async def reset():
    global session_mode
    conversation.clear()
    session_mode = "talk"
    for pattern in ("*.m4a", "*.mp3"):
        for f in AUDIO_DIR.glob(pattern):
            f.unlink(missing_ok=True)
    return {"ok": True}


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
