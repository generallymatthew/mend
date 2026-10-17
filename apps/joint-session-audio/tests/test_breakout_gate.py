#!/usr/bin/env python3
"""
Deterministic proof of the private side-conversation (breakout) gate -- no
LiveKit, no browser, mirrors tests/test_video_parity.py's split of "prove
the pure logic first" from the live end-to-end path, which needs a real
livekit-server and is a manual step per ../README.md's Known gaps.

Run:
    python tests/test_breakout_gate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from breakout_gate import BreakoutGate

IDENTITIES = ("employee_a", "employee_b")


def make_gate():
    transitions = []
    gate = BreakoutGate(IDENTITIES, on_state_changed=lambda old, new, target: transitions.append((old, new, target)))
    return gate, transitions


def test_enter_checkin_pauses_for_target():
    gate, transitions = make_gate()
    ok = gate.enter_checkin("employee_a")
    assert ok is True
    assert gate.state == "paused_checkin"
    assert gate.checkin_target == "employee_a"
    assert gate.other_identity == "employee_b"
    assert transitions == [("active", "paused_checkin", "employee_a")], transitions
    print("PASS: enter_checkin pauses the room for the named target")


def test_resume_returns_to_active():
    gate, transitions = make_gate()
    gate.enter_checkin("employee_b")
    transitions.clear()

    ok = gate.resume()
    assert ok is True
    assert gate.state == "active"
    assert gate.checkin_target is None
    assert gate.other_identity is None
    assert transitions == [("paused_checkin", "active", None)], transitions
    print("PASS: resume returns to active and clears the target")


def test_unknown_identity_rejected():
    gate, transitions = make_gate()
    ok = gate.enter_checkin("employee_c")
    assert ok is False
    assert gate.state == "active", gate.state
    assert transitions == [], f"expected no transition, got {transitions}"
    print("PASS: enter_checkin for an unknown identity is rejected, no state change")


def test_redundant_enter_checkin_same_target_is_noop():
    gate, transitions = make_gate()
    gate.enter_checkin("employee_a")
    transitions.clear()

    ok = gate.enter_checkin("employee_a")
    assert ok is True
    assert gate.state == "paused_checkin"
    assert gate.checkin_target == "employee_a"
    assert transitions == [], f"expected no transition on redundant call, got {transitions}"
    print("PASS: entering check-in again for the same target is a no-op, no double transition")


def test_enter_checkin_for_different_target_while_paused_is_rejected():
    gate, transitions = make_gate()
    gate.enter_checkin("employee_a")
    transitions.clear()

    ok = gate.enter_checkin("employee_b")
    assert ok is False
    assert gate.state == "paused_checkin"
    assert gate.checkin_target == "employee_a", "target must not silently switch"
    assert transitions == [], f"expected no transition, got {transitions}"
    print("PASS: switching the check-in target mid-pause is rejected, original target holds")


def test_redundant_resume_when_already_active_is_noop():
    gate, transitions = make_gate()
    ok = gate.resume()
    assert ok is True
    assert gate.state == "active"
    assert transitions == [], f"expected no transition, got {transitions}"
    print("PASS: resume while already active is a no-op")


def main():
    test_enter_checkin_pauses_for_target()
    test_resume_returns_to_active()
    test_unknown_identity_rejected()
    test_redundant_enter_checkin_same_target_is_noop()
    test_enter_checkin_for_different_target_while_paused_is_rejected()
    test_redundant_resume_when_already_active_is_noop()
    print("\nPASS (all)")


if __name__ == "__main__":
    main()
