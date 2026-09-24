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
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

from anthropic import Anthropic
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-intake-system-prompt.md"
MODEL = "claude-sonnet-5"
AUDIO_DIR = Path(tempfile.mkdtemp(prefix="mend-intake-audio-"))
VOICE = "Samantha"  # a built-in macOS voice; change freely, see `say -v ?` for options

app = FastAPI()
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None


def synthesize_speech(text: str) -> str | None:
    """Speaks `text` with macOS's built-in `say`, converts to .m4a (broad
    browser support), and returns a URL path to fetch it. Returns None
    (and lets the caller fall back to text-only) if `say`/`afconvert`
    aren't available -- e.g. running this on non-macOS."""
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
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    finally:
        aiff_path.unlink(missing_ok=True)
    return f"/api/audio/{file_id}.m4a"

_whisper_model = None


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("small.en", device="cpu", compute_type="int8")
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


def strip_signal(reply_text: str) -> tuple[str, str | None]:
    """Separate the visible reply from the <mend_signal> control block."""
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    signal = match.group(1).strip() if match else None
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    return visible, signal


def facilitator_reply() -> dict:
    """Assumes the latest turn just appended to `conversation` is the user's.
    On any failure, rolls that turn back off so conversation always ends on
    an assistant turn (or is empty) -- Anthropic's API rejects consecutive
    same-role turns, so a dangling unanswered user turn would break the
    next real call once a key is set."""
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set in this shell)", "signal": None}
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation,
        )
    except Exception as e:
        conversation.pop()
        return {"reply": f"(server error calling Claude: {e})", "signal": None}
    raw = "".join(block.text for block in response.content if block.type == "text")
    visible, signal = strip_signal(raw)
    conversation.append({"role": "assistant", "content": raw})
    return {"reply": visible, "signal": signal, "audio_url": synthesize_speech(visible)}


@app.post("/api/start")
async def start():
    if not conversation:
        conversation.append({
            "role": "user",
            "content": "(The employee just opened the app. Begin the conversation now with your opening line.)",
        })
        return facilitator_reply()
    return {"reply": None, "signal": None}


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
        segments, _ = get_whisper().transcribe(tmp.name)
        transcript = " ".join(seg.text.strip() for seg in segments).strip()
    if not transcript:
        return JSONResponse({"error": "couldn't transcribe audio"}, status_code=400)
    conversation.append({"role": "user", "content": transcript})
    result = facilitator_reply()
    result["transcript"] = transcript
    return result


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
