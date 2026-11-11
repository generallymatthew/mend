#!/usr/bin/env python3
"""
Local prototype of Loom's two phases: a private, one-on-one retro interview
with each team member (../facilitator-loom-intake-system-prompt.md), and a
distillation step that turns every completed interview for one sprint into
a single team-level pattern report
(../facilitator-loom-distillation-system-prompt.md), never individually
attributed. Text only, no voice.

Multi-session now (one real interview per session_id, several can run
concurrently for the same sprint), still entirely in-memory -- nothing
persisted to disk, lost on restart.

Run:
    pip install -r requirements.txt
    cp ../thimble/.env .env
    uvicorn server:app --reload --port 8425
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

# Shared local cost/usage logger (../../usage_log.py) -- same sys.path trick
# as thimble/suture/post-session-app.
sys.path.insert(0, str(ROOT.parent.parent))
from usage_log import log_usage

# Shared intake/facilitator-call primitive (../mend_intake.py), used
# identically by suture -- see that module's docstring and IDEAS.md's
# "Suture/Loom convergence..." entry (2026-11-11).
sys.path.insert(0, str(ROOT.parent))
from mend_intake import call_facilitator, parse_signal_json

INTAKE_PROMPT_FILE = ROOT.parent / "facilitator-loom-intake-system-prompt.md"
DISTILL_PROMPT_FILE = ROOT.parent / "facilitator-loom-distillation-system-prompt.md"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

# Minimum number of *completed* interviews for a sprint before distillation
# will run at all -- the team-level floor flagged as unresolved in
# loom-product-roadmap.md. 4, not the more obvious-looking 3: with only 3
# contributors, a 2-of-3 corroborated pattern can often be narrowed to "the
# one person who didn't say it" by elimination, which defeats the point.
# Still a first conservative default, not a validated number -- see the
# roadmap for why this isn't a solved problem yet (a real org's team-size
# distribution, re-identification by writing style, etc. are all untested).
MIN_CONTRIBUTORS = int(os.environ.get("LOOM_MIN_CONTRIBUTORS", "4"))

load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("mend.loom")

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


INTAKE_PROMPT = INTAKE_PROMPT_FILE.read_text()
DISTILL_PROMPT = DISTILL_PROMPT_FILE.read_text()

# One entry per in-progress or finished interview, keyed by a server-issued
# session_id the client round-trips on every call -- this is what makes
# several people's interviews able to run at once instead of one shared
# global conversation.
sessions: dict[str, dict] = {}

# Completed interviews' findings, grouped by sprint name, each entry a
# contributor's own findings list (order is the only "identity" kept, and
# only used internally to tell two findings from the same person apart from
# real corroboration across people -- never shown to the model as anything
# but an opaque index, never shown to any user at all).
completed_by_sprint: dict[str, list[list[dict]]] = {}


def facilitator_reply_blocking(session: dict) -> dict:
    conversation = session["conversation"]
    result = call_facilitator(
        client, MODEL, INTAKE_PROMPT, conversation,
        tag="loom_signal", app="loom", reply_kind="facilitator_reply",
        max_tokens=4096,
    )
    parsed = parse_signal_json(result["signal"])
    if parsed:
        session["last_findings"] = parsed.get("findings") or []
        # Only ever record findings the person actually confirmed in
        # Phase 3 of the intake prompt -- phase=="done" alone is not
        # enough, confirmed must also be true, since the model could in
        # principle report phase done without that explicit approval.
        if parsed.get("confirmed") is True and not session.get("recorded"):
            sprint = session["sprint_name"] or "(unnamed sprint)"
            completed_by_sprint.setdefault(sprint, []).append(session["last_findings"])
            session["recorded"] = True
        # Never folded into findings/completed_by_sprint -- it must never
        # reach the anonymized team report. This is the only durable
        # surface for it right now (no operator UI exists yet); logging
        # it loudly beats losing it in a debug panel that scrolls away.
        escalation = parsed.get("escalation_flagged")
        if escalation and not session.get("escalation_logged"):
            logger.warning("Loom escalation flagged, session=%s sprint=%s reason=%s",
                            session.get("id"), session.get("sprint_name"), escalation.get("reason"))
            session["escalation_logged"] = True
        session["escalation_flagged"] = escalation
    return result


@app.post("/api/start")
async def start(payload: dict):
    """payload: {sprint_name: str, optional} -> {session_id, reply, signal}"""
    sprint_name = (payload.get("sprint_name") or "").strip()
    session_id = uuid.uuid4().hex
    session = {"id": session_id, "conversation": [], "sprint_name": sprint_name, "last_findings": [], "recorded": False}
    sessions[session_id] = session
    kickoff = (
        f"(Begin the retro interview now, per your instructions."
        + (f" The sprint/project is: {sprint_name}." if sprint_name else " No sprint/project name was given yet; ask for it as part of your opening turn.")
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
    # Pick up a sprint name mentioned mid-conversation if /api/start wasn't
    # given one yet, so late-named sprints still group correctly at distill
    # time -- cheap heuristic (first "sprint"/"project" clause), good enough
    # for this prototype; a real build would just let the client confirm it.
    if not session["sprint_name"]:
        m = re.search(r"(sprint|project)[^.?!\n]{0,40}", text, re.I)
        if m:
            session["sprint_name"] = m.group(0).strip()
    return await run_in_threadpool(facilitator_reply_blocking, session)


@app.get("/api/distill")
async def distill(sprint: str):
    """?sprint=<name> -> {report} or {error, contributors, min_contributors}"""
    contributors = completed_by_sprint.get(sprint, [])
    if len(contributors) < MIN_CONTRIBUTORS:
        return JSONResponse({
            "error": f"only {len(contributors)} completed interview(s) for this sprint, "
                     f"need at least {MIN_CONTRIBUTORS} before a pattern report can run "
                     f"without risking individual attribution",
            "contributors": len(contributors),
            "min_contributors": MIN_CONTRIBUTORS,
        }, status_code=409)
    report = await run_in_threadpool(distill_blocking, contributors)
    return {"report": report, "contributors": len(contributors)}


def distill_blocking(contributors: list[list[dict]]) -> str:
    if client is None:
        return "(server error: ANTHROPIC_API_KEY is not set -- see README)"
    lines = []
    for i, findings in enumerate(contributors, start=1):
        lines.append(f"Contributor {i}:")
        for f in findings:
            lines.append(f"- ({f.get('sentiment', 'neutral')}) {f.get('summary', '')}"
                         + (f" [likely cause: {f.get('likely_cause')}]" if f.get("likely_cause") else ""))
    prompt = "\n".join(lines) + "\n\nProduce the team-level pattern report now, per your instructions."
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=DISTILL_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        return f"(server error calling Claude: {e})"
    log_usage("loom", "anthropic", MODEL, "distill_blocking",
              input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens)
    return "".join(block.text for block in response.content if block.type == "text").strip()


@app.post("/api/reset")
async def reset():
    sessions.clear()
    completed_by_sprint.clear()
    return {"ok": True}


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
