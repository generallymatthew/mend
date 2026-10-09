#!/usr/bin/env python3
"""
Local prototype of the Mend manager-app conversation: a manager thinking
through a specific conflict case involving their direct report(s), driven by
../facilitator-case-plan-system-prompt.md ("Thimble"). Text only, no voice --
see ../manager-coaching-app for that pattern if voice gets added here later.

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
import time
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-case-plan-system-prompt.md"
DB_FILE = ROOT / "cases.db"
MODEL = "claude-sonnet-5"
JOINT_SESSION_BASE_URL = os.environ.get("JOINT_SESSION_BASE_URL", "http://localhost:8421")

client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None


def load_system_prompt() -> str:
    text = SYSTEM_PROMPT_FILE.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {SYSTEM_PROMPT_FILE}")
    return match.group(1)


SYSTEM_PROMPT = load_system_prompt()

# In-memory conversation text per case id -- a prototype, not a persistence
# layer. See module docstring: only the anchor + plan (below, in SQLite)
# survive a restart.
CONVERSATIONS: dict[str, list[dict]] = {}


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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plan_steps (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(id),
                text TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                note TEXT,
                position INTEGER NOT NULL,
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
        }
        for r in rows
    ]


# --- App ---------------------------------------------------------------

app = FastAPI()


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


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
        {"role": m["role"], "content": m.get("visible", m["content"])}
        for m in CONVERSATIONS.get(case_id, [])
        if not m.get("hidden")
    ]
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
    return {"reply": visible, "signal": signal}


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
    return {"reply": result["reply"], "case": case}


MANAGING_UP_PROMPT = (
    "(System note, not from the manager: they tapped \"Draft update for your boss.\" "
    "Reply with ONLY the scripted upward-facing update itself, 2-4 sentences, nothing "
    "else before or after it -- no preamble like \"here's a draft.\")"
)


@app.post("/api/cases/{case_id}/managing-up")
async def managing_up(case_id: str):
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
        CONVERSATIONS[case_id].append({"role": "user", "content": MANAGING_UP_PROMPT, "hidden": True})
        result = facilitator_reply(case_id, conn)
        case = get_case(conn, case_id)
    return {"reply": result["reply"], "case": case}


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
    return {"reply": result["reply"], "case": case}


class PlanStepCreate(BaseModel):
    text: str


@app.post("/api/cases/{case_id}/plan")
async def add_plan_step(case_id: str, body: PlanStepCreate):
    with db() as conn:
        if get_case(conn, case_id) is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        row = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM plan_steps WHERE case_id = ?",
            (case_id,),
        ).fetchone()
        step_id = str(uuid.uuid4())
        now = time.time()
        conn.execute(
            "INSERT INTO plan_steps (id, case_id, text, done, note, position, created_at, updated_at) "
            "VALUES (?, ?, ?, 0, NULL, ?, ?, ?)",
            (step_id, case_id, body.text, row["next_pos"], now, now),
        )
        conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))
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
