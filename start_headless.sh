#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p "$HOME/.tiny_ai_screen"
pkill -f "backend/app.py" 2>/dev/null || true
nohup python3 "$DIR/backend/app.py" "$@" > "$HOME/.tiny_ai_screen/backend.log" 2>&1 &
echo "[OK] Tiny AI Screen backend started in background (PID: $!)."
echo "     Logs: ~/.tiny_ai_screen/backend.log"
echo "     API:  http://localhost:5000/data"
