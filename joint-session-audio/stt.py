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

    def push_audio(self, pcm_bytes: bytes) -> None:
        self._pending_audio.extend(pcm_bytes)
        self._recorder.feed_audio(pcm_bytes)

    def _handle_finalized(self) -> None:
        text = self._recorder.text()
        audio_bytes = bytes(self._pending_audio)
        self._pending_audio.clear()
        if not text.strip():
            return
        logger.debug("finalized participant=%s text=%r", self.participant_id, text)
        self._on_finalized_segment(audio_bytes, text)

    def shutdown(self) -> None:
        self._recorder.shutdown()
