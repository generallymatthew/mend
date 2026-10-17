#!/usr/bin/env bash
# Render start command: runs demo-app + intake-app (unmodified) behind Caddy
# on Render's injected $PORT. Mirrors ../run_all.sh's shape for local dev,
# trimmed to the two apps this deploy sends to testers, and using
# render.Caddyfile instead of ../Caddyfile (fixed :8080 -> $PORT).
#
# Every subprocess's output is tagged and sent to this script's own
# stdout/stderr, not redirected to a file -- Render only captures the
# container's own stdout as logs, and a file under this ephemeral
# container's disk is otherwise invisible from the dashboard.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PIDS=()

start_app() {
  local name="$1" dir="$2" port="$3"
  ( cd "$dir" && exec uvicorn server:app --host 0.0.0.0 --port "$port" ) \
    2>&1 | sed -u "s/^/[$name] /" &
  PIDS+=("$!")
  echo "-> $name on :$port"
}

cleanup() {
  echo "shutting down..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

start_app demo-app   apps/demo-app   8423
start_app intake-app apps/intake-app 8420

sleep 1
echo "Starting Caddy on :${PORT:-8080}"
caddy run --config deploy/render.Caddyfile --adapter caddyfile 2>&1 | sed -u "s/^/[caddy] /" &
PIDS+=("$!")

wait
