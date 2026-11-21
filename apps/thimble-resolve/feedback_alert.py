#!/usr/bin/env python3
"""
Watches analytics_events.jsonl for a spike in per-reply "feedback" events
(the thumbs-down/"confused" pill in session.html -- see its own comment)
and sends a real alert when down-flags cross a threshold in a rolling
window. Reads only the structured fields that file already contains
(session_id, turn, flag, reason) -- never conversation content, since
that file never has any to begin with.

Standalone on purpose: doesn't import server.py (heavier deps, API
clients, side effects at import time), just stdlib + python-dotenv,
same packages server.py already depends on.

Run once (e.g. from cron, every 15 min):
    python3 feedback_alert.py

Or loop in the foreground for local testing:
    python3 feedback_alert.py --loop --interval 60 --window 10 --threshold 2 --dry-run
"""
import argparse
import json
import os
import smtplib
import sys
import time
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

ANALYTICS_FILE = ROOT / "analytics_events.jsonl"
ALERT_STATE_FILE = ROOT / "feedback_alert_state.json"
ALERT_LOG_FILE = ROOT / "feedback_alert_log.jsonl"

# Same SMTP env vars server.py's maybe_send_hr_notification() already
# uses -- one mail setup for the whole app, not a second one to configure.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
MAIL_FROM = os.environ.get("MAIL_FROM", SMTP_USER)
# Deliberately a separate recipient from HR_NOTIFY_EMAIL -- that's an
# employee-consented disclosure to HR, this is a product-quality alert
# to whoever's watching Thimble's replies, almost always a different person.
FEEDBACK_ALERT_EMAIL = os.environ.get("FEEDBACK_ALERT_EMAIL", "")


def load_state() -> dict:
    if not ALERT_STATE_FILE.exists():
        return {"last_alert_ts": 0}
    try:
        return json.loads(ALERT_STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"last_alert_ts": 0}


def save_state(state: dict) -> None:
    ALERT_STATE_FILE.write_text(json.dumps(state))


def read_feedback_events(since_ts: float) -> list[dict]:
    """Every "feedback"-typed line newer than since_ts. Tolerant of a
    half-written last line (server.py appends one line per request, but a
    read racing a concurrent write could still catch a partial one) and of
    older log lines from before the feedback event type existed -- those
    just don't have event == "feedback" and get skipped."""
    if not ANALYTICS_FILE.exists():
        return []
    events = []
    with ANALYTICS_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event") != "feedback" or rec.get("ts", 0) <= since_ts:
                continue
            events.append(rec)
    return events


def send_alert(down_count: int, confused_count: int, reasons: dict, window_minutes: int, dry_run: bool) -> None:
    reason_lines = "\n".join(f"  - {slug or '(no reason given)'}: {n}" for slug, n in sorted(reasons.items(), key=lambda kv: -kv[1]))
    body = (
        f"Thimble feedback alert: {down_count} thumbs-down and {confused_count} "
        f"\"confused\" flags in the last {window_minutes} minutes.\n\n"
        f"Reasons given:\n{reason_lines or '  (none picked)'}\n\n"
        "No conversation content is included -- this alert only ever sees "
        "session_id/turn/flag/reason, same as analytics_events.jsonl itself. "
        "Check that file (or its Google Sheets mirror) for the raw events."
    )
    print(f"[feedback_alert] {'DRY RUN, not sending: ' if dry_run else ''}{body}", flush=True)
    if dry_run:
        return
    if not (FEEDBACK_ALERT_EMAIL and SMTP_HOST and SMTP_USER and SMTP_PASS):
        print("[feedback_alert] no SMTP/FEEDBACK_ALERT_EMAIL configured, logged only", flush=True)
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Mend/Thimble: {down_count + confused_count} feedback flags in {window_minutes}m"
        msg["From"] = MAIL_FROM
        msg["To"] = FEEDBACK_ALERT_EMAIL
        msg.set_content(body)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print("[feedback_alert] email sent", flush=True)
    except Exception as e:
        print(f"[feedback_alert] send failed, already logged locally: {e!r}", flush=True)


def check_once(window_minutes: int, threshold: int, cooldown_minutes: int, dry_run: bool) -> None:
    now = time.time()
    window_start = now - window_minutes * 60
    events = read_feedback_events(window_start)
    down_count = sum(1 for e in events if e.get("flag") == "down")
    confused_count = sum(1 for e in events if e.get("flag") == "confused")
    total = down_count + confused_count

    state = load_state()
    cooldown_ok = (now - state.get("last_alert_ts", 0)) >= cooldown_minutes * 60

    if total < threshold:
        print(f"[feedback_alert] {total} flag(s) in the last {window_minutes}m, below threshold {threshold} -- no alert", flush=True)
        return
    if not cooldown_ok:
        print(f"[feedback_alert] {total} flag(s) over threshold, but still in cooldown (last alert {int((now - state['last_alert_ts']) / 60)}m ago) -- skipping", flush=True)
        return

    reasons: dict[str, int] = {}
    for e in events:
        if e.get("flag") in ("down", "confused"):
            slug = e.get("reason") or "no_reason_given"
            reasons[slug] = reasons.get(slug, 0) + 1

    send_alert(down_count, confused_count, reasons, window_minutes, dry_run)
    if not dry_run:
        state["last_alert_ts"] = now
        save_state(state)
        with ALERT_LOG_FILE.open("a") as f:
            f.write(json.dumps({"ts": now, "down": down_count, "confused": confused_count, "reasons": reasons}) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--window", type=int, default=60, help="rolling window in minutes to count flags over (default: 60)")
    p.add_argument("--threshold", type=int, default=3, help="total down+confused flags in the window that triggers an alert (default: 3)")
    p.add_argument("--cooldown", type=int, default=60, help="minimum minutes between alerts, even if still over threshold (default: 60)")
    p.add_argument("--dry-run", action="store_true", help="print what would be sent without emailing or updating alert state")
    p.add_argument("--loop", action="store_true", help="keep checking on --interval instead of running once and exiting (for local testing; use cron for real deployment)")
    p.add_argument("--interval", type=int, default=300, help="seconds between checks when --loop is set (default: 300)")
    args = p.parse_args()

    if args.loop:
        print(f"[feedback_alert] looping every {args.interval}s (window={args.window}m threshold={args.threshold} cooldown={args.cooldown}m dry_run={args.dry_run})", flush=True)
        while True:
            check_once(args.window, args.threshold, args.cooldown, args.dry_run)
            time.sleep(args.interval)
    else:
        check_once(args.window, args.threshold, args.cooldown, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
