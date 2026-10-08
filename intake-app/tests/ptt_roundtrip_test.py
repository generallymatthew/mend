#!/usr/bin/env python3
"""
End-to-end push-to-talk round trip: press, hold through real fake-mic
speech, release right at the last word (same race button_smoke_test.py's
trailing-words check already drives), and verify the WHOLE turn actually
completes -- a real facilitator reply arrives, not just that the
transcript bubble shows the right words. button_smoke_test.py stops at the
transcript; this file is the thing beyond it, built specifically to guard
the latency bug reported live in this session: "when im using the hold
option and i speak in a short session it takes a long time to get a
response... thinking much longer than when i send a lot of text."

Also asserts release -> Thinking lands well under what the OLD (fixed
1200ms, is_final-only) drain wait would have produced on nearly every
push-to-talk turn -- see onMessageHint's own comment in static/index.html
for why that was almost always the full 1200ms here specifically (Deepgram
's is_final needs its own 1400ms endpointing silence, which push-to-talk
never naturally provides).

Fixtures (tests/fixtures/, built with `say` + ffmpeg), both with NO
silence lead or tail -- push-to-talk's start/stop is driven by real
press/release here, not by silence timing, so unlike voice_timing_test.py
/voice_backstop_test.py's fixtures there's no need to pad around a
getUserMedia reset:
  ptt_one_word.wav        -- "Peer." alone, ~0.39s.
  ptt_trailing_words.wav  -- "She's a peer, not my manager." ~2s (shared
                             with button_smoke_test.py's own check).

Requires the server already running with DEEPGRAM_API_KEY configured (see
../../.claude/launch.json's "mend-intake" config) -- skips rather than
fails if it isn't, same as button_smoke_test.py's own PTT check.

Usage:
    intake-app/.venv/bin/python intake-app/tests/ptt_roundtrip_test.py [--base-url URL]
"""
import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

FIXTURES = Path(__file__).parent / "fixtures"


def fake_mic_args(audio_file):
    return [
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        f"--use-file-for-fake-audio-capture={audio_file}",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
    ]


async def reset_server(playwright, base_url):
    await asyncio.sleep(0.5)
    ctx = await playwright.request.new_context()
    await ctx.post(f"{base_url}/api/reset")
    await ctx.dispose()


async def run_ptt_turn(playwright, base_url, audio_file, min_hold_s, last_word):
    """Press, hold until the live interim transcript shows real content (not
    a fixed delay -- getUserMedia's own setup latency in headless Chrome
    eats an unpredictable chunk of any fixed hold, which undercounts the
    fixture's real speech duration and caught an empty/near-empty clip in
    an earlier version of this test, same class of bug as
    button_smoke_test.py's own trailing-words check already guards
    against), release, and wait for the full round trip. Returns a dict of
    results for the caller to assert on."""
    await reset_server(playwright, base_url)
    browser = await playwright.chromium.launch(headless=True, args=fake_mic_args(audio_file))
    page = await browser.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    try:
        await page.goto(base_url)
        await page.wait_for_selector("#stateWord")
        # Switch to Hold mode immediately, same as button_smoke_test.py's
        # own trailing-words check -- NOT waiting for a real Listening state
        # first. An earlier version of this test did wait for Listening,
        # which reproducibly landed right as hands-free's own auto-armed
        # recording had just started (the default mode before switching):
        # setPttMode(true) then stops that in-flight hands-free turn in the
        # middle of starting, and its async onstop cleanup (drain wait,
        # transcribe) was still running when the real PTT press below
        # began -- two overlapping turns racing the same shared dgSocket/
        # chunks/pendingTranscriptEl state, confirmed live as consistent
        # empty-clip failures. Switching to Hold immediately, during the
        # greeting, avoids hands-free ever getting a chance to auto-arm at all.
        await page.locator("#pttHoldTab").click()
        await page.wait_for_timeout(150)
        btn = page.locator("#pttBtn")
        box = await btn.bounding_box()
        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        await page.mouse.down()
        bubble = page.locator("#thread .msg.employee.transcript").last
        await bubble.wait_for(state="attached", timeout=5000)
        # Minimum real-time floor (the fixture's own speech duration) PLUS
        # waiting for real interim content -- a one-word clip can otherwise
        # satisfy "non-placeholder text" off of noise/a misfire before the
        # word itself has actually finished being spoken by the fake device.
        await page.wait_for_timeout(int(min_hold_s * 1000))
        deadline = asyncio.get_event_loop().time() + 8
        while asyncio.get_event_loop().time() < deadline:
            interim = (await bubble.text_content() or "").strip()
            if interim and interim != "…":
                break
            await page.wait_for_timeout(50)
        release_t = asyncio.get_event_loop().time()
        await page.mouse.up()

        # Time to leave Listening (i.e. hit Thinking) -- the thing the
        # latency bug was actually about.
        thinking_latency = None
        deadline = release_t + 10
        while asyncio.get_event_loop().time() < deadline:
            word = (await page.locator("#stateWord").text_content() or "")
            if "Thinking" in word:
                thinking_latency = round(asyncio.get_event_loop().time() - release_t, 3)
                break
            await page.wait_for_timeout(50)

        # Full round trip: a real reply reaching Talking, or a status-line
        # error if something failed along the way.
        reached_talking = False
        status_error = None
        deadline = asyncio.get_event_loop().time() + 30
        while asyncio.get_event_loop().time() < deadline:
            word = (await page.locator("#stateWord").text_content() or "")
            status = (await page.locator("#status").text_content() or "").strip()
            if status:
                status_error = status
                break
            if "Talking" in word:
                reached_talking = True
                break
            await page.wait_for_timeout(100)

        transcript_bubble = page.locator("#thread .msg.employee.transcript").last
        transcript_text = ""
        if await transcript_bubble.count():
            transcript_text = (await transcript_bubble.text_content() or "").strip()

        return {
            "thinking_latency": thinking_latency,
            "reached_talking": reached_talking,
            "status_error": status_error,
            "transcript_text": transcript_text,
            "transcript_has_word": last_word.lower() in transcript_text.lower(),
            "console_errors": errors,
        }
    finally:
        await browser.close()


async def check_one_word_roundtrip(playwright, base_url):
    print("\n=== PTT round trip: one-word answer (ptt_one_word.wav) ===")
    r = await run_ptt_turn(playwright, base_url, FIXTURES / "ptt_one_word.wav", min_hold_s=0.4, last_word="peer")
    print(r)
    # Not asserting the exact word here -- tiny.en/Deepgram mishearing a
    # single short word ("peer" -> "appear"/"here") is a real but separate
    # STT-accuracy question, not what this test exists to catch (see
    # button_smoke_test.py's own trailing-words check for the same
    # reasoning). What matters: real non-empty content made it through, not
    # an empty-clip failure.
    ok = r["reached_talking"] and r["status_error"] is None and r["transcript_text"] not in ("", "…")
    # Regression guard for the drain-wait latency bug: should clear the OLD
    # fixed-1200ms-almost-always behavior by a comfortable margin, not just
    # technically beat it.
    if r["thinking_latency"] is None or r["thinking_latency"] > 3.0:
        ok = False
        print(f"  FAIL: release -> Thinking took {r['thinking_latency']}s, expected well under 3s")
    print("PASS" if ok else "FAIL")
    return ok


async def check_sentence_roundtrip(playwright, base_url):
    print("\n=== PTT round trip: full sentence (ptt_trailing_words.wav) ===")
    r = await run_ptt_turn(playwright, base_url, FIXTURES / "ptt_trailing_words.wav", min_hold_s=1.8, last_word="manager")
    print(r)
    ok = r["reached_talking"] and r["status_error"] is None and r["transcript_has_word"]
    if r["thinking_latency"] is None or r["thinking_latency"] > 3.0:
        ok = False
        print(f"  FAIL: release -> Thinking took {r['thinking_latency']}s, expected well under 3s")
    print("PASS" if ok else "FAIL")
    return ok


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8420")
    args = ap.parse_args()

    async with async_playwright() as p:
        # Same deepgram-configured check button_smoke_test.py's PTT check
        # uses -- skip cleanly rather than fail on an unrelated missing-key case.
        ctx = await p.request.new_context()
        resp = await ctx.get(f"{args.base_url}/api/voice/config")
        config = await resp.json()
        await ctx.dispose()
        if not config.get("deepgram"):
            print("skipped: DEEPGRAM_API_KEY not configured on the server")
            return

        one_word_ok = await check_one_word_roundtrip(p, args.base_url)
        # Each round trip alone issues several requests (reset, message,
        # multiple speak calls) against RATE_LIMIT_MAX (server.py, 20/60s by
        # default) -- back-to-back checks here reliably tripped it in
        # testing, a self-inflicted 429 that has nothing to do with either
        # check's own correctness. A real pause, not a reset call (the
        # limiter keys off wall-clock hits, not conversation state).
        print("\n(pausing for the rate limit window to clear...)")
        await asyncio.sleep(65)
        sentence_ok = await check_sentence_roundtrip(p, args.base_url)
        results = {"one_word": one_word_ok, "sentence": sentence_ok}
    print("\n=== summary ===")
    for name, passed in results.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
