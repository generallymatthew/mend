#!/usr/bin/env python3
"""
Local demo hub: sign-up / anonymous-invite screen plus a walkthrough of the
full journey across ../intake-app, ../joint-session-app, ../post-session-app.

Runs the real access-code + personal-email signup and one-time invite flow
from Section 3 of ../product-spec.html -- not a client-side simulation.
In-memory only (no database), same convention as every other app here:
state is lost on restart. What's real:

- Signup checks a real ORG_ACCESS_CODE (.env), not "any code works."
- An invite is a server-side record, so it resolves correctly for a real
  second person on a different device/browser, not just the same browser
  that created it.
- Crypto-shredding, not just a status flag: each invite's `from_email` is
  encrypted with a key generated just for that invite (Fernet). The key is
  deleted the moment the invite resolves (accepted or declined) -- the
  ciphertext stays but is now permanently unreadable, even by this same
  process. That's what "the key is destroyed, not the record" means in the
  spec, implemented, not just referenced in a comment.

Deliberately not built here (see the plan / product-spec.html for why):
peer-suggested invites (a distinct mechanism), invite expiry, multi-org
access codes, rate limiting, or any real password/persistent-account system
-- the access code itself is a trust model, not a cryptographic guarantee,
per the spec's own framing.

Run:
    pip install -r requirements.txt
    echo "ORG_ACCESS_CODE=WILLOW-CREEK-9F2" > .env   # or your own
    uvicorn server:app --reload --port 8423
"""
import os
import secrets
import time
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

ORG_ACCESS_CODE = os.environ.get("ORG_ACCESS_CODE", "")

app = FastAPI()

# In-memory only -- lost on restart, same convention as every other app here.
IDENTITIES: dict[str, str] = {}  # identity_token -> email
INVITES: dict[str, dict] = {}  # invite_id -> {status, ciphertext, key, joint_code}

# --- Rate limiting --------------------------------------------------------
# /api/signup is a brute-force surface for ORG_ACCESS_CODE -- a wrong guess
# costs nothing but a dict lookup, so without a limit it can be guessed as
# fast as requests arrive. General /api/* limit covers invite/accept/decline
# abuse the same way ../intake-app/server.py covers its own LLM-calling
# endpoints. In-memory fixed-window per client IP, no new dependency.
SIGNUP_RATE_MAX = int(os.environ.get("SIGNUP_RATE_MAX", "5"))
SIGNUP_RATE_WINDOW = int(os.environ.get("SIGNUP_RATE_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
_signup_hits: dict[str, list[float]] = {}
_rate_hits: dict[str, list[float]] = {}


def _too_many(bucket: dict[str, list[float]], ip: str, max_hits: int, window: int) -> bool:
    now = time.time()
    hits = [t for t in bucket.get(ip, []) if now - t < window]
    if len(hits) >= max_hits:
        bucket[ip] = hits
        return True
    hits.append(now)
    bucket[ip] = hits
    return False


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        if request.url.path == "/api/signup" and _too_many(_signup_hits, ip, SIGNUP_RATE_MAX, SIGNUP_RATE_WINDOW):
            return JSONResponse({"error": "too many attempts -- slow down and try again shortly"}, status_code=429)
        if _too_many(_rate_hits, ip, RATE_LIMIT_MAX, RATE_LIMIT_WINDOW):
            return JSONResponse({"error": "too many requests -- slow down and try again shortly"}, status_code=429)
    return await call_next(request)


def require_identity(token: str) -> str | None:
    return IDENTITIES.get(token)


@app.post("/api/signup")
async def signup(payload: dict):
    org_code = (payload.get("org_code") or "").strip()
    email = (payload.get("email") or "").strip()
    if not ORG_ACCESS_CODE:
        return JSONResponse({"error": "server has no ORG_ACCESS_CODE configured -- see README"}, status_code=500)
    if org_code != ORG_ACCESS_CODE:
        return JSONResponse({"error": "that access code isn't recognized"}, status_code=400)
    if "@" not in email:
        return JSONResponse({"error": "enter a valid personal email"}, status_code=400)
    token = secrets.token_urlsafe(24)
    IDENTITIES[token] = email
    return {"identity_token": token, "email": email}


@app.post("/api/invite")
async def create_invite(payload: dict):
    token = payload.get("identity_token") or ""
    email = require_identity(token)
    if not email:
        return JSONResponse({"error": "sign up first"}, status_code=401)

    invite_id = secrets.token_urlsafe(12)
    joint_code = secrets.token_urlsafe(6)
    key = Fernet.generate_key()
    ciphertext = Fernet(key).encrypt(email.encode())
    INVITES[invite_id] = {
        "status": "pending",
        "ciphertext": ciphertext,
        "key": key,
        "joint_code": joint_code,
    }
    return {"invite_id": invite_id}


@app.get("/api/invite/{invite_id}")
async def get_invite(invite_id: str):
    invite = INVITES.get(invite_id)
    if not invite:
        return JSONResponse({"error": "no such invite"}, status_code=404)
    result = {"status": invite["status"]}
    if invite["status"] == "pending":
        # Only reachable while the key still exists -- that's the whole point.
        result["from_email"] = Fernet(invite["key"]).decrypt(invite["ciphertext"]).decode()
    if invite["status"] == "accepted":
        result["joint_code"] = invite["joint_code"]
    return result


def _resolve_invite(invite_id: str, new_status: str) -> dict | None:
    invite = INVITES.get(invite_id)
    if not invite:
        return None
    if invite["status"] == "pending":
        invite["status"] = new_status
        invite.pop("key", None)  # crypto-shredding: ciphertext stays, key doesn't
    return invite


@app.post("/api/invite/{invite_id}/accept")
async def accept_invite(invite_id: str, payload: dict):
    token = payload.get("identity_token") or ""
    if not require_identity(token):
        return JSONResponse({"error": "sign up first"}, status_code=401)
    invite = _resolve_invite(invite_id, "accepted")
    if not invite:
        return JSONResponse({"error": "no such invite"}, status_code=404)
    return {"status": invite["status"], "joint_code": invite["joint_code"]}


@app.post("/api/invite/{invite_id}/decline")
async def decline_invite(invite_id: str, payload: dict):
    token = payload.get("identity_token") or ""
    if not require_identity(token):
        return JSONResponse({"error": "sign up first"}, status_code=401)
    invite = _resolve_invite(invite_id, "declined")
    if not invite:
        return JSONResponse({"error": "no such invite"}, status_code=404)
    return {"status": invite["status"]}


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
