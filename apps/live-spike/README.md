# Gemini Live spike

A throwaway comparison harness, **not** part of Thimble and not wired into
it. Built to answer one question from a real conversation: how does a true
duplex speech-to-speech model (Gemini Live) actually feel compared to
Thimble's cascaded Whisper/Deepgram -> Claude -> OpenAI-TTS pipeline, and
what does it cost against the GCP-for-Startups credit in practice?

Reuses Thimble's own system prompt (`apps/facilitator-intake-system-prompt.md`)
so the comparison is about the pipeline, not the persona.

## One-time setup

1. Install the gcloud CLI if you don't have it (`brew install --cask google-cloud-sdk`).
2. `gcloud auth application-default login` -- opens a browser, you sign in
   with your own Google account. No key file, no API key: this app never
   handles credential material directly, it relies on Application Default
   Credentials the SDK finds automatically.
3. `gcloud config set project YOUR_PROJECT_ID` (the project your
   GCP-for-Startups credit is attached to).
4. `gcloud services enable aiplatform.googleapis.com`
5. Copy `.env.example` to `.env` and fill in `GOOGLE_CLOUD_PROJECT` (and
   `GOOGLE_CLOUD_LOCATION` / `LIVE_MODEL` if the defaults don't match what
   your project actually has access to -- Live models are region-gated and
   the exact model name is a moving target).

## Running it

```
cd apps/live-spike
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn server:app --port 8500
```

Open http://localhost:8500, click "Start talking", and just talk -- there's
no push-to-talk and no client-side VAD, since Gemini Live's own server-side
turn detection is exactly the thing being evaluated here.

## What this deliberately doesn't do

- No idle-expiry / zero-trace handling (what Thimble just got) -- a spike,
  not a thing real users touch.
- No barge-in UI beyond logging an `[interrupted]` line when Gemini reports
  one server-side.
- No session persistence, no analytics, no access codes.

If the comparison looks good, the next step is deciding how much of this
(if any) replaces Thimble's pipeline -- not extending this spike in place.
