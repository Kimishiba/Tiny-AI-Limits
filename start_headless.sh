#!/usr/bin/env bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR="$HOME/.tiny_ai_screen"
PID_FILE="$DATA_DIR/backend.pid"
LOG_FILE="$DATA_DIR/backend.log"

mkdir -p "$DATA_DIR"

# Stop existing instance if alive via PID file
if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[INFO] Stopping existing backend (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        for _ in {1..10}; do
            if ! kill -0 "$OLD_PID" 2>/dev/null; then
                break
            fi
            sleep 0.2
        done
        kill -9 "$OLD_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
fi

# Detect Python interpreter (prefer dedicated venv)
PYTHON_BIN="python3"
if [ -x "$DATA_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$DATA_DIR/venv/bin/python3"
elif [ -x "$DIR/.venv/bin/python3" ]; then
    PYTHON_BIN="$DIR/.venv/bin/python3"
fi

nohup "$PYTHON_BIN" "$DIR/backend/app.py" "$@" > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

echo "[OK] Tiny AI Screen backend started in background (PID: $NEW_PID)."
echo "     Python: $PYTHON_BIN"
echo "     Logs:   $LOG_FILE"
echo "     API:    http://localhost:5000/data"
