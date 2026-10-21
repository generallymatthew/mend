#!/usr/bin/env python3
"""
Deterministic proof of the delay-buffer + classifier gate, no LiveKit, no
STT, no audio hardware -- see ../README.md's "Testing the gate logic without
any of the above". Submits pre-transcribed text (this test's job is the
buffer's timing/gating logic, not STT accuracy) through the real v3
classifier checkpoint and asserts: an ordinary line releases after
buffer_seconds, a scripted floor-tripping line never does.

Run:
    python tests/test_delay_buffer.py
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from delay_buffer import DEFAULT_BUFFER_SECONDS, DelayBuffer, load_default_classifier

# Same example classifier/README.md's own CLI usage demonstrates (README.md:29-30).
FLOOR_TRIPPING_TEXT = "if you say that to me one more time I swear I will hit you right now"
ORDINARY_TEXT = "I think we should talk about the deadline next week"

# NOT the production default. At the real 0.9 default, this exact phrase
# measures threats_violence=0.917 but in_progress=0.824 on the v3 checkpoint
# -- both must independently clear the bar (inference.py:59), so it does NOT
# cut at 0.9. That's a real, current finding (in_progress consistently sits
# ~0.80-0.82 on several floor-tripping rephrasings tried by hand), not a bug
# in this test harness -- it's exactly the "threshold tuning against the
# actual cost asymmetry" gap classifier/README.md's caveat #3 already flags.
# This test uses a lower threshold, same convention documented in
# ../suture/README.md's CLASSIFIER_CUT_THRESHOLD override, purely
# to deterministically exercise the cut *path* (the buffer/timing/gate
# mechanics), not to claim 0.75 is a validated production threshold.
TEST_CUT_THRESHOLD = 0.75


async def main():
    classifier = load_default_classifier(cut_threshold=TEST_CUT_THRESHOLD)
    buffer_seconds = DEFAULT_BUFFER_SECONDS

    results = {}
    latencies = {}

    def make_callbacks(label):
        def on_release(audio_bytes):
            results[label] = "released"
        def on_cut(text, scores, latency):
            results[label] = "cut"
            latencies[label] = latency
        return on_release, on_cut

    on_release_ordinary, on_cut_ordinary = make_callbacks("ordinary")
    on_release_tripping, on_cut_tripping = make_callbacks("tripping")

    buf_ordinary = DelayBuffer(
        "test_ordinary", classifier, buffer_seconds=buffer_seconds,
        on_release=on_release_ordinary, on_cut=on_cut_ordinary,
    )
    buf_tripping = DelayBuffer(
        "test_tripping", classifier, buffer_seconds=buffer_seconds,
        on_release=on_release_tripping, on_cut=on_cut_tripping,
    )

    start = time.monotonic()
    await asyncio.gather(
        buf_ordinary.submit(b"\x00\x00" * 100, ORDINARY_TEXT),
        buf_tripping.submit(b"\x00\x00" * 100, FLOOR_TRIPPING_TEXT),
    )
    elapsed = time.monotonic() - start

    print(f"elapsed for both segments (run concurrently): {elapsed:.3f}s "
          f"(buffer_seconds={buffer_seconds})")
    print(f"ordinary  -> {results.get('ordinary')}")
    print(f"tripping  -> {results.get('tripping')} "
          f"(classify latency: {latencies.get('tripping', 0):.3f}s)")

    assert results.get("ordinary") == "released", (
        f"expected ordinary text to release, got {results.get('ordinary')!r}"
    )
    assert results.get("tripping") == "cut", (
        f"expected floor-tripping text to be cut, got {results.get('tripping')!r}"
    )
    assert elapsed >= buffer_seconds - 0.1, (
        f"expected both segments to take roughly buffer_seconds={buffer_seconds}s, "
        f"got {elapsed:.3f}s -- classify latency may exceed the buffer window"
    )

    print("\nPASS")


if __name__ == "__main__":
    asyncio.run(main())
