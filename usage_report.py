#!/usr/bin/env python3
"""
Summarize usage_log.jsonl (see usage_log.py) into a running cost estimate
by app, provider, and model. Local-only estimate, not a reconciled
invoice -- check each provider's own billing dashboard for actual charges.

Run:
    python3 usage_report.py
"""
import json
from collections import defaultdict
from pathlib import Path

USAGE_LOG_FILE = Path(__file__).parent / "usage_log.jsonl"


def main() -> None:
    if not USAGE_LOG_FILE.exists():
        print(f"No usage recorded yet ({USAGE_LOG_FILE} doesn't exist).")
        return

    by_app = defaultdict(float)
    by_provider = defaultdict(float)
    by_model = defaultdict(float)
    unpriced = defaultdict(int)
    total = 0.0
    n = 0

    with USAGE_LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            n += 1
            cost = rec.get("cost_usd")
            if cost is None:
                unpriced[(rec.get("provider"), rec.get("model"))] += 1
                continue
            by_app[rec.get("app")] += cost
            by_provider[rec.get("provider")] += cost
            by_model[f"{rec.get('provider')}/{rec.get('model')}"] += cost
            total += cost

    print(f"{n} calls logged, ${total:,.4f} estimated total\n")

    print("By app:")
    for app, cost in sorted(by_app.items(), key=lambda kv: -kv[1]):
        print(f"  {app:<20} ${cost:,.4f}")

    print("\nBy provider:")
    for provider, cost in sorted(by_provider.items(), key=lambda kv: -kv[1]):
        print(f"  {provider:<20} ${cost:,.4f}")

    print("\nBy model:")
    for model, cost in sorted(by_model.items(), key=lambda kv: -kv[1]):
        print(f"  {model:<30} ${cost:,.4f}")

    if unpriced:
        print("\nCalls logged with no price on file (not in the total above -- add to usage_log.py's PRICING):")
        for (provider, model), count in sorted(unpriced.items(), key=lambda kv: -kv[1]):
            print(f"  {provider}/{model}: {count} calls")


if __name__ == "__main__":
    main()
