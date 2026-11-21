#!/usr/bin/env python3
"""
One-off diagnostic (not part of the suite): does Chrome's
--use-file-for-fake-audio-capture file replay from byte 0 on every fresh
getUserMedia() call within the same page, or run on one continuous
wall-clock timeline shared across calls? voice_timing_test.py's barge-in
fixture (interrupt_delayed.wav) assumes the former -- this checks that
assumption directly before trusting any interrupt-timing numbers.

Usage: thimble/.venv/bin/python thimble/tests/_diag_fake_audio_restart.py
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

FIXTURE = Path(__file__).parent / "fixtures" / "turn1.wav"  # 1.0s silence, then ~3.9s speech


async def sample_rms(page, label, duration_s=5.0, interval_s=0.1):
    await page.evaluate("""
        async () => {
            const stream = await navigator.mediaDevices.getUserMedia({audio: true});
            window.__ctx = new (window.AudioContext || window.webkitAudioContext)();
            const source = window.__ctx.createMediaStreamSource(stream);
            window.__analyser = window.__ctx.createAnalyser();
            window.__analyser.fftSize = 256;
            source.connect(window.__analyser);
            window.__data = new Uint8Array(window.__analyser.frequencyBinCount);
        }
    """)
    samples = []
    steps = int(duration_s / interval_s)
    for i in range(steps):
        level = await page.evaluate("""
            () => {
                window.__analyser.getByteTimeDomainData(window.__data);
                let sum = 0;
                for (let i = 0; i < window.__data.length; i++) {
                    const v = (window.__data[i] - 128) / 128;
                    sum += v * v;
                }
                return Math.sqrt(sum / window.__data.length);
            }
        """)
        samples.append(round(level, 4))
        await asyncio.sleep(interval_s)
    above = [round(i * interval_s, 2) for i, v in enumerate(samples) if v > 0.03]
    speech_onset = above[0] if above else None
    print(f"{label}: speech first detected at t={speech_onset}s into this stream "
          f"(fixture has speech starting at ~1.0s if replayed from byte 0)")
    print(f"  samples: {samples}")
    await page.evaluate("() => { window.__ctx.close(); }")
    return speech_onset


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                f"--use-file-for-fake-audio-capture={FIXTURE}",
            ],
        )
        page = await browser.new_page()
        # about:blank has no mediaDevices (not a secure context); a local
        # file:// page is, and -- unlike navigating to the real app -- won't
        # also fire the app's OWN getUserMedia calls and compete for the
        # fake device while we're trying to isolate just this diagnostic's.
        await page.goto("file:///private/tmp/claude-501/-Users-matt-Documents-Mend/b6544956-eca1-4090-9f16-fcba209d40a9/scratchpad/blank.html")

        onset1 = await sample_rms(page, "call #1 (t=0 after page load)")
        print("...waiting 3s wall-clock before second getUserMedia() call...")
        await asyncio.sleep(3.0)
        onset2 = await sample_rms(page, "call #2 (3s wall-clock after call #1 started)")

        await browser.close()

        print()
        if onset1 is not None and onset2 is not None and abs(onset1 - onset2) < 0.3:
            print("CONCLUSION: file restarts from byte 0 on each getUserMedia() call "
                  "(both calls saw speech at the same relative offset).")
        else:
            print("CONCLUSION: file does NOT restart per call -- looks like one continuous "
                  "timeline/loop shared across calls (onsets differ).")


if __name__ == "__main__":
    asyncio.run(main())
