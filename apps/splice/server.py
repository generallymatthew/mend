#!/usr/bin/env python3
"""
Local prototype of the Mend group session: several strangers (e.g. 6 OSS
contributors at an impasse on one issue) joining one shared room to discuss,
propose options, and vote -- option A from the UI review ("video first":
a video grid, chat + proposals in a sidebar, one open vote pinned below
the grid).

Single-room, in-memory state only -- this is a prototype to test the
interaction pattern (shared proposals, live vote tally, chat), not a
deployable multi-tenant service. State is lost on restart, same convention
as every other app here.

Video is NOT real peer-to-peer video. Each browser tab shows its own camera
in its own tile (getUserMedia, local only) and every other participant's
tile is a placeholder with their initials -- there is no signaling server or
SFU here. Wiring real multi-party video needs a provider (LiveKit or Daily,
per ../joint-session-architecture.md's own reasoning for why that's rented,
not built from scratch) and is deliberately out of scope for this prototype.

Thimble (the facilitator) is a real Claude call, not scripted: driven by
../facilitator-group-session-system-prompt.md, given the issue, participant
list, recent chat and current proposals/tallies each time someone asks it
to weigh in, and posted back into the chat as a message from "Thimble".
It never votes and can't be removed.

Run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...   # your own key; Thimble replies with an
                                    # error message in chat if unset, rest
                                    # of the app still works
    uvicorn server:app --reload --port 8440

Then open http://localhost:8440 in several tabs (or share the URL on one
LAN) to simulate several participants in the same room.
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# Shared local cost/usage logger, same cross-app import convention every
# other -app/server.py here uses (no shared package layout in this repo).
sys.path.insert(0, str(ROOT.parent.parent))
from usage_log import log_usage

SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-group-session-system-prompt.md"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

app = FastAPI()


# ---------------------------------------------------------------------------
# In-memory room state. One room for this prototype -- a real deployment
# would key all of this by room_id.
# ---------------------------------------------------------------------------

class Participant:
    def __init__(self, name: str, id: Optional[str] = None, preferred_method: str = "video"):
        self.id = id or uuid.uuid4().hex[:8]
        self.name = name
        self.joined_at = time.time()
        self.speaking = False
        self.preferred_method = preferred_method  # "video" | "text" -- set once, at onboarding
        # Someone who said they'd rather type starts muted with video off;
        # either control still works normally after that, this is just the
        # sensible default to land on, not a restriction.
        self.muted = preferred_method == "text"
        self.video_off = preferred_method == "text"


class Proposal:
    def __init__(self, text: str, author_id: str):
        self.id = uuid.uuid4().hex[:8]
        self.text = text
        self.author_id = author_id
        self.created_at = time.time()
        self.votes: dict[str, str] = {}  # participant_id -> "yes" | "no" | "abstain"
        self.open = True


THIMBLE_ID = "thimble"


class Room:
    def __init__(self):
        self.participants: dict[str, Participant] = {THIMBLE_ID: Participant("Thimble", id=THIMBLE_ID)}
        self.messages: list[dict] = []
        self.proposals: list[Proposal] = []
        self.issue_title = "oss-repo#482 — Deprecate legacy config loader"
        self.sockets: dict[str, WebSocket] = {}
        self.thimble_busy = False  # true while a reply is in flight, to stop pile-up clicks

    def state(self) -> dict:
        return {
            "issue_title": self.issue_title,
            "thimble_busy": self.thimble_busy,
            "participants": [
                {
                    "id": p.id,
                    "name": p.name,
                    "speaking": p.speaking,
                    "muted": p.muted,
                    "video_off": p.video_off,
                    "preferred_method": p.preferred_method,
                    "is_facilitator": p.id == THIMBLE_ID,
                }
                for p in self.participants.values()
            ],
            "messages": self.messages[-200:],
            "proposals": [
                {
                    "id": pr.id,
                    "text": pr.text,
                    "author_id": pr.author_id,
                    "open": pr.open,
                    "tally": tally(pr),
                    "votes": pr.votes,
                }
                for pr in self.proposals
            ],
        }


def tally(proposal: Proposal) -> dict:
    counts = {"yes": 0, "no": 0, "abstain": 0}
    for choice in proposal.votes.values():
        counts[choice] = counts.get(choice, 0) + 1
    return counts


room = Room()


async def broadcast():
    payload = json.dumps({"type": "state", "state": room.state()})
    dead = []
    for pid, ws in room.sockets.items():
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(pid)
    for pid in dead:
        room.sockets.pop(pid, None)


# ---------------------------------------------------------------------------
# REST: join, message, proposal, vote. Each mutates room state then
# broadcasts the new state to every connected socket.
# ---------------------------------------------------------------------------

class JoinBody(BaseModel):
    name: str
    preferred_method: str = "video"  # "video" | "text"


class MessageBody(BaseModel):
    participant_id: str
    text: str


class ProposalBody(BaseModel):
    participant_id: str
    text: str


class VoteBody(BaseModel):
    participant_id: str
    proposal_id: str
    choice: str  # "yes" | "no" | "abstain"


class SpeakingBody(BaseModel):
    participant_id: str
    speaking: bool


class MuteBody(BaseModel):
    participant_id: str
    muted: bool


class VideoBody(BaseModel):
    participant_id: str
    video_off: bool


class LeaveBody(BaseModel):
    participant_id: str


class AskThimbleBody(BaseModel):
    participant_id: str


@app.post("/api/join")
async def join(body: JoinBody):
    method = body.preferred_method if body.preferred_method in ("video", "text") else "video"
    p = Participant(body.name.strip() or "Anonymous", preferred_method=method)
    room.participants[p.id] = p
    await broadcast()
    return {"participant_id": p.id, "state": room.state()}


@app.post("/api/message")
async def message(body: MessageBody):
    p = room.participants.get(body.participant_id)
    if not p:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    text = body.text.strip()
    if not text:
        return JSONResponse({"error": "empty message"}, status_code=400)
    room.messages.append(
        {"author_id": p.id, "author_name": p.name, "text": text, "at": time.time()}
    )
    await broadcast()
    return {"ok": True}


@app.post("/api/proposal")
async def proposal(body: ProposalBody):
    p = room.participants.get(body.participant_id)
    if not p:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    text = body.text.strip()
    if not text:
        return JSONResponse({"error": "empty proposal"}, status_code=400)
    room.proposals.append(Proposal(text, p.id))
    await broadcast()
    return {"ok": True}


@app.post("/api/vote")
async def vote(body: VoteBody):
    if body.choice not in ("yes", "no", "abstain"):
        return JSONResponse({"error": "invalid choice"}, status_code=400)
    pr = next((pr for pr in room.proposals if pr.id == body.proposal_id), None)
    if not pr:
        return JSONResponse({"error": "unknown proposal"}, status_code=404)
    if body.participant_id not in room.participants:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    pr.votes[body.participant_id] = body.choice
    await broadcast()
    return {"ok": True}


@app.post("/api/speaking")
async def speaking(body: SpeakingBody):
    p = room.participants.get(body.participant_id)
    if not p:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    p.speaking = body.speaking
    await broadcast()
    return {"ok": True}


@app.post("/api/mute")
async def mute(body: MuteBody):
    p = room.participants.get(body.participant_id)
    if not p or p.id == THIMBLE_ID:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    p.muted = body.muted
    await broadcast()
    return {"ok": True}


@app.post("/api/video")
async def video(body: VideoBody):
    p = room.participants.get(body.participant_id)
    if not p or p.id == THIMBLE_ID:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    p.video_off = body.video_off
    await broadcast()
    return {"ok": True}


@app.post("/api/leave")
async def leave(body: LeaveBody):
    """Removes you from the room -- the control-bar "Leave" button. Only
    ever removes the caller themselves; there's no kick-another-participant
    feature in this prototype."""
    if body.participant_id == THIMBLE_ID:
        return JSONResponse({"error": "can't remove Thimble"}, status_code=400)
    p = room.participants.pop(body.participant_id, None)
    if not p:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    ws = room.sockets.pop(body.participant_id, None)
    if ws:
        try:
            await ws.close()
        except Exception:
            pass
    await broadcast()
    return {"ok": True}


def build_thimble_prompt() -> str:
    lines = [f"Issue under discussion: {room.issue_title}", ""]
    names = [p.name for p in room.participants.values() if p.id != THIMBLE_ID]
    lines.append(f"Participants ({len(names)}): " + ", ".join(names))
    lines.append("")
    lines.append("Recent chat:")
    for m in room.messages[-40:]:
        lines.append(f"{m['author_name']}: {m['text']}")
    if not room.messages:
        lines.append("(no messages yet)")
    lines.append("")
    lines.append("Current proposals:")
    if room.proposals:
        for pr in room.proposals:
            t = tally(pr)
            lines.append(f"- \"{pr.text}\" -- {t['yes']} yes, {t['no']} no, {t['abstain']} abstain")
    else:
        lines.append("(none yet)")
    lines.append("")
    lines.append("Weigh in now as Thimble: ask the next useful question, name an implicit "
                  "proposal, or nudge the group toward a vote, per your system prompt.")
    return "\n".join(lines)


def thimble_reply_blocking(prompt: str) -> str:
    """Synchronous, blocking Anthropic call -- always invoke via
    run_in_threadpool from a route handler, same reasoning as thimble's
    facilitator_reply(): uvicorn's single-threaded event loop would
    otherwise stall every other request in the room for the call's full
    duration."""
    if client is None:
        return "(Thimble is offline: ANTHROPIC_API_KEY is not set in this shell)"
    system_prompt = SYSTEM_PROMPT_FILE.read_text()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        return f"(Thimble had trouble replying: {e})"
    log_usage("splice", "anthropic", MODEL, "thimble_reply",
              input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens)
    return "".join(block.text for block in response.content if block.type == "text").strip()


@app.post("/api/ask-thimble")
async def ask_thimble(body: AskThimbleBody):
    if body.participant_id not in room.participants:
        return JSONResponse({"error": "unknown participant"}, status_code=404)
    if room.thimble_busy:
        return JSONResponse({"error": "Thimble is already replying"}, status_code=409)
    room.thimble_busy = True
    try:
        prompt = build_thimble_prompt()
        reply = await run_in_threadpool(thimble_reply_blocking, prompt)
        room.messages.append(
            {"author_id": THIMBLE_ID, "author_name": "Thimble", "text": reply, "at": time.time()}
        )
    finally:
        room.thimble_busy = False
    await broadcast()
    return {"ok": True}


@app.websocket("/ws/{participant_id}")
async def ws_endpoint(websocket: WebSocket, participant_id: str):
    await websocket.accept()
    room.sockets[participant_id] = websocket
    await websocket.send_text(json.dumps({"type": "state", "state": room.state()}))
    try:
        while True:
            await websocket.receive_text()  # unused; client only listens
    except WebSocketDisconnect:
        room.sockets.pop(participant_id, None)


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
