#!/usr/bin/env python3
"""
Local prototype of the Mend seam conversation: a manager thinking
through a specific conflict case involving their direct report(s), driven by
../facilitator-case-plan-system-prompt.md ("Thimble"). Text only, no voice --
see ../thimble for the voice-memo + TTS pattern if voice gets added here
later.

Persistence is deliberately narrow, per seam/WORKFLOW.md: a case's
role-anonymized state anchor (tension_summary / last_action / next_action)
and its plan steps live in a local SQLite file (cases.db, git-ignored) and
survive a restart. The actual back-and-forth conversation text does not --
it lives only in this process's memory (`CONVERSATIONS`, keyed by case id),
same "nothing persisted" principle the rest of this repo's apps follow for
transcripts. Restarting the server loses the exact wording of a case's
conversation so far, but not the case itself: the anchor and plan are
re-seeded into a fresh conversation via a hidden context message the next
time that case is opened.

With SEAM_TEST_MODE=true, that case/plan storage moves off disk entirely:
the "cases.db" above becomes a SQLite database that lives only in this
process's RAM (a shared-cache `:memory:` database), so restarting the
process -- or a redeploy -- drops every case and plan step along with the
conversation text. Used for the tester round, where testers are told
nothing they enter is kept.

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
import traceback
import uuid
from pathlib import Path

import gspread
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google.oauth2.service_account import Credentials as GoogleCredentials
from pydantic import BaseModel

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-case-plan-system-prompt.md"
COACHING_SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-manager-coaching-system-prompt.md"
TONE_CHECK_SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-tone-check-system-prompt.md"
MEETING_STRATEGY_SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-meeting-strategy-system-prompt.md"
DB_FILE = ROOT / "cases.db"
TEST_MODE = os.environ.get("SEAM_TEST_MODE", "").lower() in ("1", "true", "yes")
# Shared-cache in-memory DB: every sqlite3.connect() to this name within the
# process sees the same data, as long as at least one connection stays open
# (hence _TEST_DB_KEEPALIVE below) -- nothing ever touches disk.
TEST_DB_URI = "file:seam_test_db?mode=memory&cache=shared"
MODEL = "claude-sonnet-5"
JOINT_SESSION_BASE_URL = os.environ.get("JOINT_SESSION_BASE_URL", "http://localhost:8421")

client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

# Push-to-talk dictation for text entries -- local Whisper only, one-shot
# (record, release, transcribe, drop text into the field; never auto-sent).
# Deliberately not the full live-conversation pipeline apps/thimble
# built (VAD, partial/streaming transcripts, Deepgram): this just needs to
# turn one short clip into text. See thimble/server.py's own
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
COACHING_SYSTEM_PROMPT = load_system_prompt(COACHING_SYSTEM_PROMPT_FILE)
TONE_CHECK_SYSTEM_PROMPT = load_system_prompt(TONE_CHECK_SYSTEM_PROMPT_FILE)
MEETING_STRATEGY_SYSTEM_PROMPT = load_system_prompt(MEETING_STRATEGY_SYSTEM_PROMPT_FILE)

# Which system prompt a "cases" row's conversation uses, keyed by its kind
# column -- "conflict" rows (adjacent dispute, case-plan prompt, can offer a
# peer hand-off) and "coaching" rows (manager rehearsing a conversation with
# their own report, manager-coaching prompt, never a hand-off) share the same
# table/endpoints/control-block schema, they just load different personas.
CASE_SYSTEM_PROMPTS = {"conflict": SYSTEM_PROMPT, "coaching": COACHING_SYSTEM_PROMPT}

# A router, not a facilitator persona, so it stays inline here rather than
# in its own reviewable prompt file like the ones above.
CLASSIFY_SYSTEM_PROMPT = """Decide which one of four kinds of help the manager is asking for, from what they've said so far. Reply with exactly one lowercase word, nothing else:
conflict -- tension or friction involving their direct report and someone else (a peer, another team, or another of their reports) -- the manager is adjudicating or thinking through a dispute between other people, not delivering feedback themselves.
coaching -- the manager preparing for or rehearsing a hard performance or conduct conversation THEY need to have with their own direct report -- they themselves are about to deliver the difficult feedback, not mediate between others.
meeting -- preparing strategy or approach for a meeting they're walking into.
written -- help answering or drafting a specific message, email, or reply.
unsure -- genuinely can't tell yet from what they've said."""

# In-memory conversation text per case id -- a prototype, not a persistence
# layer. See module docstring: only the anchor + plan (below, in SQLite)
# survive a restart.
CONVERSATIONS: dict[str, list[dict]] = {}

# Same "chat text never persists" treatment, for meeting-strategy sessions.
# Only the final strategy_text (meeting_sessions table) survives a restart;
# the back-and-forth that produced it does not.
MEETING_CONVERSATIONS: dict[str, list[dict]] = {}

# Same treatment again, for written (tone-check) sessions. Only a short
# title/preview (written_sessions table) survives a restart; the drafts and
# feedback that produced them do not. A session's row isn't written until
# its first exchange completes -- see post_written_message -- so a draft
# abandoned before any reply never shows up anywhere.
WRITTEN_CONVERSATIONS: dict[str, list[dict]] = {}

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
    if TEST_MODE:
        conn = sqlite3.connect(TEST_DB_URI, uri=True)
    else:
        conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# Keeps the shared-cache in-memory DB alive between requests -- if the last
# connection to it closed, the data would vanish. Never closed on purpose.
_TEST_DB_KEEPALIVE = db() if TEST_MODE else None


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'open',
                kind TEXT NOT NULL DEFAULT 'conflict',
                stage TEXT,
                title TEXT,
                tension_summary TEXT,
                last_action TEXT,
                next_action TEXT,
                floor_triggered TEXT,
                handoff_ready INTEGER NOT NULL DEFAULT 0,
                handoff_code TEXT,
                closing_check_result TEXT,
                closing_check_want TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(cases)")}
        if "kind" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN kind TEXT NOT NULL DEFAULT 'conflict'")
        if "handoff_ready" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN handoff_ready INTEGER NOT NULL DEFAULT 0")
        if "handoff_code" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN handoff_code TEXT")
        if "title" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN title TEXT")
        if "closing_check_result" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN closing_check_result TEXT")
        if "closing_check_want" not in existing_cols:
            conn.execute("ALTER TABLE cases ADD COLUMN closing_check_want TEXT")
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS written_sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                preview TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                event_type TEXT NOT NULL,
                turn_number INTEGER,
                ts REAL NOT NULL
            )
        """)


init_db()


def log_event(conn: sqlite3.Connection, session_id: str, mode: str, event_type: str, turn_number: int | None = None) -> None:
    """Pilot-eval instrumentation: one row per session_start/turn/output_generated.
    See docs/pitch-strategy/25_SEAM_SOLO_MANAGER_COHORT_AND_OUTREACH_STRATEGY.md for
    the metrics (turn count, duration, completion rate, re-open rate) this feeds."""
    conn.execute(
        "INSERT INTO session_events (session_id, mode, event_type, turn_number, ts) VALUES (?, ?, ?, ?, ?)",
        (session_id, mode, event_type, turn_number, time.time()),
    )


def case_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "status": row["status"],
        "kind": row["kind"],
        "stage": row["stage"],
        "title": row["title"],
        "tension_summary": row["tension_summary"],
        "last_action": row["last_action"],
        "next_action": row["next_action"],
        "floor_triggered": row["floor_triggered"],
        "handoff_ready": bool(row["handoff_ready"]),
        "handoff_code": row["handoff_code"],
        "closing_check_result": row["closing_check_result"],
        "closing_check_want": row["closing_check_want"],
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


@app.exception_handler(Exception)
async def log_unhandled_exception(request: Request, exc: Exception):
    # Render only captures stdout/stderr as logs (see deploy/start.sh) -- an
    # unhandled exception here would otherwise surface to a tester as a bare
    # 500 with zero trace anywhere a human could find it.
    print(f"[error] unhandled exception on {request.method} {request.url.path}: {exc!r}", flush=True)
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "internal error"})


@app.get("/health")
async def health():
    checks = {"anthropic_key": client is not None}
    try:
        with db() as conn:
            conn.execute("SELECT 1")
        checks["db"] = True
    except Exception as e:
        checks["db"] = False
        checks["db_error"] = str(e)
    healthy = checks["anthropic_key"] and checks["db"]
    return JSONResponse(status_code=200 if healthy else 503, content={"ok": healthy, **checks})


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/survey")
async def survey_page():
    return FileResponse(ROOT / "static" / "survey.html")


@app.get("/survey/post")
async def survey_post_page():
    return FileResponse(ROOT / "static" / "survey-after.html")


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

# Serves the repo-root "Mend Pitch" explainer videos (self-contained
# dc.html docs, same ones pitch/microsite/videos.html already iframes) so
# "Create peer session" can show the Session Opening video in a modal
# instead of generating real handoff links -- manager test builds only
# have one tester, so the actual two-person joint session can't run.
app.mount("/pitch-assets", StaticFiles(directory=ROOT.parent.parent / "Mend Pitch"), name="pitch-assets")


# No explicit Cache-Control meant browsers could serve a stale cached copy
# of index.html/static/* on an ordinary reload instead of revalidating with
# the server -- this app changes multiple times a day right now (same bug,
# same fix already shipped in ../thimble/server.py), so no caching at
# all is the right default during active development.
@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in ("/", "/survey", "/survey/post") or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store"
    return response


class ClassifyRequest(BaseModel):
    messages: list[str]


@app.post("/api/classify")
async def classify(body: ClassifyRequest):
    """Stateless router for the unified composer: given the manager's
    pending opening turn(s), before any real case/meeting/written session
    exists yet, decide which of the three it is. Never touches CONVERSATIONS
    or the DB -- the caller creates the real session itself once it has a
    concrete answer and replays these same turns into it for real."""
    if client is None:
        return {"type": "unsure"}
    try:
        response = client.messages.create(
            model=MODEL,
            # Not just "conflict"/"meeting"/"written"/"unsure" worth of
            # tokens -- claude-sonnet-5 emits a thinking block ahead of the
            # one-word answer, and 10 tokens was consumed entirely by that
            # preamble, leaving no text block at all (every call silently
            # fell through to "unsure" below, regardless of input).
            max_tokens=300,
            system=CLASSIFY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n\n".join(body.messages)}],
        )
    except Exception:
        return {"type": "unsure"}
    raw = "".join(block.text for block in response.content if block.type == "text").strip().lower()
    if raw not in ("conflict", "coaching", "meeting", "written"):
        return {"type": "unsure"}
    return {"type": raw}


@app.get("/api/cases")
async def list_cases():
    with db() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY updated_at DESC").fetchall()
        return [case_row_to_dict(r) for r in rows]


class CaseCreate(BaseModel):
    kind: str = "conflict"


@app.post("/api/cases")
async def create_case(body: CaseCreate = CaseCreate()):
    if body.kind not in CASE_SYSTEM_PROMPTS:
        return JSONResponse({"error": f"kind must be one of {sorted(CASE_SYSTEM_PROMPTS)}"}, status_code=400)
    now = time.time()
    case_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO cases (id, status, kind, stage, created_at, updated_at) VALUES (?, 'open', ?, NULL, ?, ?)",
            (case_id, body.kind, now, now),
        )
        log_event(conn, case_id, body.kind, "session_start")
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


def facilitator_reply(case_id: str, conn: sqlite3.Connection, kind: str = "conflict") -> dict:
    """Assumes the latest turn just appended to CONVERSATIONS[case_id] is the
    user's. On failure, rolls that turn back off so the conversation always
    ends on an assistant turn (Anthropic's API rejects consecutive same-role
    turns). `kind` selects which of CASE_SYSTEM_PROMPTS drives this case's
    conversation -- same control-block schema either way, see
    CASE_SYSTEM_PROMPTS' own comment."""
    conversation = CONVERSATIONS[case_id]
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set in this shell)", "signal": None}
    visible_history = [{"role": m["role"], "content": m["content"]} for m in conversation]
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=CASE_SYSTEM_PROMPTS.get(kind, SYSTEM_PROMPT),
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
        for key in ("stage", "tension_summary", "last_action", "next_action", "floor_triggered", "closing_check_result", "closing_check_want"):
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
        turn_number = sum(1 for m in CONVERSATIONS[case_id] if m["role"] == "user" and not m.get("hidden"))
        log_event(conn, case_id, case["kind"], "turn", turn_number)
        result = facilitator_reply(case_id, conn, case["kind"])
        case = get_case(conn, case_id)
        if case["handoff_ready"]:
            log_event(conn, case_id, case["kind"], "output_generated", turn_number)
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
    """Mints a fresh suture room code for this case's peer hand-off.
    Carries no case context across -- per WORKFLOW.md, the peer session starts
    with zero knowledge of the manager's notes, just two anonymous role links.
    Idempotent per case: calling it again returns the same links rather than
    minting a new room each time the manager reopens the banner."""
    with db() as conn:
        case = get_case(conn, case_id)
        if case is None:
            return JSONResponse({"error": "no such case"}, status_code=404)
        if case["kind"] != "conflict":
            return JSONResponse({"error": "hand-off only applies to conflict cases"}, status_code=400)
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
        result = facilitator_reply(case_id, conn, case["kind"])
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


def strip_tone_check(reply_text: str) -> dict | None:
    match = re.search(r"<tone_check>(.*?)</tone_check>", reply_text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None


def truncate(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


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
        log_event(conn, session_id, "meeting", "session_start")
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
        turn_number = sum(1 for m in MEETING_CONVERSATIONS[session_id] if m["role"] == "user" and not m.get("hidden"))
        log_event(conn, session_id, "meeting", "turn", turn_number)
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
                log_event(conn, session_id, "meeting", "output_generated", turn_number)
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


# --- Written (tone-check, chat) -----------------------------------------
#
# A chat UI like Conflicts/Meetings, not the old single draft-box-plus-card:
# the manager pastes a draft, Thimble replies in the same thread, and they
# can paste another one right after. Two things set it apart from those two:
#
# - Launch state is always a blank, ready-to-type thread (see
#   createWrittenSession in index.html, called the moment the section is
#   first opened) -- never the last session reopened, for speed.
# - A session's row in written_sessions isn't created until its first
#   exchange actually completes (see post_written_message below), and
#   list_written_sessions only returns rows with a preview. A draft typed
#   and abandoned never becomes a list item; one that got a reply does.

def written_session_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "preview": row["preview"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_written_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM written_sessions WHERE id = ?", (session_id,)).fetchone()
    return written_session_row_to_dict(row) if row else None


@app.get("/api/written-sessions")
async def list_written_sessions():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM written_sessions WHERE preview IS NOT NULL ORDER BY updated_at DESC"
        ).fetchall()
        return [written_session_row_to_dict(r) for r in rows]


@app.post("/api/written-sessions")
async def create_written_session():
    now = time.time()
    session_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO written_sessions (id, title, preview, created_at, updated_at) VALUES (?, NULL, NULL, ?, ?)",
            (session_id, now, now),
        )
        log_event(conn, session_id, "written", "session_start")
        session = get_written_session(conn, session_id)
    WRITTEN_CONVERSATIONS[session_id] = []
    return session


@app.get("/api/written-sessions/{session_id}")
async def get_written_session_detail(session_id: str):
    with db() as conn:
        session = get_written_session(conn, session_id)
        if session is None:
            return JSONResponse({"error": "no such written session"}, status_code=404)
    messages = [
        {"role": m["role"], "content": m.get("visible", m["content"])}
        for m in WRITTEN_CONVERSATIONS.get(session_id, [])
        if not m.get("hidden")
    ]
    return {"session": session, "messages": messages}


def written_facilitator_reply(session_id: str, conn: sqlite3.Connection) -> dict:
    """Same shape as facilitator_reply/meeting_strategy_reply, for the
    tone-check prompt. Each user turn is still graded as its own draft per
    TONE_CHECK_SYSTEM_PROMPT (it always answers in the same <tone_check>
    block), but now sits in a real back-and-forth thread instead of a
    single stateless call."""
    conversation = WRITTEN_CONVERSATIONS[session_id]
    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set in this shell)", "feedback": None}
    visible_history = [{"role": m["role"], "content": m["content"]} for m in conversation]
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=TONE_CHECK_SYSTEM_PROMPT,
            messages=visible_history,
        )
    except Exception as e:
        conversation.pop()
        return {"reply": f"(server error calling Claude: {e})", "feedback": None}
    raw = "".join(block.text for block in response.content if block.type == "text")
    if not raw:
        conversation.pop()
        return {"reply": "(server error: empty response from Claude, try again)", "feedback": None}
    result = strip_tone_check(raw)
    if result is None or "feedback" not in result or "rewrite" not in result:
        conversation.pop()
        return {"reply": "(couldn't parse a tone-check response, try again)", "feedback": None}
    display = f"{result['feedback']}\n\nTry this instead:\n{result['rewrite']}"
    conversation.append({"role": "assistant", "content": raw, "visible": display, "hidden": False})
    return {"reply": display, "feedback": result["feedback"]}


@app.post("/api/written-sessions/{session_id}/messages")
async def post_written_message(session_id: str, body: Message):
    with db() as conn:
        session = get_written_session(conn, session_id)
        if session is None:
            return JSONResponse({"error": "no such written session"}, status_code=404)
        if session_id not in WRITTEN_CONVERSATIONS:
            WRITTEN_CONVERSATIONS[session_id] = []
        WRITTEN_CONVERSATIONS[session_id].append({"role": "user", "content": body.content, "hidden": False})
        turn_number = sum(1 for m in WRITTEN_CONVERSATIONS[session_id] if m["role"] == "user" and not m.get("hidden"))
        log_event(conn, session_id, "written", "turn", turn_number)
        result = written_facilitator_reply(session_id, conn)
        if result["feedback"] is not None:
            fields = {"preview": truncate(result["feedback"], 70)}
            if not session["title"]:
                fields["title"] = truncate(body.content, 50)
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE written_sessions SET {set_clause}, updated_at = ? WHERE id = ?",
                (*fields.values(), time.time(), session_id),
            )
        session = get_written_session(conn, session_id)
    return {"reply": result["reply"], "session": session}


# Two surveys, deliberately separate instruments, not one form reused twice:
# the pre-use one (static/survey.html, below) is a discovery/outreach
# instrument sent to prospective manager testers to gauge their existing
# conflict-management pressures and interest in Seam's 3 offerings BEFORE
# they've used the app at all -- answers have to be uncontaminated by
# having just seen Seam work, or "how confident do you feel handling this"
# would be measuring the demo, not their actual baseline. The second one
# (static/survey-after.html, /api/survey/post further down) is post-use
# feedback on a specific case they just worked, the Seam equivalent of
# ../thimble's /api/survey ("how did that go"). Same "nothing about a real
# case/conversation is recorded" boundary as the rest of this file applies
# to both -- these are the tester's own opinions, not case content.
#
# Shares the same Google Sheet (GOOGLE_SHEET_ID) as ../thimble's survey, on
# its own "Seam" worksheet tab rather than a separate spreadsheet, per
# explicit request -- same service account
# (GOOGLE_SERVICE_ACCOUNT_JSON), copied into this app's own .env from
# ../thimble/.env since each app loads its env independently. In
# production, Render's dashboard needs both vars added to Seam's own
# service the same way they're already set on Thimble's -- not something
# this session can do from here.
SURVEY_FILE = ROOT / "survey_responses.jsonl"
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
SURVEY_WORKSHEET_TITLE = "Seam"
SURVEY_SHEET_HEADER = [
    "Timestamp", "Conflict frequency", "First move", "Confidence (1-5)",
    "Feels judged", "Pressure source", "How managed",
    "Useful: Conflicts (1-5)", "Would use: Conflicts",
    "Useful: Written (1-5)", "Would use: Written",
    "Useful: Meetings (1-5)", "Would use: Meetings",
    "Team size", "Overall interest (1-5)", "Email", "Comments",
]
_sheet = None
_sheet_init_failed = False


def get_survey_sheet():
    """Returns the "Seam" worksheet of GOOGLE_SHEET_ID (the same spreadsheet
    ../thimble's survey writes to, its own tab), authenticated via the same
    service account. Creates the worksheet with its header row on first use
    if it doesn't exist yet. Returns None, logging why, if either env var is
    unset or auth fails -- a survey submission still succeeds either way,
    falling back to SURVEY_FILE/stdout below. See ../thimble/server.py's
    own get_survey_sheet() for the one-time Google Cloud Console setup
    steps (already done once for that service account/sheet)."""
    global _sheet, _sheet_init_failed
    if _sheet is not None or _sheet_init_failed:
        return _sheet
    if not GOOGLE_SHEET_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        _sheet_init_failed = True
        return None
    try:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = GoogleCredentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        spreadsheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID)
        try:
            _sheet = spreadsheet.worksheet(SURVEY_WORKSHEET_TITLE)
        except gspread.WorksheetNotFound:
            _sheet = spreadsheet.add_worksheet(
                title=SURVEY_WORKSHEET_TITLE, rows=1000, cols=len(SURVEY_SHEET_HEADER)
            )
            _sheet.append_row(SURVEY_SHEET_HEADER, table_range="A1")
    except Exception as e:
        print(f"[survey] Google Sheets auth/open failed, falling back to local log: {e}", flush=True)
        _sheet_init_failed = True
        return None
    return _sheet


SURVEY_RADIO_FIELDS = {
    "conflict_frequency": {"rarely", "occasionally", "regularly", "constantly"},
    "first_move": {"talk_direct", "loop_in_hr_or_manager", "wait_and_see", "other"},
    "feels_judged": {"yes", "somewhat", "no"},
    "pressure_source": {"leadership", "hr", "employees", "myself", "not_much"},
    "would_use_conflicts": {"yes", "maybe", "no"},
    "would_use_written": {"yes", "maybe", "no"},
    "would_use_meetings": {"yes", "maybe", "no"},
    "team_size": {"1-3", "4-8", "9-15", "16+"},
}
SURVEY_SCALE_FIELDS = ("confidence", "useful_conflicts", "useful_written", "useful_meetings", "overall_interest")


@app.post("/api/survey")
async def submit_survey(request: Request):
    data = await request.json()
    if data.get("conflict_frequency") not in SURVEY_RADIO_FIELDS["conflict_frequency"]:
        return JSONResponse({"error": "conflict_frequency is required"}, status_code=400)
    radios = {}
    for field, valid_values in SURVEY_RADIO_FIELDS.items():
        value = data.get(field)
        if value not in valid_values and value is not None:
            return JSONResponse({"error": f"invalid {field} value"}, status_code=400)
        radios[field] = value
    scales = {}
    for field in SURVEY_SCALE_FIELDS:
        value = data.get(field)
        if value is not None and (not isinstance(value, int) or not (1 <= value <= 5)):
            return JSONResponse({"error": f"{field} must be an integer 1-5"}, status_code=400)
        scales[field] = value
    # Generous caps, not unbounded -- this is open free text from an
    # unauthenticated page.
    email = str(data.get("email") or "")[:200]
    pressure_management = str(data.get("pressure_management") or "")[:4000]
    comments = str(data.get("comments") or "")[:4000]
    record = {
        "ts": time.time(),
        **radios,
        **scales,
        "email": email,
        "pressure_management": pressure_management,
        "comments": comments,
    }
    sheet = get_survey_sheet()
    if sheet is not None:
        try:
            # table_range pins where gspread appends, same reasoning as
            # ../thimble/server.py's own append_row call -- without it, a
            # real submission there once landed with every value shifted
            # columns off from auto-detection.
            await run_in_threadpool(
                sheet.append_row,
                [
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(record["ts"])) + " UTC",
                    radios["conflict_frequency"] or "",
                    radios["first_move"] or "",
                    scales["confidence"] if scales["confidence"] is not None else "",
                    radios["feels_judged"] or "",
                    radios["pressure_source"] or "",
                    pressure_management,
                    scales["useful_conflicts"] if scales["useful_conflicts"] is not None else "",
                    radios["would_use_conflicts"] or "",
                    scales["useful_written"] if scales["useful_written"] is not None else "",
                    radios["would_use_written"] or "",
                    scales["useful_meetings"] if scales["useful_meetings"] is not None else "",
                    radios["would_use_meetings"] or "",
                    radios["team_size"] or "",
                    scales["overall_interest"] if scales["overall_interest"] is not None else "",
                    email,
                    comments,
                ],
                table_range=f"A1:{chr(ord('A') + len(SURVEY_SHEET_HEADER) - 1)}1",
            )
        except Exception as e:
            # A real write failure (quota, revoked share, transient network
            # error) shouldn't lose the response -- it still lands in the
            # fallback log below.
            print(f"[survey] Sheets append failed, response saved to local log only: {e}", flush=True)
    with SURVEY_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[survey] {json.dumps(record)}", flush=True)
    return {"ok": True}


# Post-use survey (static/survey-after.html) -- see the comment above
# SURVEY_FILE for how this differs from the pre-use one. Own file, own
# sheet tab, own cache variable: kept as a parallel block rather than
# generalizing get_survey_sheet() into something both share, since the two
# surveys have different fields/header and this only runs twice total.
SURVEY_POST_FILE = ROOT / "survey_responses_post.jsonl"
SURVEY_POST_WORKSHEET_TITLE = "Seam Post-Use"
SURVEY_POST_SHEET_HEADER = [
    "Timestamp", "Overall (1-5)", "Read felt right", "Changed approach",
    "Plan panel value", "Would use for real case", "Issues", "Comments", "Email",
]
_sheet_post = None
_sheet_post_init_failed = False


def get_survey_post_sheet():
    """Same auth/create-if-missing pattern as get_survey_sheet() above, just
    against the "Seam Post-Use" tab of the same spreadsheet instead of
    "Seam". See that function's docstring for the one-time setup notes."""
    global _sheet_post, _sheet_post_init_failed
    if _sheet_post is not None or _sheet_post_init_failed:
        return _sheet_post
    if not GOOGLE_SHEET_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        _sheet_post_init_failed = True
        return None
    try:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = GoogleCredentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        spreadsheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID)
        try:
            _sheet_post = spreadsheet.worksheet(SURVEY_POST_WORKSHEET_TITLE)
        except gspread.WorksheetNotFound:
            _sheet_post = spreadsheet.add_worksheet(
                title=SURVEY_POST_WORKSHEET_TITLE, rows=1000, cols=len(SURVEY_POST_SHEET_HEADER)
            )
            _sheet_post.append_row(SURVEY_POST_SHEET_HEADER, table_range="A1")
    except Exception as e:
        print(f"[survey/post] Google Sheets auth/open failed, falling back to local log: {e}", flush=True)
        _sheet_post_init_failed = True
        return None
    return _sheet_post


SURVEY_POST_RADIO_FIELDS = {
    "read_felt_right": {"yes", "partly", "no"},
    "changed_approach": {"yes", "somewhat", "no"},
    "plan_panel_value": {"both", "mostly_chat", "mostly_plan", "neither"},
    "would_use_real_case": {"yes", "maybe", "no"},
}


@app.post("/api/survey/post")
async def submit_survey_post(request: Request):
    data = await request.json()
    overall_rating = data.get("overall_rating")
    if not isinstance(overall_rating, int) or not (1 <= overall_rating <= 5):
        return JSONResponse({"error": "overall_rating must be an integer 1-5"}, status_code=400)
    radios = {}
    for field, valid_values in SURVEY_POST_RADIO_FIELDS.items():
        value = data.get(field)
        if value not in valid_values and value is not None:
            return JSONResponse({"error": f"invalid {field} value"}, status_code=400)
        radios[field] = value
    issues_raw = data.get("issues") or []
    if not isinstance(issues_raw, list):
        return JSONResponse({"error": "issues must be a list"}, status_code=400)
    issues = [str(i)[:40] for i in issues_raw][:10]
    comments = str(data.get("comments") or "")[:4000]
    email = str(data.get("email") or "")[:200]
    record = {
        "ts": time.time(),
        "overall_rating": overall_rating,
        **radios,
        "issues": issues,
        "comments": comments,
        "email": email,
    }
    sheet = get_survey_post_sheet()
    if sheet is not None:
        try:
            await run_in_threadpool(
                sheet.append_row,
                [
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(record["ts"])) + " UTC",
                    overall_rating,
                    radios["read_felt_right"] or "",
                    radios["changed_approach"] or "",
                    radios["plan_panel_value"] or "",
                    radios["would_use_real_case"] or "",
                    ", ".join(issues),
                    comments,
                    email,
                ],
                table_range=f"A1:{chr(ord('A') + len(SURVEY_POST_SHEET_HEADER) - 1)}1",
            )
        except Exception as e:
            print(f"[survey/post] Sheets append failed, response saved to local log only: {e}", flush=True)
    with SURVEY_POST_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[survey/post] {json.dumps(record)}", flush=True)
    return {"ok": True}
