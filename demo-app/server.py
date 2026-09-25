#!/usr/bin/env python3
"""
Local demo hub: sign-up / anonymous-invite screen plus a walkthrough of the
full journey across ../intake-app, ../joint-session-app, ../post-session-app.

No LLM calls, no persistence -- this app just serves one static page. Signup
and invite state live in the browser's localStorage, standing in for the
shared-org-access-code + personal-email flow in ../product-spec.html. It is
NOT a real implementation of that flow (no server, no crypto-shredding, no
real invite delivery) -- it's a click-through of what the UX would feel like.

Run:
    pip install -r requirements.txt
    uvicorn server:app --reload --port 8423
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
app = FastAPI()


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
