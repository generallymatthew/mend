#!/usr/bin/env python3
"""
Monthly per-company usage digest, the "one-way digest" promised in
docs/pitch-strategy/03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md:
"42 sessions run | ~118 hrs reclaimed | 0 statutory escalations" --
no login portal, no queryable database, no drill-down.

Reads only the aggregate fields analytics_events.jsonl already carries
(session_id, ts, event, turn, company) -- never conversation content,
same "nothing is recorded" boundary as feedback_alert.py. "Hours
reclaimed" is an estimate (session count * an assumed average session
length), not a measured duration, since no per-session start/end pairing
is attempted here; refine later if a real average is measured.

The "0 statutory escalations" line comes from screen_signal_log.jsonl's
own signal field, counting the consent-gated/auto-notify floor
categories server.py already classifies -- see maybe_send_hr_notification.

Run monthly (e.g. from cron, on the 1st):
    python3 digest.py

Or preview without sending:
    python3 digest.py --dry-run --since-days 30
"""
import argparse
import json
import smtplib
import sys
import time
from collections import defaultdict
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
import os

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

ANALYTICS_FILE = ROOT / "analytics_events.jsonl"
SCREEN_LOG_FILE = ROOT / "screen_signal_log.jsonl"

# Same SMTP env vars server.py and feedback_alert.py already use -- one
# mail setup for the whole app.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
MAIL_FROM = os.environ.get("MAIL_FROM", SMTP_USER)

# {company name: recipient email} -- deliberately separate from
# ACCESS_CODES (that maps code -> company, this maps company -> who gets
# the digest), since the HR/Risk contact's email isn't something to carry
# in a cookie-readable access code. Same "edit an env var, restart" story
# as ACCESS_CODES in server.py.
def _load_digest_recipients() -> dict[str, str]:
    raw = os.environ.get("DIGEST_RECIPIENTS", "")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError as e:
        print(f"[digest] DIGEST_RECIPIENTS isn't valid JSON ({e}) -- no recipients loaded", flush=True)
    return {}


DIGEST_RECIPIENTS = _load_digest_recipients()

# Used only to turn a session count into an estimated hours-reclaimed
# figure for the digest copy -- a placeholder until a real measured
# average session length exists. Override with DIGEST_AVG_SESSION_MINUTES.
AVG_SESSION_MINUTES = float(os.environ.get("DIGEST_AVG_SESSION_MINUTES", "18"))

# The consent-gated/auto-notify floor categories server.py's
# maybe_send_hr_notification already treats as the ones worth a company's
# attention -- see facilitator-thimble-resolve-intake-system-prompt.md's mandatory-floor
# section. Anything else in screen_signal_log.jsonl isn't counted here.
ESCALATION_CATEGORIES = {
    "harassment_discrimination", "discrimination_retaliation",
    "illegal_activity", "threats_violence", "immediate_safety_risk",
}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def build_digests(since_ts: float) -> dict[str, dict]:
    """One entry per company name seen in the window, keyed off whatever
    company strings actually appear in the data -- not off ACCESS_CODES,
    so a digest still gets built even if a code was later revoked."""
    sessions_by_company: dict[str, set[str]] = defaultdict(set)
    for rec in _read_jsonl(ANALYTICS_FILE):
        if rec.get("event") != "session_start" or rec.get("ts", 0) <= since_ts:
            continue
        company = rec.get("company")
        if not company:
            continue
        sessions_by_company[company].add(rec.get("session_id"))

    escalations_by_company: dict[str, int] = defaultdict(int)
    for rec in _read_jsonl(SCREEN_LOG_FILE):
        if rec.get("ts", 0) <= since_ts:
            continue
        # log_screen_signal (server.py) writes floor_triggered as a
        # top-level field, null or one of the five floor category strings
        # from facilitator-thimble-resolve-intake-system-prompt.md's <mend_signal> block.
        category = rec.get("floor_triggered")
        if category in ESCALATION_CATEGORIES:
            # screen_signal_log.jsonl has session_id, not company -- cross
            # into the session set built above rather than re-deriving it.
            for company, sessions in sessions_by_company.items():
                if rec.get("session_id") in sessions:
                    escalations_by_company[company] += 1

    digests = {}
    for company, sessions in sessions_by_company.items():
        count = len(sessions)
        digests[company] = {
            "sessions": count,
            "hours_reclaimed": round(count * AVG_SESSION_MINUTES / 60, 1),
            "escalations": escalations_by_company.get(company, 0),
        }
    return digests


def format_digest_body(company: str, stats: dict, window_days: int) -> str:
    return (
        f"Thimble usage digest for {company} -- last {window_days} days.\n\n"
        f"  {stats['sessions']} sessions run\n"
        f"  ~{stats['hours_reclaimed']} hrs reclaimed (estimated)\n"
        f"  {stats['escalations']} statutory-floor escalations\n\n"
        "No conversation content, no per-employee breakdown, no login --\n"
        "this is the whole digest, by design. Questions: reply to this email."
    )


def send_digest(recipient: str, company: str, body: str, dry_run: bool) -> None:
    print(f"[digest] {'DRY RUN, not sending: ' if dry_run else ''}to {recipient} ({company}):\n{body}\n", flush=True)
    if dry_run:
        return
    if not (recipient and SMTP_HOST and SMTP_USER and SMTP_PASS):
        print(f"[digest] no SMTP/recipient configured for {company} -- logged only, not sent", flush=True)
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Thimble monthly digest -- {company}"
        msg["From"] = MAIL_FROM
        msg["To"] = recipient
        msg.set_content(body)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print(f"[digest] sent to {recipient}", flush=True)
    except Exception as e:
        print(f"[digest] send failed for {company}: {e!r}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--since-days", type=int, default=30, help="window in days to aggregate over (default: 30)")
    p.add_argument("--dry-run", action="store_true", help="print what would be sent without emailing")
    args = p.parse_args()

    since_ts = time.time() - args.since_days * 86400
    digests = build_digests(since_ts)

    if not digests:
        print("[digest] no sessions attributed to any company in this window -- nothing to send", flush=True)
        return

    for company, stats in sorted(digests.items()):
        recipient = DIGEST_RECIPIENTS.get(company, "")
        body = format_digest_body(company, stats, args.since_days)
        send_digest(recipient, company, body, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
