"""
The broadcast-delay mechanism from ../joint-session-architecture.md: each
employee's outbound audio is held for `buffer_seconds` before it's released
to the *other* employee, so the fast classifier (../classifier/inference.py)
has a window to gate it. This module owns only the buffer + classifier-gate
decision, not the audio transport or the STT itself -- see agent.py for how
a LiveKit room wires an STT engine's finalized chunks into `submit()`.

Segment = one STT-finalized (audio, text) pair for one speaker. Each segment
is delayed and classified independently, concurrently with any other segment
already in flight for the same speaker -- this is a proof-of-concept for the
gate mechanism itself (see joint-session-architecture.md's "Not yet
designed"), not a production-hardened sequencer; overlapping segments with
very different classify latencies could in principle release out of order.
Real deployment would need explicit per-speaker sequencing on top of this.
"""
import asyncio
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).parent
CLASSIFIER_DIR = ROOT.parent / "classifier"
sys.path.insert(0, str(CLASSIFIER_DIR))
from inference import ConflictClassifier  # noqa: E402

logger = logging.getLogger("mend.joint_session_audio.delay_buffer")

# Same checkpoint and threshold convention as ../joint-session-app/server.py:
# v3, not v4 -- see classifier/README.md's Results section and commit
# 314e6c2 for why v4's cut_trigger F1 regressed despite fixing
# illegal_activity.
DEFAULT_MODEL_DIR = CLASSIFIER_DIR / "output" / "mend-conflict-classifier-v3"
DEFAULT_CUT_THRESHOLD = 0.9
DEFAULT_BUFFER_SECONDS = 1.5


def load_default_classifier(cut_threshold: float = DEFAULT_CUT_THRESHOLD) -> ConflictClassifier:
    return ConflictClassifier(str(DEFAULT_MODEL_DIR), cut_threshold=cut_threshold)


class DelayBuffer:
    def __init__(
        self,
        participant_id: str,
        classifier: ConflictClassifier,
        buffer_seconds: float = DEFAULT_BUFFER_SECONDS,
        executor: Optional[ThreadPoolExecutor] = None,
        on_release: Optional[Callable[[bytes], None]] = None,
        on_cut: Optional[Callable[[str, dict, float], None]] = None,
    ):
        self.participant_id = participant_id
        self.classifier = classifier
        self.buffer_seconds = buffer_seconds
        self._executor = executor
        self.on_release = on_release
        self.on_cut = on_cut

    async def submit(self, audio_bytes: bytes, text: str) -> Optional[bytes]:
        """Delay one finalized STT segment, gate it on the classifier, then
        either release the audio (return it / fire on_release) or drop it
        (return None / fire on_cut). Awaiting this call blocks for roughly
        `buffer_seconds` minus however long classification took -- callers
        that need several segments in flight at once should
        `asyncio.create_task(buffer.submit(...))` rather than await serially.
        """
        start = time.monotonic()
        loop = asyncio.get_running_loop()
        cut, scores = await loop.run_in_executor(
            self._executor, self.classifier.should_cut, text
        )
        classify_latency = time.monotonic() - start
        remaining = self.buffer_seconds - classify_latency
        if remaining > 0:
            await asyncio.sleep(remaining)

        if cut:
            logger.info(
                "CUT participant=%s latency=%.3fs scores=%s text=%r",
                self.participant_id, classify_latency, scores, text,
            )
            if self.on_cut:
                self.on_cut(text, scores, classify_latency)
            return None

        logger.info(
            "release participant=%s latency=%.3fs text=%r",
            self.participant_id, classify_latency, text,
        )
        if self.on_release:
            self.on_release(audio_bytes)
        return audio_bytes
