#!/usr/bin/env python3
"""
Automated timing/behavior test for the Thimble voice conversation
(static/index.html), so this doesn't need a human to repeat the same
"I had a problem on Friday..." prompt by hand every run.

Drives a real Chromium via Playwright with Chrome's fake-audio-capture flags
(--use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<wav>),
which feeds real WAV samples into getUserMedia as if a real mic captured
them -- the browser's VAD, partial-transcription calls, and silence-timeout
endpointing all run for real against that audio. What this can't exercise:
real microphone hardware (echo/gain/device-switch quirks).

Fixtures (tests/fixtures/, built with ffmpeg + macOS `say`). Chrome's fake
file-capture device RESTARTS THE FILE AT BYTE 0 ON EVERY FRESH
getUserMedia() CALL -- confirmed directly (see _diag_fake_audio_restart.py
and the git history around this comment for the long, wrong-footed path to
this conclusion: an earlier version of this file claimed the opposite,
"one continuous timeline," which was actually just an artifact of a
diagnostic that never stopped its first stream before opening a second one
on top of it). This matters a lot for fixture design, because EVERY new
mic consumer -- the real recording turn, and separately Thimble's own
interrupt-monitor stream (armed the instant avatarState becomes 'thinking',
even before any reply audio exists) -- replays the SAME file from its start.
So anything placed near the start of the file will be "heard" again by the
very next fresh consumer, almost immediately:
  turn1.wav              -- 12s silence, ~3.9s of real speech (the
                            employee's turn), then 20s silence. The 12s
                            lead is deliberately longer than a typical
                            single-reply Talking phase (measured ~1.3-8.5s)
                            so that when the interrupt-monitor's own fresh
                            getUserMedia() call resets to byte 0 the instant
                            thinking begins, it hits only silence and never
                            falsely self-interrupts a clean reply -- this
                            was the actual cause of a long stretch of zero
                            successful plain-turn runs: the interrupt
                            monitor kept re-hearing this fixture's own
                            opening line seconds into every single reply.
  interrupt_longtail.wav -- 6.5s silence, ~3.9s opening line, 3s silence
                            (ends that first turn -- bumped from an earlier
                            1.5s, which Deepgram's endpointing didn't
                            reliably treat as a real gap), then ~15.6s of
                            continuous speech, then 20s trailing silence.
                            The 6.5s lead is deliberately SHORTER than the
                            12s above: it's tuned to clear typical Thinking
                            latency (~2-5s measured) so the interrupt
                            monitor's byte-0 reset lands a couple seconds
                            into real Talking, not during Thinking itself
                            and not back on top of the opening line's own
                            reset window. Confirmed live: this reliably
                            produces a genuine mid-reply cutoff, including
                            Claude itself noticing ("Looks like that got cut
                            off -- go ahead, I've got time.").

Both fixtures still have to clear Thimble's own GREETING first, which plays
before the real mic ever arms for listening -- measured at ~29-33s wall
clock for the current several-sentence intro text (watch_s below budgets
for that). If the greeting text in static/index.html changes length
enough to matter, re-measure before trusting these numbers again.

State is read straight from the DOM (#stateWord), the same text a real user
sees -- "Listening...", "Thinking...", "Talking..." -- polled on an interval
and timestamped, rather than reaching into JS internals.

Requires the server already running (see ../../.claude/launch.json's
"mend-intake" config, or: uvicorn server:app --port 8420 --app-dir intake-app).

Usage:
    intake-app/.venv/bin/python intake-app/tests/voice_timing_test.py [--runs N] [--base-url URL]
"""
import argparse
import asyncio
import statistics
import time
from pathlib import Path

from playwright.async_api import async_playwright

FIXTURES = Path(__file__).parent / "fixtures"
POLL_INTERVAL_S = 0.05


async def record_state_timeline(page, t0, poll_until):
    """Poll #stateWord every POLL_INTERVAL_S; return [(t_rel_s, state_word), ...].

    `t0` is wall-clock navigation start (captured right before page.goto()),
    not loop start -- timestamps are relative to that, so a state change that
    already happened during page load/greeting (before this loop's first
    poll) still gets its real elapsed time, not 0. Previously anchored to
    loop start instead: any run where setup (greeting + VAD endpointing)
    finished before the first poll showed a false ~0.02s "Thinking", because
    that was just time-since-first-poll, not time-since-navigation --
    confirmed by comparing against a page.evaluate(performance.now()) probe.
    """
    timeline = []
    last = None
    while time.monotonic() < poll_until:
        word = await page.locator("#stateWord").text_content()
        if word != last:
            timeline.append((round(time.monotonic() - t0, 3), word))
            last = word
        await asyncio.sleep(POLL_INTERVAL_S)
    return timeline


def first_real_listening_index(timeline):
    """Index of the first 'Listening' entry, i.e. where Thimble's own
    greeting ends and the real mic turn begins. Greeting playback goes
    through the exact same Thinking->Talking state pair a real reply does
    (it's generated + synthesized the same way), so any "first matching
    pair" search over the whole timeline will find the greeting's own
    transition instead of the real one -- this was a real bug here:
    "Thinking -> Talking" latency was silently measuring greeting latency
    in every report before this fix. Scope every search to start here."""
    for i, (_, w) in enumerate(timeline):
        if "Listening" in w:
            return i
    return None


def transition_latency(timeline, from_word, to_word, start_idx=0):
    """First (from_word -> to_word) gap at or after start_idx, or None."""
    for i in range(start_idx, len(timeline) - 1):
        if from_word in timeline[i][1] and to_word in timeline[i + 1][1]:
            return round(timeline[i + 1][0] - timeline[i][0], 3)
    return None


async def reset_server(playwright, base_url):
    """POST /api/reset so each run starts from a fresh greeting, not an
    accumulated conversation history from the previous run (the server's
    conversation state is single-user in-memory, shared across runs).

    A settle delay comes first: server.py's conversation list has no locking
    (it's a single-user prototype, not meant for concurrent/rapid-fire
    access), and the previous run's reply/TTS call keeps running in a
    threadpool even after that run's browser closes. Resetting too soon
    races it -- confirmed live: facilitator_reply's conversation.pop() threw
    IndexError when a reset cleared the list out from under it mid-call,
    which then 500'd the next run's own greeting request."""
    await asyncio.sleep(2.0)
    request_ctx = await playwright.request.new_context()
    await request_ctx.post(f"{base_url}/api/reset")
    await request_ctx.dispose()


async def run_one_turn(playwright, base_url, audio_fixture, watch_s):
    """Launch one fresh browser with a given fake-mic WAV, return the state timeline."""
    await reset_server(playwright, base_url)
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--use-fake-ui-for-media-stream",  # auto-accept the mic permission prompt
            "--use-fake-device-for-media-stream",
            f"--use-file-for-fake-audio-capture={audio_fixture}",
            # Without these, headless Chromium treats this page as a
            # backgrounded/occluded tab and throttles it -- confirmed live:
            # the fake-mic device went completely silent (all-zero PCM sent
            # over /ws/voice) during the ~30s idle gap waiting out Thimble's
            # own greeting, even though the WAV file has real speech sitting
            # right there at that timestamp. These three flags together
            # stopped the throttling and the speech came through correctly.
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
        ],
    )
    page = await browser.new_page()
    console_lines = []
    page.on("console", lambda msg: console_lines.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: console_lines.append(f"[pageerror] {exc}"))
    t0 = time.monotonic()  # navigation start -- the timeline's time-zero, see record_state_timeline's docstring
    await page.goto(base_url)
    await page.wait_for_selector("#stateWord")
    timeline = await record_state_timeline(page, t0, poll_until=t0 + watch_s)
    await browser.close()
    return timeline, console_lines


TURN1_LEAD_S = 12.0  # turn1.wav's own silence lead -- see module docstring


async def test_plain_turn(playwright, base_url, runs):
    """real listening -> thinking -> talking timing, repeated `runs` times."""
    print(f"\n=== plain turn x{runs} (turn1.wav) ===")
    thinking_lat, talking_lat = [], []
    for i in range(runs):
        timeline, console_lines = await run_one_turn(playwright, base_url, FIXTURES / "turn1.wav", watch_s=90)
        print(f"run {i + 1}: " + " -> ".join(f"{w}@{t}s" for t, w in timeline))
        for line in console_lines:
            print(f"    {line}")
        start_idx = first_real_listening_index(timeline)
        if start_idx is None:
            continue
        l1 = transition_latency(timeline, "Listening", "Thinking", start_idx)
        l2 = transition_latency(timeline, "Thinking", "Talking", start_idx)
        # l1 includes turn1.wav's own TURN1_LEAD_S of silence before the
        # fixture's speech even starts -- subtract it to get the real
        # silence-wait + STT latency a person's own pause would produce.
        if l1 is not None:
            thinking_lat.append(round(l1 - TURN1_LEAD_S, 3))
        if l2 is not None:
            talking_lat.append(l2)
    _report("Listening -> Thinking (STT + silence-wait, fixture lead subtracted)", thinking_lat)
    _report("Thinking -> Talking (LLM + TTS)", talking_lat)


async def test_interruption(playwright, base_url, runs):
    """Barge-in: the interrupt-monitor's own fresh getUserMedia() call resets
    interrupt_longtail.wav to byte 0, landing on real speech a couple
    seconds into the real reply's Talking phase (see module docstring) --
    should cut Talking short, same as a person actually interrupting."""
    print(f"\n=== interruption x{runs} (interrupt_longtail.wav) ===")
    interrupt_lat, no_interrupt = [], 0
    for i in range(runs):
        timeline, console_lines = await run_one_turn(playwright, base_url, FIXTURES / "interrupt_longtail.wav", watch_s=90)
        print(f"run {i + 1}: " + " -> ".join(f"{w}@{t}s" for t, w in timeline))
        for line in console_lines:
            print(f"    {line}")
        start_idx = first_real_listening_index(timeline)
        if start_idx is None:
            continue
        # First REAL Talking (the reply), not the greeting's -- scoped past start_idx.
        talking_start = next((t for t, w in timeline[start_idx:] if "Talking" in w), None)
        if talking_start is None:
            continue
        after_talking = [(t, w) for t, w in timeline if t > talking_start]
        cut_short = next((t for t, w in after_talking if "Talking" not in w), None)
        if cut_short is not None:
            interrupt_lat.append(round(cut_short - talking_start, 3))
        else:
            no_interrupt += 1
    print(f"completed cycles with no interrupt observed: {no_interrupt}")
    _report("Talking -> interrupted", interrupt_lat)


def _report(label, values):
    if not values:
        print(f"{label}: no data")
        return
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    print(f"{label}: mean={mean:.3f}s stdev={stdev:.3f}s n={len(values)} values={values}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8420")
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()

    async with async_playwright() as p:
        await test_plain_turn(p, args.base_url, args.runs)
        await test_interruption(p, args.base_url, args.runs)


if __name__ == "__main__":
    asyncio.run(main())
