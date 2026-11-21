"""
Gemini Live spike -- NOT Thimble, not wired into it, nothing shared at
runtime. A standalone throwaway app to answer one question: how does a true
duplex speech-to-speech model (Gemini Live, via Vertex AI so usage can draw
against the GCP-for-Startups credit) actually feel compared to Thimble's
cascaded Whisper/Deepgram -> Claude -> OpenAI-TTS pipeline, and what does it
cost in practice? Reuses Thimble's own system prompt so the comparison is
apples-to-apples on persona/behavior, not on infra.

No client-side VAD, no barge-in handling, no session persistence, no
idle-expiry -- all the things Thimble's pipeline hand-rolls are exactly what
Gemini Live's server-side turn detection is supposed to replace. This spike
exists to find out whether that's actually true, not to reimplement those
safeguards here too.

Requires:
  - A GCP project with the Vertex AI API enabled (`gcloud services enable
    aiplatform.googleapis.com`).
  - `gcloud auth application-default login` run once, locally, so the
    google-genai SDK can find Application Default Credentials. No API key or
    service-account file is handled by this code.
  - GOOGLE_CLOUD_PROJECT (and optionally GOOGLE_CLOUD_LOCATION, default
    us-central1) set in apps/live-spike/.env.
"""
import asyncio
import os
import re
import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
# "global" is required for the Live (bidiGenerateContent) websocket on
# Vertex AI as of this writing -- every concrete region tried (us-central1,
# us-east1/4, us-west1, europe-west1/4, asia-northeast1) returned a 1008
# policy-violation close even though the model exists (confirmed GA via a
# plain REST GET on publishers/google/models/gemini-live-2.5-flash), while
# "global" connected cleanly. Live models are a moving target generally, so
# override via .env if this stops being true.
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
LIVE_MODEL = os.environ.get("LIVE_MODEL", "gemini-live-2.5-flash")

# Same fenced-prompt file and extraction Thimble's server.py uses (see its
# load_system_prompt()), read directly rather than importing Thimble's
# module -- this app has no other dependency on Thimble and shouldn't gain
# one just to share six lines of parsing.
SYSTEM_PROMPT_FILE = ROOT.parent / "facilitator-intake-system-prompt.md"


def load_system_prompt() -> str:
    text = SYSTEM_PROMPT_FILE.read_text()
    match = re.search(r"```\n(.*?)\n```", text, re.S)
    if not match:
        raise RuntimeError(f"couldn't find fenced system prompt in {SYSTEM_PROMPT_FILE}")
    return match.group(1)


SYSTEM_PROMPT = load_system_prompt()

app = FastAPI()

_client = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not PROJECT_ID:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT isn't set -- put it in apps/live-spike/.env "
                "(the project tied to your GCP-for-Startups credit)."
            )
        _client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    return _client


LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=types.Content(parts=[types.Part(text=SYSTEM_PROMPT)]),
)


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws.accept()
    try:
        client = get_client()
    except RuntimeError as e:
        await ws.send_json({"type": "error", "message": str(e)})
        await ws.close()
        return

    try:
        async with client.aio.live.connect(model=LIVE_MODEL, config=LIVE_CONFIG) as session:

            async def pump_browser_to_gemini():
                # Continuous mic audio in, no client-side VAD -- Gemini
                # Live's own server-side turn detection decides when the
                # user has finished speaking. That's the entire thing this
                # spike exists to evaluate.
                while True:
                    chunk = await ws.receive_bytes()
                    await session.send_realtime_input(
                        audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                    )

            async def pump_gemini_to_browser():
                async for response in session.receive():
                    if response.data:
                        await ws.send_bytes(response.data)
                    server_content = response.server_content
                    if server_content and server_content.input_transcription:
                        await ws.send_json({
                            "type": "transcript_in",
                            "text": server_content.input_transcription.text,
                        })
                    if server_content and server_content.output_transcription:
                        await ws.send_json({
                            "type": "transcript_out",
                            "text": server_content.output_transcription.text,
                        })
                    if server_content and server_content.interrupted:
                        await ws.send_json({"type": "interrupted"})

            browser_task = asyncio.create_task(pump_browser_to_gemini())
            gemini_task = asyncio.create_task(pump_gemini_to_browser())
            done, pending = await asyncio.wait(
                {browser_task, gemini_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            for task in done:
                exc = task.exception()
                if exc:
                    raise exc
    except WebSocketDisconnect:
        pass
    except Exception:
        traceback.print_exc()
        try:
            await ws.send_json({"type": "error", "message": "see server logs"})
        except Exception:
            pass
