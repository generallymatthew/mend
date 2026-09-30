#!/usr/bin/env python3
"""
Proof-of-concept: does annotating a transcript line with real prosody flags
(../joint-session-audio/prosody.py's actual vocabulary -- pitch_elevated,
energy_elevated, pace_elevated, pace_slowed, pitch_lowered, pitch_flattened,
hesitant) change how the REAL facilitator system prompt + REAL model reads
it? Not a live integration -- joint-session-audio and joint-session-app are
still two disconnected processes, see ../joint-session-audio/README.md's
"Prosody / tone signal" section -- just a controlled, direct test of whether
the idea has value before building the real bridge between them.

Method: build one shared conversation prefix (kickoff + a mundane workplace
disagreement) with ONE real facilitator turn, then branch into two variants
that differ in exactly one place -- how Employee A's next, deliberately
text-ambiguous line ("Fine, whatever you say.") is annotated -- and make one
real API call per variant for the facilitator's next turn. Same model, same
system prompt, same everything else; the only variable is the tone
annotation. "Fine, whatever you say." is chosen because it's the exact case
this whole feature exists for: text that reads as calm or compliant on its
own, but where real delivery could mean the opposite.

Requires ANTHROPIC_API_KEY (already set in this app's own .env). Calls the
real Claude API -- costs a few cents, not free, not run automatically.

Usage:
    python poc_prosody_in_prompt.py
"""
import json
import re
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

MODEL = "claude-sonnet-5"
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-joint-session-system-prompt.md"


def load_system_prompt() -> str:
    text = SYSTEM_PROMPT_FILE.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {SYSTEM_PROMPT_FILE}")
    return match.group(1)


def strip_signal(reply_text: str):
    match = re.search(r"<mend_signal>(.*?)</mend_signal>", reply_text, re.S)
    visible = re.sub(r"<mend_signal>.*?</mend_signal>", "", reply_text, flags=re.S).strip()
    if not match:
        return visible, None
    try:
        return visible, json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return visible, None


SYSTEM_PROMPT = load_system_prompt()
client = Anthropic()

KICKOFF_TURN = (
    "(Both employees have just joined the joint session, having already "
    "completed their private side conversations. Begin the session now: frame what "
    "it's for and manage the room.)"
)


def call(conversation):
    response = client.messages.create(model=MODEL, max_tokens=4096, system=SYSTEM_PROMPT, messages=conversation)
    raw = "".join(block.text for block in response.content if block.type == "text")
    return strip_signal(raw)


def run_scenario(scenario_name, prefix_turns, variants):
    """prefix_turns: list of user-turn strings, each gets a real facilitator
    reply appended before the next, building shared context. variants: list
    of (label, final_user_turn) branching off the same prefix -- exactly one
    more real call each, so the prefix's own sampling variance can't leak
    into the comparison."""
    print("#" * 70)
    print(f"# SCENARIO: {scenario_name}")
    print("#" * 70, "\n")

    conversation = [{"role": "user", "content": KICKOFF_TURN}]
    opening, _ = call(conversation)
    conversation.append({"role": "assistant", "content": opening})
    print("=== Facilitator opening (shared) ===")
    print(opening, "\n")

    for turn in prefix_turns:
        conversation.append({"role": "user", "content": turn})
        reply, signal = call(conversation)
        conversation.append({"role": "assistant", "content": reply})
        print(f"=== Facilitator, after: {turn[:70]}... (shared) ===")
        print(reply, "\n")

    shared_prefix = list(conversation)
    results = []
    for label, line in variants:
        convo = list(shared_prefix)
        convo.append({"role": "user", "content": line})
        reply, signal = call(convo)
        results.append((label, line, reply, signal))
        print(f"=== {label} ===")
        print(f"Employee A's line sent: {line!r}")
        print(f"Facilitator reply:\n{reply}\n")
        print(f"Signal: session_state={signal.get('session_state') if signal else None}, "
              f"severity_tier={signal.get('severity_tier') if signal else None}, "
              f"checkin_target={signal.get('checkin_target') if signal else None}\n")

    print("=== SUMMARY:", scenario_name, "===")
    for label, line, reply, signal in results:
        print(f"{label}:")
        print(f"  session_state={signal.get('session_state') if signal else None}  "
              f"severity_tier={signal.get('severity_tier') if signal else None}  "
              f"checkin_target={signal.get('checkin_target') if signal else None}")
    if results[0][3] and results[1][3]:
        same = (results[0][3].get("session_state") == results[1][3].get("session_state")
                and results[0][3].get("severity_tier") == results[1][3].get("severity_tier"))
        print(f"{'SAME' if same else 'DIFFERENT'} session_state/severity_tier between baseline and tone-annotated variant.")
    print()
    return results


def main():
    # Scenario 1: "Fine, whatever you say." -- already a textbook
    # passive-aggressive phrase in written English on its own, so this is
    # the easy case: does text alone already carry enough signal?
    run_scenario(
        "Textually-loaded line (a phrase that already reads as passive-aggressive in text alone)",
        prefix_turns=[
            "[Employee A]: Thanks for setting this up. I wanted to talk about the presentation last week -- "
            "I put together most of the analysis, but in the meeting Alex presented it like it was entirely "
            "their own work, no mention of my contribution.",
            "[Employee B]: I didn't mean to leave that out, I just went with what felt natural to present.",
        ],
        variants=[
            ("BASELINE (text only, no tone signal)",
             "[Employee A]: Fine, whatever you say."),
            ("WITH PROSODY (same words, annotated with real flags from prosody.py)",
             "[Employee A, voice: pace_elevated, energy_elevated relative to their own earlier baseline]: "
             "Fine, whatever you say."),
        ],
    )

    # Scenario 2: a genuinely neutral line -- no negative connotation in the
    # words themselves at all, the fairer test of whether tone adds signal
    # text alone doesn't already carry.
    run_scenario(
        "Textually-neutral line (words alone carry no negative signal either way)",
        prefix_turns=[
            "[Employee B]: I know you've had a lot on your plate already, but could you also pick up the "
            "client follow-ups from the Meridian account this week? I just don't have the bandwidth.",
        ],
        variants=[
            ("BASELINE (text only, no tone signal)",
             "[Employee A]: Sure, I can take care of that too."),
            ("WITH PROSODY (same words, annotated with real flags from prosody.py)",
             "[Employee A, voice: pitch_flattened, pace_slowed relative to their own earlier baseline]: "
             "Sure, I can take care of that too."),
        ],
    )


if __name__ == "__main__":
    main()
