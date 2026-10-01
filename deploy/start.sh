#!/usr/bin/env bash
# Render start command: runs demo-app + intake-app (unmodified) behind Caddy
# on Render's injected $PORT. Mirrors ../run_all.sh's shape for local dev,
# trimmed to the two apps this deploy sends to testers, and using
# render.Caddyfile instead of ../Caddyfile (fixed :8080 -> $PORT).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

LOG_DIR="$PWD/.run_logs"
mkdir -p "$LOG_DIR"

PIDS=()

start_app() {
  local name="$1" dir="$2" port="$3"
  ( cd "$dir" && exec uvicorn server:app --port "$port" ) \
    >"$LOG_DIR/$name.log" 2>&1 &
  PIDS+=("$!")
  echo "-> $name on :$port (log: $LOG_DIR/$name.log)"
}

cleanup() {
  echo "shutting down..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

start_app demo-app   demo-app   8423
start_app intake-app intake-app 8420

sleep 1
echo "Starting Caddy on :${PORT:-8080}"
caddy run --config deploy/render.Caddyfile --adapter caddyfile >"$LOG_DIR/caddy.log" 2>&1 &
PIDS+=("$!")

wait
