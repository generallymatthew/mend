# Render deploy image for demo-app + intake-app behind Caddy. Build context
# is the repo root (see render.yaml's dockerContext), since intake-app
# reads ../facilitator-intake-system-prompt.md and ../product-spec.html at
# runtime -- the whole repo ships, not just the two app folders.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl debian-keyring debian-archive-keyring apt-transport-https gnupg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
       -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
       -o /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update && apt-get install -y --no-install-recommends caddy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r demo-app/requirements.txt -r intake-app/requirements.txt

# Pre-download the Whisper model at build time, not on a tester's first
# request -- avoids a slow, surprising first-reply latency in prod.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en')"

RUN chmod +x deploy/start.sh

ENV WHISPER_MODEL=tiny.en
CMD ["deploy/start.sh"]
