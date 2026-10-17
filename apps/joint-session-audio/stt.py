"""
Streaming STT wrapper around RealtimeSTT (https://github.com/KoljaB/RealtimeSTT),
chosen over whisper_streaming per ../joint-session-architecture.md's "Suggested
stack": it's Python-native, has voice-activity detection built in, and takes
raw PCM frames directly via a callback rather than owning its own I/O loop --
a better fit for pushing audio frames in from a LiveKit track than a wrapper
built around reading from a live microphone device itself.

This is the "rolling transcript window" -> "fast real-time classifier" leg of
the per-participant pipeline diagram in that doc. It does not talk to
DelayBuffer directly -- agent.py wires `on_finalized_segment` to
`DelayBuffer.submit`, keeping STT and the delay/classify gate as separate,
independently testable pieces.

Real-time budget: ../joint-session-architecture.md:68 estimates roughly
500-800ms latency for open-source streaming Whisper setups -- that number is
unverified for this specific setup and should be measured (see
tests/test_delay_buffer.py's latency logging) before trusting a given
buffer_seconds value.
"""
import logging
from typing import Callable

from RealtimeSTT import AudioToTextRecorder

logger = logging.getLogger("mend.joint_session_audio.stt")

SAMPLE_RATE = 16000  # RealtimeSTT and LiveKit's default PCM format both expect 16kHz mono


class StreamingSTT:
    """One instance per connected employee. Feed raw 16kHz mono PCM frames via
    `push_audio`; `on_finalized_segment(audio_bytes, text)` fires once
    RealtimeSTT's own VAD decides an utterance is complete."""

    def __init__(self, participant_id: str, on_finalized_segment: Callable[[bytes, str], None]):
        self.participant_id = participant_id
        self._on_finalized_segment = on_finalized_segment
        self._pending_audio = bytearray()
        self._recorder = AudioToTextRecorder(
            use_microphone=False,  # frames are pushed in from LiveKit, not a local mic
            spinner=False,
            model="base.en",  # faster-whisper model size; swap for latency/accuracy tradeoff
            language="en",
            on_recording_stop=self._handle_finalized,
        )
        # Found live, in two separate layers -- both needed:
        #
        # 1. Without `.listen()`, the recorder never once started a
        # recording -- RealtimeSTT's own recording worker thread only acts
        # on voice activity when `start_recording_on_voice_activity` is
        # True, and that flag is set ONLY by `.listen()` (or the `.text()`/
        # `.wait_audio()` call a typical caller loops on) -- construction
        # alone never sets it. feed_audio() was reaching the recorder's
        # audio queue the whole time (confirmed live), but with nothing
        # ever arming listening, the worker thread's VAD check was
        # unreachable code every single pass, so `on_recording_stop` could
        # never fire regardless of any buffering/pacing fix.
        #
        # 2. `.listen()` alone (confirmed live, the next bug found once (1)
        # was fixed) gets recording STARTED but never stopped: RealtimeSTT's
        # own end-of-speech check in core/recording.py is gated behind a
        # SEPARATE flag, `stop_recording_on_voice_deactivity`, which
        # `.listen()` does not touch -- only `.text()`/`.wait_audio()`'s
        # internal bookkeeping sets it (core/lifecycle.py's
        # wait_for_recorded_audio), which this event-driven/callback usage
        # never calls. Left unset, it defaults to False forever, so once
        # recording starts here it simply never ends regardless of how much
        # silence follows. Setting it directly alongside `.listen()` is the
        # real fix, confirmed live: "recording started" now reliably
        # followed by "recording stopped" once real silence gaps play out.
        #
        # `.listen()`/`.text()` would also work (that's the library's own
        # intended blocking-loop pattern) but `.text()` blocks synchronously
        # waiting for a full record cycle -- wrong fit for a constructor or
        # a quick re-arm after each callback.
        self._recorder.listen()
        self._recorder.stop_recording_on_voice_deactivity = True

    def _rearm_listening(self) -> None:
        # stop_recording() (inside RealtimeSTT) clears both
        # start_recording_on_voice_activity and stop_recording_on_voice_
        # deactivity and does not set either again on its own -- confirmed
        # by reading core/lifecycle.py's stop_recording, which has no
        # equivalent of wait_audio()'s re-arm branch. Without repeating both
        # calls here after every finalized segment, only ever the FIRST
        # utterance of a session would transcribe; found live testing
        # multi-sentence real speech, where only silence followed the first
        # segment forever after.
        self._recorder.listen()
        self._recorder.stop_recording_on_voice_deactivity = True

    def push_audio(self, pcm_bytes: bytes) -> None:
        self._pending_audio.extend(pcm_bytes)
        self._recorder.feed_audio(pcm_bytes)

    def _handle_finalized(self) -> None:
        text = self._recorder.text()
        audio_bytes = bytes(self._pending_audio)
        self._pending_audio.clear()
        self._rearm_listening()
        if not text.strip():
            return
        logger.debug("finalized participant=%s text=%r", self.participant_id, text)
        self._on_finalized_segment(audio_bytes, text)

    def shutdown(self) -> None:
        self._recorder.shutdown()
