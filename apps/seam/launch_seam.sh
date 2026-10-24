#!/bin/bash
PORT=8460
SEAM_DIR="/Users/matt/Documents/Mend/apps/seam"
LOG="/Users/matt/Documents/Mend/.run_logs/seam.log"
APP="/Users/matt/Applications/Chrome Apps.localized/Seam.app"

if ! lsof -i ":$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    mkdir -p "$(dirname "$LOG")"
    ( cd "$SEAM_DIR" && set -a && source .env && set +a && nohup .venv/bin/uvicorn server:app --port "$PORT" > "$LOG" 2>&1 & )
    for i in $(seq 1 30); do
        curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break
        sleep 0.5
    done
fi

open -a "$APP"
