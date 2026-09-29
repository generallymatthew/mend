#!/usr/bin/env python3
"""
Deterministic proof of the symmetric video-parity gate -- no LiveKit, no
browser, no camera hardware, mirrors tests/test_delay_buffer.py's split of
"prove the pure logic first" from "the live end-to-end path needs a real
browser+camera, documented as a manual step in ../README.md's Known gaps."

Run:
    python tests/test_video_parity.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from video_parity import VideoParityGate

IDENTITIES = ("employee_a", "employee_b")


def make_gate():
    transitions = []
    gate = VideoParityGate(IDENTITIES, on_mode_changed=lambda old, new: transitions.append((old, new)))
    return gate, transitions


def both_consent_and_live(gate):
    gate.set_consent("employee_a", True)
    gate.set_consent("employee_b", True)
    gate.set_camera_live("employee_a", True)
    gate.set_camera_live("employee_b", True)


def test_both_consent_both_live_goes_active():
    gate, transitions = make_gate()
    both_consent_and_live(gate)
    assert gate.mode == "video_active", gate.mode
    print("PASS: both consent + both live -> video_active")


def test_one_never_consents_stays_avatar_forever():
    gate, transitions = make_gate()
    gate.set_consent("employee_a", True)
    gate.set_camera_live("employee_a", True)
    # employee_b never consents at all
    gate.set_camera_live("employee_b", True)
    assert gate.mode == "avatar_audio_only", gate.mode
    assert transitions == [], f"expected no transitions, got {transitions}"
    print("PASS: one participant never consenting -> avatar_audio_only forever")


def test_drop_after_both_live_falls_back_once():
    gate, transitions = make_gate()
    both_consent_and_live(gate)
    assert gate.mode == "video_active"
    transitions.clear()  # only count transitions from here on

    gate.set_camera_live("employee_a", False)  # the drop
    assert gate.mode == "avatar_audio_only", gate.mode
    assert transitions == [("video_active", "avatar_audio_only")], transitions
    print("PASS: drop after both-live -> avatar_audio_only, fires exactly once")


def test_latch_no_revert_after_drop():
    gate, transitions = make_gate()
    both_consent_and_live(gate)
    gate.set_camera_live("employee_a", False)  # drop -> latched
    transitions.clear()

    gate.set_camera_live("employee_a", True)  # "camera comes back"
    assert gate.mode == "avatar_audio_only", (
        f"expected the latch to hold, got {gate.mode}"
    )
    assert transitions == [], f"expected no transition on recovery, got {transitions}"
    print("PASS: camera coming back after a drop does not revert mode (latch holds)")


def test_disconnect_equivalent_triggers_same_fallback():
    gate, transitions = make_gate()
    both_consent_and_live(gate)
    transitions.clear()

    # agent.py treats participant_disconnected the same as an explicit
    # track_unpublished -- both call set_camera_live(identity, False).
    gate.set_camera_live("employee_b", False)
    assert gate.mode == "avatar_audio_only", gate.mode
    assert transitions == [("video_active", "avatar_audio_only")], transitions
    print("PASS: disconnect-equivalent triggers the same fallback as an explicit unpublish")


def main():
    test_both_consent_both_live_goes_active()
    test_one_never_consents_stays_avatar_forever()
    test_drop_after_both_live_falls_back_once()
    test_latch_no_revert_after_drop()
    test_disconnect_equivalent_triggers_same_fallback()
    print("\nPASS (all)")


if __name__ == "__main__":
    main()
