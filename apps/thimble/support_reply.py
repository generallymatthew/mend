#!/usr/bin/env python3
"""
Drafts replies to the support inbox (see docs/pitch-strategy/34_STRIPE_CHECKOUT_SETUP.md's
"relationship management by email only" model) using Thimble's
support-reply-system-prompt.md persona -- distinct from the in-session
facilitator persona, since this one talks to buyers/HR contacts, not
employees in a session.

Deliberately drafts only, never sends. Sending a wrong answer to a real
customer (a promised refund that didn't happen, a made-up feature) is a
real trust cost for a product whose whole pitch is restraint and
accuracy -- a human reads and sends every reply themselves. This also
keeps it outside the "send a message on the user's behalf" line: Claude
drafts, the founder decides and hits send from their own mail client.

Needs IMAP (to read the inbox and file drafts) and SMTP (only to know
the From/Reply-To address to put on the draft, no sending happens here).
Works against any IMAP mailbox -- the founder@mend.work inbox as of
2026-11 is receive-only via forwarding (see FUNDING.md), so point this
at wherever that forwards to until a real mailbox exists at that domain.

Env vars (.env, same file server.py/digest.py already load):
    SUPPORT_IMAP_HOST, SUPPORT_IMAP_USER, SUPPORT_IMAP_PASS
    SUPPORT_IMAP_FOLDER        default "INBOX"
    SUPPORT_DRAFTS_FOLDER      default "Drafts"
    SUPPORT_FROM_ADDRESS       what the draft's From/Reply-To header says,
                                e.g. founder@mend.work
    ANTHROPIC_API_KEY          same key server.py uses

Run (e.g. from cron, every 15 min):
    python3 support_reply.py

Preview without touching the mailbox's draft folder or read flags:
    python3 support_reply.py --dry-run
"""
import argparse
import email
import imaplib
import json
import os
import sys
import time
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr, make_msgid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

SUPPORT_IMAP_HOST = os.environ.get("SUPPORT_IMAP_HOST", "")
SUPPORT_IMAP_USER = os.environ.get("SUPPORT_IMAP_USER", "")
SUPPORT_IMAP_PASS = os.environ.get("SUPPORT_IMAP_PASS", "")
SUPPORT_IMAP_FOLDER = os.environ.get("SUPPORT_IMAP_FOLDER", "INBOX")
SUPPORT_DRAFTS_FOLDER = os.environ.get("SUPPORT_DRAFTS_FOLDER", "Drafts")
SUPPORT_FROM_ADDRESS = os.environ.get("SUPPORT_FROM_ADDRESS", SUPPORT_IMAP_USER)

SYSTEM_PROMPT_FILE = ROOT / "support-reply-system-prompt.md"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

# Message-IDs already drafted, so a run that overlaps the previous one
# (or a message that's read but not yet actually replied to by the
# founder) never gets a duplicate draft. Keyed by Message-ID, not UID,
# since UIDs aren't stable across folders/providers the way Message-ID is.
STATE_FILE = ROOT / "support_reply_state.json"
FLAG_LOG_FILE = ROOT / "support_reply_flags.jsonl"


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"drafted_message_ids": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"drafted_message_ids": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))


def decode_str(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def extract_body(msg: email.message.Message) -> str:
    """Plain-text body only -- never renders/executes HTML, and a reply
    is drafted from what a person actually wrote, not from any script or
    link an HTML part might carry."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                charset = part.get_content_charset() or "utf-8"
                try:
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    continue
        return ""
    if msg.get_content_type() == "text/plain":
        charset = msg.get_content_charset() or "utf-8"
        try:
            return msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            return ""
    return ""


def fetch_unread(conn: imaplib.IMAP4_SSL) -> list[tuple[str, email.message.Message]]:
    conn.select(SUPPORT_IMAP_FOLDER)
    typ, data = conn.search(None, "UNSEEN")
    if typ != "OK":
        return []
    out = []
    for num in data[0].split():
        typ, msg_data = conn.fetch(num, "(RFC822)")
        if typ != "OK" or not msg_data or not msg_data[0]:
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        out.append((num.decode(), msg))
    return out


def draft_reply(client: Anthropic, system_prompt: str, sender_name: str, subject: str, body: str) -> tuple[str, str | None]:
    """Returns (reply_body, flag_reason_or_None)."""
    user_turn = (
        f"From: {sender_name}\nSubject: {subject}\n\n{body.strip()}"
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_turn}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text").strip()
    flag_reason = None
    lines = text.splitlines()
    if lines and lines[-1].strip().startswith("[[FLAG:") and lines[-1].strip().endswith("]]"):
        flag_reason = lines[-1].strip()[len("[[FLAG:"):-2].strip()
        text = "\n".join(lines[:-1]).rstrip()
    return text, flag_reason


def build_draft_message(to_addr: str, subject: str, body: str, in_reply_to: str | None, references: str | None) -> bytes:
    msg = EmailMessage()
    msg["From"] = SUPPORT_FROM_ADDRESS
    msg["To"] = to_addr
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    msg["Message-ID"] = make_msgid()
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    msg.set_content(body)
    return msg.as_bytes()


def append_draft(conn: imaplib.IMAP4_SSL, raw: bytes) -> bool:
    typ, _ = conn.append(SUPPORT_DRAFTS_FOLDER, r"(\Draft)", imaplib.Time2Internaldate(time.time()), raw)
    return typ == "OK"


def log_flag(message_id: str, sender: str, subject: str, reason: str) -> None:
    record = {"ts": time.time(), "message_id": message_id, "sender": sender, "subject": subject, "reason": reason}
    with FLAG_LOG_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[support_reply] FLAGGED for founder attention -- {sender!r} / {subject!r}: {reason}", flush=True)


def check_once(dry_run: bool) -> None:
    if not (SUPPORT_IMAP_HOST and SUPPORT_IMAP_USER and SUPPORT_IMAP_PASS):
        print("[support_reply] SUPPORT_IMAP_HOST/USER/PASS not set -- nothing to do", flush=True)
        return
    if not SYSTEM_PROMPT_FILE.exists():
        print(f"[support_reply] missing {SYSTEM_PROMPT_FILE}", flush=True)
        return
    system_prompt = SYSTEM_PROMPT_FILE.read_text()
    client = Anthropic()
    state = load_state()
    drafted_ids = set(state.get("drafted_message_ids", []))

    conn = imaplib.IMAP4_SSL(SUPPORT_IMAP_HOST)
    conn.login(SUPPORT_IMAP_USER, SUPPORT_IMAP_PASS)
    try:
        unread = fetch_unread(conn)
        print(f"[support_reply] {len(unread)} unread message(s) in {SUPPORT_IMAP_FOLDER}", flush=True)
        for num, msg in unread:
            message_id = msg.get("Message-ID") or f"<no-id-{num}@local>"
            if message_id in drafted_ids:
                continue
            sender_name, sender_addr = parseaddr(decode_str(msg.get("From")))
            subject = decode_str(msg.get("Subject")) or "(no subject)"
            body = extract_body(msg)
            if not body.strip():
                print(f"[support_reply] skipping {message_id} -- no plain-text body found", flush=True)
                continue

            reply_body, flag_reason = draft_reply(client, system_prompt, sender_name or sender_addr, subject, body)

            if dry_run:
                print(f"[support_reply] DRY RUN -- would draft reply to {sender_addr} ({subject!r}):\n{reply_body}\n", flush=True)
                if flag_reason:
                    print(f"[support_reply] DRY RUN -- would flag: {flag_reason}", flush=True)
                continue

            references = msg.get("References") or msg.get("Message-ID") or ""
            raw = build_draft_message(sender_addr, subject, reply_body, msg.get("Message-ID"), references)
            if append_draft(conn, raw):
                print(f"[support_reply] drafted reply to {sender_addr} ({subject!r})", flush=True)
                drafted_ids.add(message_id)
            else:
                print(f"[support_reply] failed to file draft for {message_id} -- will retry next run", flush=True)
                continue

            if flag_reason:
                log_flag(message_id, sender_addr, subject, flag_reason)

        if not dry_run:
            state["drafted_message_ids"] = list(drafted_ids)
            save_state(state)
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="print what would be drafted/flagged without touching the mailbox or state file")
    p.add_argument("--loop", action="store_true", help="keep checking on --interval instead of running once and exiting (for local testing; use cron for real deployment)")
    p.add_argument("--interval", type=int, default=300, help="seconds between checks when --loop is set (default: 300)")
    args = p.parse_args()

    if args.loop:
        print(f"[support_reply] looping every {args.interval}s (dry_run={args.dry_run})", flush=True)
        while True:
            check_once(args.dry_run)
            time.sleep(args.interval)
    else:
        check_once(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
