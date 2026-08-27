#!/usr/bin/env bash
pkill -f "backend/app.py" 2>/dev/null && echo "[OK] Backend server stopped." || echo "[INFO] No running backend found."
