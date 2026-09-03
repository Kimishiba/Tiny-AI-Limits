#!/bin/bash
cd "$(dirname "$0")"
CANDIDATES=(
    "$VIRTUAL_ENV/bin/python3"
    "$(pwd)/.venv/bin/python3"
    "$HOME/.tiny_ai_screen/venv/bin/python3"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "$(command -v python3 2>/dev/null || true)"
    "/usr/bin/python3"
)

PYTHON_BIN=""
for CANDIDATE in "${CANDIDATES[@]}"; do
    if [ -n "$CANDIDATE" ] && [ -x "$CANDIDATE" ]; then
        USER_SITE="$("$CANDIDATE" -m site --user-site 2>/dev/null || true)"
        if [ -n "$USER_SITE" ] && [ -d "$USER_SITE" ]; then
            export PYTHONPATH="$USER_SITE:$PYTHONPATH"
        fi
        if "$CANDIDATE" -c "import flask, requests, rumps, zeroconf" >/dev/null 2>&1; then
            PYTHON_BIN="$CANDIDATE"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" backend/app.py "$@"
