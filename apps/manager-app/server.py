#!/usr/bin/env python3
"""
Local prototype of the Mend manager-app conversation: a manager thinking
through a specific conflict case involving their direct report(s), driven by
../facilitator-case-plan-system-prompt.md ("Thimble"). Text only, no voice --
see ../intake-app for the voice-memo + TTS pattern if voice gets added here
later.

Persistence is deliberately narrow, per manager-app/WORKFLOW.md: a case's
role-anonymized state anchor (tension_summary / last_action / next_action)
and its plan steps live in a local SQLite file (cases.db, git-ignored) and
survive a restart. The actual back-and-forth conversation text does not --
it lives only in this process's memory (`CONVERSATIONS`, keyed by case id),
same "nothing persisted" principle the rest of this repo's apps follow for
transcripts. Restarting the server loses the exact wording of a case's
conversation so far, but not the case itself: the anchor and plan are
re-seeded into a fresh conversation via a hidden context message the next
time that case is opened.

Run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...   # your own key, set in your shell/.env, never pasted into chat
    uvicorn server:app --reload --port 8426
"""
import json
import os
import re
import secrets
import sqlite3
import tempfile
import time
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-case-plan-system-prompt.md"
TONE_CHECK_SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-tone-check-system-prompt.md"
MEETING_STRATEGY_SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-meeting-strategy-system-prompt.md"
DB_FILE = ROOT / "cases.db"
MODEL = "claude-sonnet-5"
JOINT_SESSION_BASE_URL = os.environ.get("JOINT_SESSION_BASE_URL", "http://localhost:8421")

client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

# Push-to-talk dictation for text entries -- local Whisper only, one-shot
# (record, release, transcribe, drop text into the field; never auto-sent).
# Deliberately not the full live-conversation pipeline apps/intake-app
# built (VAD, partial/streaming transcripts, Deepgram): this just needs to
# turn one short clip into text. See intake-app/server.py's own
# get_whisper/transcribe_file for the pattern this mirrors.
WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL", "tiny.en")
WHISPER_CPU_THREADS = int(os.environ.get("WHISPER_CPU_THREADS", str(os.cpu_count() or 4)))
_whisper_model = None


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            WHISPER_MODEL_NAME, device="cpu", compute_type="int8", cpu_threads=WHISPER_CPU_THREADS,
        )
    return _whisper_model


def transcribe_file(path: str) -> str:
    """Synchronous, CPU-bound -- always call via run_in_threadpool from a
    route handler, never directly."""
    model = get_whisper()
    segments, _info = model.transcribe(path, beam_size=1)
    return " ".join(seg.text.strip() for seg in segments).strip()


def load_system_prompt(path: Path) -> str:
    text = path.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {path}")
    return match.group(1)


SYSTEM_PROMPT = load_system_prompt(SYSTEM_PROMPT_FILE)
TONE_CHECK_SYSTEM_PROMPT = load_system_prompt(TONE_CHECK_SYSTEM_PROMPT_FILE)
MEETING_STRATEGY_SYSTEM_PROMPT = load_system_prompt(MEETING_STRATEGY_SYSTEM_PROMPT_FILE)

# In-memory conversation text per case id -- a prototype, not a persistence
# layer. See module docstring: only the anchor + plan (below, in SQLite)
# survive a restart.
CONVERSATIONS: dict[str, list[dict]] = {}

# Same "chat text never persists" treatment, for meeting-strategy sessions.
# Only the final strategy_text (meeting_sessions table) survives a restart;
# the back-and-forth that produced it does not.
MEETING_CONVERSATIONS: dict[str, list[dict]] = {}

# In-memory per-case name roster (name.lower() -> {"name", "slot", "descriptor"}),
# same "never touches disk" treatment as CONVERSATIONS -- a real name the
# manager types is exactly the kind of thing that must never reach cases.db.
# Used only to redact the manager's own messages for display (see
# redact_names below); never consulted when building what the model itself
# sees, which still gets the raw conversation for real continuity.
ROSTERS: dict[str, dict[str, dict]] = {}


def merge_names(case_id: str, names: list[dict] | None) -> None:
    if not names:
        return
    roster = ROSTERS.setdefault(case_id, {})
    for entry in names:
        name = (entry.get("name") or "").strip()
        slot = entry.get("slot")
        if not name or not slot:
            continue
        key = name.lower()
        existing = roster.get(key)
        if existing:
            # Slot is sticky once assigned -- even if the model wobbles on
            # which letter a name gets later, the display stays consistent.
            if entry.get("descriptor"):
                existing["descriptor"] = entry["descriptor"]
        else:
            roster[key] = {"name": name, "slot": slot, "descriptor": entry.get("descriptor") or ""}


def redact_names(text: str, case_id: str) -> str:
    roster = ROSTERS.get(case_id)
    if not roster or not text:
        return text
    # Longest name first so e.g. "Dave" doesn't get replaced inside "Dave Jr."
    # before the longer form has a chance to match.
    for key in sorted(roster, key=len, reverse=True):
        info = roster[key]
        pattern = re.compile(r"\b" + re.escape(info["name"]) + r"\b", re.IGNORECASE)
        text = pattern.sub(f"Employee {info['slot']}", text)
    return text


def roster_for_case(case_id: str) -> dict:
    return {f"Employee {info['slot']}": info["descriptor"] for info in ROSTERS.get(case_id, {}).values()}


# --- Storage ---------------------------------------------------------------

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'open',
                stage TEXT,
                title TEXT,
                tension_summary TEXT,
                last_action TEXT,
                next_action TEXT,
                floor_triggered TEXT,
                handoff_ready INTEGER NOT NULL DEFAULT 0,
                handoff_code TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(cases)")}
        if "handoff_ready" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN handoff_ready INTEGER NOT NULL DEFAULT 0")
        if "handoff_code" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN handoff_code TEXT")
        if "title" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN title TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plan_steps (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(id),
                text TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                note TEXT,
                position INTEGER NOT NULL,
                added_by TEXT NOT NULL DEFAULT 'user',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        existing_step_cols = {row["name"] for row in conn.execute("PRAGMA table_info(plan_steps)")}
        if "added_by" not in existing_step_cols:
            conn.execute("ALTER TABLE plan_steps ADD COLUMN added_by TEXT NOT NULL DEFAULT 'user'")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meeting_sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                goal_summary TEXT,
                strategy_text TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)


init_db()


def case_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "status": row["status"],
        "stage": row["stage"],
        "title": row["title"],
        "tension_summary": row["tension_summary"],
        "last_action": row["last_action"],
        "next_action": row["next_action"],
        "floor_triggered": row["floor_triggered"],
        "handoff_ready": bool(row["handoff_ready"]),
        "handoff_code": row["handoff_code"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_case(conn: sqlite3.Connection, case_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    return case_row_to_dict(row) if row else None


def get_plan_steps(conn: sqlite3.Connection, case_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM plan_steps WHERE case_id = ? ORDER BY position ASC",
        (case_id,),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "text": r["text"],
            "done": bool(r["done"]),
            "note": r["note"],
            "position": r["position"],
            "added_by": r["added_by"],
        }
        for r in rows
    ]


def insert_plan_step(conn: sqlite3.Connection, case_id: str, text: str, added_by: str = "user") -> None:
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM plan_steps WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    now = time.time()
    conn.execute(
        "INSERT INTO plan_steps (id, case_id, text, done, note, position, added_by, created_at, updated_at) "
        "VALUES (?, ?, ?, 0, NULL, ?, ?, ?, ?)",
        (str(uuid.uuid4()), case_id, text, row["next_pos"], added_by, now, now),
    )
    conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))


def add_seam_plan_steps(conn: sqlite3.Connection, case_id: str, texts: list[str] | None) -> None:
    """Lets the facilitator itself contribute plan steps (see the signal's
    `plan_steps_to_add`), not just the manager typing into the "+ add a
    step" row. De-duplicated by exact trimmed/lowercased text against what's
    already on the case, since the model isn't shown the current plan list
    mid-conversation and can otherwise repeat a step it already added."""
    if not texts:
        return
    existing = {
        r["text"].strip().lower()
        for r in conn.execute("SELECT text FROM plan_steps WHERE case_id = ?", (case_id,))
    }
    for text in texts:
        text = (text or "").strip()
        if not text or text.lower() in existing:
            continue
        insert_plan_step(conn, case_id, text, added_by="seam")
        existing.add(text.lower())


# --- App ---------------------------------------------------------------

app = FastAPI()


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/sw.js")
async def service_worker():
    # Served at root, not /static/sw.js, so its default scope covers the
    # whole app -- a service worker's scope is its own path by default.
    return FileResponse(
        ROOT / "static" / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


# No explicit Cache-Control meant browsers could serve a stale cached copy
# of index.html/static/* on an ordinary reload instead of revalidating with
# the server -- this app changes multiple times a day right now (same bug,
# same fix already shipped in ../intake-app/server.py), so no caching at
# all is the right default during active development.
@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/cases")
async def list_cases():
    with db() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY updated_at DESC").fetchall()
        return [case_row_to_dict(r) for r in rows]


DEFAULT_PLAN_STEPS = ["Action item goes here", "Action item goes here"]


@app.post("/api/cases")
async def create_case():
    now = time.time()
    case_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO cases (id, status, stage, created_at, updated_at) VALUES (?, 'open', NULL, ?, ?)",
            (case_id, now, now),
        )
        for position, text in enumerate(DEFAULT_PLAN_STEPS):
            conn.execute(
                "INSERT INTO plan_steps (id, case_id, text, done, note, position, created_at, updated_at) "
                "VALUES (?, ?, ?, 0, NULL, ?, ?, ?)",
                (str(uuid.uuid4()), case_id, text, position, now, now),
            )
        case = get_case(conn, case_id)
    CONVERSATIONS[case_id] = []
    return case


@app.get("/api/cases/{case_id}")
async def get_case_detail(case_id: str):
    with db() as conn:
        case = get_case(conn, case_id)
        if case is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        plan = get_plan_steps(conn, case_id)
    messages = [
        {"role": m["role"], "content": redact_names(m.get("visible", m["content"]), case_id)}
        for m in CONVERSATIONS.get(case_id, [])
        if not m.get("hidden")
    ]
    case["roster"] = roster_for_case(case_id)
    return {"case": case, "plan": plan, "messages": messages}


class StatusUpdate(BaseModel):
    status: str


@app.patch("/api/cases/{case_id}")
async def update_case_status(case_id: str, body: StatusUpdate):
    if body.status not in ("open", "closed"):
        return JSONResponse({"error": "status must be 'open' or 'closed'"}, status_code=400)
    with db() as conn:
        if get_case(conn, case_id) is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        conn.execute(
            "UPDATE cases SET status = ?, updated_at = ? WHERE id = ?",
            (body.status, time.time(), case_id),
        )
        return get_case(conn, case_id)


def strip_signal(reply_text: str) -> tuple[str, dict | None]:
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    if not match:
        return visible, None
    try:
        return visible, json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return visible, None


def seed_context_message(case: dict, plan: list[dict]) -> str | None:
    """A hidden user-role turn reminding the model what's on file for this
    case, used when a conversation starts fresh (new case, or this case's
    in-memory history was lost to a server restart)."""
    parts = []
    if case["tension_summary"]:
        parts.append(f"The tension so far: {case['tension_summary']}")
    if case["last_action"]:
        parts.append(f"Last action taken: {case['last_action']}")
    if case["next_action"]:
        parts.append(f"Agreed next action: {case['next_action']}")
    if plan:
        step_lines = "\n".join(
            f"- [{'done' if s['done'] else 'pending'}] {s['text']}" + (f" (note: {s['note']})" if s["note"] else "")
            for s in plan
        )
        parts.append(f"Plan steps on file:\n{step_lines}")
    if not parts:
        return None
    return (
        "(System note, not from the manager: resuming an existing case. "
        "Here's what's on file so far, from the last session -- pick back up naturally, "
        "don't re-ask things already established here.)\n\n" + "\n".join(parts)
    )


def facilitator_reply(case_id: str, conn: sqlite3.Connection) -> dict:
    """Assumes the latest turn just appended to CONVERSATIONS[case_id] is the
    user's. On failure, rolls that turn back off so the conversation always
    ends on an assistant turn (Anthropic's API rejects consecutive same-role
    turns)."""
    conversation = CONVERSATIONS[case_id]
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set in this shell)", "signal": None}
    visible_history = [{"role": m["role"], "content": m["content"]} for m in conversation]
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=visible_history,
        )
    except Exception as e:
        conversation.pop()
        return {"reply": f"(server error calling Claude: {e})", "signal": None}
    raw = "".join(block.text for block in response.content if block.type == "text")
    if not raw:
        conversation.pop()
        return {"reply": "(server error: empty response from Claude, try again)", "signal": None}
    visible, signal = strip_signal(raw)
    conversation.append({"role": "assistant", "content": raw, "visible": visible, "hidden": False})

    if signal:
        fields = {}
        for key in ("stage", "tension_summary", "last_action", "next_action", "floor_triggered"):
            if signal.get(key) is not None:
                fields[key] = signal[key]
        if signal.get("case_title"):
            fields["title"] = signal["case_title"]
        if signal.get("handoff_ready") is not None:
            fields["handoff_ready"] = int(bool(signal["handoff_ready"]))
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE cases SET {set_clause}, updated_at = ? WHERE id = ?",
                (*fields.values(), time.time(), case_id),
            )
        else:
            conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (time.time(), case_id))
        merge_names(case_id, signal.get("names"))
        add_seam_plan_steps(conn, case_id, signal.get("plan_steps_to_add"))
    # Defense in depth: the prompt already tells the model never to use a
    # real name in its own reply text, but redact here too in case a name
    # slips through (as it occasionally does) -- same safety net applied to
    # historical messages on reload (see get_case_detail).
    return {"reply": redact_names(visible, case_id), "signal": signal}


class Message(BaseModel):
    content: str


@app.post("/api/cases/{case_id}/messages")
async def post_message(case_id: str, body: Message):
    with db() as conn:
        case = get_case(conn, case_id)
        if case is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        plan = get_plan_steps(conn, case_id)

        if case_id not in CONVERSATIONS:
            CONVERSATIONS[case_id] = []
            seed = seed_context_message(case, plan)
            if seed:
                CONVERSATIONS[case_id].append({"role": "user", "content": seed, "hidden": True})
                CONVERSATIONS[case_id].append({
                    "role": "assistant",
                    "content": "Got it, picking this back up.",
                    "hidden": True,
                })

        CONVERSATIONS[case_id].append({"role": "user", "content": body.content, "hidden": False})
        result = facilitator_reply(case_id, conn)
        case = get_case(conn, case_id)
        case["roster"] = roster_for_case(case_id)
        plan = get_plan_steps(conn, case_id)
    return {
        "reply": result["reply"],
        "case": case,
        "plan": plan,
        "user_message_redacted": redact_names(body.content, case_id),
    }


@app.post("/api/cases/{case_id}/handoff")
async def create_handoff(case_id: str):
    """Mints a fresh joint-session-app room code for this case's peer hand-off.
    Carries no case context across -- per WORKFLOW.md, the peer session starts
    with zero knowledge of the manager's notes, just two anonymous role links.
    Idempotent per case: calling it again returns the same links rather than
    minting a new room each time the manager reopens the banner."""
    with db() as conn:
        case = get_case(conn, case_id)
        if case is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        code = case["handoff_code"]
        if not code:
            code = secrets.token_urlsafe(8)
            conn.execute(
                "UPDATE cases SET handoff_code = ?, updated_at = ? WHERE id = ?",
                (code, time.time(), case_id),
            )
    return {
        "role_a_url": f"{JOINT_SESSION_BASE_URL}/?code={code}&role=a",
        "role_b_url": f"{JOINT_SESSION_BASE_URL}/?code={code}&role=b",
    }


@app.post("/api/cases/{case_id}/start")
async def start_case(case_id: str):
    """Kicks off a brand-new case's first message. Only meaningful when the
    case has no messages yet; harmless (just gets a reply) otherwise."""
    with db() as conn:
        case = get_case(conn, case_id)
        if case is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        plan = get_plan_steps(conn, case_id)
        if case_id not in CONVERSATIONS:
            CONVERSATIONS[case_id] = []
            seed = seed_context_message(case, plan)
            if seed:
                CONVERSATIONS[case_id].append({"role": "user", "content": seed, "hidden": True})
                CONVERSATIONS[case_id].append({
                    "role": "assistant",
                    "content": "Got it, picking this back up.",
                    "hidden": True,
                })
        CONVERSATIONS[case_id].append({
            "role": "user",
            "content": "(The manager just opened this case. Begin with your opening line.)",
            "hidden": True,
        })
        result = facilitator_reply(case_id, conn)
        case = get_case(conn, case_id)
        case["roster"] = roster_for_case(case_id)
        plan = get_plan_steps(conn, case_id)
    return {"reply": result["reply"], "case": case, "plan": plan}


class PlanStepCreate(BaseModel):
    text: str


@app.post("/api/cases/{case_id}/plan")
async def add_plan_step(case_id: str, body: PlanStepCreate):
    with db() as conn:
        if get_case(conn, case_id) is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        insert_plan_step(conn, case_id, body.text, added_by="user")
        return get_plan_steps(conn, case_id)


class PlanStepUpdate(BaseModel):
    text: str | None = None
    done: bool | None = None
    note: str | None = None


@app.patch("/api/cases/{case_id}/plan/{step_id}")
async def update_plan_step(case_id: str, step_id: str, body: PlanStepUpdate):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM plan_steps WHERE id = ? AND case_id = ?", (step_id, case_id)
        ).fetchone()
        if row is None:
            return JSONResponse({"error": "no such plan step"}, status_code=404)
        fields = {}
        if body.text is not None:
            fields["text"] = body.text
        if body.done is not None:
            fields["done"] = int(body.done)
        if body.note is not None:
            fields["note"] = body.note
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            now = time.time()
            conn.execute(
                f"UPDATE plan_steps SET {set_clause}, updated_at = ? WHERE id = ?",
                (*fields.values(), now, step_id),
            )
            conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))
        return get_plan_steps(conn, case_id)


@app.delete("/api/cases/{case_id}/plan/{step_id}")
async def delete_plan_step(case_id: str, step_id: str):
    with db() as conn:
        conn.execute("DELETE FROM plan_steps WHERE id = ? AND case_id = ?", (step_id, case_id))
        conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (time.time(), case_id))
        return get_plan_steps(conn, case_id)


class ToneCheckRequest(BaseModel):
    content: str


def strip_tone_check(reply_text: str) -> dict | None:
    match = re.search(r"<tone_check>(.*?)</tone_check>", reply_text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None


@app.post("/api/tone-check")
async def tone_check(body: ToneCheckRequest):
    """Stateless, one-shot: no case, no persistence, nothing written to
    cases.db. The manager pastes a draft, gets feedback plus a rewrite
    back; neither the draft nor the response is stored anywhere."""
    if not body.content.strip():
        return JSONResponse({"error": "content is required"}, status_code=400)
    if client is None:
        return JSONResponse({"error": "ANTHROPIC_API_KEY is not set in this shell"}, status_code=500)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=TONE_CHECK_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": body.content}],
        )
    except Exception as e:
        return JSONResponse({"error": f"error calling Claude: {e}"}, status_code=502)
    raw = "".join(block.text for block in response.content if block.type == "text")
    result = strip_tone_check(raw)
    if result is None or "feedback" not in result or "rewrite" not in result:
        return JSONResponse({"error": "couldn't parse a tone-check response, try again"}, status_code=502)
    return {"feedback": result["feedback"], "rewrite": result["rewrite"]}


@app.post("/api/voice")
async def post_voice(file: UploadFile):
    """Transcription only, no persistence: the clip is written to a temp
    file for the length of this request and discarded after. Returns the
    transcript text for the frontend to drop into whichever text field the
    manager was dictating into; never calls the facilitator itself."""
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=True) as tmp:
        body = await file.read()
        tmp.write(body)
        tmp.flush()
        try:
            transcript = await run_in_threadpool(transcribe_file, tmp.name)
        except Exception:
            transcript = ""
    if not transcript:
        return JSONResponse({"error": "couldn't transcribe audio"}, status_code=400)
    return {"transcript": transcript}


# --- Meeting Strategy --------------------------------------------------

def meeting_session_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "goal_summary": row["goal_summary"],
        "strategy_text": row["strategy_text"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_meeting_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM meeting_sessions WHERE id = ?", (session_id,)).fetchone()
    return meeting_session_row_to_dict(row) if row else None


def strip_meeting_signal(reply_text: str) -> tuple[str, dict | None]:
    match = re.search(r"<meeting_strategy_signal>(.*?)</meeting_strategy_signal>", reply_text, re.S)
    visible = re.sub(r"<meeting_strategy_signal>.*?</meeting_strategy_signal>", "", reply_text, flags=re.S).strip()
    if not match:
        return visible, None
    try:
        return visible, json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return visible, None


@app.get("/api/meeting-sessions")
async def list_meeting_sessions():
    with db() as conn:
        rows = conn.execute("SELECT * FROM meeting_sessions ORDER BY updated_at DESC").fetchall()
        return [meeting_session_row_to_dict(r) for r in rows]


@app.post("/api/meeting-sessions")
async def create_meeting_session():
    now = time.time()
    session_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO meeting_sessions (id, title, goal_summary, strategy_text, created_at, updated_at) "
            "VALUES (?, NULL, NULL, NULL, ?, ?)",
            (session_id, now, now),
        )
        session = get_meeting_session(conn, session_id)
    MEETING_CONVERSATIONS[session_id] = []
    return session


@app.get("/api/meeting-sessions/{session_id}")
async def get_meeting_session_detail(session_id: str):
    with db() as conn:
        session = get_meeting_session(conn, session_id)
        if session is None:
            return JSONResponse({"error": "no such meeting session"}, status_code=404)
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in MEETING_CONVERSATIONS.get(session_id, [])
        if not m.get("hidden")
    ]
    return {"session": session, "messages": messages}


def meeting_strategy_reply(session_id: str, conn: sqlite3.Connection) -> dict:
    """Same shape as facilitator_reply, for the meeting-strategy prompt and
    conversation store instead of the case-plan ones."""
    conversation = MEETING_CONVERSATIONS[session_id]
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set in this shell)", "signal": None}
    visible_history = [{"role": m["role"], "content": m["content"]} for m in conversation]
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=MEETING_STRATEGY_SYSTEM_PROMPT,
            messages=visible_history,
        )
    except Exception as e:
        conversation.pop()
        return {"reply": f"(server error calling Claude: {e})", "signal": None}
    raw = "".join(block.text for block in response.content if block.type == "text")
    if not raw:
        conversation.pop()
        return {"reply": "(server error: empty response from Claude, try again)", "signal": None}
    visible, signal = strip_meeting_signal(raw)
    conversation.append({"role": "assistant", "content": raw, "hidden": False})
    return {"reply": visible, "signal": signal}


@app.post("/api/meeting-sessions/{session_id}/messages")
async def post_meeting_message(session_id: str, body: Message):
    with db() as conn:
        session = get_meeting_session(conn, session_id)
        if session is None:
            return JSONResponse({"error": "no such meeting session"}, status_code=404)

        if session_id not in MEETING_CONVERSATIONS:
            MEETING_CONVERSATIONS[session_id] = []

        MEETING_CONVERSATIONS[session_id].append({"role": "user", "content": body.content, "hidden": False})
        result = meeting_strategy_reply(session_id, conn)

        signal = result["signal"]
        if signal:
            fields = {}
            if signal.get("title"):
                fields["title"] = signal["title"]
            if signal.get("goal_summary"):
                fields["goal_summary"] = signal["goal_summary"]
            if signal.get("strategy_ready") and signal.get("strategy_text"):
                fields["strategy_text"] = signal["strategy_text"]
            if fields:
                set_clause = ", ".join(f"{k} = ?" for k in fields)
                conn.execute(
                    f"UPDATE meeting_sessions SET {set_clause}, updated_at = ? WHERE id = ?",
                    (*fields.values(), time.time(), session_id),
                )
            else:
                conn.execute("UPDATE meeting_sessions SET updated_at = ? WHERE id = ?", (time.time(), session_id))
        session = get_meeting_session(conn, session_id)
    return {"reply": result["reply"], "session": session}
