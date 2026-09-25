#!/usr/bin/env python3
"""
Local prototype of the joint session: two employees (you, playing both
sides by switching hats) plus the facilitator, driven by
../facilitator-joint-session-system-prompt.md.

This tests the facilitator's own conversational logic only -- turn-taking,
the routine close staying identical regardless of outcome, the rising-
tension pause, the silent wind-down. It does NOT implement the real-time
audio delay buffer or the fast hard-cut classifier from
../joint-session-architecture.md; those are a separate, harder problem
(intercepting audio between two humans in real time) that a text harness
like this can't exercise. This only validates what the facilitator itself
decides to say and when.

Single-user, in-memory conversation, nothing persisted. Same setup as
../intake-app/ -- copy your .env over or create a fresh one here.

Run:
    pip install -r requirements.txt
    cp ../intake-app/.env .env   # or create fresh with your own key
    uvicorn server:app --reload --port 8421
"""
import os
import re
import tempfile
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-joint-session-system-prompt.md"
MODEL = "claude-sonnet-5"
AUDIO_DIR = Path(tempfile.mkdtemp(prefix="mend-joint-audio-"))
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

# In-memory conversation state -- a prototype, not a persistence layer.
conversation: list[dict] = []


def strip_signal(reply_text: str) -> tuple[str, str | None]:
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    signal = match.group(1).strip() if match else None
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    return visible, signal


def synthesize_speech(text: str) -> str | None:
    if not text:
        return None
    import subprocess
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
    """Assumes the latest turn just appended to `conversation` is a user
    (employee) turn. Rolls it back on any failure so conversation always
    ends on an assistant turn or empty -- same reasoning as intake-app."""
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
async def start():
    if not conversation:
        conversation.append({
            "role": "user",
            "content": (
                "(Both employees have just joined the joint session, having already "
                "completed their private caucuses. Begin the session now: frame what "
                "it's for and manage the room.)"
            ),
        })
        return facilitator_reply()
    return {"reply": None, "signal": None}


@app.post("/api/message")
async def post_message(payload: dict):
    speaker = payload.get("speaker", "").strip()
    text = payload.get("text", "").strip()
    if speaker not in ("Employee A", "Employee B") or not text:
        return JSONResponse({"error": "need a speaker (Employee A or Employee B) and text"}, status_code=400)
    conversation.append({"role": "user", "content": f"[{speaker}]: {text}"})
    return facilitator_reply()


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
