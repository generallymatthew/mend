#!/usr/bin/env python3
"""
Local prototype of the joint session with two real, separate participants,
driven by ../facilitator-joint-session-system-prompt.md.

Each participant connects as Employee A or Employee B over a WebSocket
(/ws/{code}/{role}) using a link you hand out, e.g.:

    http://localhost:8421/?code=test1&role=a
    http://localhost:8421/?code=test1&role=b

The facilitator only opens the session once both roles are connected. The
one privacy boundary this enforces beyond "both sides see everything" is the
facilitator's private check-in (mend_signal.session_state ==
"paused_checkin"): only the addressed employee (checkin_target) can talk or
hear the facilitator's reply during that window; the other side just sees a
neutral pause.

Outside a check-in, employee-to-employee messages are mutually visible --
*unless* the real tier-3 hard-cut classifier (../classifier/inference.py,
the mend-conflict-classifier-v3 checkpoint) scores a message as an active,
escalating threat, in which case it's withheld from the other participant
entirely and the facilitator is told a cut happened (see CLASSIFIER_MODEL
below and facilitator-joint-session-system-prompt.md's `external_cut_reported`).
This is still not the real audio delay buffer from
../joint-session-architecture.md -- that's a genuine real-time-audio
engineering problem, separate from this text prototype -- but it's the same
classifier's actual decision logic, not a placeholder.

Opening both role links yourself in two tabs still covers solo testing,
same as the old single-user harness this replaces.

In-memory only, one process, nothing persisted. Same .env setup as before.

Run:
    pip install -r requirements.txt
    cp ../intake-app/.env .env   # or create fresh with your own key
    uvicorn server:app --reload --port 8421
"""
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-joint-session-system-prompt.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("mend.joint_session")

# Real tier-3 hard-cut classifier (../classifier/inference.py). v3 is the
# reference checkpoint, not v4 -- v4 fixed illegal_activity but regressed
# cut_trigger F1 (0.90 -> 0.81), see classifier/README.md and commit
# 314e6c2. Optional/soft-fail: if torch/transformers aren't installed or the
# checkpoint is missing, CLASSIFIER_MODEL stays None and every message is
# just treated as a non-cut, same as before this integration existed.
CLASSIFIER_DIR = ROOT.parent / "classifier"
CLASSIFIER_MODEL_DIR = CLASSIFIER_DIR / "output" / "mend-conflict-classifier-v3"
# inference.py's own unvalidated-guess default (see classifier/README.md's
# "Threshold tuning against the actual cost asymmetry"). Overridable via env
# for local testing only -- not a substitute for real precision/recall
# tuning, which is out of scope here.
CLASSIFIER_CUT_THRESHOLD = float(os.environ.get("CLASSIFIER_CUT_THRESHOLD", "0.9"))
CLASSIFIER_MODEL = None
try:
    sys.path.insert(0, str(CLASSIFIER_DIR))
    from inference import ConflictClassifier  # noqa: E402

    if CLASSIFIER_MODEL_DIR.is_dir():
        CLASSIFIER_MODEL = ConflictClassifier(str(CLASSIFIER_MODEL_DIR), cut_threshold=CLASSIFIER_CUT_THRESHOLD)
        logger.info("loaded hard-cut classifier from %s (cut_threshold=%s)", CLASSIFIER_MODEL_DIR, CLASSIFIER_CUT_THRESHOLD)
    else:
        logger.warning("classifier checkpoint not found at %s -- tier-3 hard-cut disabled", CLASSIFIER_MODEL_DIR)
except Exception:
    logger.exception("couldn't load the hard-cut classifier -- tier-3 hard-cut disabled, running without it")
MODEL = "claude-sonnet-5"
AUDIO_DIR = Path(tempfile.mkdtemp(prefix="mend-joint-audio-"))
VOICE = "Samantha"  # a built-in macOS voice, used only if OPENAI_API_KEY isn't set; see `say -v ?`

# Optional higher-quality voice via OpenAI TTS -- same pattern as
# ../intake-app/server.py. Falls back to macOS `say` above if
# OPENAI_API_KEY isn't set, or if the OpenAI call fails.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_TTS_VOICE = os.environ.get("OPENAI_TTS_VOICE", "alloy")

ROLE_SLUGS = {"a": "employee_a", "b": "employee_b"}
SPEAKER_LABEL = {"employee_a": "Employee A", "employee_b": "Employee B"}
OTHER_ROLE = {"employee_a": "employee_b", "employee_b": "employee_a"}

# --- Rate limiting --------------------------------------------------------
# Same reasoning as ../intake-app/server.py, but there's no per-request HTTP
# endpoint to hook here -- every real message is a WebSocket frame, so the
# limiter lives inside the receive loop instead of an HTTP middleware.
# In-memory fixed-window per client IP.
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

KICKOFF_TURN = (
    "(Both employees have just joined the joint session, having already "
    "completed their private side conversations. Begin the session now: frame what "
    "it's for and manage the room.)"
)


class Session:
    """One joint-session room. A prototype's worth of state, not a
    persistence layer -- lost on process restart, same as before."""

    def __init__(self, code: str):
        self.code = code
        self.conversation: list[dict] = []
        self.state: dict = {}
        self.sockets: dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
        self.started = False
        self.ended = False
        # Accumulated across turns, unlike floor_category/triggered_by --
        # a below-floor pattern doesn't end the session the same turn it's
        # noticed (see facilitator-joint-session-system-prompt.md), so it
        # can't be read off just the final turn's signal. First-fired-wins:
        # the model isn't asked to keep restating it once flagged.
        self.below_floor_pattern: str | None = None
        self.pattern_shown_by: str | None = None


SESSIONS: dict[str, Session] = {}


def get_session(code: str) -> Session:
    return SESSIONS.setdefault(code, Session(code))


def strip_signal(reply_text: str) -> tuple[str, dict | None]:
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    if not match:
        return visible, None
    try:
        return visible, json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return visible, None


def synthesize_speech_openai(text: str) -> str | None:
    """Speaks `text` with OpenAI's TTS, saves the returned mp3, and returns
    a URL path to fetch it. Returns None on any failure so the caller falls
    back to macOS `say`."""
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini-tts", "voice": OPENAI_TTS_VOICE, "input": text},
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
    except Exception:
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


def facilitator_reply(session: Session) -> dict:
    """Assumes the latest turn just appended to session.conversation is a
    user turn. Rolls it back on any failure so conversation always ends on
    an assistant turn or empty -- same reasoning as intake-app. Caller must
    hold session.lock."""
    if client is None:
        session.conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set -- see README)", "signal": None}
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=session.conversation,
        )
    except Exception as e:
        session.conversation.pop()
        return {"reply": f"(server error calling Claude: {e})", "signal": None}
    raw = "".join(block.text for block in response.content if block.type == "text")
    if not raw:
        session.conversation.pop()
        return {
            "reply": f"(server error: no text in response, stop_reason={response.stop_reason} -- "
                     f"likely ran out of max_tokens mid-thinking; try again or raise the limit)",
            "signal": None,
        }
    visible, signal = strip_signal(raw)
    session.conversation.append({"role": "assistant", "content": raw})
    return {"reply": visible, "signal": signal, "audio_url": synthesize_speech(visible)}


async def send_to(session: Session, role: str, payload: dict) -> None:
    ws = session.sockets.get(role)
    if ws is None:
        return
    try:
        await ws.send_json(payload)
    except Exception:
        if session.sockets.get(role) is ws:
            del session.sockets[role]


async def broadcast_result(
    session: Session, sender_role: str | None, sender_text: str | None, result: dict, cut: bool = False,
) -> None:
    """Route one facilitator turn's visible output to the right role(s),
    enforcing the two privacy boundaries this prototype cares about: the
    private check-in stays private to whichever role it's addressed to, and
    a tier-3 hard-cut withholds the triggering message from the other role
    entirely."""
    prev_state = session.state.get("session_state", "active")
    prev_checkin_target = session.state.get("checkin_target")

    signal = result.get("signal") or {}
    new_state = signal.get("session_state", prev_state)
    checkin_target = signal.get("checkin_target")
    triggered_by = signal.get("triggered_by")

    # First-fired-wins accumulation -- see Session.__init__. This can fire
    # on any turn, long before (or after) the session actually ends, unlike
    # floor_category/triggered_by which are only ever read off the same
    # turn that also closes the room.
    if signal.get("below_floor_pattern") and session.below_floor_pattern is None:
        session.below_floor_pattern = signal["below_floor_pattern"]
        session.pattern_shown_by = signal.get("pattern_shown_by")

    # `triggered_by` (which employee's words fired floor_category) must
    # never reach the shared room broadcast -- both roles currently receive
    # the same `signal` alongside every "message" event, and revealing *who*
    # while they're still together is exactly the premature disclosure the
    # system prompt's hard boundaries forbid. It only ever travels inside
    # the per-role "ended" event below, computed separately for each side.
    public_signal = {k: v for k, v in signal.items() if k != "triggered_by"} if signal else None

    # The sender's own message: said in the open room unless the room was
    # already paused when they sent it (in which case only checkin_target
    # could have sent it at all -- enforced by the caller), or unless the
    # classifier just flagged it as a real-time cut, in which case the
    # sender's own screen still shows it (they know what they typed; the
    # facilitator's own transcript has it too) but it's withheld from the
    # other role -- "only what's delivered to the other person is cut"
    # (joint-session-architecture.md).
    # Never attach `signal` to the sender's own echoed message: it reflects
    # the facilitator's read of what happens *after* this turn (may already
    # be paused_checkin), and the sender-echo goes out before the
    # facilitator's own reply is routed. Attaching it here would leak
    # checkin_target to the non-addressed role a beat before their "paused"
    # event arrives -- exactly the metadata the private check-in must not
    # expose. The signal only ever travels with the facilitator's reply,
    # which is already routed to the correct recipient(s) below.
    if sender_role is not None:
        if prev_state != "paused_checkin":
            for role in ("employee_a", "employee_b"):
                if cut and role != sender_role:
                    continue
                await send_to(session, role, {
                    "type": "message", "from": sender_role, "text": sender_text,
                    "private": False,
                })
        else:
            await send_to(session, sender_role, {
                "type": "message", "from": sender_role, "text": sender_text,
                "private": True,
            })

    reply_text = result.get("reply")
    audio_url = result.get("audio_url")

    if new_state == "paused_checkin" and checkin_target:
        await send_to(session, checkin_target, {
            "type": "message", "from": "facilitator", "text": reply_text,
            "private": True, "audio_url": audio_url, "signal": public_signal,
        })
        if prev_state != "paused_checkin":
            await send_to(session, OTHER_ROLE[checkin_target], {"type": "paused"})
    else:
        for role in ("employee_a", "employee_b"):
            await send_to(session, role, {
                "type": "message", "from": "facilitator", "text": reply_text,
                "private": False, "audio_url": audio_url, "signal": public_signal,
            })
        if prev_state == "paused_checkin" and prev_checkin_target:
            await send_to(session, OTHER_ROLE[prev_checkin_target], {"type": "resumed", "signal": public_signal})

        # The model is never actually instructed to emit session_state:
        # "ended" -- joint-session-architecture.md's state machine treats
        # WINDING_DOWN -> ENDED as something the orchestration layer
        # declares once employees are moved apart, not a model decision.
        # winding_down + ready_to_close is the real, already-guaranteed
        # signal that this turn's reply *is* the routine close (see the
        # system prompt's "same turn" rule); "ended" is kept as a literal
        # check too in case a future prompt revision emits it directly.
        room_closed = new_state == "ended" or (new_state == "winding_down" and signal.get("ready_to_close"))
        if room_closed and not session.ended:
            session.ended = True
            floor_category = signal.get("floor_category")
            for role in ("employee_a", "employee_b"):
                if not floor_category:
                    escalation = "none"
                elif triggered_by == role:
                    escalation = "own_conduct"
                elif triggered_by == OTHER_ROLE.get(role):
                    escalation = "other_party_conduct"
                else:
                    # A floor category fired but the model didn't name who
                    # -- shouldn't happen now that triggered_by is asked
                    # for, but fail toward disclosing less, not more.
                    escalation = "none"

                if not session.below_floor_pattern:
                    coaching_role = None
                elif session.pattern_shown_by == role:
                    coaching_role = "shown"
                elif session.pattern_shown_by == OTHER_ROLE.get(role):
                    coaching_role = "experienced"
                else:
                    # Flagged but the model didn't name who -- same
                    # fail-toward-disclosing-less choice as escalation above.
                    coaching_role = None

                await send_to(session, role, {
                    "type": "ended", "escalation": escalation,
                    "category": floor_category if escalation != "none" else None,
                    "coaching_pattern": session.below_floor_pattern if coaching_role else None,
                    "coaching_role": coaching_role,
                })

    session.state = signal or session.state


async def maybe_start(session: Session) -> None:
    if session.started or len(session.sockets) < 2:
        return
    session.started = True
    for r in ("employee_a", "employee_b"):
        await send_to(session, r, {"type": "thinking"})
    async with session.lock:
        session.conversation.append({"role": "user", "content": KICKOFF_TURN})
        result = facilitator_reply(session)
    await broadcast_result(session, sender_role=None, sender_text=None, result=result)


async def handle_reset(session: Session) -> None:
    session.conversation.clear()
    session.state = {}
    session.started = False
    session.ended = False
    for f in AUDIO_DIR.glob("*.m4a"):
        f.unlink(missing_ok=True)
    for role in ("employee_a", "employee_b"):
        await send_to(session, role, {"type": "reset"})
    await maybe_start(session)


@app.websocket("/ws/{code}/{role_slug}")
async def joint_session_ws(websocket: WebSocket, code: str, role_slug: str):
    role = ROLE_SLUGS.get(role_slug)
    if role is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    session = get_session(code)
    session.sockets[role] = websocket

    if len(session.sockets) < 2:
        await send_to(session, role, {"type": "waiting"})
    else:
        for r in ("employee_a", "employee_b"):
            await send_to(session, r, {"type": "ready"})
        await maybe_start(session)

    try:
        while True:
            payload = await websocket.receive_json()
            msg_type = payload.get("type")

            if msg_type == "reset":
                await handle_reset(session)
                continue

            if msg_type != "message":
                continue

            text = (payload.get("text") or "").strip()
            if not text:
                continue

            ip = websocket.client.host if websocket.client else "unknown"
            if ws_rate_limited(ip):
                await send_to(session, role, {"type": "error", "error": "too many messages -- slow down and try again shortly"})
                continue

            current_state = session.state.get("session_state", "active")
            checkin_target = session.state.get("checkin_target")
            next_speaker = session.state.get("next_speaker", "either")
            if current_state == "paused_checkin" and role != checkin_target:
                await send_to(session, role, {"type": "error", "error": "session is paused for the other participant"})
                continue
            if current_state != "paused_checkin" and next_speaker not in ("either", role):
                await send_to(session, role, {"type": "error", "error": "not your turn yet"})
                continue

            # Only the open room needs the real-time cut: a private
            # check-in already withholds everything from the other party,
            # so there's nothing left for the classifier to protect there.
            cut = False
            if CLASSIFIER_MODEL is not None and current_state != "paused_checkin":
                cut, scores = CLASSIFIER_MODEL.should_cut(text)
                logger.info("classifier scores for %s's message: cut=%s scores=%s", role, cut, scores)

            for r in ("employee_a", "employee_b"):
                await send_to(session, r, {"type": "thinking"})

            async with session.lock:
                session.conversation.append({"role": "user", "content": f"[{SPEAKER_LABEL[role]}]: {text}"})
                if cut:
                    session.conversation.append({
                        "role": "user",
                        "content": (
                            f"(Orchestration layer: a real-time cut was just triggered on {SPEAKER_LABEL[role]}'s "
                            "message above, before it reached the other participant. external_cut_reported=true. "
                            "Treat this as a tier-3 cut per your instructions: move to winding_down now.)"
                        ),
                    })
                result = facilitator_reply(session)
            await broadcast_result(session, sender_role=role, sender_text=text, result=result, cut=cut)
    except WebSocketDisconnect:
        if session.sockets.get(role) is websocket:
            del session.sockets[role]
        other = session.sockets.get(OTHER_ROLE[role])
        if other:
            await send_to(session, OTHER_ROLE[role], {"type": "waiting"})


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    path = AUDIO_DIR / filename
    if ".." in filename or not path.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    media_type = "audio/mpeg" if path.suffix == ".mp3" else "audio/mp4"
    return FileResponse(path, media_type=media_type)


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
