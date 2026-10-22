import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent

sys.path.insert(0, str(REPO_ROOT))

import os

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from usage_log import log_usage
from threads import THREADS

load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / "apps" / "thimble" / ".env")

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None


def _first_text(response) -> str:
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


app = FastAPI()
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


class ThreadRequest(BaseModel):
    job: str


THREAD_SYSTEM_PROMPT = (
    "You generate a realistic, understated Slack thread between two coworkers for a "
    "manager self-assessment tool. You're given a structural cause (the real reason "
    "this will escalate) and a fixed sequence of beats (what each message needs to "
    "accomplish). Your job is to pick two coworker roles relevant to the manager's own "
    "job or team, invent two first names, and write one message per beat, in that exact "
    "order, that fulfills each beat's intent using domain-appropriate specifics.\n\n"
    "Rules:\n"
    "- Never state the structural cause outright. No one in the thread explains why "
    "they're really upset; it stays in subtext, deflection, and clipped replies.\n"
    "- Lowercase, casual, realistic chat style. Short messages, one to three sentences "
    "each. No stage directions, no narration, just the message text.\n"
    "- No em-dashes anywhere.\n"
    "- Keep the exact same escalation shape as the beats: don't soften or resolve it "
    "early, don't add extra messages.\n"
    "- The two roles should plausibly exist on or near a team doing the manager's "
    "stated job, and plausibly collide the way the structural cause describes.\n\n"
    "Output ONLY valid JSON, no markdown fences, in exactly this shape:\n"
    '{"role_a": "<short role label for person A>", "role_b": "<short role label for '
    'person B>", "messages": [{"from": "<first name>", "text": "<message text>"}, ...]}\n'
    "The messages array must have exactly one entry per beat, in the same order."
)


@app.post("/api/thread")
def get_thread(req: ThreadRequest):
    thread_id = random.choice(list(THREADS.keys()))
    thread = THREADS[thread_id]

    if client is None:
        return {
            "thread_id": thread_id,
            "role_a": "Person A",
            "role_b": "Person B",
            "messages": [
                {"from": "A" if b["from"] == "A" else "B", "text": "(server error: ANTHROPIC_API_KEY is not set)"}
                for b in thread["beats"][:1]
            ],
        }

    beats_text = "\n".join(f"{i + 1}. [{b['from']}] {b['intent']}" for i, b in enumerate(thread["beats"]))
    user_prompt = (
        f"Manager's job/team: {req.job}\n\n"
        f"Structural cause: {thread['structural_cause']}\n\n"
        f"Beats:\n{beats_text}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1400,
        system=THREAD_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    log_usage(
        "manager-read-test",
        "anthropic",
        MODEL,
        "generate_thread",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    raw = _first_text(response).strip()

    try:
        parsed = _extract_json(raw)
        messages = parsed["messages"]
        if len(messages) != len(thread["beats"]):
            raise ValueError("beat count mismatch")
        role_a = parsed.get("role_a", "Person A")
        role_b = parsed.get("role_b", "Person B")
    except (json.JSONDecodeError, KeyError, ValueError):
        role_a, role_b = "Person A", "Person B"
        messages = [{"from": b["from"], "text": "(couldn't generate this message, try again)"} for b in thread["beats"]]

    return {"thread_id": thread_id, "role_a": role_a, "role_b": role_b, "messages": messages}


class ScoreRequest(BaseModel):
    thread_id: str
    messages: list[dict]  # [{"from": "<name>", "text": "..."}]
    what: str
    why: str
    do: str


BAND_POINTS = {
    "what": {"high": 30, "mid": 15, "low": 5},
    "why": {"high": 40, "mid": 20, "low": 5},
    "do": {"high": 30, "mid": 15, "low": 0},
}

SCORE_SYSTEM_PROMPT = (
    "You grade a manager's diagnosis of a coworker text thread for a self-assessment tool. "
    "The thread shows a dispute between two reports that LOOKS like a personality clash but "
    "is actually driven by a structural cause (colliding deadlines, mismatched metrics, or a "
    "missing process gate) that is never stated outright in the thread.\n\n"
    "The manager answered three questions. Grade each answer into exactly one band: high, "
    "mid, or low, using these criteria:\n\n"
    "WHAT'S HAPPENING:\n"
    "- high: names it as a task, process, or handoff breakdown.\n"
    "- mid: mentions both a structural read and a personality read, doesn't commit to one.\n"
    "- low: names it as a personality clash, tone problem, or attitude issue.\n\n"
    "WHY IS IT HAPPENING:\n"
    "- high: identifies the specific structural cause: colliding metrics, deadlines, or a "
    "missing review/handoff step, grounded in what's actually in this thread.\n"
    "- mid: gestures at pressure or constraints generically, without naming the specific "
    "collision in this thread.\n"
    "- low: attributes it to character: ego, laziness, poor communication skills, "
    "unprofessionalism.\n\n"
    "WHAT TO DO ABOUT IT:\n"
    "- high: proposes a structural fix the two reports can run themselves without the "
    "manager approving each step (an SLA, a review gate, a routing change).\n"
    "- mid: proposes a reasonable fix but still routes it through the manager as approver "
    "or mediator.\n"
    "- low: proposes the manager stepping in to judge, arbitrate, or extract an apology.\n\n"
    "For each question, write one short plain-English note (one sentence, second person, no "
    "em-dashes, no aphorism-style reversals) on why you gave that band, referencing what the "
    "manager actually wrote.\n\n"
    "Output in exactly this format, nothing else:\n"
    "NOTE_WHAT: <note>\n"
    "NOTE_WHY: <note>\n"
    "NOTE_DO: <note>\n"
    "BAND_WHAT: high|mid|low\n"
    "BAND_WHY: high|mid|low\n"
    "BAND_DO: high|mid|low"
)

ARCHETYPES = {
    "moral_arbiter": {
        "label": "The Moral Arbiter",
        "blurb": "You read this as a conflict between people, not a conflict between the jobs they're doing.",
    },
    "bureaucratic_arbiter": {
        "label": "The Bureaucratic Arbiter",
        "blurb": "You saw the real cause, then still put yourself in the room as the one who has to sign off.",
    },
    "systems_architect": {
        "label": "The Systems Architect",
        "blurb": "You named the structural collision and handed the fix back to the people who can actually run it.",
    },
}


def _archetype(bands: dict) -> str:
    if bands["what"] == "low":
        return "moral_arbiter"
    if bands["what"] in ("high", "mid") and bands["why"] in ("high", "mid") and bands["do"] == "low":
        return "bureaucratic_arbiter"
    if bands["what"] == "high" and bands["why"] == "high" and bands["do"] == "high":
        return "systems_architect"
    total = sum(BAND_POINTS[q][bands[q]] for q in ("what", "why", "do"))
    if total >= 75:
        return "systems_architect"
    if total >= 40:
        return "bureaucratic_arbiter"
    return "moral_arbiter"


@app.post("/api/score")
def score(req: ScoreRequest):
    if client is None:
        return {"error": "server error: ANTHROPIC_API_KEY is not set"}

    transcript = "\n".join(f"{m['from']}: {m['text']}" for m in req.messages)
    user_prompt = (
        f"Thread:\n{transcript}\n\n"
        f"Manager's answers:\n"
        f"What's happening: {req.what}\n"
        f"Why is it happening: {req.why}\n"
        f"What do you do about it: {req.do}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SCORE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    log_usage(
        "manager-read-test",
        "anthropic",
        MODEL,
        "score",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    raw = _first_text(response).strip()

    notes = {"what": "", "why": "", "do": ""}
    bands = {"what": "mid", "why": "mid", "do": "mid"}
    key_map = {
        "NOTE_WHAT": ("notes", "what"),
        "NOTE_WHY": ("notes", "why"),
        "NOTE_DO": ("notes", "do"),
        "BAND_WHAT": ("bands", "what"),
        "BAND_WHY": ("bands", "why"),
        "BAND_DO": ("bands", "do"),
    }
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().upper()
        value = value.strip()
        if key in key_map:
            target, field = key_map[key]
            if target == "notes":
                notes[field] = value
            else:
                value_lower = value.lower()
                if value_lower in ("high", "mid", "low"):
                    bands[field] = value_lower

    breakdown = {
        q: {"band": bands[q], "points": BAND_POINTS[q][bands[q]], "note": notes[q]}
        for q in ("what", "why", "do")
    }
    total = sum(b["points"] for b in breakdown.values())
    archetype_key = _archetype(bands)
    archetype = ARCHETYPES[archetype_key]

    return {
        "score": total,
        "archetype_label": archetype["label"],
        "archetype_blurb": archetype["blurb"],
        "breakdown": breakdown,
    }
