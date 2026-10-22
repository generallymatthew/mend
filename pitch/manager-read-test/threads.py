# Each thread is a fixed conflict *shape*: a sequence of "beats" (what each
# message needs to accomplish structurally) rather than literal text. The
# manager's job gets used to re-skin the beats into domain-appropriate
# dialogue (new names, new jargon, new artifact being disputed), but the
# beat count, order, and underlying structural collision never change. This
# mirrors conflict-test's precanned-shape-not-regenerated-shape principle:
# the thing being tested stays fixed, only the surface changes.

THREADS = {
    "analytics-schema": {
        "structural_cause": (
            "One person's deadline-driven metric (e.g. a launch date, a client "
            "commitment) collides with the other person's integrity/stability "
            "metric (e.g. historical data correctness, uptime, a compliance "
            "requirement). Person A makes a change to serve their own deadline, "
            "genuinely believing it's minor, without realizing it breaks something "
            "Person B is accountable for."
        ),
        "beats": [
            {"from": "A", "intent": "Pings B with a routine status check ahead of an imminent planning or deadline meeting, asking for an input B owns."},
            {"from": "B", "intent": "Casually reveals they already changed something upstream for their own reasons, downplaying it as minor."},
            {"from": "A", "intent": "Asks exactly what changed, flagging that it could affect something A's team depends on."},
            {"from": "B", "intent": "Deflects to documentation or history instead of explaining directly, suggests raising it later in a group setting."},
            {"from": "A", "intent": "Spells out precisely what broke and why it violates an agreed process, citing a prior team agreement."},
            {"from": "B", "intent": "Responds with a single dismissive, near-wordless acknowledgment (like a one-emoji reply), not engaging with the substance."},
            {"from": "A", "intent": "Pushes back that the dismissive reply isn't enough, states the concrete cost or rework this will cause, asks for a specific accommodation (revert or delay)."},
            {"from": "B", "intent": "Refuses the accommodation citing their own fixed deadline, redirects the disagreement into an upcoming group meeting instead of resolving it directly."},
            {"from": "A", "intent": "Curtly agrees to raise it in the group meeting, signaling the disagreement is unresolved and will now surface in front of others."},
        ],
    },
    "checkout-revert": {
        "structural_cause": (
            "Person A builds and ships something they believe was already approved. "
            "Person B owns a technical or operational constraint (e.g. a performance "
            "budget, a safety limit, a compliance threshold) that the shipped thing "
            "quietly violates, because the approval A is pointing to never actually "
            "covered that constraint. Neither one documented the gap."
        ),
        "beats": [
            {"from": "A", "intent": "Notifies B that something has been pushed and is ready, implying it's basically finished and fine."},
            {"from": "B", "intent": "Reviews it and flags a concrete problem that violates a constraint B is accountable for."},
            {"from": "A", "intent": "Asserts it's already approved, implying B is raising this too late to matter."},
            {"from": "B", "intent": "Asks pointedly who approved it and for what, noting there's no sign-off covering the specific constraint B flagged."},
            {"from": "A", "intent": "Says it's been sitting in shared documentation for days, implying B should have caught it earlier and is the one being slow."},
            {"from": "B", "intent": "Rejects that framing, says they don't track every document that gets touched, holds their position."},
            {"from": "A", "intent": "States a hard deadline is coming regardless, implying this ships no matter what B thinks."},
            {"from": "B", "intent": "Unilaterally blocks or reverts the thing, asserting their constraint overrides the deadline."},
            {"from": "A", "intent": "Sarcastically criticizes the timing of B raising this so close to the deadline."},
        ],
    },
}
