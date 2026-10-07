#!/usr/bin/env python3
"""
Automated regression test for the Deepgram-path turn-ending backstop
(static/index.html's DG_HANG_BACKSTOP_PRE_MS / DG_HANG_BACKSTOP_POST_MS /
DG_SPEECH_CONFIRM_MS, see their own comments). Covers three real bugs found
and fixed live in the same session, in order:

  1. "a one-word answer leaves the mic listening forever" -- the original
     single DG_HANG_BACKSTOP_MS (4000ms) was the only thing ending a turn
     Deepgram's own endpointing never caught at all.
  2. "it just interrupted me" -- shortening that single constant to clear
     Deepgram's normal ~1.5-2s post-speech latency faster also shortened the
     PRE-speech grace period (ordinary reaction time before answering),
     since one timer counted quiet time from recording start either way.
  3. "it also just cut me off" -- splitting pre/post wasn't enough on its
     own: a single loud frame (room-tail echo off Thimble's own
     just-finished voice) could flip the post-speech-length path on
     immediately, arming the SHORT timer before the person had said
     anything real.

Fixtures (tests/fixtures/, built with ffmpeg + macOS `say`). Same
byte-0-reset behavior as voice_timing_test.py's fixtures -- see that
module's own docstring for why fixture design doesn't need to account for
the greeting's own length.
  one_word.wav   -- 3s silence, "Peer." (~0.4s), 10s trailing silence.
                    Should end the turn comfortably under
                    DG_HANG_BACKSTOP_PRE_MS after the word -- confirms bug 1
                    stays fixed without being so fast it risks bug 3 again.
  late_start.wav -- 6s silence (longer reaction time than a one-word
                    answer), then a full sentence, then 10s trailing
                    silence. The recording must NOT end during the 6s lead
                    -- confirms bug 2 stays fixed (6s is comfortably inside
                    DG_HANG_BACKSTOP_PRE_MS=8000 but would have tripped the
                    old single 4000/2200ms constant).
  echo_blip.wav  -- a 150ms tone at t=0 (simulating a room-tail/echo blip),
                    ~3s silence, "Peer.", 10s trailing silence. The blip
                    alone must NOT arm the short post-speech timer -- if it
                    did, the turn would end at roughly blip_time +
                    DG_HANG_BACKSTOP_POST_MS, well before the real word at
                    3.15s ever gets spoken -- confirms bug 3 stays fixed.

Requires the server already running (DEEPGRAM_API_KEY configured) -- see
../../.claude/launch.json's "mend-intake" config.

Usage:
    intake-app/.venv/bin/python intake-app/tests/voice_backstop_test.py [--runs N] [--base-url URL]
"""
import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent))
from voice_timing_test import (
    FIXTURES,
    first_real_listening_index,
    run_one_turn,
    transition_latency,
)

WATCH_S = 60  # covers the full greeting (~29-33s) plus turn processing


async def check_one_word(playwright, base_url, runs):
    """one_word.wav: must end the turn, not hang. Bug 1's regression guard."""
    print(f"\n=== one-word answer x{runs} (one_word.wav) ===")
    ok = 0
    for i in range(runs):
        timeline, console_lines = await run_one_turn(playwright, base_url, FIXTURES / "one_word.wav", watch_s=WATCH_S)
        print(f"run {i + 1}: " + " -> ".join(f"{w}@{t}s" for t, w in timeline))
        start_idx = first_real_listening_index(timeline)
        if start_idx is None:
            print("  FAIL: never reached a real Listening state")
            continue
        lat = transition_latency(timeline, "Listening", "Thinking", start_idx)
        if lat is None:
            print("  FAIL: never left Listening -- turn hung")
            continue
        # Speech starts at the fixture's own 3s lead; anything landing well
        # under ~15s total (3s lead + word + a generous multiple of the
        # post-speech backstop) means the turn ended, not hung.
        print(f"  Listening -> Thinking: {lat}s raw")
        if lat < 15.0:
            ok += 1
        else:
            print("  FAIL: took too long to end the turn")
    print(f"passed: {ok}/{runs}")
    return ok == runs


async def check_late_start(playwright, base_url, runs):
    """late_start.wav: must NOT end the turn during the 6s pre-speech lead. Bug 2's regression guard."""
    print(f"\n=== late start x{runs} (late_start.wav) ===")
    ok = 0
    for i in range(runs):
        timeline, console_lines = await run_one_turn(playwright, base_url, FIXTURES / "late_start.wav", watch_s=WATCH_S)
        print(f"run {i + 1}: " + " -> ".join(f"{w}@{t}s" for t, w in timeline))
        start_idx = first_real_listening_index(timeline)
        if start_idx is None:
            print("  FAIL: never reached a real Listening state")
            continue
        lat = transition_latency(timeline, "Listening", "Thinking", start_idx)
        if lat is None:
            print("  FAIL: never left Listening at all")
            continue
        print(f"  Listening -> Thinking: {lat}s raw")
        # Must be AFTER the 6s lead (the sentence can't have been heard
        # before it was spoken) -- a cutoff during the lead would land
        # well under 6s.
        if lat > 6.0:
            ok += 1
        else:
            print("  FAIL: cut off during the pre-speech silence, before the sentence was spoken")
    print(f"passed: {ok}/{runs}")
    return ok == runs


async def check_echo_blip(playwright, base_url, runs):
    """echo_blip.wav: the leading blip must not end the turn before the real word at ~3.15s. Bug 3's regression guard."""
    print(f"\n=== echo blip x{runs} (echo_blip.wav) ===")
    ok = 0
    for i in range(runs):
        timeline, console_lines = await run_one_turn(playwright, base_url, FIXTURES / "echo_blip.wav", watch_s=WATCH_S)
        print(f"run {i + 1}: " + " -> ".join(f"{w}@{t}s" for t, w in timeline))
        start_idx = first_real_listening_index(timeline)
        if start_idx is None:
            print("  FAIL: never reached a real Listening state")
            continue
        lat = transition_latency(timeline, "Listening", "Thinking", start_idx)
        if lat is None:
            print("  FAIL: never left Listening at all")
            continue
        print(f"  Listening -> Thinking: {lat}s raw")
        # The real word doesn't start until ~3.15s -- if the blip alone had
        # armed the short post-speech timer, this would land well before
        # that (blip at 0 + ~2.2s backstop =~ 2.2s).
        if lat > 3.0:
            ok += 1
        else:
            print("  FAIL: cut off by the leading blip before the real word was spoken")
    print(f"passed: {ok}/{runs}")
    return ok == runs


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8420")
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()

    async with async_playwright() as p:
        results = {
            "one_word": await check_one_word(p, args.base_url, args.runs),
            "late_start": await check_late_start(p, args.base_url, args.runs),
            "echo_blip": await check_echo_blip(p, args.base_url, args.runs),
        }
    print("\n=== summary ===")
    for name, passed in results.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
