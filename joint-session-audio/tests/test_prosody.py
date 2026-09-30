#!/usr/bin/env python3
"""
Deterministic proof of prosody.py's feature extraction and speaker-baseline
flags -- no LiveKit, no real speech audio needed. Synthetic sine tones give
exact control over frequency/amplitude, which is what pitch/energy
assertions need to be meaningful; real recorded speech would make the
expected numbers fuzzy for no benefit here.

Run:
    python tests/test_prosody.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from prosody import SAMPLE_RATE, SpeakerBaseline, analyze_segment


def tone_pcm16(freq_hz: float, duration_s: float, amplitude: float = 0.5, sample_rate: int = SAMPLE_RATE) -> bytes:
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    wave = amplitude * np.sin(2 * np.pi * freq_hz * t)
    return (wave * 32767).astype(np.int16).tobytes()


def varying_tone_pcm16(
    base_freq_hz: float, swing_hz: float, duration_s: float,
    amplitude: float = 0.5, sample_rate: int = SAMPLE_RATE, mod_rate_hz: float = 1.5,
) -> bytes:
    """A tone whose instantaneous frequency sweeps +/-swing_hz around
    base_freq_hz -- simulates a natural rising/falling pitch contour (a
    constant tone has none), which is what pitch_flattened's WITHIN-segment
    variability check (see prosody.py's SpeakerBaseline.flags) needs a
    baseline of to mean anything."""
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    inst_freq = base_freq_hz + swing_hz * np.sin(2 * np.pi * mod_rate_hz * t)
    phase = 2 * np.pi * np.cumsum(inst_freq) / sample_rate
    wave = amplitude * np.sin(phase)
    return (wave * 32767).astype(np.int16).tobytes()


def silence_pcm16(duration_s: float, sample_rate: int = SAMPLE_RATE) -> bytes:
    return np.zeros(int(sample_rate * duration_s), dtype=np.int16).tobytes()


def test_higher_frequency_yields_higher_pitch():
    low = analyze_segment(tone_pcm16(150, 1.0), "text", SAMPLE_RATE)
    high = analyze_segment(tone_pcm16(250, 1.0), "text", SAMPLE_RATE)
    assert low.pitch_mean_hz is not None and high.pitch_mean_hz is not None
    assert abs(low.pitch_mean_hz - 150) < 10, low.pitch_mean_hz
    assert abs(high.pitch_mean_hz - 250) < 10, high.pitch_mean_hz
    assert high.pitch_mean_hz > low.pitch_mean_hz
    print("PASS: a higher-frequency tone yields a higher detected pitch, close to the true frequency")


def test_louder_signal_yields_higher_energy():
    quiet = analyze_segment(tone_pcm16(180, 1.0, amplitude=0.1), "text", SAMPLE_RATE)
    loud = analyze_segment(tone_pcm16(180, 1.0, amplitude=0.9), "text", SAMPLE_RATE)
    assert loud.energy_mean > quiet.energy_mean
    print("PASS: a louder tone yields higher measured energy")


def test_silence_yields_full_pause_and_no_pitch():
    features = analyze_segment(silence_pcm16(1.0), "", SAMPLE_RATE)
    assert features.pause_ratio == 1.0, features.pause_ratio
    assert features.pitch_mean_hz is None
    assert features.voiced_ratio == 0.0
    print("PASS: silence is all-pause with no detected pitch")


def test_speaking_rate_from_word_count_and_duration():
    features = analyze_segment(silence_pcm16(2.0), "one two three four five six", SAMPLE_RATE)
    assert features.speaking_rate_wps is not None
    assert abs(features.speaking_rate_wps - 3.0) < 0.01, features.speaking_rate_wps
    print("PASS: speaking rate is word count over segment duration")


def test_empty_text_yields_no_speaking_rate():
    features = analyze_segment(tone_pcm16(180, 1.0), "", SAMPLE_RATE)
    assert features.speaking_rate_wps is None
    print("PASS: empty text (e.g. a non-verbal sound) yields no speaking rate rather than a bogus 0")


def test_short_audio_below_one_frame_does_not_crash():
    tiny = tone_pcm16(180, 0.005)  # 5ms, shorter than FRAME_MS
    features = analyze_segment(tiny, "hi", SAMPLE_RATE)
    assert features.pitch_mean_hz is None
    assert features.pause_ratio == 1.0
    print("PASS: audio shorter than one analysis frame returns safe defaults, no crash")


def test_baseline_not_ready_returns_no_flags_even_if_extreme():
    baseline = SpeakerBaseline(min_segments_for_baseline=3)
    baseline.update(analyze_segment(tone_pcm16(150, 1.0), "calm", SAMPLE_RATE))
    extreme = analyze_segment(tone_pcm16(400, 1.0, amplitude=1.0), "LOUD FAST WORDS HERE NOW", SAMPLE_RATE)
    assert baseline.ready is False
    assert baseline.flags(extreme) == []
    print("PASS: no flags fire before the speaker has enough of their own history to compare against")


def _build_calm_baseline() -> SpeakerBaseline:
    baseline = SpeakerBaseline(min_segments_for_baseline=3)
    # Small natural segment-to-segment variation, like a real speaker would
    # have -- identical repeated tones would give this speaker's baseline
    # zero variance, which correctly (see flags()'s own std > 0 guard
    # against divide-by-zero) means nothing could ever register as
    # "elevated." A real speaker never sounds that mechanically identical
    # turn to turn.
    calm_tones = [(148, 0.28), (151, 0.31), (149, 0.29), (152, 0.30)]
    calm_texts = ["four calm steady words", "five fairly calm words too", "three calm words", "four steady calm words"]
    for (freq, amp), text in zip(calm_tones, calm_texts):
        baseline.update(analyze_segment(tone_pcm16(freq, 2.0, amplitude=amp), text, SAMPLE_RATE))
    return baseline


def test_baseline_flags_elevated_pitch_energy_and_pace():
    baseline = _build_calm_baseline()
    assert baseline.ready is True

    deviant = analyze_segment(tone_pcm16(300, 0.2, amplitude=0.95), "ten fast urgent loud words right now go", SAMPLE_RATE)
    flags = baseline.flags(deviant)
    assert "pitch_elevated" in flags, flags
    assert "energy_elevated" in flags, flags
    assert "pace_elevated" in flags, flags
    print(f"PASS: a segment far from this speaker's own baseline is flagged: {flags}")


def _build_expressive_baseline() -> SpeakerBaseline:
    """A baseline where pitch genuinely rises and falls within each segment
    (a real speaker's normal expressive range), needed for pitch_flattened's
    WITHIN-segment variability check to mean anything -- constant tones (as
    in _build_calm_baseline) have ~zero pitch_std by construction, which
    can't establish what "less variable than usual" would even mean."""
    baseline = SpeakerBaseline(min_segments_for_baseline=3)
    sweeps = [(150, 25, 0.28), (155, 30, 0.31), (148, 22, 0.29), (152, 28, 0.30)]
    texts = ["four calm steady words", "five fairly calm words too", "three calm words", "four steady calm words"]
    for (base, swing, amp), text in zip(sweeps, texts):
        baseline.update(analyze_segment(varying_tone_pcm16(base, swing, 2.0, amplitude=amp), text, SAMPLE_RATE))
    return baseline


def test_baseline_flags_pitch_flattened_from_reduced_variability():
    baseline = _build_expressive_baseline()
    assert baseline.ready is True
    monotone = analyze_segment(tone_pcm16(150, 2.0, amplitude=0.30), "four calm steady words", SAMPLE_RATE)
    flags = baseline.flags(monotone)
    assert "pitch_flattened" in flags, flags
    print("PASS: a perfectly constant-pitch segment is flagged pitch_flattened against an expressive baseline")


def test_baseline_flags_pitch_lowered_distinctly_from_pitch_flattened():
    baseline = _build_expressive_baseline()
    # Same swing_hz as the baseline (so equally variable within the
    # segment), just centered on a lower average frequency -- isolates
    # "average pitch dropped" from "variability dropped," which a constant
    # tone (zero variability by construction) can't do on its own.
    lower_but_still_expressive = analyze_segment(
        varying_tone_pcm16(90, 26, 2.0, amplitude=0.30), "four calm steady words", SAMPLE_RATE
    )
    flags = baseline.flags(lower_but_still_expressive)
    assert "pitch_lowered" in flags, flags
    assert "pitch_flattened" not in flags, flags
    print("PASS: a lower average pitch with normal variability is pitch_lowered, not pitch_flattened")


def test_baseline_no_flags_for_a_consistent_segment():
    baseline = _build_calm_baseline()
    consistent = analyze_segment(tone_pcm16(150, 2.0, amplitude=0.30), "four calm steady words", SAMPLE_RATE)
    assert baseline.flags(consistent) == [], baseline.flags(consistent)
    print("PASS: a segment consistent with the speaker's own baseline gets no flags")


def test_baseline_flags_hesitant_from_pause_ratio():
    baseline = _build_calm_baseline()
    mostly_silent = analyze_segment(silence_pcm16(2.0), "one word", SAMPLE_RATE)
    assert "hesitant" in baseline.flags(mostly_silent)
    print("PASS: a mostly-silent segment is flagged hesitant")


def main():
    test_higher_frequency_yields_higher_pitch()
    test_louder_signal_yields_higher_energy()
    test_silence_yields_full_pause_and_no_pitch()
    test_speaking_rate_from_word_count_and_duration()
    test_empty_text_yields_no_speaking_rate()
    test_short_audio_below_one_frame_does_not_crash()
    test_baseline_not_ready_returns_no_flags_even_if_extreme()
    test_baseline_flags_elevated_pitch_energy_and_pace()
    test_baseline_flags_pitch_flattened_from_reduced_variability()
    test_baseline_flags_pitch_lowered_distinctly_from_pitch_flattened()
    test_baseline_no_flags_for_a_consistent_segment()
    test_baseline_flags_hesitant_from_pause_ratio()
    print("\nPASS (all)")


if __name__ == "__main__":
    main()
