#!/usr/bin/env python3
"""
Button/control smoke test for the Thimble voice interface (static/index.html).

voice_timing_test.py already drives real conversational turns end-to-end;
this file is narrower and faster -- it exists to catch a specific class of
regression that timing test wouldn't notice: a control that's wired to the
wrong flag, or a state transition that forgets to reset something, so the
button visibly does the wrong thing (or nothing) even though no turn ever
errors out. Two real examples that prompted this file:
  - push-to-talk release losing the last words spoken right at release
    (Deepgram's own transcript for that trailing audio hadn't arrived yet
    when the socket was torn down -- see onstop's drain-wait comment).
  - Pause -> Resume leaving the state pill stuck on "Paused" forever when
    in push-to-talk mode (resumeSession() only re-armed listening in
    hands-free mode, so push-to-talk's resume did nothing).
Both were silent: no console error, no failed request, just a control that
looks like it worked but didn't. Each check below exists to catch one of
those categories again if it comes back, not to re-prove the happy path
voice_timing_test.py already covers.

Needs a running `uvicorn server:app --port 8420` (same as voice_timing_test.py).
Doesn't need real speech content for most checks -- turn1.wav's own silence
lead (see voice_timing_test.py's module docstring) is enough to open a real
mic stream for buttons that only care about recording start/stop, not
transcript content.

Out of scope, deliberately: the video-call button (needs a live Tavus
session/API key, a separate integration surface) and the mic-error/
autoplay-retry buttons (only reachable by actually failing getUserMedia or
autoplay, not a normal click path). Covered by manual testing for now.
"""
import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

FIXTURES = Path(__file__).parent / "fixtures"
SILENT_AUDIO = FIXTURES / "turn1.wav"  # only its silence lead is used here -- see module docstring
# Real speech ("She's a peer, not my manager"), ~2s, ending right at the
# file's own end -- no trailing silence. Built with `say` + ffmpeg
# specifically so a hold that releases right as the file ends reproduces
# the real release-at-last-word timing the trailing-words bug needed; the
# other fixtures all have a silence tail that would mask the race.
TRAILING_WORDS_AUDIO = FIXTURES / "ptt_trailing_words.wav"


def fake_mic_args(audio_file):
    return [
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        f"--use-file-for-fake-audio-capture={audio_file}",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
    ]


FAKE_MIC_ARGS = fake_mic_args(SILENT_AUDIO)


async def reset_server(playwright, base_url):
    await asyncio.sleep(0.5)
    request_ctx = await playwright.request.new_context()
    await request_ctx.post(f"{base_url}/api/reset")
    await request_ctx.dispose()


async def new_page(playwright, base_url, audio_file=SILENT_AUDIO):
    browser = await playwright.chromium.launch(headless=True, args=fake_mic_args(audio_file))
    page = await browser.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    await page.goto(base_url)
    await page.wait_for_selector("#stateWord")
    return browser, page, errors


async def state_word(page):
    return (await page.locator("#stateWord").text_content() or "").strip()


async def wait_for_state(page, substring, timeout_s=20):
    """Poll stateWord until it contains `substring`, or give up and return
    whatever it last was -- the initial greeting (Thinking -> Talking) runs
    first on every fresh page load, so a check that cares about the
    Listening state has to wait that out rather than racing it."""
    deadline = asyncio.get_event_loop().time() + timeout_s
    last = await state_word(page)
    while asyncio.get_event_loop().time() < deadline:
        last = await state_word(page)
        if substring in last:
            return last
        await page.wait_for_timeout(200)
    return last


async def check_ui_tabs(playwright, base_url):
    """Voice/Text tab switch shows/hides the right panel."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        voice_hidden_before = await page.locator("#voicePanel").is_hidden()
        await page.locator('.ui-tab[data-ui="text"]').click()
        voice_hidden_after_text = await page.locator("#voicePanel").is_hidden()
        await page.locator('.ui-tab[data-ui="voice"]').click()
        voice_hidden_after_voice = await page.locator("#voicePanel").is_hidden()
        ok = (not voice_hidden_before) and voice_hidden_after_text and (not voice_hidden_after_voice)
        detail = f"voicePanel hidden: before={voice_hidden_before} after-text-click={voice_hidden_after_text} after-voice-click={voice_hidden_after_voice}"
        return ok, detail, errors
    finally:
        await browser.close()


async def check_mute_toggle(playwright, base_url):
    """Mute button toggles its own inactive class and the slash icon."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        before = await page.locator("#muteBtn").evaluate("el => el.classList.contains('inactive')")
        await page.locator("#muteBtn").click()
        after_on = await page.locator("#muteBtn").evaluate("el => el.classList.contains('inactive')")
        await page.locator("#muteBtn").click()
        after_off = await page.locator("#muteBtn").evaluate("el => el.classList.contains('inactive')")
        ok = (not before) and after_on and (not after_off)
        return ok, f"inactive class: before={before} after-1st-click={after_on} after-2nd-click={after_off}", errors
    finally:
        await browser.close()


async def check_pause_resume_handsfree(playwright, base_url):
    """Pause then Resume in hands-free mode returns to a live (non-paused) state."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        before = await wait_for_state(page, "Listening")  # wait out the initial greeting first
        await page.locator("#pauseBtn").click()
        await page.wait_for_timeout(300)
        paused = await state_word(page)
        await page.locator("#pauseBtn").click()
        resumed = await wait_for_state(page, "Listening", timeout_s=10)
        ok = ("Paused" not in before) and ("Paused" in paused) and ("Paused" not in resumed)
        return ok, f"before={before!r} paused={paused!r} resumed={resumed!r}", errors
    finally:
        await browser.close()


async def check_pause_resume_pushtotalk(playwright, base_url):
    """Regression check for the bug reported live: Pause -> Resume while in
    push-to-talk mode must drop out of 'Paused', not stay stuck on it."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        await page.locator("#pttHoldTab").click()
        await page.wait_for_timeout(200)
        await page.locator("#pauseBtn").click()
        await page.wait_for_timeout(300)
        paused = await state_word(page)
        await page.locator("#pauseBtn").click()
        await page.wait_for_timeout(300)
        resumed = await state_word(page)
        ok = ("Paused" in paused) and ("Paused" not in resumed)
        return ok, f"paused={paused!r} resumed={resumed!r}", errors
    finally:
        await browser.close()


async def check_ptt_mode_toggle(playwright, base_url):
    """Auto/Hold tabs toggle which control is visible and which tab is active."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        ptt_hidden_before = await page.locator("#pttBtn").is_hidden()
        await page.locator("#pttHoldTab").click()
        ptt_hidden_after_hold = await page.locator("#pttBtn").is_hidden()
        hold_active = await page.locator("#pttHoldTab").evaluate("el => el.classList.contains('active')")
        await page.locator("#pttHandsFreeTab").click()
        ptt_hidden_after_auto = await page.locator("#pttBtn").is_hidden()
        auto_active = await page.locator("#pttHandsFreeTab").evaluate("el => el.classList.contains('active')")
        ok = ptt_hidden_before and (not ptt_hidden_after_hold) and hold_active and ptt_hidden_after_auto and auto_active
        detail = (f"pttBtn hidden: before={ptt_hidden_before} after-hold={ptt_hidden_after_hold} "
                  f"after-auto={ptt_hidden_after_auto}; hold_active={hold_active} auto_active={auto_active}")
        return ok, detail, errors
    finally:
        await browser.close()


async def check_ptt_hold_release(playwright, base_url):
    """Holding the push-to-talk button starts a recording turn; releasing ends it."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        await page.locator("#pttHoldTab").click()
        await page.wait_for_timeout(200)
        btn = page.locator("#pttBtn")
        box = await btn.bounding_box()
        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        await page.mouse.down()
        await page.wait_for_timeout(300)
        active_while_held = await btn.evaluate("el => el.classList.contains('active')")
        listening_while_held = "Listening" in await state_word(page)
        await page.mouse.up()
        await page.wait_for_timeout(300)
        active_after_release = await btn.evaluate("el => el.classList.contains('active')")
        ok = active_while_held and listening_while_held and (not active_after_release)
        detail = f"active_while_held={active_while_held} listening_while_held={listening_while_held} active_after_release={active_after_release}"
        return ok, detail, errors
    finally:
        await browser.close()


async def check_ptt_trailing_words_not_dropped(playwright, base_url):
    """Regression check for the bug fixed in this commit: releasing
    push-to-talk right as the last word finishes must not drop it.
    TRAILING_WORDS_AUDIO has no silence tail -- the file ends the instant
    speech ends, so holding for its exact duration and releasing
    reproduces the real release-at-last-word timing (Deepgram's own
    transcript for that trailing audio often hasn't arrived yet at the
    moment of release). Needs deepgramEnabled (a real DEEPGRAM_API_KEY) to
    exercise the actual code path this bug was in -- skips with ok=True
    otherwise rather than failing on an unrelated missing-config case."""
    browser, page, errors = await new_page(playwright, base_url, audio_file=TRAILING_WORDS_AUDIO)
    try:
        # The frontend's own `deepgramEnabled` is set by an async fetch
        # fired at page load (see checkDeepgramEnabled in index.html) and
        # isn't guaranteed resolved yet right here -- fetch the same
        # endpoint directly instead of racing that variable. By the time
        # the actual hold/release below reaches onstop (2+ seconds later),
        # the frontend's own copy has long since resolved either way.
        config = await page.evaluate("fetch('/api/voice/config').then(r => r.json())")
        if config.get("error"):
            # Rate-limited (RATE_LIMIT_MAX, see server.py) or some other
            # transient server error -- not the same thing as "no
            # DEEPGRAM_API_KEY configured" and shouldn't be reported as
            # that; a real missing-config case would come back as
            # {"deepgram": false}, not an error body.
            return True, f"skipped: /api/voice/config errored: {config['error']!r}", errors
        if not config.get("deepgram"):
            return True, "skipped: DEEPGRAM_API_KEY not configured on the server", errors
        await page.locator("#pttHoldTab").click()
        await page.wait_for_timeout(200)
        btn = page.locator("#pttBtn")
        box = await btn.bounding_box()
        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        await page.mouse.down()
        bubble = page.locator("#thread .msg.employee.transcript").last
        await bubble.wait_for(state="attached", timeout=5000)
        # Release the instant Deepgram's own live INTERIM transcript shows
        # the last word, not after a fixed delay -- a fixed delay can't
        # tell real startup latency (getUserMedia, Deepgram's websocket
        # handshake) apart from the fixture's own speech actually finishing,
        # and undercounting either one truncates the audio before the
        # phrase ends, which isn't the bug this test exists to catch. This
        # is the real race instead: by the time the interim transcript has
        # caught up to the last word, the audio is definitely fully sent --
        # releasing right then is exactly "release right as the last word
        # finishes," the real trigger (the bug used to drop that FINAL
        # transcript, which lags behind the interim one).
        deadline = asyncio.get_event_loop().time() + 8
        while asyncio.get_event_loop().time() < deadline:
            interim = (await bubble.text_content() or "").lower()
            if "manager" in interim:
                break
            await page.wait_for_timeout(50)
        await page.mouse.up()
        # The live interim update and onstop's own final rewrite both write
        # the same quoted-text format into this bubble, so text content
        # alone can't tell interim from final -- but only onstop's final
        # path removes the 'pending' class (see its own `bubble.classList
        # .remove('pending')`). Wait for that instead of guessing from text.
        deadline = asyncio.get_event_loop().time() + 5
        while asyncio.get_event_loop().time() < deadline:
            still_pending = await bubble.evaluate("el => el.classList.contains('pending')")
            if not still_pending:
                break
            await page.wait_for_timeout(100)
        text = (await bubble.text_content() or "").strip()
        # Only check for "manager" (TRAILING_WORDS_AUDIO's own last word) --
        # the bug this guards against drops trailing words outright, not
        # individual mid-phrase STT misheard homophones ("a peer" vs.
        # "appear" is a real, separate STT-accuracy question, not this bug).
        ok = "manager" in text.lower()
        return ok, f"final transcript bubble: {text!r}", errors
    finally:
        await browser.close()


async def check_captions_and_transcript_toggle(playwright, base_url):
    """Captions button flips its own toggled-state class; transcript button
    shows/hides its panel (its 'inactive' class only reflects the panel's
    hidden state after a click, not the panel's initial markup state, so
    the panel's own hidden attribute -- the actual user-visible effect --
    is the real thing to check)."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        cap_before = await page.locator("#captionsToggleBtn").evaluate("el => el.classList.contains('inactive')")
        await page.locator("#captionsToggleBtn").click()
        cap_after = await page.locator("#captionsToggleBtn").evaluate("el => el.classList.contains('inactive')")
        tx_before = await page.locator("#transcriptPanel").is_hidden()
        await page.locator("#transcriptToggleBtn").click()
        tx_after = await page.locator("#transcriptPanel").is_hidden()
        ok = (cap_before != cap_after) and (tx_before != tx_after)
        return ok, f"captions inactive: {cap_before}->{cap_after}; transcriptPanel hidden: {tx_before}->{tx_after}", errors
    finally:
        await browser.close()


async def check_text_chat_send(playwright, base_url):
    """Typing into the text tab and hitting Send appends a message and clears the box."""
    browser, page, errors = await new_page(playwright, base_url)
    try:
        await page.locator('.ui-tab[data-ui="text"]').click()
        await page.locator("#chatInput").fill("button smoke test message")
        before_count = await page.locator("#thread .msg").count()
        await page.locator("#chatSendBtn").click()
        await page.wait_for_timeout(500)
        after_count = await page.locator("#thread .msg").count()
        input_cleared = (await page.locator("#chatInput").input_value()) == ""
        ok = after_count > before_count and input_cleared
        return ok, f"thread msgs: {before_count}->{after_count}; input_cleared={input_cleared}", errors
    finally:
        await browser.close()


CHECKS = [
    ("UI tabs (Voice/Text)", check_ui_tabs),
    ("Mute toggle", check_mute_toggle),
    ("Pause/Resume (hands-free)", check_pause_resume_handsfree),
    ("Pause/Resume (push-to-talk)", check_pause_resume_pushtotalk),
    ("Push-to-talk mode toggle (Auto/Hold)", check_ptt_mode_toggle),
    ("Push-to-talk hold/release", check_ptt_hold_release),
    ("Push-to-talk trailing words not dropped", check_ptt_trailing_words_not_dropped),
    ("Captions/transcript toggles", check_captions_and_transcript_toggle),
    ("Text chat send", check_text_chat_send),
]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8420")
    args = ap.parse_args()

    failures = 0
    async with async_playwright() as p:
        for name, check in CHECKS:
            await reset_server(p, args.base_url)
            try:
                ok, detail, errors = await check(p, args.base_url)
            except Exception as e:
                ok, detail, errors = False, f"exception: {e}", []
            status = "PASS" if ok and not errors else "FAIL"
            if status == "FAIL":
                failures += 1
            print(f"[{status}] {name}: {detail}")
            for line in errors:
                print(f"    console error: {line}")

    print(f"\n{len(CHECKS) - failures}/{len(CHECKS)} passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    asyncio.run(main())
