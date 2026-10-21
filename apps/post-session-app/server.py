#!/usr/bin/env python3
"""
Local prototype of the post-session follow-up: a private 1:1 with one
employee after a joint session ended, driven by
../facilitator-post-session-system-prompt.md.

Since this conversation normally starts with context from a joint session
that already happened (was anything escalated, and about whom), and this
harness doesn't chain to a real joint-session run, /api/start takes a
small scenario configuration instead of just firing blind. Text + voice
memo, text + spoken replies, same pattern as thimble and
suture. Single-user, in-memory, nothing persisted.

Run:
    pip install -r requirements.txt
    cp ../thimble/.env .env
    uvicorn server:app --reload --port 8422
"""
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent

# Shared local cost/usage logger (../usage_log.py) -- same sys.path trick as
# thimble/server.py and suture/server.py.
sys.path.insert(0, str(ROOT.parent.parent))
from usage_log import log_usage
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-post-session-system-prompt.md"
MODEL = "claude-sonnet-5"
AUDIO_DIR = Path(tempfile.mkdtemp(prefix="mend-post-audio-"))
VOICE = "Samantha"

load_dotenv(ROOT / ".env")

app = FastAPI()
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

# --- Rate limiting --------------------------------------------------------
# Same reasoning as ../thimble/server.py: a free/public pilot with no
# request limit on endpoints that call a paid LLM API is an open invitation
# to run up the bill. In-memory fixed-window limiter per client IP.
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
_rate_hits: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        hits = [t for t in _rate_hits.get(ip, []) if now - t < RATE_LIMIT_WINDOW]
        if len(hits) >= RATE_LIMIT_MAX:
            return JSONResponse({"error": "too many requests -- slow down and try again shortly"}, status_code=429)
        hits.append(now)
        _rate_hits[ip] = hits
    return await call_next(request)


def load_system_prompt() -> str:
    text = SYSTEM_PROMPT_FILE.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {SYSTEM_PROMPT_FILE}")
    return match.group(1)


SYSTEM_PROMPT = load_system_prompt()
conversation: list[dict] = []

_whisper_model = None
# Same latency fix as ../thimble/server.py, applied here too: "small.en"
# was noticeably slower than needed, and CTranslate2's own cpu_threads=0
# default measured slower on real hardware than just handing it every
# logical core (no accuracy cost, unlike the model-size trade). See
# thimble/README.md's "Why voice used to feel stuck on 'transcribing...'"
# for the actual numbers this is based on.
WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL", "tiny.en")
WHISPER_CPU_THREADS = int(os.environ.get("WHISPER_CPU_THREADS", str(os.cpu_count() or 4)))
# Same beam-size fix as ../thimble/server.py: greedy decoding (beam_size=1)
# measured ~30% faster than faster-whisper's own default (beam_size=5) on
# tiny.en, same transcript in that test -- see thimble/server.py's comment.
WHISPER_BEAM_SIZE = int(os.environ.get("WHISPER_BEAM_SIZE", "1"))


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            WHISPER_MODEL_NAME, device="cpu", compute_type="int8", cpu_threads=WHISPER_CPU_THREADS,
        )
    return _whisper_model


@app.on_event("startup")
async def preload_whisper():
    # Loads (and on first run, downloads) the model now, during startup,
    # instead of lazily on the first voice message -- same fix as
    # thimble/server.py, this app was missing it (this one still loaded
    # cold on whichever turn happened to be first).
    get_whisper()

FLOOR_CATEGORIES = {
    "harassment_discrimination": "harassment or discrimination based on a protected characteristic",
    "threats_violence": "threats or violence",
    "illegal_activity": "illegal activity",
    "immediate_safety_risk": "immediate safety risk",
}

# Below-floor patterns (product-spec.html's "Below the floor, still harmful"
# callout) -- never escalates to HR, unlike FLOOR_CATEGORIES above. Labels
# are for the kickoff note only; the facilitator prompt does the actual
# explaining.
COACHING_PATTERNS = {
    "coercive_control": "coercive control / gaslighting",
}


def strip_signal(reply_text: str) -> tuple[str, str | None]:
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    signal = match.group(1).strip() if match else None
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    return visible, signal


def synthesize_speech(text: str) -> str | None:
    if not text:
        return None
    file_id = uuid.uuid4().hex
    aiff_path = AUDIO_DIR / f"{file_id}.aiff"
    m4a_path = AUDIO_DIR / f"{file_id}.m4a"
    try:
        subprocess.run(["say", "-v", VOICE, "-o", str(aiff_path), text], check=True, capture_output=True)
        subprocess.run(
            ["afconvert", str(aiff_path), str(m4a_path), "-f", "m4af", "-d", "aac"],
            check=True, capture_output=True,
        )
    except Exception:
        return None
    finally:
        aiff_path.unlink(missing_ok=True)
    return f"/api/audio/{file_id}.m4a"


def facilitator_reply(synthesize: bool = False) -> dict:
    """synthesize=False by default -- see thimble/server.py's
    facilitator_reply docstring for the full reasoning. Callers get reply
    text back fast and fetch audio separately via POST /api/speak."""
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set -- see README)", "signal": None}
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
    log_usage("post-session-app", "anthropic", MODEL, "facilitator_reply",
              input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens)
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


@app.post("/api/start")
async def start(payload: dict):
    """payload: {escalation: 'none' | 'own_conduct' | 'other_party_conduct',
                 category: one of FLOOR_CATEGORIES keys (if escalation != 'none'),
                 coaching_role: 'shown' | 'experienced', optional,
                 coaching_pattern: one of COACHING_PATTERNS keys, optional,
                 context: free-text note on what happened, optional}"""
    if conversation:
        return {"reply": None, "signal": None}

    escalation = payload.get("escalation", "none")
    category = payload.get("category")
    coaching_role = payload.get("coaching_role")
    coaching_pattern = payload.get("coaching_pattern")
    context = payload.get("context", "").strip()

    if escalation == "none":
        escalation_note = "Nothing was escalated in the joint session that just ended."
    else:
        cat_label = FLOOR_CATEGORIES.get(category, category or "an unspecified category")
        whose = "this employee's own conduct" if escalation == "own_conduct" else "the other party's conduct (not this employee's)"
        escalation_note = f"Something was escalated in the joint session: {whose}, category: {cat_label}."

    # Below-floor pattern -- never HR-bound, unlike escalation_note above.
    # See product-spec.html's "Below the floor, still harmful" callout and
    # this prompt's "Below-floor pattern" section.
    if not coaching_role:
        coaching_note = ""
    else:
        pattern_label = COACHING_PATTERNS.get(coaching_pattern, coaching_pattern or "a harmful communication pattern")
        if coaching_role == "shown":
            coaching_note = f" The joint session also flagged that this employee showed signs of {pattern_label} toward the other party."
        else:
            coaching_note = f" The joint session also flagged that the other party showed signs of {pattern_label} toward this employee."

    context_note = f" Additional context on what happened: {context}" if context else ""

    kickoff = (
        f"(This employee just came out of a joint session with the other party. {escalation_note}"
        f"{coaching_note}{context_note} Begin the follow-up now, handling the escalation disclosure "
        f"first if applicable, then the below-floor pattern disclosure if applicable, per your "
        f"instructions.)"
    )
    conversation.append({"role": "user", "content": kickoff})
    return facilitator_reply()


@app.post("/api/message")
async def post_message(payload: dict):
    text = payload.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)
    conversation.append({"role": "user", "content": text})
    return facilitator_reply()


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
    docstring. Stateless, no coupling to `conversation`."""
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty text"}, status_code=400)
    return {"audio_url": synthesize_speech(text)}


@app.post("/api/reset")
async def reset():
    conversation.clear()
    for f in AUDIO_DIR.glob("*.m4a"):
        f.unlink(missing_ok=True)
    return {"ok": True}


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    path = AUDIO_DIR / filename
    if ".." in filename or not path.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="audio/mp4")


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
