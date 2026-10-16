"""
Shared test-only conversation log. Benchmark/comparison harnesses
(adaptive_persona_compare.py, benchmark_audit.py, etc.) call log_conversation()
after each run; server.py reads the same file to serve the conversation
history viewer at /conversation-history.

This is test data only, never wired into the real intake session flow in
server.py's /api/* conversation endpoints, which stays true to the
"nothing is recorded" principle for actual users.
"""
import json
import time
import uuid
from pathlib import Path

LOG_FILE = Path(__file__).parent / "conversation_log.jsonl"

# Same four dimensions the simulated persona self-reports on -- a human
# rater scores the same scale, so the two are directly comparable.
RATING_METRICS = ("feel_equipped", "feel_understood", "trust_advice", "would_say_it")


def log_conversation(
    harness,
    scenario_id,
    system_id,
    prompt_name,
    prompt_text,
    transcript,
    objective_score=None,
    self_report=None,
    turns=None,
):
    record = {
        "id": uuid.uuid4().hex[:12],
        "ts": time.time(),
        "harness": harness,
        "scenario_id": scenario_id,
        "system_id": system_id,
        "prompt_name": prompt_name,
        "prompt_text": prompt_text,
        "transcript": transcript,
        "objective_score": objective_score,
        "self_report": self_report,
        "turns": turns,
        "human_ratings": [],
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return record["id"]


def load_conversations():
    if not LOG_FILE.exists():
        return []
    records = []
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def get_conversation(conv_id):
    for record in load_conversations():
        if record["id"] == conv_id:
            return record
    return None


def add_human_rating(conv_id, rater, scores, notes=None):
    """Append one more person's rating -- never overwrites an earlier rater's.
    `scores` is a dict with the four RATING_METRICS keys, each 1-5."""
    records = load_conversations()
    found = False
    for record in records:
        if record["id"] == conv_id:
            record.setdefault("human_ratings", []).append({
                "rater": rater,
                "ts": time.time(),
                **{m: scores[m] for m in RATING_METRICS},
                "notes": notes,
            })
            found = True
    if not found:
        return False
    with LOG_FILE.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return True
