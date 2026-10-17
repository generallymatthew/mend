#!/usr/bin/env python3
"""
Manual validation of prosody.py against real synthesized speech -- macOS
`say` (genuine formants/harmonics/prosody, not the sine tones
test_prosody.py's unit tests use), not a live human recording: this
sandboxed dev environment has no microphone, same constraint already
documented for the video opt-in gate (../README.md's "Known gaps"). This is
a real step up from sine tones (exercises the pitch tracker against an
actual complex speech signal) but still not a substitute for real recorded
human speech, particularly for anything claiming to read genuine affect
(sarcasm, deadpan delivery) -- see the printed summary's caveats.

Requires macOS (`say`) and `ffmpeg` on PATH. Not part of tests/test_prosody.py's
suite (that one's deterministic and platform-independent); run this by hand:

    python tests/validate_prosody_real_speech.py

What this found, last run: pitch/energy/speaking-rate tracking all behave
correctly on real speech (not just sine tones) -- pitch stays stable across
utterances from the same voice, a genuinely loud+fast segment correctly
fires energy_elevated/pace_elevated, a genuinely pitch-shifted segment
correctly fires pitch_elevated too. It also caught a real bug: an earlier
version of pitch_flattened compared a segment's AVERAGE pitch to the
baseline, which conflates "lower pitch" with "flatter/less-varying pitch" --
two different things. Fixed in prosody.py (pitch_lowered vs pitch_flattened
are now separate checks). What it could NOT validate: whether
pitch_flattened fires correctly on genuine human deadpan/sarcastic
delivery -- macOS's TTS engine has no real "flat affect" mode, and slowing
the rate down on short punctuated sentences produced MORE pitch variability
in testing (each short sentence gets its own falling terminal contour), not
less. That needs real recorded human speech to validate, still not possible
here.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from prosody import SAMPLE_RATE, SpeakerBaseline, analyze_segment

VOICE = "Samantha"

# (name, text, say_extra_args, ffmpeg_audio_filter_or_None)
BASELINE_SEGMENTS = [
    ("calm1", "I wanted to talk about the schedule for next week.", ["-r", "175"], None),
    ("calm2", "It's been a pretty normal week, nothing major to report.", ["-r", "180"], None),
    ("calm3", "I think we can figure out a time that works for both of us.", ["-r", "170"], None),
    ("calm4", "Thanks for checking in, I appreciate you asking.", ["-r", "178"], None),
    ("calm5", "I think the project is on track for now.", ["-r", "172"], None),
    ("calm6", "Let me know if you need anything else from me.", ["-r", "182"], None),
]
TEST_SEGMENTS = [
    (
        "escalating (loud + fast)", "escalating",
        "He keeps taking credit for my work in front of the whole team and I am done staying quiet about it.",
        ["-r", "320"], "volume=6dB",
    ),
    (
        "pitch_urgent (pitch-shifted + fast + loud)", "pitch_urgent",
        "[[pbas +35]][[rate 300]]Stop interrupting me every single time I try to speak in this meeting.",
        [], "volume=5dB",
    ),
    (
        "flat_sarcastic (slow, attempted deadpan)", "flat_sarcastic",
        "Sure. That's just great. No problem at all.",
        ["-r", "140"], None,
    ),
]


def synthesize_pcm16(workdir: Path, name: str, text: str, say_args, audio_filter) -> bytes:
    aiff = workdir / f"{name}.aiff"
    subprocess.run(["say", "-v", VOICE, *say_args, "-o", str(aiff), text], check=True)
    pcm = workdir / f"{name}.pcm"
    cmd = ["ffmpeg", "-y", "-i", str(aiff), "-ar", str(SAMPLE_RATE), "-ac", "1"]
    if audio_filter:
        cmd += ["-filter:a", audio_filter]
    cmd += ["-f", "s16le", str(pcm)]
    subprocess.run(cmd, check=True, capture_output=True)
    return pcm.read_bytes()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        baseline = SpeakerBaseline()

        print("=== Building baseline from 6 calm real-speech segments ===")
        for name, text, say_args, audio_filter in BASELINE_SEGMENTS:
            audio = synthesize_pcm16(workdir, name, text, say_args, audio_filter)
            features = analyze_segment(audio, text, SAMPLE_RATE)
            print(
                f"  {name}: pitch={features.pitch_mean_hz:.1f}Hz energy={features.energy_mean:.4f} "
                f"rate={features.speaking_rate_wps:.2f}wps flags={baseline.flags(features)}"
            )
            baseline.update(features)

        print(
            f"\nBaseline: pitch_mean={baseline._pitch.mean:.1f}Hz(std={baseline._pitch.std:.1f}) "
            f"pitch_variability={baseline._pitch_variability.mean:.1f}Hz(std={baseline._pitch_variability.std:.1f}) "
            f"energy={baseline._energy.mean:.4f}(std={baseline._energy.std:.4f}) "
            f"rate={baseline._rate.mean:.2f}wps(std={baseline._rate.std:.2f})\n"
        )

        print("=== Test segments against the established baseline ===")
        for label, name, text, say_args, audio_filter in TEST_SEGMENTS:
            audio = synthesize_pcm16(workdir, name, text, say_args, audio_filter)
            features = analyze_segment(audio, text, SAMPLE_RATE)
            flags = baseline.flags(features)
            print(f"{label}:")
            print(
                f"  pitch_mean={features.pitch_mean_hz:.1f}Hz pitch_std={features.pitch_std_hz:.1f}Hz "
                f"energy={features.energy_mean:.4f} rate={features.speaking_rate_wps:.2f}wps"
            )
            print(f"  -> flags: {flags}\n")


if __name__ == "__main__":
    main()
