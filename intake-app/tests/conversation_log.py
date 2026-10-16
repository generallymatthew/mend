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
        "human_score": None,
        "human_notes": None,
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


def rate_conversation(conv_id, human_score, human_notes=None):
    records = load_conversations()
    found = False
    for record in records:
        if record["id"] == conv_id:
            record["human_score"] = human_score
            record["human_notes"] = human_notes
            found = True
    if not found:
        return False
    with LOG_FILE.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return True
