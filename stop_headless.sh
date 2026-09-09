#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="$HOME/.tiny_ai_screen"
PID_FILE="$DATA_DIR/backend.pid"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[INFO] Stopping Tiny AI Screen backend (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        for _ in {1..15}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 0.2
        done
        if kill -0 "$PID" 2>/dev/null; then
            echo "[WARN] Backend did not stop gracefully; sending SIGKILL..."
            kill -9 "$PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
        echo "[OK] Backend server stopped."
        exit 0
    fi
    rm -f "$PID_FILE"
fi

echo "[INFO] No running backend found."
exit 0
