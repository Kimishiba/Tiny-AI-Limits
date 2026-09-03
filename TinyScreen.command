#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH="/Users/alessandro.longoni/Library/Python/3.9/lib/python/site-packages:$PYTHONPATH"
PYTHON_BIN="$HOME/.tiny_ai_screen/venv/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi
exec "$PYTHON_BIN" backend/app.py
