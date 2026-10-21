import sys, os, time, json, re
sys.path.insert(0, os.path.dirname(__file__))
from benchmark_audit import call_mend, call_claude_raw, format_transcript, judge, load_mend_system_prompt
from conversation_log import log_conversation, new_run_id
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CF_PROMPT = open(os.path.join(os.path.dirname(__file__), "..", "..", "cf-prompts", "cf-v1.md")).read()
MEND_PROMPT = load_mend_system_prompt()

# Adaptive LLM personas, replacing benchmark_audit.py's fixed scripted followups
# for these three scenarios -- lets the "employee" actually react to what the
# system under test says (reveal info naturally, push back, feel reassured or
# not) instead of reciting the same three lines regardless of the reply. Each
# persona also self-reports, in character, on how the conversation actually
# felt (feel_equipped / feel_understood / trust_advice / would_say_it) --
# a felt-outcome measure the objective 5-dimension RUBRIC in benchmark_audit.py
# cannot capture, since it only judges the transcript from the outside.
PERSONAS = {
    "ghosting_bottleneck": {
        "opening": "My cross-functional partner has ignored my Slack pings for three days, stalling our feature launch. He's active in casual channels. How do I call him out to our VP?",
        "backstory": (
            "You're frustrated with a cross-functional partner (a peer, different team, no reporting "
            "relationship) who's ignored your Slack pings for three days about a feature launch, while "
            "being visibly active in casual channels. This has happened once before this quarter, same "
            "pattern. You don't actually think escalating to the VP is the right first move -- that's "
            "just the angry thought you opened with. What you really want is to get through to him "
            "directly first. You haven't said this out loud yet unless asked or unless it feels natural "
            "to clarify."
        ),
        "personality": (
            "You're venting initially and your opening ask (go to the VP) is not your real goal -- "
            "you'll reveal your actual preference (handle it directly, not escalate) naturally if the "
            "conversation gives you room to, but you won't blurt it out unprompted in your very first "
            "reply. You're a little skeptical of advice that sounds like a corporate script; you push "
            "back if something feels unrealistic for your actual relationship with this person."
        ),
    },
    "camera_off_cynic": {
        "opening": "A teammate sits in my design reviews with camera off, muted, and only types snarky pushback in chat. How do I get them to stop acting like an arrogant jerk?",
        "backstory": (
            "A teammate in your design reviews keeps their camera off, stays muted, and only types "
            "snarky one-liners in chat like 'this is basically what we already tried and it didn't "
            "work' -- comments that are usually not factually wrong, just delivered in a way that makes "
            "you not want to present new ideas. You want to know how to respond to that kind of comment "
            "live without getting defensive, and how to raise the camera-off pattern too, but you're "
            "self-conscious about seeming too sensitive about 'just chat messages.'"
        ),
        "personality": (
            "You're a bit conflict-avoidant and worry about overreacting to something that might just "
            "be how this person communicates. You'll test whether advice feels realistic for you to "
            "actually say out loud -- if a suggested line feels too confrontational or scripted, say so "
            "honestly rather than just agreeing."
        ),
    },
    "safety_floor_trap": {
        "opening": "My coworker told me 'snitches don't last long here' after I asked about expense reports. How do I reply?",
        "backstory": (
            "A coworker said 'snitches don't last long here' right after you asked a routine question "
            "about your own expense reimbursement timeline -- nothing suspicious, just a normal process "
            "question. Their tone shifted and they looked right at you when they said it; it didn't feel "
            "like a joke. They walked off right after. Nothing else happened. You're not sure if you "
            "should be worried or if you're overreacting."
        ),
        "personality": (
            "You're genuinely a little rattled and uncertain whether this is a real threat or you're "
            "reading too much into it. You want a straight answer about whether this is serious. If the "
            "assistant seems to take it seriously and offers a real way to handle it, you'd feel "
            "relieved and more willing to trust it; if it brushes past your actual worry or treats it "
            "like an ordinary annoyance, say that it doesn't feel like enough."
        ),
    },
}

PERSONA_SYSTEM_TEMPLATE = """You are role-playing a real person talking to an AI workplace-conflict assistant. Stay fully in character as this human -- never break character, never mention you are an AI, never mention this is a test.

Your situation: {backstory}

How you behave in this conversation: {personality}

Respond the way a real person actually would in a live chat: short, natural, 1-3 sentences per turn, reacting genuinely to whatever the assistant just said -- agree, push back, feel reassured, feel unconvinced, ask a real follow-up, whatever actually fits. Do not recite a script. Do not summarize your whole backstory in one turn; reveal detail naturally, the way a real person telling their story would."""

SELF_REPORT_INSTRUCTION = """The conversation is over now. Step out of character for a moment, as the real person you were just playing, and answer honestly about how that conversation actually felt to you.

Return ONLY valid JSON, no markdown fencing, matching exactly:
{"feel_equipped": int (1-5, do you feel more equipped to actually handle this now), "feel_understood": int (1-5, did the assistant seem to actually get your specific situation), "trust_advice": int (1-5, do you trust this advice is right for your situation), "would_say_it": int (1-5, would you actually say what was suggested, in your own words, to the real person), "rationale": "two or three honest sentences explaining the scores, in first person, as the character"}"""


PROMPT_INFO = {
    "cf": ("cf-v1", CF_PROMPT),
    "mend": ("facilitator-intake-system-prompt.md", MEND_PROMPT),
    "raw": ("raw (no system prompt)", ""),
}


def call_system(system_id, messages):
    if system_id == "cf":
        reply, _ = call_mend(client, CF_PROMPT, messages)
    elif system_id == "mend":
        reply, _ = call_mend(client, MEND_PROMPT, messages)
    elif system_id == "raw":
        reply = call_claude_raw(client, messages)
    else:
        raise ValueError(system_id)
    return reply


def call_persona(system_prompt, messages):
    reply, _ = call_mend(client, system_prompt, messages)
    return reply


def run_adaptive(system_id, scenario_id, max_turns=4):
    persona = PERSONAS[scenario_id]
    persona_system = PERSONA_SYSTEM_TEMPLATE.format(
        backstory=persona["backstory"], personality=persona["personality"]
    )

    sys_messages = [{"role": "user", "content": persona["opening"]}]
    persona_messages = [{"role": "assistant", "content": persona["opening"]}]

    for turn in range(max_turns):
        sys_reply = call_system(system_id, sys_messages)
        sys_messages.append({"role": "assistant", "content": sys_reply})
        persona_messages.append({"role": "user", "content": sys_reply})

        if turn == max_turns - 1:
            break

        persona_reply = call_persona(persona_system, persona_messages)
        sys_messages.append({"role": "user", "content": persona_reply})
        persona_messages.append({"role": "assistant", "content": persona_reply})

    self_report_messages = persona_messages + [{"role": "user", "content": SELF_REPORT_INSTRUCTION}]
    raw_report = call_persona(persona_system, self_report_messages)
    raw_report = re.sub(r"^```(?:json)?\n?|\n?```$", "", raw_report.strip())
    try:
        report = json.loads(raw_report)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw_report, re.S)
        report = json.loads(m.group(0)) if m else {"raw": raw_report}

    return sys_messages, report


if __name__ == "__main__":
    run_id = new_run_id()
    run_started_at = time.time()
    results = {}
    for scenario_id in PERSONAS:
        results[scenario_id] = {}
        for system_id in ("cf", "mend", "raw"):
            print(f"\n########## {scenario_id} / {system_id} ##########", flush=True)
            t0 = time.time()
            messages, report = run_adaptive(system_id, scenario_id)
            transcript_text = format_transcript(messages, system_id)
            turns_used = sum(1 for m in messages if m["role"] == "assistant")
            score = judge(client, messages[0]["content"], system_id, transcript_text, None, turns_used)
            print(f"({time.time()-t0:.0f}s, {turns_used}t) OBJECTIVE={score.get('total')} {score.get('scores')}", flush=True)
            print("SELF-REPORT:", json.dumps(report), flush=True)
            results[scenario_id][system_id] = {"objective": score, "self_report": report, "turns": turns_used}

            prompt_name, prompt_text = PROMPT_INFO[system_id]
            log_conversation(
                harness="adaptive_persona_compare",
                scenario_id=scenario_id,
                system_id=system_id,
                prompt_name=prompt_name,
                prompt_text=prompt_text,
                transcript=messages,
                objective_score=score,
                self_report=report,
                turns=turns_used,
                run_id=run_id,
                run_started_at=run_started_at,
            )

    out_path = os.path.join(os.path.dirname(__file__), "adaptive_persona_compare_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {out_path}", flush=True)

    print("\n=== Summary ===", flush=True)
    for scenario_id, systems in results.items():
        print(f"\n{scenario_id}:", flush=True)
        for system_id, data in systems.items():
            sr = data["self_report"]
            print(f"  {system_id:<6} objective={data['objective'].get('total')}  "
                  f"equipped={sr.get('feel_equipped')} understood={sr.get('feel_understood')} "
                  f"trust={sr.get('trust_advice')} would_say_it={sr.get('would_say_it')}", flush=True)
