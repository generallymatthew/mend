# Render deploy image for demo-app + intake-app behind Caddy. Build context
# is the repo root (see render.yaml's dockerContext), since intake-app
# reads ../facilitator-intake-system-prompt.md and ../product-spec.html at
# runtime -- the whole repo ships, not just the two app folders.
#
# Caddy comes from its own official image (copied binary), not apt --
# Cloudsmith's Debian apt repo for Caddy has an expired signing subkey,
# which fails OpenPGP verification on current Debian (trixie) base images.
FROM caddy:2 AS caddy

FROM python:3.11-slim
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r demo-app/requirements.txt -r intake-app/requirements.txt

# Pre-download the Whisper model at build time, not on a tester's first
# request -- avoids a slow, surprising first-reply latency in prod.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en')"

RUN chmod +x deploy/start.sh

ENV WHISPER_MODEL=tiny.en
CMD ["deploy/start.sh"]
