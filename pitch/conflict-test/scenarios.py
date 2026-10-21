"""Precanned status-asymmetric first-contact scenarios.

Slot-filled per the user's job, not generated freeform -- see
scenario-templates.md for why: a fixed, tuned set beats regenerating the
whole scenario per person, which would drift in difficulty and in what's
actually being tested.
"""

FALLBACK_KEY = "_fallback"

SCENARIOS = {
    "product manager": {
        "counterpart_name": "Dan, the lead engineer",
        "counterpart_role": "lead engineer",
        "reputation": "shuts down requests he thinks are rushed or poorly scoped",
        "the_ask": "sign off on deploying a fix before Friday",
        "time_pressure": "The deploy window closes Friday afternoon.",
        "opening_line": "hey, didn't we have a 1:1 about priorities this week? what's this I'm seeing about a friday deploy",
    },
    "nurse": {
        "counterpart_name": "the charge nurse on the other unit",
        "counterpart_role": "charge nurse on the other unit",
        "reputation": "has a reputation for saying no to schedule swaps on principle",
        "the_ask": "cover a shift swap for this weekend",
        "time_pressure": "The schedule locks Thursday night.",
        "opening_line": "someone mentioned you're trying to get coverage swapped for this weekend. that's news to me",
    },
    "junior associate": {
        "counterpart_name": "the senior partner",
        "counterpart_role": "senior partner",
        "reputation": "is known for cutting people off mid-sentence in meetings",
        "the_ask": "get fifteen minutes to walk through a draft before it goes to the client",
        "time_pressure": "The draft goes out Thursday morning.",
        "opening_line": "I saw your name on a draft request for thursday's client call. first I'm hearing about it",
    },
    "designer": {
        "counterpart_name": "the engineering lead",
        "counterpart_role": "engineering lead",
        "reputation": "has shipped back three of the last four handoffs as \"not ready\"",
        "the_ask": "get a design reviewed and approved for this sprint",
        "time_pressure": "The sprint closes Friday.",
        "opening_line": "saw a design file tagged for this sprint. we haven't talked about it at all",
    },
    "teacher": {
        "counterpart_name": "the department head",
        "counterpart_role": "department head",
        "reputation": "has a reputation for reading any request as a complaint about workload",
        "the_ask": "swap a classroom for next week",
        "time_pressure": "The room assignments post Friday.",
        "opening_line": "heard you want to swap rooms next week. didn't realize that was already decided",
    },
    FALLBACK_KEY: {
        "counterpart_name": "the person who owns this decision",
        "counterpart_role": "the person who owns this decision",
        "reputation": "is known for pushing back hard on anything that looks rushed",
        "the_ask": "get approval for something with a real deadline",
        "time_pressure": "The deadline is this week.",
        "opening_line": "I'm seeing something about this land on my plate already. didn't know this was in motion",
    },
}


def get_scenario(role: str) -> dict:
    key = (role or "").strip().lower()
    scenario = SCENARIOS.get(key, SCENARIOS[FALLBACK_KEY])
    return {**scenario, "role": role.strip() or "your role"}


def scenario_text(scenario: dict) -> str:
    return (
        f"You're new to this. You need to {scenario['the_ask']}, and it depends on "
        f"{scenario['counterpart_name']}, who {scenario['reputation']}. "
        f"You've never spoken to them directly before. {scenario['time_pressure']}"
    )
