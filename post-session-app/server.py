#!/usr/bin/env python3
"""
Local prototype of the post-session follow-up: a private 1:1 with one
employee after a joint session ended, driven by
../facilitator-post-session-system-prompt.md.

Since this conversation normally starts with context from a joint session
that already happened (was anything escalated, and about whom), and this
harness doesn't chain to a real joint-session run, /api/start takes a
small scenario configuration instead of just firing blind. Text + voice
memo, text + spoken replies, same pattern as intake-app and
joint-session-app. Single-user, in-memory, nothing persisted.

Run:
    pip install -r requirements.txt
    cp ../intake-app/.env .env
    uvicorn server:app --reload --port 8422
"""
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-post-session-system-prompt.md"
MODEL = "claude-sonnet-5"
AUDIO_DIR = Path(tempfile.mkdtemp(prefix="mend-post-audio-"))
VOICE = "Samantha"

load_dotenv(ROOT / ".env")

app = FastAPI()
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None


def load_system_prompt() -> str:
    text = SYSTEM_PROMPT_FILE.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {SYSTEM_PROMPT_FILE}")
    return match.group(1)


SYSTEM_PROMPT = load_system_prompt()
conversation: list[dict] = []

_whisper_model = None


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("small.en", device="cpu", compute_type="int8")
    return _whisper_model

FLOOR_CATEGORIES = {
    "harassment_discrimination": "harassment or discrimination based on a protected characteristic",
    "threats_violence": "threats or violence",
    "illegal_activity": "illegal activity",
    "immediate_safety_risk": "immediate safety risk",
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


def facilitator_reply() -> dict:
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set -- see README)", "signal": None}
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
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
    return {"reply": visible, "signal": signal, "audio_url": synthesize_speech(visible)}


@app.post("/api/start")
async def start(payload: dict):
    """payload: {escalation: 'none' | 'own_conduct' | 'other_party_conduct',
                 category: one of FLOOR_CATEGORIES keys (if escalation != 'none'),
                 context: free-text note on what happened, optional}"""
    if conversation:
        return {"reply": None, "signal": None}

    escalation = payload.get("escalation", "none")
    category = payload.get("category")
    context = payload.get("context", "").strip()

    if escalation == "none":
        escalation_note = "Nothing was escalated in the joint session that just ended."
    else:
        cat_label = FLOOR_CATEGORIES.get(category, category or "an unspecified category")
        whose = "this employee's own conduct" if escalation == "own_conduct" else "the other party's conduct (not this employee's)"
        escalation_note = f"Something was escalated in the joint session: {whose}, category: {cat_label}."

    context_note = f" Additional context on what happened: {context}" if context else ""

    kickoff = (
        f"(This employee just came out of a joint session with the other party. {escalation_note}"
        f"{context_note} Begin the follow-up now, handling the escalation disclosure first if "
        f"applicable, per your instructions.)"
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
