# Render deploy image for demo-app + Thimble behind Caddy. Build context
# is the repo root (see render.yaml's dockerContext), since Thimble
# reads ../facilitator-intake-system-prompt.md and ../../product-spec.html
# at runtime -- the whole repo ships, not just the two app folders.
#
# Caddy is fetched as a plain release binary, not via apt or copied from
# the official Caddy image. apt: Cloudsmith's Debian repo for Caddy has an
# expired signing subkey, failing OpenPGP verification on current Debian
# (trixie) base images. The official image's binary carries a Linux file
# capability (cap_net_bind_service) that Render's sandboxed build/runtime
# won't honor on a multi-stage COPY -- "Operation not permitted" on exec.
# A plain release tarball has no such capability set.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && CADDY_VERSION=2.8.4 \
    && curl -fsSL "https://github.com/caddyserver/caddy/releases/download/v${CADDY_VERSION}/caddy_${CADDY_VERSION}_linux_amd64.tar.gz" -o /tmp/caddy.tar.gz \
    && tar -xzf /tmp/caddy.tar.gz -C /usr/local/bin caddy \
    && chmod +x /usr/local/bin/caddy \
    && rm /tmp/caddy.tar.gz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r apps/demo-app/requirements.txt -r apps/thimble/requirements.txt

# Pre-download the Whisper model at build time, not on a tester's first
# request -- avoids a slow, surprising first-reply latency in prod.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en')"

RUN chmod +x deploy/start.sh

ENV WHISPER_MODEL=tiny.en
CMD ["deploy/start.sh"]
