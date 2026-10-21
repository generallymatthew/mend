#!/usr/bin/env python3
"""
Mints LiveKit room-access tokens for the joint-session-audio prototype and
serves the mic-capture page. This process does not touch audio itself --
that's agent.py (the LiveKit Agents worker) and the local `livekit-server
--dev` process. All three run together; see README.md.

Same `/?code=&role=` convention as ../suture, so a link like

    http://localhost:8424/?code=test1&role=a
    http://localhost:8424/?code=test1&role=b

hands out one role each. In-memory only, no persistence, matches every
other app here.

Run:
    pip install -r requirements.txt
    livekit-server --dev   # separate terminal, see README.md
    python agent.py dev    # separate terminal
    uvicorn server:app --reload --port 8424
"""
import os
from pathlib import Path

import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from livekit import api

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")

ROLE_IDENTITIES = {"a": "employee_a", "b": "employee_b"}

app = FastAPI()
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

_lkapi: api.LiveKitAPI | None = None


def get_lkapi() -> api.LiveKitAPI:
    # Lazy singleton: this admin client is only needed by the manual
    # breakout-room trigger below, not by every request.
    global _lkapi
    if _lkapi is None:
        _lkapi = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    return _lkapi


@app.on_event("shutdown")
async def _close_lkapi():
    if _lkapi is not None:
        await _lkapi.aclose()


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/config")
def config():
    return JSONResponse({"livekit_url": LIVEKIT_URL})


@app.get("/api/token")
def token(code: str, role: str, video_consent: bool = False):
    identity = ROLE_IDENTITIES.get(role)
    if identity is None:
        raise HTTPException(status_code=400, detail="role must be 'a' or 'b'")
    room_name = f"joint-audio-{code}"
    grant = api.VideoGrants(room_join=True, room=room_name, can_publish=True, can_subscribe=True)
    # video_consent rides in as a participant attribute (structured
    # key/value, not the single-string .metadata) -- agent.py reads it on
    # participant_connected to seed video_parity.VideoParityGate. Defaults
    # to False: skipping this param, same as declining outright, fails safe
    # to avatar_audio_only, never to video_active. See
    # ../joint-session-audio/README.md's "Video opt-in" section.
    jwt = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_grants(grant)
        .with_attributes({"video_consent": "true" if video_consent else "false"})
        .to_jwt()
    )
    return JSONResponse({"token": jwt, "room": room_name, "identity": identity})


# --- Manual/test-only breakout-room trigger --------------------------------
# agent.py owns the actual BreakoutGate + audio isolation, in its own
# process, as a participant inside the room. This process is not a
# participant -- it never joins a room itself, only mints tokens -- so the
# only way to reach a running agent job is the room's own data channel via
# the admin RoomService API (self-hosted-compatible; see breakout_gate.py's
# module docstring). A real facilitator-LLM integration would send this
# exact same control message from wherever it runs; these two endpoints are
# that seam, exposed here so the mechanism can be exercised by hand or by
# tests/test_breakout_gate.py's live-server counterpart, not because this
# process makes any decision about when a check-in should happen.
@app.post("/api/room/{code}/checkin")
async def trigger_checkin(code: str, payload: dict):
    target = payload.get("target")
    if target not in ("employee_a", "employee_b"):
        raise HTTPException(status_code=400, detail="target must be 'employee_a' or 'employee_b'")
    room_name = f"joint-audio-{code}"
    await get_lkapi().room.send_data(
        api.SendDataRequest(
            room=room_name,
            data=json.dumps({"type": "breakout_checkin", "target": target}).encode(),
            # kind defaults to RELIABLE -- a dropped control message would
            # leave the room stuck paused (or never paused), unlike an
            # ordinary audio frame where dropping one is harmless.
        )
    )
    return {"sent": "breakout_checkin", "target": target}


@app.post("/api/room/{code}/resume")
async def trigger_resume(code: str):
    room_name = f"joint-audio-{code}"
    await get_lkapi().room.send_data(
        api.SendDataRequest(
            room=room_name,
            data=json.dumps({"type": "breakout_resume"}).encode(),
        )
    )
    return {"sent": "breakout_resume"}
