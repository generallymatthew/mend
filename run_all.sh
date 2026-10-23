#!/usr/bin/env bash
# Runs the whole product locally behind one entry point:
# http://localhost:8080/ -- Spool at the root, Thimble/Suture/
# post-session/Seam under /intake/, /joint/, /post/, /manager/ (see Caddyfile).
#
# Starts all four apps' own uvicorn (each in its own .venv, unmodified) in
# the background, then Caddy in the foreground. Ctrl-C stops Caddy and
# everything else together -- no orphaned processes left holding ports.
#
# Each app still needs its own .env (see that app's README) and dependencies
# installed in its own .venv first; this script doesn't set either up.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

LOG_DIR="$PWD/.run_logs"
mkdir -p "$LOG_DIR"

PIDS=()

start_app() {
  local name="$1" dir="$2" port="$3"
  if [ ! -x "$dir/.venv/bin/uvicorn" ]; then
    echo "!! $dir/.venv/bin/uvicorn not found -- see $dir/README.md for setup" >&2
    exit 1
  fi
  ( cd "$dir" && exec .venv/bin/uvicorn server:app --port "$port" ) \
    >"$LOG_DIR/$name.log" 2>&1 &
  PIDS+=("$!")
  echo "-> $name on :$port (log: $LOG_DIR/$name.log)"
}

cleanup() {
  echo
  echo "shutting down..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  # Give them a moment, then confirm the ports are actually free.
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

start_app spool            apps/spool             8423
start_app thimble         apps/thimble           8420
start_app suture          apps/suture            8421
start_app post-session    apps/post-session-app  8422
start_app seam            apps/seam              8460

# joint-session-audio needs livekit-server (`brew install livekit`) and its
# own agent.py worker in addition to its uvicorn app -- see that app's
# README.md. Opt-in only: skip it if that setup hasn't been done yet, same
# spirit as start_app's own missing-venv check.
if [ -x apps/joint-session-audio/.venv/bin/uvicorn ] && command -v livekit-server >/dev/null 2>&1; then
  ( cd apps/joint-session-audio && exec livekit-server --dev ) \
    >"$LOG_DIR/joint-session-audio-livekit.log" 2>&1 &
  PIDS+=("$!")
  echo "-> joint-session-audio livekit-server --dev (log: $LOG_DIR/joint-session-audio-livekit.log)"

  ( cd apps/joint-session-audio && exec .venv/bin/python agent.py dev ) \
    >"$LOG_DIR/joint-session-audio-agent.log" 2>&1 &
  PIDS+=("$!")
  echo "-> joint-session-audio agent.py (log: $LOG_DIR/joint-session-audio-agent.log)"

  start_app joint-session-audio apps/joint-session-audio 8424
else
  echo "-- skipping joint-session-audio (needs .venv + 'brew install livekit' -- see its README.md)"
fi

sleep 1
echo
echo "All four apps starting -- logs in $LOG_DIR/"
echo "Opening the proxy on http://localhost:8080/ (Ctrl-C to stop everything)"
echo

# Backgrounded (not the script's last foreground command) and tracked in
# PIDS like the uvicorn processes above -- a bare foreground `caddy run`
# here doesn't reliably receive SIGINT forwarded from this script when
# launched non-interactively, which left it (and everything else) running
# after Ctrl-C in testing. macOS ships bash 3.2 (no `wait -n`), so this
# blocks on all of them together; the trap above is what actually does the
# killing once a signal arrives.
caddy run --config Caddyfile --adapter caddyfile >"$LOG_DIR/caddy.log" 2>&1 &
PIDS+=("$!")

wait
