#!/usr/bin/env python3
"""
End-to-end push-to-talk round trip, now via the text composer's own
hold-to-dictate mic button (push-to-talk moved out of the Voice panel and
into the composer, per explicit request -- Voice mode is hands-free only
now). Press, hold through real fake-mic speech, release right at the last
word (same race button_smoke_test.py's own composer check already drives),
and verify the transcript actually lands in the text input, not just that
Deepgram produced the right words internally. button_smoke_test.py's own
"Composer mic trailing words not dropped" check covers that same ground at
a narrower scope; this file adds the latency regression guard: release ->
chatInput filled must land well under what the OLD (fixed 1200ms,
is_final-only) drain wait would have produced on nearly every
push-to-talk turn -- see onMessageHint's own comment in static/index.html
for why that was almost always the full 1200ms for a hold-to-release turn
specifically (Deepgram's is_final needs its own 1400ms endpointing
silence, which a manual release never naturally provides).

Also guards a second real bug found live while building this file's
composer-era version: composerPress's deferred-release-stop path used to
measure "how long has this been held" from the ORIGINAL button press, not
from when recording actually started -- if getUserMedia() took longer than
the minimum-hold floor to resolve (confirmed: >1900ms in one observed
headless run), that stale elapsed time already exceeded the floor by the
time recording began, so mediaRecorder.stop() fired within milliseconds of
.start(), capturing a near-empty clip. Composer mode has no live interim
bubble to show this going wrong (unlike the old Voice-panel button), so it
surfaced as a silently empty chatInput rather than an obviously-short
transcript.

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
fails if it isn't.

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


async def run_composer_turn(playwright, base_url, audio_file, last_word):
    """Press the composer's mic button, hold until Deepgram's own JS state
    (dgFinalText/dgInterimText -- there's no UI bubble in the composer flow
    to poll instead, see module docstring) shows the real word, release,
    and wait for chatInput to fill. Returns a dict of results for the
    caller to assert on."""
    await reset_server(playwright, base_url)
    browser = await playwright.chromium.launch(headless=True, args=fake_mic_args(audio_file))
    page = await browser.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    try:
        await page.goto(base_url)
        await page.wait_for_selector("#stateWord")
        # Switch to Text immediately, during the greeting -- NOT waiting for
        # a real Listening state first. An earlier version of this file (from
        # when push-to-talk still lived in the Voice panel) learned this the
        # hard way: waiting for Listening reliably landed right as hands-free's
        # own auto-armed recording had just started, and switching away mid-start
        # raced its async cleanup against the real press moments later --
        # confirmed live as consistent empty-clip failures unrelated to the
        # actual thing under test. Switching away immediately avoids hands-free
        # ever getting a chance to auto-arm at all.
        await page.locator('.ui-tab[data-ui="text"]').click()
        await page.wait_for_timeout(200)  # let the tab switch/layout settle before trusting a bounding box
        btn = page.locator("#composerMicBtn")
        box = await btn.bounding_box()
        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        await page.mouse.down()
        deadline = asyncio.get_event_loop().time() + 8
        while asyncio.get_event_loop().time() < deadline:
            dg_text = await page.evaluate("(dgFinalText + ' ' + dgInterimText).toLowerCase()")
            if last_word.lower() in dg_text:
                break
            await page.wait_for_timeout(50)
        release_t = asyncio.get_event_loop().time()
        await page.mouse.up()

        # Time to chatInput actually filling -- the thing the latency bug
        # (the old Voice-panel drain-wait tax) was really about, now measured
        # on the composer's own path.
        fill_latency = None
        text = ""
        deadline = release_t + 10
        while asyncio.get_event_loop().time() < deadline:
            text = (await page.locator("#chatInput").input_value()).strip()
            if text:
                fill_latency = round(asyncio.get_event_loop().time() - release_t, 3)
                break
            await page.wait_for_timeout(50)

        return {
            "fill_latency": fill_latency,
            "text": text,
            "text_has_word": last_word.lower() in text.lower(),
            "console_errors": errors,
        }
    finally:
        await browser.close()


async def check_one_word_roundtrip(playwright, base_url):
    print("\n=== Composer round trip: one-word answer (ptt_one_word.wav) ===")
    r = await run_composer_turn(playwright, base_url, FIXTURES / "ptt_one_word.wav", last_word="peer")
    print(r)
    # Not asserting the exact word here -- tiny.en/Deepgram mishearing a
    # single short word ("peer" -> "appear"/"here") is a real but separate
    # STT-accuracy question, not what this test exists to catch (see
    # button_smoke_test.py's own trailing-words check for the same
    # reasoning). What matters: real non-empty content made it through, not
    # an empty-clip failure.
    ok = r["text"] not in ("", "…") and not r["console_errors"]
    if r["fill_latency"] is None or r["fill_latency"] > 3.0:
        ok = False
        print(f"  FAIL: release -> chatInput filled took {r['fill_latency']}s, expected well under 3s")
    print("PASS" if ok else "FAIL")
    return ok


async def check_sentence_roundtrip(playwright, base_url):
    print("\n=== Composer round trip: full sentence (ptt_trailing_words.wav) ===")
    r = await run_composer_turn(playwright, base_url, FIXTURES / "ptt_trailing_words.wav", last_word="manager")
    print(r)
    ok = r["text_has_word"] and not r["console_errors"]
    if r["fill_latency"] is None or r["fill_latency"] > 3.0:
        ok = False
        print(f"  FAIL: release -> chatInput filled took {r['fill_latency']}s, expected well under 3s")
    print("PASS" if ok else "FAIL")
    return ok


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8420")
    args = ap.parse_args()

    async with async_playwright() as p:
        ctx = await p.request.new_context()
        resp = await ctx.get(f"{args.base_url}/api/voice/config")
        config = await resp.json()
        await ctx.dispose()
        if not config.get("deepgram"):
            print("skipped: DEEPGRAM_API_KEY not configured on the server")
            return

        one_word_ok = await check_one_word_roundtrip(p, args.base_url)
        # Each round trip alone issues several requests against
        # RATE_LIMIT_MAX (server.py, 20/60s by default) -- back-to-back
        # checks here reliably tripped it in testing, a self-inflicted 429
        # that has nothing to do with either check's own correctness. A
        # real pause, not a reset call (the limiter keys off wall-clock
        # hits, not conversation state).
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
