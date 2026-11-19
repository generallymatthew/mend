#!/usr/bin/env python3
"""
Local prototype of Swatch's first phase: a private, one-on-one conversation
with one reviewer about one specific design artifact
(../facilitator-swatch-intake-system-prompt.md), turning a raw gut reaction
into a confirmed, attributed note. Text only, no voice.

Unlike Loom, Swatch's output is NOT anonymized -- each confirmed note is
shown with the reviewer's own name, no minimum-contributor floor, no
distillation step. See the intake prompt and
../swatch-product-roadmap.md for why.

Later phases (live audio-only group session, anonymous clarification
relay) are not built -- this is intake only, same scope cut Loom started
with.

Multi-session, in-memory only, nothing persisted to disk, lost on restart.

Run:
    pip install -r requirements.txt
    cp ../thimble/.env .env
    uvicorn server:app --reload --port 8426
"""
import logging
import os
import re
import sys
import time
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent

# Shared local cost/usage logger (../../usage_log.py).
sys.path.insert(0, str(ROOT.parent.parent))
from usage_log import log_usage

# Shared intake/facilitator-call primitive (../mend_intake.py).
sys.path.insert(0, str(ROOT.parent))
from mend_intake import call_facilitator, parse_signal_json

INTAKE_PROMPT_FILE = ROOT.parent / "facilitator-swatch-intake-system-prompt.md"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("mend.swatch")

app = FastAPI()
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

# --- Rate limiting --------------------------------------------------------
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


INTAKE_PROMPT = INTAKE_PROMPT_FILE.read_text()

# One entry per in-progress or finished reviewer session, keyed by a
# server-issued session_id -- lets several reviewers work on the same
# artifact concurrently.
sessions: dict[str, dict] = {}

# Confirmed, attributed notes, grouped by artifact name. Each entry is
# {"reviewer_name": str, "note": str, "heuristic": str | None}. Shown to
# the group as-is -- no anonymization, no corroboration floor, unlike Loom.
notes_by_artifact: dict[str, list[dict]] = {}


def facilitator_reply_blocking(session: dict) -> dict:
    conversation = session["conversation"]
    result = call_facilitator(
        client, MODEL, INTAKE_PROMPT, conversation,
        tag="swatch_signal", app="swatch", reply_kind="facilitator_reply",
        max_tokens=4096,
    )
    parsed = parse_signal_json(result["signal"])
    if parsed:
        session["last_note"] = parsed.get("note")
        session["last_heuristic"] = parsed.get("heuristic")
        # Only ever record a note the reviewer actually confirmed in
        # Phase 3 -- phase=="done" alone isn't enough, confirmed must also
        # be true, same discipline as Loom.
        if parsed.get("confirmed") is True and not session.get("recorded"):
            artifact = session["artifact_name"] or "(unnamed artifact)"
            notes_by_artifact.setdefault(artifact, []).append({
                "reviewer_name": session["reviewer_name"] or "(unnamed reviewer)",
                "note": session["last_note"],
                "heuristic": session["last_heuristic"],
            })
            session["recorded"] = True
        escalation = parsed.get("escalation_flagged")
        if escalation and not session.get("escalation_logged"):
            logger.warning("Swatch escalation flagged, session=%s artifact=%s reason=%s",
                            session.get("id"), session.get("artifact_name"), escalation.get("reason"))
            session["escalation_logged"] = True
        session["escalation_flagged"] = escalation
    return result


@app.post("/api/start")
async def start(payload: dict):
    """payload: {artifact_name: str, reviewer_name: str} -> {session_id, reply, signal}"""
    artifact_name = (payload.get("artifact_name") or "").strip()
    reviewer_name = (payload.get("reviewer_name") or "").strip()
    session_id = uuid.uuid4().hex
    session = {
        "id": session_id, "conversation": [],
        "artifact_name": artifact_name, "reviewer_name": reviewer_name,
        "last_note": None, "last_heuristic": None, "recorded": False,
    }
    sessions[session_id] = session
    kickoff = (
        "(Begin the private reframing conversation now, per your instructions."
        + (f" The artifact is: {artifact_name}." if artifact_name else " No artifact name was given yet; ask for it as part of your opening turn.")
        + (f" The reviewer's name is {reviewer_name}." if reviewer_name else " No reviewer name was given yet; ask for it if you need it before posting the note.")
        + ")"
    )
    session["conversation"].append({"role": "user", "content": kickoff})
    result = await run_in_threadpool(facilitator_reply_blocking, session)
    result["session_id"] = session_id
    return result


@app.post("/api/message")
async def post_message(payload: dict):
    session_id = payload.get("session_id")
    session = sessions.get(session_id)
    if session is None:
        return JSONResponse({"error": "unknown or expired session_id"}, status_code=404)
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)
    session["conversation"].append({"role": "user", "content": text})
    # Pick up an artifact name mentioned mid-conversation if /api/start
    # wasn't given one yet -- same cheap heuristic Loom uses for sprint names.
    if not session["artifact_name"]:
        m = re.search(r"(screen|flow|artifact|design)[^.?!\n]{0,40}", text, re.I)
        if m:
            session["artifact_name"] = m.group(0).strip()
    return await run_in_threadpool(facilitator_reply_blocking, session)


@app.get("/api/notes")
async def get_notes(artifact: str):
    """?artifact=<name> -> {notes: [...]} -- every confirmed, attributed note for this artifact."""
    return {"notes": notes_by_artifact.get(artifact, [])}


@app.post("/api/reset")
async def reset():
    sessions.clear()
    notes_by_artifact.clear()
    return {"ok": True}


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
