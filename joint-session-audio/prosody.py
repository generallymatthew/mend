"""
Prosodic-feature extraction for one STT-finalized audio segment: pitch,
loudness/energy, speaking rate, and pauses -- interpretable acoustic signals
a text transcript alone can't carry. A flat, deadpan "sure, that's fine"
reads identically to a sincere one once it's been transcribed to text; this
module gives a facilitator (human or a future LLM) something a transcript
alone doesn't: whether THIS segment sounded unusually tense, fast, flat, or
loud *for this same speaker*, relative to how they've sounded earlier in the
session.

Deliberately NOT a sarcasm or intent classifier, and doesn't claim to be one
-- see ../joint-session-architecture.md and README.md's "Prosody" section
for why: reliable audio-only sarcasm/intent detection is a hard, unsolved
research problem, and this product leans hard toward precision over false
positives everywhere else it makes an automated call (../classifier/README.md's
Results section shows what happens when an under-validated signal gets
trusted too early, even with good intentions behind it). Output here is
auxiliary context for a human or a future prompt to weigh alongside the
transcript, not a confidence score or a decision -- it is NOT wired into
../classifier/inference.py's real-time cut decision.

Every function here is pure/stateless except SpeakerBaseline, and none of it
needs a live LiveKit server -- see tests/test_prosody.py.
"""
import dataclasses
from typing import List, Optional

import numpy as np

SAMPLE_RATE = 16000  # matches stt.py -- RealtimeSTT/LiveKit's shared PCM16 mono rate

FRAME_MS = 30
HOP_MS = 15
MIN_PITCH_HZ = 70.0   # below typical human speech F0 floor
MAX_PITCH_HZ = 400.0  # above typical human speech F0 ceiling
VOICED_CORR_THRESHOLD = 0.3  # normalized autocorrelation peak needed to call a frame voiced
SILENCE_RMS = 0.02  # frames below this (int16-normalized RMS) count as a pause, not speech


@dataclasses.dataclass
class ProsodyFeatures:
    duration_s: float
    pitch_mean_hz: Optional[float]  # None if no voiced frames were found at all
    pitch_std_hz: Optional[float]
    energy_mean: float
    energy_std: float
    speaking_rate_wps: Optional[float]  # None if text is empty
    pause_ratio: float  # fraction of frames below SILENCE_RMS
    voiced_ratio: float  # fraction of frames with a detectable pitch


def _pcm16_to_float(audio_bytes: bytes) -> np.ndarray:
    samples = np.frombuffer(audio_bytes, dtype=np.int16)
    return samples.astype(np.float32) / 32768.0


def _frame_signal(samples: np.ndarray, sample_rate: int, frame_ms: int, hop_ms: int) -> np.ndarray:
    frame_len = max(1, int(sample_rate * frame_ms / 1000))
    hop_len = max(1, int(sample_rate * hop_ms / 1000))
    if len(samples) < frame_len:
        return np.empty((0, frame_len), dtype=np.float32)
    n_frames = 1 + (len(samples) - frame_len) // hop_len
    return np.stack([samples[i * hop_len : i * hop_len + frame_len] for i in range(n_frames)])


def _frame_pitch_hz(frame: np.ndarray, sample_rate: int) -> Optional[float]:
    """Autocorrelation pitch estimate for one frame, or None if unvoiced/too
    quiet. Plain numpy autocorrelation rather than a dedicated pitch-tracking
    library -- accurate enough to answer "is this segment's pitch notably
    higher or more variable than usual for this speaker," not phonetics-grade
    precision, which this doesn't need."""
    frame = frame - frame.mean()
    if np.sqrt(np.mean(frame ** 2)) < SILENCE_RMS:
        return None
    corr = np.correlate(frame, frame, mode="full")
    corr = corr[len(corr) // 2 :]
    corr = corr / (corr[0] + 1e-12)
    min_lag = int(sample_rate / MAX_PITCH_HZ)
    max_lag = min(int(sample_rate / MIN_PITCH_HZ), len(corr) - 1)
    if max_lag <= min_lag:
        return None
    search = corr[min_lag : max_lag + 1]
    peak_idx = int(np.argmax(search))
    if search[peak_idx] < VOICED_CORR_THRESHOLD:
        return None
    return sample_rate / (min_lag + peak_idx)


def analyze_segment(audio_bytes: bytes, text: str, sample_rate: int = SAMPLE_RATE) -> ProsodyFeatures:
    """Extract prosodic features from one finalized STT segment's raw PCM16
    mono audio and its transcribed text (used only for a word count, to get
    speaking rate -- no re-transcription happens here)."""
    samples = _pcm16_to_float(audio_bytes)
    duration_s = len(samples) / sample_rate if sample_rate else 0.0
    word_count = len(text.split())
    speaking_rate = (word_count / duration_s) if (text.strip() and duration_s > 0) else None

    frames = _frame_signal(samples, sample_rate, FRAME_MS, HOP_MS)
    if len(frames) == 0:
        return ProsodyFeatures(duration_s, None, None, 0.0, 0.0, speaking_rate, 1.0, 0.0)

    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    pause_ratio = float(np.mean(rms < SILENCE_RMS))

    pitches = [p for p in (_frame_pitch_hz(f, sample_rate) for f in frames) if p is not None]
    voiced_ratio = len(pitches) / len(frames)
    pitch_mean = float(np.mean(pitches)) if pitches else None
    pitch_std = float(np.std(pitches)) if len(pitches) > 1 else (0.0 if pitches else None)

    return ProsodyFeatures(
        duration_s=duration_s,
        pitch_mean_hz=pitch_mean,
        pitch_std_hz=pitch_std,
        energy_mean=float(np.mean(rms)),
        energy_std=float(np.std(rms)),
        speaking_rate_wps=speaking_rate,
        pause_ratio=pause_ratio,
        voiced_ratio=voiced_ratio,
    )


@dataclasses.dataclass
class _RunningStat:
    """Welford's streaming mean/variance -- a speaker's baseline updates for
    the whole session without ever storing their past segments."""

    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (x - self.mean)

    @property
    def std(self) -> float:
        return (self.m2 / (self.n - 1)) ** 0.5 if self.n >= 2 else 0.0


class SpeakerBaseline:
    """Tracks one speaker's own rolling pitch/energy/pace across a session,
    so a later segment can be judged against how THIS person normally
    sounds rather than a fixed population threshold. Baseline F0 alone
    varies hugely across speakers (adult men vs. women, individual
    variation) -- an absolute pitch cutoff would mostly just be a proxy for
    "who's talking," not for tension."""

    def __init__(self, min_segments_for_baseline: int = 3):
        self.min_segments_for_baseline = min_segments_for_baseline
        self._pitch = _RunningStat()
        self._energy = _RunningStat()
        self._rate = _RunningStat()

    @property
    def ready(self) -> bool:
        return self._energy.n >= self.min_segments_for_baseline

    def update(self, features: ProsodyFeatures) -> None:
        if features.pitch_mean_hz is not None:
            self._pitch.update(features.pitch_mean_hz)
        self._energy.update(features.energy_mean)
        if features.speaking_rate_wps is not None:
            self._rate.update(features.speaking_rate_wps)

    def flags(self, features: ProsodyFeatures, z_threshold: float = 1.5) -> List[str]:
        """Human-readable flags for how far THIS segment sits from this
        speaker's own baseline -- deliberately legible rather than a single
        opaque score, so a person (or a future prompt) can weigh it
        themselves instead of trusting a black box. Empty, including while
        the baseline is still warming up (`ready` is False): "no flags yet"
        is the honest answer when there isn't enough of this speaker's own
        history to compare against."""
        if not self.ready:
            return []
        out: List[str] = []
        if features.pitch_mean_hz is not None and self._pitch.std > 0:
            z = (features.pitch_mean_hz - self._pitch.mean) / self._pitch.std
            if z >= z_threshold:
                out.append("pitch_elevated")
            elif z <= -z_threshold:
                # notably flatter/lower than this speaker's own norm -- can
                # read as deadpan delivery or withdrawal, not a claim of
                # which; see module docstring
                out.append("pitch_flattened")
        if self._energy.std > 0:
            z = (features.energy_mean - self._energy.mean) / self._energy.std
            if z >= z_threshold:
                out.append("energy_elevated")
        if features.speaking_rate_wps is not None and self._rate.std > 0:
            z = (features.speaking_rate_wps - self._rate.mean) / self._rate.std
            if z >= z_threshold:
                out.append("pace_elevated")
            elif z <= -z_threshold:
                out.append("pace_slowed")
        if features.pause_ratio >= 0.5:
            out.append("hesitant")
        return out
