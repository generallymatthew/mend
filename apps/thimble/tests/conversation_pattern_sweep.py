#!/usr/bin/env python3
"""
Exploratory sweep over the shape of Thimble's conversation, not a pass/fail
regression test -- same spirit as safety_floor_sweep.py, but for the
employee-conflict path's Phase 1 flow (speed-to-value, archetype diversity,
redundant-question bugs) rather than the safety floor.

Runs a handful of SCENARIOS, each a short scripted multi-turn conversation
written to sound like a plausible real employee, REPEATS times (independent
/api/reset sessions) against the live /api/message endpoint. Saves every
full transcript to a timestamped file for manual read-through -- the actual
point of this script, since "does this read naturally and avoid the tics
we've been fixing" is a judgment call, not something worth building a strict
assertion for -- and prints a compact summary flagging the specific
mechanical bugs already found and fixed once (disclosure-preamble phrases,
corporate jargon, pop-psychology labels, numbered question lists, and a
simple same-question-twice-in-a-row heuristic) so a regression shows up at a
glance without reading every transcript every time.

Needs a running `uvicorn server:app --port 8420` with a real
ANTHROPIC_API_KEY configured. Costs real tokens: 5 scenarios x repeats x up
to 3 turns each.

Usage:
    thimble/.venv/bin/python thimble/tests/conversation_pattern_sweep.py [--base-url URL] [--repeats N] [--out DIR]
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from safety_floor_test import parse_signal, post  # noqa: E402

# Each scenario is a short list of scripted employee turns, written to be a
# plausible real reply regardless of the exact wording Thimble comes back
# with (we don't control that), not a rigid question/answer script. Picks
# up the archetypes from facilitator-intake-system-prompt.md's "showing
# understanding early" section, plus the name-calling deflection and the
# manager-coaching track, which that section doesn't cover.
SCENARIOS = {
    "avoidant_peer": [
        "My coworker keeps agreeing in standup to send me the API spec by end of day, then just goes quiet. I have to chase him every single time and I'm sick of it. It's been about 3 weeks now, and that's really the main thing, nothing else going on. He's a peer, not my manager.",
        "Honestly I don't know, we don't talk about his workload much. Maybe he's just busy, I don't know.",
        "Yeah, I think I'd want some wording to bring this up with him directly, without sounding like I'm attacking him.",
    ],
    "reversing_manager": [
        "My manager told me in our 1:1 last week that I could lead the migration project, then in today's team meeting she gave it to someone else without saying anything to me first. This has happened a couple times before too, she'll agree to something and then just act like it never happened.",
        "I think she's got a lot of pressure from her own boss honestly, she's been stressed lately.",
        "I want to say something to her about it, but I don't want to come across as entitled.",
    ],
    "cross_team_pushback": [
        "I sent a simple status check to the platform team asking when our API migration would be done, and the lead responded really defensively, like I was accusing them of being slow. I was just asking for a date.",
        "No, that's really it, it was just that one really sharp reply, nothing else happened.",
        "I guess I'd like to know how to ask for updates without setting them off like that again.",
    ],
    "name_calling": [
        "My manager is honestly just a complete idiot. He has no idea what he's doing and it's infuriating to work for him.",
        "He keeps changing the requirements on my project every single week without warning, so I end up redoing work constantly.",
        "No, that's really it, that's the main thing.",
    ],
    "repetitive_venting": [
        "My manager completely dismissed my proposal in the planning meeting today, didn't even really engage with it, just moved on to someone else's idea in about ten seconds.",
        "It's just really frustrating, she didn't even give it a real chance, she just brushed past it like it wasn't worth discussing.",
        "Yeah, I keep thinking about it, it really bothered me that she didn't even engage with what I actually said.",
        "Yeah, let's look at what might actually be behind it.",
    ],
    "manager_coaching_track": [
        "I need to have a conversation with one of my reports, she's missed three deadlines in the last month and I don't know how to bring it up without sounding harsh.",
        "She's generally a strong performer, this is new over the last month or so.",
        "I think I just want help figuring out how to open the conversation.",
    ],
    # Pulled from docs/pitch-strategy/14_WORKPLACE_SCENARIOS.md -- a wider
    # spread of real conflict shapes than the archetypes above cover,
    # including one (flip_the_frame_own_report) that exercises a prompt
    # branch ("if the other person is actually a direct report... flip the
    # frame instead") none of the scenarios above ever reach.
    "credit_stealing": [
        "My co-lead on a launch presented our results to the whole company and took credit for everything using \"I\" the entire time, didn't mention me once. This is the second time it's happened in two months. I haven't said anything, I'm not sure if I'm overreacting, and we still have to work closely together for the next launch.",
        "No, that's really the main thing, it's just happened twice now in the recap meetings specifically.",
        "I think I want to say something, but I don't want to make it weird since we're still co-leading the next launch together.",
    ],
    "micromanagement": [
        "My manager reviews every single piece of my work line by line, even stuff I've done successfully for over a year, and rewrites small things without explaining why. When I asked for clearer expectations up front, he just said \"use your judgment,\" but then edited the result anyway.",
        "It's been going on for a few months now, and it's making me second-guess decisions that used to feel automatic.",
        "I guess I want to figure out how to ask for more trust without sounding like I'm complaining, especially since I'm up for a promotion he'll weigh in on.",
    ],
    "passive_aggressive_escalation": [
        "A coworker and I used to just hash out disagreements directly, but lately it's turned into pointed Slack messages and he's started CC'ing our manager on stuff we used to resolve ourselves. Neither of us has actually said there's a problem, it's all just tone and who's copied on what.",
        "No, nothing new happened today specifically, it's just been building for a few weeks now.",
        "I want to actually talk to him directly instead of letting it keep happening over Slack and CCs.",
    ],
    "flip_the_frame_own_report": [
        "One of the people I manage keeps challenging my decisions in front of the rest of the team instead of bringing it up privately. I'm not sure if she's trying to undermine me or if she genuinely just thinks the team benefits from debating things openly and hasn't noticed how it lands.",
        "No, that's really it, it's specifically happening in team meetings when I make a call on something.",
        "I want to raise it with her without coming across as thin-skinned or shutting down healthy debate.",
    ],
    "harassment_adjacent": [
        "A coworker keeps commenting on my appearance, stuff like \"you look great today,\" and lingers at my desk to chat about non-work stuff even after I've tried to wrap things up and change the subject. I haven't said anything directly to him because nothing he's said is really over the line on its own, and I don't want to seem difficult.",
        "No, that's really it, it's just been building up over a few weeks.",
        "I'm not sure if I'm overreacting or if this is actually worth saying something about.",
    ],
    # Neither of thimble's own two tracks: not the manager's own conflict
    # (employee-conflict path) and not rehearsing a conversation with their
    # OWN direct report (manager-coaching path) -- a manager caught between
    # two OTHER people who report to them is exactly facilitator-case-plan-
    # system-prompt.md's (seam's) job instead. Scripted to see how
    # thimble's prompt actually handles a request outside both of its
    # own tracks, rather than guessing from reading the prompt text.
    "manager_mediating_two_reports": [
        "I'm a manager and two people on my team have been openly clashing in meetings for weeks over how a shared process should run. They've both come to me separately asking me to back their side. I've been trying to stay neutral but it's starting to affect how the rest of the team plans around them.",
        "No, that's really it, it's been building for a few weeks in our team meetings specifically.",
        "I guess I want help figuring out how to handle this without picking a side or making it worse.",
    ],
    "role_elimination_coaching": [
        "I need to tell one of my direct reports that his role is being eliminated in a reorg. It's not a performance thing at all, it's a budget decision made above me, but I'm anxious about him asking why and me not having a satisfying answer.",
        "He's been a strong performer, this really is just about the budget, nothing he did.",
        "I want to be honest with him without being cold about it, I just don't know how to open it.",
    ],
}

MAX_TURNS = 4  # repetitive_venting needs 4 turns to exercise its accept-the-pivot-offer step

# Phrases the system prompt now explicitly bans, checked literally here so a
# regression (the model reaching for a new unbanned variant, which is
# exactly what happened across this file's own fix history) shows up
# immediately instead of waiting for the next manual spot-check.
DISCLOSURE_PREAMBLES = [
    "i want to be upfront", "i want to be transparent", "let me assure you",
    "for the record", "to be straight with you", "to be clear,", "i should mention",
]
ON_YOUR_SIDE = ["on your side", "on my side"]
CORPORATE_JARGON = [
    "bandwidth panic", "swimlane", "synergy", "operational friction",
    "cognitive overload", "status threat", "calibrating the dynamic",
]
POP_PSYCH_LABELS = ["gaslight", "narcissist", "toxic dynamic", "trauma bond"]


def check_reply(text: str) -> list[str]:
    """Returns a list of short flag strings for anything this reply trips --
    empty list means clean. Case-insensitive substring checks, deliberately
    simple (false negatives on a truly novel phrasing are expected and fine,
    this is a tripwire, not the actual review)."""
    lower = text.lower()
    flags = []
    for phrase in DISCLOSURE_PREAMBLES:
        if phrase in lower:
            flags.append(f"disclosure-preamble:{phrase!r}")
    for phrase in ON_YOUR_SIDE:
        if phrase in lower:
            flags.append(f"on-your-side:{phrase!r}")
    for phrase in CORPORATE_JARGON:
        if phrase in lower:
            flags.append(f"jargon:{phrase!r}")
    for phrase in POP_PSYCH_LABELS:
        if phrase in lower:
            flags.append(f"pop-psych-label:{phrase!r}")
    if re.search(r"\n\s*1[.)]\s", text) and re.search(r"\n\s*2[.)]\s", text):
        flags.append("numbered-question-list")
    return flags


def question_sentences(text: str) -> list[str]:
    return [s.strip().lower() for s in re.split(r"(?<=[.?!])\s+", text) if s.strip().endswith("?")]


def jaccard(a: str, b: str) -> float:
    wa, wb = set(a.split()), set(b.split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def likely_duplicate_question(prev_text: str, cur_text: str) -> str | None:
    """Flags a same-question-twice-in-a-row pattern: any question sentence in
    the current reply that's a close word-overlap match for one in the
    previous reply. This is the exact shape of the vent-check and
    relationship-question bugs found live-testing this prompt earlier --
    a cheap heuristic, not a real semantic check, so it's reported as a
    flag to manually confirm, not treated as ground truth."""
    for cur_q in question_sentences(cur_text):
        for prev_q in question_sentences(prev_text):
            if jaccard(prev_q, cur_q) > 0.45:
                return f"possible repeat question: prev={prev_q!r} cur={cur_q!r}"
    return None


def run_scenario(client, base_url, turns):
    post(client, base_url, "/api/reset")
    transcript = []
    prev_reply = ""
    track_turn = None
    all_flags = []
    for i, user_msg in enumerate(turns[:MAX_TURNS], start=1):
        # server.py's own cost-protection rate limiter is 20 req/60s per IP
        # (shared across every endpoint this script hits: /api/reset +
        # /api/message per turn) -- a bare sweep across several scenarios
        # blows through that in well under a minute. This isn't working
        # around the limiter, just pacing requests to stay under it, the
        # same way a real spaced-out conversation would.
        time.sleep(4)
        data = post(client, base_url, "/api/message", {"text": user_msg})
        reply = data.get("reply", "")
        signal = parse_signal(data.get("signal"))
        if track_turn is None and signal.get("track"):
            track_turn = i
        flags = check_reply(reply)
        dup = likely_duplicate_question(prev_reply, reply) if prev_reply else None
        if dup:
            flags.append(dup)
        all_flags.extend(f"turn {i}: {f}" for f in flags)
        transcript.append({"turn": i, "user": user_msg, "thimble": reply, "signal": signal, "flags": flags})
        prev_reply = reply
    return transcript, track_turn, all_flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8420")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--out", default=None, help="Directory to write transcripts to (default: alongside this script)")
    ap.add_argument("--scenario", action="append", help="Limit to one or more scenario names (repeatable); default is all")
    args = ap.parse_args()

    scenarios = {k: v for k, v in SCENARIOS.items() if not args.scenario or k in args.scenario}
    out_dir = Path(args.out) if args.out else Path(__file__).parent / "pattern_sweep_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"sweep_{stamp}.jsonl"

    print(f"{'scenario':<24} {'run':<5} {'track@turn':<11} flags")
    print("-" * 100)
    with httpx.Client() as client, open(out_path, "w") as out_f:
        for name, turns in scenarios.items():
            for run_i in range(1, args.repeats + 1):
                try:
                    transcript, track_turn, flags = run_scenario(client, args.base_url, turns)
                except Exception as e:
                    print(f"{name:<24} {run_i:<5} ERROR: {e}")
                    continue
                out_f.write(json.dumps({"scenario": name, "run": run_i, "transcript": transcript}) + "\n")
                flag_str = "; ".join(flags) if flags else "clean"
                print(f"{name:<24} {run_i:<5} {str(track_turn):<11} {flag_str}")
    print(f"\nFull transcripts written to {out_path}")


if __name__ == "__main__":
    main()
