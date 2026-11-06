#!/usr/bin/env python3
"""
Local prototype of Loom's one phase so far: a private, one-on-one retro
interview with a single team member, driven by
../facilitator-loom-intake-system-prompt.md. Text only, no voice, no
distillation-across-the-team step yet (see loom-product-roadmap.md) --
this is just the per-person interview, same shape as
../post-session-app/server.py minus voice/audio.

Single-user, in-memory conversation -- nothing persisted to disk, lost on
restart.

Run:
    pip install -r requirements.txt
    cp ../thimble/.env .env
    uvicorn server:app --reload --port 8425
"""
import os
import re
import sys
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent

# Shared local cost/usage logger (../../usage_log.py) -- same sys.path trick
# as thimble/suture/post-session-app.
sys.path.insert(0, str(ROOT.parent.parent))
from usage_log import log_usage

SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-loom-intake-system-prompt.md"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

load_dotenv(ROOT / ".env")

app = FastAPI()
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

# --- Rate limiting --------------------------------------------------------
# Same reasoning as thimble/post-session-app: no request cap on an
# LLM-backed endpoint is an open invitation to run up the bill.
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


SYSTEM_PROMPT = SYSTEM_PROMPT_FILE.read_text()
conversation: list[dict] = []


def strip_signal(reply_text: str) -> tuple[str, str | None]:
    match = re.search(r"<loom_signal>(.*?)</loom_signal>", reply_text, re.S)
    signal = match.group(1).strip() if match else None
    visible = re.sub(r"<loom_signal>.*?</loom_signal>", "", reply_text, flags=re.S).strip()
    return visible, signal


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
    log_usage("loom", "anthropic", MODEL, "facilitator_reply",
              input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens)
    raw = "".join(block.text for block in response.content if block.type == "text")
    if not raw:
        conversation.pop()
        return {
            "reply": f"(server error: no text in response, stop_reason={response.stop_reason})",
            "signal": None,
        }
    visible, signal = strip_signal(raw)
    conversation.append({"role": "assistant", "content": raw})
    return {"reply": visible, "signal": signal}


@app.post("/api/start")
async def start(payload: dict):
    """payload: {sprint_name: str, optional}"""
    if conversation:
        return {"reply": None, "signal": None}
    sprint_name = (payload.get("sprint_name") or "").strip()
    kickoff = (
        f"(Begin the retro interview now, per your instructions."
        + (f" The sprint/project is: {sprint_name}." if sprint_name else " No sprint/project name was given yet; ask for it as part of your opening turn.")
        + ")"
    )
    conversation.append({"role": "user", "content": kickoff})
    return facilitator_reply()


@app.post("/api/message")
async def post_message(payload: dict):
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)
    conversation.append({"role": "user", "content": text})
    return facilitator_reply()


@app.post("/api/reset")
async def reset():
    conversation.clear()
    return {"ok": True}


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
