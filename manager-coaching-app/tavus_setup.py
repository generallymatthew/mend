#!/usr/bin/env python3
"""
One-time provisioning script for the optional Tavus video-avatar mode.
Creates a Tavus PAL whose custom LLM points at this app's /llm/chat/completions
shim (so the avatar speaks the real facilitator's replies, not Tavus's own
default model), and prints the pal_id to put in .env as TAVUS_PAL_ID.

Run once, after:
  - TAVUS_API_KEY and TAVUS_FACE_ID are set in .env (see README.md)
  - LLM_SHIM_SECRET is set in .env to any random string you make up
  - a public tunnel to this app is running (e.g. `cloudflared tunnel --url
    http://localhost:8425`) and PUBLIC_LLM_BASE_URL in .env is set to the
    https URL it printed

Run again (it creates a new PAL each time) whenever PUBLIC_LLM_BASE_URL
changes -- a cloudflared quick tunnel gets a new URL every time it restarts.
"""
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

api_key = os.environ.get("TAVUS_API_KEY")
face_id = os.environ.get("TAVUS_FACE_ID")
shim_secret = os.environ.get("LLM_SHIM_SECRET")
public_base_url = os.environ.get("PUBLIC_LLM_BASE_URL")

missing = [name for name, val in [
    ("TAVUS_API_KEY", api_key), ("TAVUS_FACE_ID", face_id),
    ("LLM_SHIM_SECRET", shim_secret), ("PUBLIC_LLM_BASE_URL", public_base_url),
] if not val]
if missing:
    raise SystemExit(f"Missing from .env: {', '.join(missing)} -- see README.md's video setup section")

resp = httpx.post(
    "https://tavusapi.com/v2/pals",
    headers={"x-api-key": api_key, "Content-Type": "application/json"},
    json={
        "pal_name": "Mend manager-coaching facilitator",
        "system_prompt": "Speak naturally and warmly; the words you say come from another system.",
        "default_face_id": face_id,
        "layers": {
            "llm": {
                "model": "mend-manager-coaching-facilitator",
                "base_url": public_base_url.rstrip("/"),
                "api_key": shim_secret,
            },
        },
    },
    timeout=30,
)

if resp.status_code >= 400:
    raise SystemExit(f"Tavus error {resp.status_code}: {resp.text}")

pal_id = resp.json().get("pal_id") or resp.json().get("uuid") or resp.json().get("persona_id")
print(f"Created PAL pointed at {public_base_url}")
print(f"Add this to .env:\nTAVUS_PAL_ID={pal_id}")
