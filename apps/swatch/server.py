#!/usr/bin/env python3
"""
Local prototype of Swatch's design-crit side: a private, one-on-one
conversation with one reviewer about one specific design artifact
(../facilitator-swatch-intake-system-prompt.md), turning a raw gut reaction
into a confirmed, attributed note; then a live, audio-only-in-the-real-
version (text-only here) group session where those confirmed notes
actually get presented and discussed
(../facilitator-swatch-live-system-prompt.md).

Unlike Loom, Swatch's output is NOT anonymized -- each confirmed note is
shown with the reviewer's own name, no minimum-contributor floor, no
distillation step. See the intake prompt and
../swatch-product-roadmap.md for why.

The live session here is text-first over a WebSocket, same incremental
scope cut Suture itself started with before real LiveKit audio
(../joint-session-audio/) became a separate follow-on -- no LiveKit, no
TTS, no turn-taking classifier in this pass. Any participant name can
join a room keyed by artifact name; there's no fixed role count the way
Suture has employee_a/employee_b, since a crit's headcount varies.

The anonymous clarification relay lets any live-session participant send
Thimble a private question (tied to whichever note is currently on the
floor) instead of asking it in the open; Thimble answers it directly from
that reviewer's private intake transcript when it grounds a real answer,
or poses it to the note's author otherwise -- either way the result posts
publicly to the whole room, never back to the asker alone, since there's
no asker identity to protect once it's out. This hides the question's
content and authorship, not the fact that *a* question landed right then
-- an accepted, documented limit, not a solved guarantee.

Multi-session, in-memory only, nothing persisted to disk, lost on restart.

Run:
    pip install -r requirements.txt
    cp ../thimble/.env .env
    uvicorn server:app --reload --port 8426
"""
import asyncio
import logging
import os
import re
import sys
import time
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
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
LIVE_PROMPT_FILE = ROOT.parent / "facilitator-swatch-live-system-prompt.md"
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
LIVE_PROMPT = LIVE_PROMPT_FILE.read_text()

# One entry per in-progress or finished reviewer session, keyed by a
# server-issued session_id -- lets several reviewers work on the same
# artifact concurrently.
sessions: dict[str, dict] = {}

# Confirmed, attributed notes, grouped by artifact name. Each entry is
# {"reviewer_name": str, "note": str, "heuristic": str | None}. Shown to
# the group as-is -- no anonymization, no corroboration floor, unlike Loom.
notes_by_artifact: dict[str, list[dict]] = {}

# --- Live group session ----------------------------------------------------
# One room per artifact name -- no fixed role slots (unlike Suture's
# employee_a/employee_b), since a crit's headcount varies. Any number of
# named participants can join; the room only actually starts once someone
# sends {"type": "start"} (idempotent -- see handle_live_start), so
# everyone has a chance to join before the facilitator presents the first
# note.
WS_RATE_MAX = int(os.environ.get("WS_RATE_MAX", "20"))
WS_RATE_WINDOW = int(os.environ.get("WS_RATE_WINDOW", "60"))
_ws_rate_hits: dict[str, list[float]] = {}


def ws_rate_limited(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _ws_rate_hits.get(ip, []) if now - t < WS_RATE_WINDOW]
    if len(hits) >= WS_RATE_MAX:
        _ws_rate_hits[ip] = hits
        return True
    hits.append(now)
    _ws_rate_hits[ip] = hits
    return False


class LiveSession:
    """One live crit room, keyed by artifact name. A prototype's worth of
    state, not a persistence layer -- lost on process restart."""

    def __init__(self, artifact: str):
        self.artifact = artifact
        self.conversation: list[dict] = []
        self.state: dict = {}
        self.sockets: dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
        self.started = False
        self.ended = False
        # Snapshot of notes_by_artifact[artifact] taken the moment the room
        # starts -- current_note_index in the model's signal indexes into
        # this list, so a note confirmed mid-session (a reviewer still
        # finishing their private pass) doesn't shift indices out from
        # under an already-open room.
        self.notes: list[dict] = []
        # Updated from the model's own signal after every public turn --
        # lets a relay question default to "about whatever's on the floor
        # right now" without the asker having to say which note.
        self.current_note_index: int | None = None


LIVE_SESSIONS: dict[str, LiveSession] = {}


def get_live_session(artifact: str) -> LiveSession:
    return LIVE_SESSIONS.setdefault(artifact, LiveSession(artifact))


def live_facilitator_reply(session: LiveSession) -> dict:
    result = call_facilitator(
        client, MODEL, LIVE_PROMPT, session.conversation,
        tag="swatch_live_signal", app="swatch", reply_kind="live_facilitator_reply",
        max_tokens=4096,
    )
    result["signal"] = parse_signal_json(result["signal"])
    return result


def build_live_kickoff_turn(session: LiveSession) -> str:
    if not session.notes:
        lines = "(No confirmed notes exist for this artifact yet.)"
    else:
        lines = "\n".join(
            f"- {n['reviewer_name']}: {n['note']}" + (f" [heuristic: {n['heuristic']}]" if n.get("heuristic") else "")
            for n in session.notes
        )
    return (
        f"(The live crit session for \"{session.artifact}\" is starting. "
        f"There are {len(session.notes)} confirmed note(s):\n{lines}\n"
        "Open the session now per your instructions: name the artifact and "
        "how many notes are in, then present the first one.)"
    )


async def send_to_live(session: LiveSession, name: str, payload: dict) -> None:
    ws = session.sockets.get(name)
    if ws is None:
        return
    try:
        await ws.send_json(payload)
    except Exception:
        if session.sockets.get(name) is ws:
            del session.sockets[name]


async def broadcast_live(session: LiveSession, payload: dict) -> None:
    for name in list(session.sockets):
        await send_to_live(session, name, payload)


async def handle_live_start(session: LiveSession) -> None:
    if session.started:
        return
    session.started = True
    session.notes = list(notes_by_artifact.get(session.artifact, []))
    await broadcast_live(session, {"type": "thinking"})
    async with session.lock:
        session.conversation.append({"role": "user", "content": build_live_kickoff_turn(session)})
        result = await run_in_threadpool(live_facilitator_reply, session)
    await broadcast_live_result(session, result)


async def handle_live_message(session: LiveSession, name: str, text: str) -> None:
    await broadcast_live(session, {"type": "thinking"})
    async with session.lock:
        session.conversation.append({"role": "user", "content": f"[{name}]: {text}"})
        result = await run_in_threadpool(live_facilitator_reply, session)
    await broadcast_live_result(session, result, sender=name, sender_text=text)


async def broadcast_live_result(session: LiveSession, result: dict, sender: str | None = None, sender_text: str | None = None) -> None:
    if sender is not None:
        await broadcast_live(session, {"type": "message", "from": sender, "text": sender_text})
    signal = result.get("signal") or {}
    if signal.get("current_note_index") is not None:
        session.current_note_index = signal.get("current_note_index")
    await broadcast_live(session, {
        "type": "message", "from": "facilitator", "text": result.get("reply"), "signal": signal,
    })
    if signal.get("session_state") == "ended" and not session.ended:
        session.ended = True
        await broadcast_live(session, {"type": "ended"})


def find_grounding_transcript(artifact: str, reviewer_name: str) -> str | None:
    """The reviewer's own private reframing conversation for this artifact,
    if it's still in memory -- what grounds a relayed question's direct
    answer. Last confirmed match wins; a prototype's worth of lookup, not
    an index."""
    match = None
    for s in sessions.values():
        if s.get("artifact_name") == artifact and s.get("reviewer_name") == reviewer_name and s.get("recorded"):
            match = s
    if match is None:
        return None
    lines = [
        f"[{turn.get('role')}] {turn.get('content')}"
        for turn in match["conversation"]
        if isinstance(turn.get("content"), str)
    ]
    return "\n".join(lines)


def build_relay_turn(session: LiveSession, text: str) -> str:
    note = None
    if session.current_note_index is not None and 0 <= session.current_note_index < len(session.notes):
        note = session.notes[session.current_note_index]

    header = (
        "(RELAY -- a private question came in through the anonymous relay, not for "
        "broadcast as-is. Decide whether you can answer it yourself, grounded in the "
        "record below, or whether it needs the note's author. Post your decision to "
        "the whole room now as a normal facilitator turn, in your own voice.)"
    )
    if note:
        header += f"\n\nIt concerns {note['reviewer_name']}'s note: \"{note['note']}\"."
    header += f"\n\nPrivate question: \"{text}\""

    grounding = find_grounding_transcript(session.artifact, note["reviewer_name"]) if note else None
    if grounding:
        header += (
            f"\n\n{note['reviewer_name']}'s private reframing conversation about this "
            "artifact, for grounding only -- don't quote it verbatim or reveal anything "
            "beyond what's needed to answer:\n" + grounding
        )
    else:
        header += (
            "\n\n(No private record is available to ground a direct answer -- if you "
            "can't answer confidently, pose the question to the room or to the note's "
            "author instead of guessing.)"
        )
    return header


async def handle_live_ask(session: LiveSession, asker: str, text: str) -> None:
    await send_to_live(session, asker, {"type": "ask_received"})
    await broadcast_live(session, {"type": "thinking"})
    async with session.lock:
        session.conversation.append({"role": "user", "content": build_relay_turn(session, text)})
        result = await run_in_threadpool(live_facilitator_reply, session)
    await broadcast_live_result(session, result)


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
    LIVE_SESSIONS.clear()
    return {"ok": True}


@app.websocket("/ws/live/{artifact}/{participant_name}")
async def live_session_ws(websocket: WebSocket, artifact: str, participant_name: str):
    session = get_live_session(artifact)
    await websocket.accept()
    session.sockets[participant_name] = websocket
    await send_to_live(session, participant_name, {
        "type": "joined", "started": session.started, "ended": session.ended,
        "participants": list(session.sockets),
    })

    try:
        while True:
            payload = await websocket.receive_json()
            msg_type = payload.get("type")

            ip = websocket.client.host if websocket.client else "unknown"
            if msg_type in ("start", "message", "ask_private") and ws_rate_limited(ip):
                await send_to_live(session, participant_name, {
                    "type": "error", "error": "too many messages -- slow down and try again shortly",
                })
                continue

            if msg_type == "start":
                await handle_live_start(session)
                continue

            if msg_type not in ("message", "ask_private"):
                continue

            text = (payload.get("text") or "").strip()
            if not text:
                continue
            if not session.started:
                await send_to_live(session, participant_name, {"type": "error", "error": "session hasn't started yet"})
                continue
            if session.ended:
                await send_to_live(session, participant_name, {"type": "error", "error": "session has ended"})
                continue

            if msg_type == "ask_private":
                await handle_live_ask(session, participant_name, text)
            else:
                await handle_live_message(session, participant_name, text)
    except WebSocketDisconnect:
        if session.sockets.get(participant_name) is websocket:
            del session.sockets[participant_name]


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
