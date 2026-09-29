"""
Private side-conversation ("breakout") gate: tracks whether the joint-session
room is paused for a private check-in with one employee, and who that
employee is. See ../joint-session-architecture.md's "Session state machine"
section for the conceptual version, and its "Not yet designed" note on how
the private breakout sub-room is implemented in LiveKit specifically --
this module, plus its wiring into agent.py below, is that piece.

Deliberately mirrors ../joint-session-app/server.py's own session_state /
checkin_target vocabulary (paused_checkin) rather than inventing a new one,
so a future integration connecting the two has a natural interface to call
into. That integration -- giving this audio bridge an actual facilitator
voice, driven live by joint-session-app's LLM -- is explicitly out of scope
here; see README.md's Scope boundaries.

No LiveKit dependency here -- same split as delay_buffer.py and
video_parity.py, so this is unit-testable without a live server (see
tests/test_breakout_gate.py). agent.py is what wires real audio
publish/subscribe control into enter_checkin/resume and reacts to
on_state_changed.
"""
import logging
from typing import Callable, Literal, Optional

logger = logging.getLogger("mend.joint_session_audio.breakout_gate")

SessionState = Literal["active", "paused_checkin"]


class BreakoutGate:
    """Tracks the room's side-conversation state for exactly two employee
    identities. Conservative by design: entering a check-in for a new target
    while already paused for a different one is rejected rather than
    silently switching targets, and redundant enter/resume calls are
    no-ops -- same "don't guess, don't double-fire" posture as
    VideoParityGate."""

    def __init__(
        self,
        identities: tuple[str, str],
        on_state_changed: Optional[Callable[[SessionState, SessionState, Optional[str]], None]] = None,
    ):
        self._identities = set(identities)
        self.state: SessionState = "active"
        self.checkin_target: Optional[str] = None
        self._on_state_changed = on_state_changed

    def enter_checkin(self, target_identity: str) -> bool:
        if target_identity not in self._identities:
            logger.warning("enter_checkin: unknown identity %s", target_identity)
            return False
        if self.state == "paused_checkin":
            if self.checkin_target == target_identity:
                return True  # already paused for this person -- no-op
            logger.warning(
                "enter_checkin: already paused for %s, ignoring request for %s",
                self.checkin_target, target_identity,
            )
            return False
        self._transition("paused_checkin", target_identity)
        return True

    def resume(self) -> bool:
        if self.state == "active":
            return True  # already active -- no-op
        self._transition("active", None)
        return True

    @property
    def other_identity(self) -> Optional[str]:
        """The non-target employee while paused, None otherwise."""
        if self.checkin_target is None:
            return None
        return next(i for i in self._identities if i != self.checkin_target)

    def _transition(self, new_state: SessionState, checkin_target: Optional[str]) -> None:
        old_state = self.state
        self.state = new_state
        self.checkin_target = checkin_target
        logger.info("breakout state %s -> %s (target=%s)", old_state, new_state, checkin_target)
        if self._on_state_changed:
            self._on_state_changed(old_state, new_state, checkin_target)
