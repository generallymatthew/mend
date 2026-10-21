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
from scenarios import get_scenario, scenario_text

load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / "apps" / "thimble" / ".env")

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
client = Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None

MAX_USER_TURNS = 3


def _first_text(response) -> str:
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""

app = FastAPI()
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


class ScenarioRequest(BaseModel):
    role: str


class ReplyRequest(BaseModel):
    role: str
    history: list[dict]  # [{"from": "them"|"me", "text": "..."}]
    message: str


class ReadoutRequest(BaseModel):
    role: str
    history: list[dict]


@app.post("/api/scenario")
def start_scenario(req: ScenarioRequest):
    scenario = get_scenario(req.role)
    return {
        "scenario_text": scenario_text(scenario),
        "counterpart_name": scenario["counterpart_name"],
        "opening_line": scenario["opening_line"],
    }


def _counterpart_system_prompt(scenario: dict) -> str:
    return (
        f"You are playing {scenario['counterpart_name']} in a short roleplay used by a "
        f"self-assessment tool about handling conflict and social dynamics. You are "
        f"{scenario['reputation']}. The other person is a {scenario['role']} contacting "
        f"you for the first time to {scenario['the_ask']}. {scenario['time_pressure']}\n\n"
        "How you react to their message:\n"
        "- If it leads with their own deadline or pressure before acknowledging your time "
        "or your stake in it: respond short and skeptical, ask why you're hearing about "
        "this only now. Don't refuse outright, but don't help yet either.\n"
        "- If it gives real context first and leaves you an actual say in the outcome, not "
        "just notice of a decision already made: engage, ask one clarifying question, move "
        "toward a workable answer.\n"
        "- If it's vague or all pressure with no specifics: ask for specifics before "
        "engaging at all.\n\n"
        "Stay fully in character. Lowercase, terse, realistic texting style, matching the "
        "voice of your opening line. One to two sentences. Never break character, never "
        "acknowledge this is an exercise, never use em-dashes."
    )


@app.post("/api/reply")
def reply(req: ReplyRequest):
    scenario = get_scenario(req.role)
    if client is None:
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set)", "done": True}

    messages = []
    for turn in req.history:
        role = "assistant" if turn["from"] == "them" else "user"
        messages.append({"role": role, "content": turn["text"]})
    messages.append({"role": "user", "content": req.message})

    response = client.messages.create(
        model=MODEL,
        max_tokens=150,
        system=_counterpart_system_prompt(scenario),
        messages=messages,
    )
    log_usage(
        "conflict-test",
        "anthropic",
        MODEL,
        "counterpart_reply",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    reply_text = _first_text(response).strip()

    user_turns = sum(1 for turn in req.history if turn["from"] == "me") + 1
    done = user_turns >= MAX_USER_TURNS

    return {"reply": reply_text, "done": done}


READOUT_SYSTEM_PROMPT = (
    "You write short, specific readouts for a self-assessment exercise. The person just "
    "finished a roleplay testing how they handle a status-asymmetric first contact: asking "
    "something from a stranger who can say no, where that person already has a reputation "
    "for pushing back.\n\n"
    "Judge the WHOLE conversation, not just the opening message. What matters is whether "
    "they read and adapted to the counterpart as it went: did they keep the same approach "
    "even after the counterpart signaled friction, did they only supply real content once "
    "pressed for it, or did they give the counterpart what they needed from the start and "
    "stay attuned to them throughout (not backsliding into pressure once things got easier).\n\n"
    "Given the full transcript, write a readout with exactly three parts, as plain prose, "
    "no headers or labels:\n"
    "1. One concrete observation tied to what they actually wrote, drawn from across the "
    "conversation, not just the first message. Quote back the specific line that best shows "
    "whether they adjusted or didn't.\n"
    "2. Name the general pattern that reflects: did they hold one approach regardless of the "
    "counterpart's reaction, did they only adapt once pressed, or did they read the room from "
    "the start. Without labeling the person as a type.\n"
    "3. One sentence connecting it to why this is hard to see in the moment it actually "
    "matters.\n\n"
    "Keep it under 120 words total. Second person. Plain, direct sentences. No aphorism-"
    "style headline reversals (no 'X is the symptom, Y is the cause' constructions). No "
    "em-dashes anywhere in the text.\n\n"
    "Then, on a final line by itself, classify the whole conversation into exactly one of "
    "these three categories and output ONLY that line in the exact format shown:\n"
    "CATEGORY: A -- held the same approach throughout even as the counterpart signaled "
    "friction; never adapted.\n"
    "CATEGORY: B -- started self-focused or caused friction, but adjusted once the "
    "counterpart's reaction made the mismatch visible; recovered, didn't lead that way.\n"
    "CATEGORY: C -- read the counterpart's position from the start, gave them what they "
    "needed to engage, and stayed attuned throughout without backsliding.\n"
    "Output the final line as exactly 'CATEGORY: A', 'CATEGORY: B', or 'CATEGORY: C' with "
    "nothing else on that line."
)

CATEGORY_INFO = {
    "A": {"score": 35, "label": "Didn't read the room"},
    "B": {"score": 70, "label": "Caught up"},
    "C": {"score": 95, "label": "Read it from the start"},
}


@app.post("/api/readout")
def readout(req: ReadoutRequest):
    scenario = get_scenario(req.role)
    if client is None:
        return {"readout": "(server error: ANTHROPIC_API_KEY is not set)"}

    transcript = "\n".join(
        f"{'Counterpart' if turn['from'] == 'them' else 'You'}: {turn['text']}"
        for turn in req.history
    )
    user_prompt = (
        f"Scenario: a {scenario['role']} needed to {scenario['the_ask']} from "
        f"{scenario['counterpart_name']}, who {scenario['reputation']}, on first contact.\n\n"
        f"Transcript:\n{transcript}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=320,
        system=READOUT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    log_usage(
        "conflict-test",
        "anthropic",
        MODEL,
        "readout",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    raw = _first_text(response).strip()

    category = "B"  # fallback if the model ever skips the line
    lines = raw.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped.upper().startswith("CATEGORY:"):
            value = stripped.split(":", 1)[1].strip().upper()
            if value in CATEGORY_INFO:
                category = value
            lines = lines[:i]
            break
    readout_text = "\n".join(lines).strip()

    info = CATEGORY_INFO[category]
    return {"readout": readout_text, "score": info["score"], "label": info["label"]}
