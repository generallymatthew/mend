"""
Shared local usage/cost logger for every app's own paid API calls
(Anthropic, OpenAI TTS, Deepgram STT/TTS). Each app imports this the same
way suture already reaches into ../classifier: sys.path.insert
then a plain import, no packaging.

Appends one JSON line per billed call to usage_log.jsonl at the repo root
(shared across apps, so a single file gives the whole product's spend, not
just one app's) -- same append-only JSONL shape as thimble/server.py's
own SCREEN_LOG_FILE/log_screen_signal, for consistency with the one local
logging convention that already exists in this codebase.

Prices below are manually maintained (no billing API gives these back
per-call) and will drift out of date -- they're for a running estimate to
catch "something's burning a lot of money" early, not a reconciled invoice.
Check the provider's own dashboard for actual billed totals.
"""
import json
import time
from pathlib import Path

USAGE_LOG_FILE = Path(__file__).parent / "usage_log.jsonl"

# $ per unit. Anthropic/OpenAI chat: per 1M tokens. TTS: per 1M characters.
# Deepgram STT: per minute of audio. Source: each provider's public pricing
# page, captured 2026-10 -- re-check before trusting this for anything that
# actually matters.
PRICING = {
    ("anthropic", "claude-sonnet-5", "input"): 3.00 / 1_000_000,
    ("anthropic", "claude-sonnet-5", "output"): 15.00 / 1_000_000,
    ("anthropic", "claude-haiku-4-5-20251001", "input"): 1.00 / 1_000_000,
    ("anthropic", "claude-haiku-4-5-20251001", "output"): 5.00 / 1_000_000,
    ("openai", "tts-1", "chars"): 15.00 / 1_000_000,
    ("openai", "gpt-4o-mini-tts", "chars"): 12.00 / 1_000_000,
    ("deepgram", "aura-asteria-en", "chars"): 15.00 / 1_000_000,
    ("deepgram", "nova-2", "minutes"): 0.0043,
}


def _cost(provider: str, model: str, **amounts: float) -> float | None:
    total = 0.0
    found = False
    for unit, amount in amounts.items():
        if amount is None:
            continue
        price = PRICING.get((provider, model, unit))
        if price is None:
            continue
        total += price * amount
        found = True
    return total if found else None


def log_usage(
    app: str,
    provider: str,
    model: str,
    kind: str,
    *,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    chars: int | None = None,
    seconds: float | None = None,
) -> None:
    """Append one usage record. `kind` is a free-text label for what the
    call was for (e.g. "facilitator_reply", "judge_vote", "tts", "stt") --
    useful for telling a cheap-but-frequent call site apart from an
    expensive-but-rare one in the same app."""
    minutes = seconds / 60 if seconds is not None else None
    cost = _cost(
        provider,
        model,
        input=input_tokens,
        output=output_tokens,
        chars=chars,
        minutes=minutes,
    )
    record = {
        "ts": time.time(),
        "app": app,
        "provider": provider,
        "model": model,
        "kind": kind,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "chars": chars,
        "seconds": seconds,
        "cost_usd": cost,
    }
    with USAGE_LOG_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
