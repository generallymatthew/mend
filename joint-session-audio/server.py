#!/usr/bin/env python3
"""
Mints LiveKit room-access tokens for the joint-session-audio prototype and
serves the mic-capture page. This process does not touch audio itself --
that's agent.py (the LiveKit Agents worker) and the local `livekit-server
--dev` process. All three run together; see README.md.

Same `/?code=&role=` convention as ../joint-session-app, so a link like

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
