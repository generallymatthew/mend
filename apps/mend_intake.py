"""
Shared conversation-with-a-facilitator primitive, used by both suture and
loom (and, going forward, any new mode built on the same intake
mechanism). See IDEAS.md's "Suture/Loom convergence..." entry
(2026-11-11): both apps already implemented this near-identically --
this module is that consolidation, not a merge of either app's own
topology (suture keeps its fixed two-role joint room, loom keeps its
many-independent-threads-pooled-by-sprint shape).

Each caller is still responsible for appending the latest user turn to
its own `conversation` list before calling `call_facilitator`, and for
parsing/acting on the returned raw `signal` string itself (its shape
differs per prompt -- suture's <mend_signal>, loom's <loom_signal>).
"""
import json
import re

ROOT = __import__("pathlib").Path(__file__).parent

# Mode registry: metadata only, for now -- which intake prompt a mode uses
# and a label for what kind of thing its triage step is watching for. Not
# yet wired to swap in a different classifier automatically or to pick a
# prompt by name instead of a hardcoded path; each app still loads and
# calls its own prompt file directly. Exists so "mode" has one shared
# vocabulary across apps as retro/critique modes get built out, per
# IDEAS.md 2026-11-11.
MODES = {
    "conflict": {
        "intake_prompt": ROOT / "facilitator-suture-intake-system-prompt.md",
        "escalation": "harassment",
    },
    "retro": {
        "intake_prompt": ROOT / "facilitator-loom-intake-system-prompt.md",
        "escalation": "toxic_dynamic",
    },
    "critique": {
        "intake_prompt": ROOT / "facilitator-loom-intake-system-prompt.md",
        "escalation": "toxic_dynamic",
    },
}


def strip_signal(reply_text: str, tag: str) -> tuple[str, str | None]:
    """Extract the <tag>...</tag> control block, if present, and return
    (visible_text_with_block_removed, raw_signal_text_or_None). The raw
    signal text is NOT parsed as JSON here -- a malformed block shouldn't
    cost the caller the visible reply too. Parse it yourself."""
    match = re.search(rf"<{tag}>(.*?)</{tag}>", reply_text, re.S)
    visible = re.sub(rf"<{tag}>.*?</{tag}>", "", reply_text, flags=re.S).strip()
    return visible, (match.group(1).strip() if match else None)


def call_facilitator(
    client,
    model: str,
    system_prompt: str,
    conversation: list[dict],
    *,
    tag: str,
    app: str,
    reply_kind: str,
    max_tokens: int = 8192,
) -> dict:
    """Calls the model against `conversation`, whose last turn must already
    be the new user turn the caller just appended. Rolls that turn back
    out of `conversation` on any failure or empty reply, so `conversation`
    always ends on a complete assistant turn or is left unchanged -- same
    convention suture and loom each implemented separately before this.
    On success, strips the <tag> control block out of the visible text and
    appends the raw assistant turn (signal included) back onto
    `conversation`, so the model sees its own prior signal next turn.

    Returns {"reply": <visible text>, "signal": <raw signal text or None>}.
    `signal` is NOT parsed as JSON -- each app's signal shape differs.
    """
    from usage_log import log_usage  # repo root; caller's sys.path already has it

    if client is None:
        conversation.pop()
        return {"reply": "(server error: ANTHROPIC_API_KEY is not set -- see README)", "signal": None}
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=conversation,
        )
    except Exception as e:
        conversation.pop()
        return {"reply": f"(server error calling Claude: {e})", "signal": None}
    log_usage(
        app, "anthropic", model, reply_kind,
        input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens,
    )
    raw = "".join(block.text for block in response.content if block.type == "text")
    if not raw:
        conversation.pop()
        return {
            "reply": f"(server error: no text in response, stop_reason={response.stop_reason})",
            "signal": None,
        }
    visible, signal = strip_signal(raw, tag)
    conversation.append({"role": "assistant", "content": raw})
    return {"reply": visible, "signal": signal}


def parse_signal_json(signal_text: str | None) -> dict | None:
    """Convenience for the common case: parse the raw signal text as JSON,
    returning None on any failure (unset or malformed) instead of raising."""
    if not signal_text:
        return None
    try:
        return json.loads(signal_text)
    except json.JSONDecodeError:
        return None
