"""
Symmetric video-parity gate: each employee opts in or out of showing real
webcam video: see facilitator-joint-session-system-prompt.md's future
video-awareness boundary and misc/'s reference sketch for the fairness
requirement this implements. If either employee never consented, or their
camera goes live-then-drops, BOTH employees fall back to voice + a neutral
avatar for the rest of the session -- nobody gets a one-sided view of the
room. See ../joint-session-audio/README.md's "Video opt-in" section.

No LiveKit dependency here -- same split as delay_buffer.py, so this is
unit-testable without a live server (see tests/test_video_parity.py).
agent.py is what wires real LiveKit participant/track events into
set_consent/set_camera_live and reacts to on_mode_changed.
"""
import logging
from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

logger = logging.getLogger("mend.joint_session_audio.video_parity")

RoomVideoMode = Literal["video_active", "avatar_audio_only"]


@dataclass
class ParticipantVideoStatus:
    identity: str
    consented: bool = False
    camera_live: bool = False


class VideoParityGate:
    """Tracks both employees' consent + live-camera state and derives the
    room's video mode. One-way latch: once the room has fallen back to
    avatar_audio_only, it never returns to video_active for the rest of the
    session, regardless of whether consent or camera state later look
    "fine" again -- there is deliberately no re-enable flow (see the plan's
    "Scope boundaries" and misc/'s own sketch, which declares but never
    implements a re-enable event either)."""

    def __init__(
        self,
        identities: tuple[str, str],
        on_mode_changed: Optional[Callable[[RoomVideoMode, RoomVideoMode], None]] = None,
    ):
        self._status = {i: ParticipantVideoStatus(i) for i in identities}
        self._ever_dropped = False
        self.mode: RoomVideoMode = "avatar_audio_only"
        self._on_mode_changed = on_mode_changed

    def set_consent(self, identity: str, consented: bool) -> RoomVideoMode:
        self._status[identity].consented = consented
        return self._recompute()

    def set_camera_live(self, identity: str, live: bool) -> RoomVideoMode:
        self._status[identity].camera_live = live
        return self._recompute()

    def _recompute(self) -> RoomVideoMode:
        old_mode = self.mode
        statuses = list(self._status.values())
        both_ready = all(s.consented and s.camera_live for s in statuses)
        new_mode: RoomVideoMode = (
            "video_active" if both_ready and not self._ever_dropped else "avatar_audio_only"
        )

        if new_mode == "avatar_audio_only" and old_mode == "video_active":
            self._ever_dropped = True

        self.mode = new_mode
        if new_mode != old_mode:
            logger.info("video mode %s -> %s", old_mode, new_mode)
            if self._on_mode_changed:
                self._on_mode_changed(old_mode, new_mode)
        return new_mode
