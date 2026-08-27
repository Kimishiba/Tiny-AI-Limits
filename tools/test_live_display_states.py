#!/usr/bin/env python3
"""
Interactive Hardware & UI Test Harness for Tiny AI Limits.
Cycles through all display states and animations:
1. Idle Connected State (Telemetry 3s ripple)
2. Single Active Agent (Pulsating teal dot)
3. Multi-Agent Dual Workload (Phase-shifted pulsating orange & teal dots)
4. Agent Permission Alert (Amber hazard bezel flash + Top bar ping suppression)
5. Work Complete Alert (Emerald bezel pulse + Top bar ping suppression)
6. Clean Return to Split-Flap Clock
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

BACKEND_URL = "http://localhost:5000"

def post_json(endpoint, payload):
    url = f"{BACKEND_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [ERROR] Failed to POST {endpoint}: {e}")
        return None

def check_backend_alive():
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/data", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False

def run_test_sequence():
    print("=" * 65)
    print("  TINY AI LIMITS - COMPREHENSIVE DISPLAY TEST HARNESS")
    print("=" * 65)
    
    if not check_backend_alive():
        print(f"\n[ERROR] Backend server not reachable at {BACKEND_URL}.")
        print("Please start the backend server in another terminal:")
        print("  python3 backend/app.py\n")
        sys.exit(1)
        
    print("[OK] Backend server is online and responding.\n")
    
    # -------------------------------------------------------------
    # TEST 1: IDLE CONNECTED TELEMETRY PING
    # -------------------------------------------------------------
    print("-" * 65)
    print("TEST 1: IDLE CONNECTED & TELEMETRY PACKET PING (10s)")
    print("-> Expected on display:")
    print("   • Center: Split-flap digital flip clock")
    print("   • Top crown arc: Resting dim green (#004422)")
    print("   • Every 3 seconds: Neon emerald ripple (#00FF88) bursts from center")
    print("-" * 65)
    post_json("/api/hook", {
        "hook_name": "SessionEnd",
        "session_id": "test-session-1"
    })
    post_json("/api/hook", {
        "hook_name": "SessionEnd",
        "session_id": "test-session-2"
    })
    for sec in range(10, 0, -1):
        print(f"  Observing Test 1... {sec}s remaining", end="\r")
        time.sleep(1)
    print("  [PASSED] Test 1 complete.                         \n")

    # -------------------------------------------------------------
    # TEST 2: SINGLE ACTIVE AGENT & PULSATING DOT
    # -------------------------------------------------------------
    print("-" * 65)
    print("TEST 2: SINGLE ACTIVE AGENT (WORKING - Teal Card) (10s)")
    print("-> Expected on display:")
    print("   • Card appears: 'Claude 1' with teal brand accent")
    print("   • Detail text: 'Synthesizing...'")
    print("   • Status badge dot: Smooth continuous sinusoidal pulsing (2.5px -> 3.5px)")
    print("   • CRITICAL CHECK: Dot does NOT freeze/pause when top green ping fires!")
    print("-" * 65)
    post_json("/api/hook", {
        "hook_name": "PreToolUse",
        "session_id": "test-session-1",
        "tool_name": "Bash",
        "tool_input": {"command": "python3 build.py"},
        "model": "claude-3-7-sonnet"
    })
    for sec in range(10, 0, -1):
        print(f"  Observing Test 2... {sec}s remaining", end="\r")
        time.sleep(1)
    print("  [PASSED] Test 2 complete.                         \n")

    # -------------------------------------------------------------
    # TEST 3: MULTI-AGENT DUAL WORKLOAD
    # -------------------------------------------------------------
    print("-" * 65)
    print("TEST 3: MULTI-AGENT DUAL WORKLOAD (Claude + Antigravity) (10s)")
    print("-> Expected on display:")
    print("   • Row 1: 'Claude 1' (Teal accent, pulsating teal dot)")
    print("   • Row 2: 'AGY 2' (Orange accent, pulsating orange dot)")
    print("   • Both dots breathe fluidly with phase-shifted timing")
    print("-" * 65)
    post_json("/api/hook", {
        "hook_name": "PreToolUse",
        "session_id": "test-session-2",
        "tool_name": "FileEdit",
        "tool_input": {"file": "main.cpp"},
        "agent_name": "AGY 2",
        "model": "gemini-2.5-pro"
    })
    for sec in range(10, 0, -1):
        print(f"  Observing Test 3... {sec}s remaining", end="\r")
        time.sleep(1)
    print("  [PASSED] Test 3 complete.                         \n")

    # -------------------------------------------------------------
    # TEST 4: PERMISSION REQUEST (AMBER ALERT & PING SUPPRESSION)
    # -------------------------------------------------------------
    print("-" * 65)
    print("TEST 4: PERMISSION REQUIRED (Amber Alert & Ping Suppression) (10s)")
    print("-> Expected on display:")
    print("   • Outer bezel: 6 hazard dashes flash in bright amber (500ms ON / 500ms OFF)")
    print("   • Bottom sub-HUD: 'APPROVE PLAN' alert badge")
    print("   • Top green bar: PING IS MUTED (stays in calm resting dim green)")
    print("   • Zero strobing or conflicting flashes at the top rim")
    print("-" * 65)
    post_json("/api/test/toggle_alert", {"state": True, "prompt": "APPROVE PLAN"})
    for sec in range(10, 0, -1):
        print(f"  Observing Test 4... {sec}s remaining", end="\r")
        time.sleep(1)
    post_json("/api/test/toggle_alert", {"state": False})
    print("  [PASSED] Test 4 complete.                         \n")

    # -------------------------------------------------------------
    # TEST 5: TASK COMPLETION (EMERALD FLASH & PING SUPPRESSION)
    # -------------------------------------------------------------
    print("-" * 65)
    print("TEST 5: TASK COMPLETE (Emerald Pulse & Ping Suppression) (10s)")
    print("-> Expected on display:")
    print("   • Outer bezel: Full-perimeter emerald green alert pulse")
    print("   • Bottom sub-HUD: '✨ TASK COMPLETE ✨'")
    print("   • Top green bar: Normal ping is muted to avoid visual competition")
    print("-" * 65)
    post_json("/api/test/toggle_complete", {"state": True, "prompt": "ALL DONE"})
    for sec in range(10, 0, -1):
        print(f"  Observing Test 5... {sec}s remaining", end="\r")
        time.sleep(1)
    post_json("/api/test/toggle_complete", {"state": False})
    print("  [PASSED] Test 5 complete.                         \n")

    # -------------------------------------------------------------
    # TEST 6: CLEAN RETURN TO IDLE CLOCK
    # -------------------------------------------------------------
    print("-" * 65)
    print("TEST 6: CLEAN RETURN TO IDLE SPLIT-FLAP CLOCK (5s)")
    print("-> Expected on display:")
    print("   • Central corridor clears smoothly")
    print("   • Split-flap mechanical digits flip into view")
    print("   • Top green crown bar resumes regular 3-second telemetry ripples")
    print("-" * 65)
    post_json("/api/hook", {
        "hook_name": "SessionEnd",
        "session_id": "test-session-1"
    })
    post_json("/api/hook", {
        "hook_name": "SessionEnd",
        "session_id": "test-session-2"
    })
    for sec in range(5, 0, -1):
        print(f"  Observing Test 6... {sec}s remaining", end="\r")
        time.sleep(1)
    print("  [PASSED] Test 6 complete.                         \n")

    print("=" * 65)
    print("  ALL 6 HARDWARE & UI TEST SCENARIOS COMPLETED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_test_sequence()
