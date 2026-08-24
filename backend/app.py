import json
import glob
import os
import platform
import socket
import time
import subprocess
import requests
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread
from zeroconf import ServiceInfo, Zeroconf

# Config file setup
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".tiny_ai_screen")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    default_config = {
        "auto_location": True,
        "manual_location_name": "Berlin",
        "lat": 52.5200,
        "lon": 13.4050,
        "antigravity_5h_quota": 200,
        "antigravity_account_email": None,
        "screen_type": "auto"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_config.update(cfg)
        except Exception:
            pass
    return default_config

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

from flask import Flask, jsonify, request, send_file
import webbrowser

config = load_config()
app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route('/')
@app.route('/emulator')
@app.route('/simulator')
@app.route('/round')
def serve_emulator():
    emulator_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emulator", "index.html")
    if os.path.exists(emulator_path):
        return send_file(emulator_path, max_age=0)
    return "Emulator file not found", 404

@app.route('/faces')
@app.route('/qbit')
def serve_qbit_prototype():
    prototype_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emulator", "qbit_faces_prototype.html")
    if os.path.exists(prototype_path):
        return send_file(prototype_path)
    return "QBIT Prototype file not found", 404

@app.route('/setup')
def serve_setup_page():
    setup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emulator", "setup.html")
    if os.path.exists(setup_path):
        return send_file(setup_path)
    return "Setup page not found", 404

@app.route('/setup/vendor/<path:filename>')
def serve_setup_vendor(filename):
    # Self-bundled (via esbuild) so the setup page never depends on a live
    # CDN at runtime -- see emulator/vendor/README.md for how it was built.
    vendor_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emulator", "vendor")
    safe_path = os.path.normpath(os.path.join(vendor_dir, filename))
    if not safe_path.startswith(vendor_dir) or not os.path.exists(safe_path):
        return "Not found", 404
    return send_file(safe_path)

# --- Geocoding Helper ---
def geocode_city(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(city_name)}&count=1&language=en&format=json"
        res = requests.get(url, timeout=5)
        data = res.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            name = result.get("name", city_name)
            country = result.get("country_code", "")
            full_name = f"{name}, {country}".upper() if country else name.upper()
            return result["latitude"], result["longitude"], full_name
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None, None

# --- Weather Data Logic ---
def get_location():
    if not config.get("auto_location", True):
        return config.get("lat", 52.5200), config.get("lon", 13.4050), config.get("manual_location_name", "BERLIN")
    
    try:
        res = requests.get('http://ip-api.com/json/', timeout=5)
        data = res.json()
        city = data.get('city', 'DETECTED').upper()
        return data['lat'], data['lon'], city
    except:
        return 51.5074, -0.1278, "LONDON"

# The ESP32 polls /data every 3s, and get_weather() used to hit ip-api.com +
# open-meteo.com on every single call -- ~28,800 requests/day to each free
# API, which exhausts open-meteo's daily quota well before the day is over
# (seen as a 429 "Daily API request limit exceeded", masquerading as a
# "location not found" style all-zero fallback on the OLED). Weather doesn't
# need second-by-second freshness anyway, so cache it.
_weather_cache = {"data": None, "timestamp": 0}
_WEATHER_CACHE_TTL_SECONDS = 600

def get_weather():
    now = time.time()
    if _weather_cache["data"] is not None and (now - _weather_cache["timestamp"]) < _WEATHER_CACHE_TTL_SECONDS:
        return _weather_cache["data"]

    lat, lon, loc_name = get_location()
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation"
        res = requests.get(url, timeout=5)
        data = res.json()
        if res.status_code != 200:
            raise Exception(f"HTTP {res.status_code}: {data.get('reason', data)}")

        current_temp = data['current_weather']['temperature']

        hours_until_rain = -1
        hourly_precip = data['hourly']['precipitation']
        current_time = data['current_weather']['time']

        try:
            current_index = data['hourly']['time'].index(current_time)
            for i in range(current_index, len(hourly_precip)):
                if hourly_precip[i] > 0:
                    hours_until_rain = i - current_index
                    break
        except ValueError:
            pass

        result = {
            "temperature": current_temp,
            "hours_until_rain": hours_until_rain,
            "date_string": datetime.now().strftime("%a %d %b").upper(),
            "location_name": loc_name
        }
        _weather_cache["data"] = result
        _weather_cache["timestamp"] = now
        return result
    except Exception as e:
        print(f"Weather error: {e}")
        # loc_name was already resolved successfully above (this failure is
        # about the weather API, not location) -- keep it instead of
        # discarding it for a generic "UNKNOWN" that makes it look like
        # location detection failed too.
        result = {
            "temperature": 0.0,
            "hours_until_rain": -1,
            "date_string": "ERR",
            "location_name": loc_name
        }
        # Cache failures too (briefly) so a rate-limited/down API doesn't get
        # hammered again on the very next 3s poll.
        _weather_cache["data"] = result
        _weather_cache["timestamp"] = now
        return result

# --- Claude Data Extraction Logic ---
def get_claude_dirs():
    dirs = []
    user_home = os.path.expanduser("~")
    dirs.append(os.path.join(user_home, ".claude"))
    dirs.append(os.path.join(user_home, ".config", "claude"))
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            dirs.append(os.path.join(appdata, "Claude"))
            dirs.append(os.path.join(appdata, "claude-code"))
    elif system == "Darwin":
        dirs.append(os.path.join(user_home, "Library", "Application Support", "Claude"))
        dirs.append(os.path.join(user_home, "Library", "Application Support", "claude-code"))
    return [d for d in dirs if os.path.exists(d)]

# Our corporate Claude plan has no monthly/weekly quota, so there's no real
# ceiling to show a Xk/limit bar against -- that used to be a fabricated
# 500k constant. Instead this reports actual tokens processed *today*,
# deliberately excluding cache_read_input_tokens: a single long session can
# replay tens of millions of cheap cached-context tokens per turn, which
# swamps the number with something proportional to turn count rather than
# real new work (input + output + freshly-cached context).
def scan_claude_tokens_today():
    total_tokens = 0
    today_local = datetime.now().date()
    for c_dir in get_claude_dirs():
        for filepath in glob.glob(os.path.join(c_dir, "**", "*.jsonl"), recursive=True):
            try:
                if os.path.getmtime(filepath) < (time.time() - 2 * 86400):
                    continue
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except Exception:
                            continue
                        if entry.get("type") != "assistant":
                            continue
                        ts = entry.get("timestamp")
                        if not ts:
                            continue
                        try:
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
                        except Exception:
                            continue
                        if dt.date() != today_local:
                            continue
                        usage = (entry.get("message") or {}).get("usage") or {}
                        total_tokens += usage.get("input_tokens", 0) or 0
                        total_tokens += usage.get("output_tokens", 0) or 0
                        total_tokens += usage.get("cache_creation_input_tokens", 0) or 0
            except Exception:
                pass
    return total_tokens

# Antigravity ships as several separate products -- the standalone GUI app,
# the CLI ("agy"), and the IDE extension -- each running its own process with
# its own session data under a differently-named sibling of ~/.gemini. A
# session in any one of them can be the one waiting on the user, so anything
# that needs to inspect "brain" transcripts has to check all of them, not just
# the GUI app's. (~/.gemini/antigravity-backup is a stale backup directory,
# not a live product, so it's deliberately excluded.)
def _antigravity_brain_dirs():
    home = os.path.expanduser("~")
    candidates = ["antigravity", "antigravity-cli", "antigravity-ide"]
    dirs = [os.path.join(home, ".gemini", name, "brain") for name in candidates]
    return [d for d in dirs if os.path.exists(d)]

# --- Antigravity Data Extraction Logic (fallback heuristic) ---
# Superseded by get_antigravity_quota() below, which reads the real quota
# from Antigravity's own local RPC endpoint when it's running. This heuristic
# (counting PLANNER_RESPONSE turns in the trailing 5h as a proxy for "work
# done") only kicks in if that RPC call fails/isn't available, e.g. Antigravity
# isn't running locally at all. `antigravity_5h_quota` in config.json is a
# guessed ceiling for this fallback path only -- tune it against the real
# app's reading if you ever need to rely on it.
def scan_antigravity_5h_limits(quota_limit=None):
    if quota_limit is None:
        quota_limit = config.get("antigravity_5h_quota", 200)
    total_steps = 0
    now = time.time()

    # Confirmed (2026-08-21): this is a genuine rolling window, not a
    # fixed-duration session like Claude's -- each turn individually ages
    # out exactly 5h after it happened, so "used" is the sum of everything
    # in the trailing 5 real-time hours. A prior attempt modeled this as a
    # fixed cycle anchored to first use (reset sharply every 5h); that was
    # based on a wrong assumption and has been reverted.
    five_hours_ago = now - (5 * 3600)

    for brain_dir in _antigravity_brain_dirs():
        pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
        for filepath in glob.glob(pattern):
            try:
                if os.path.getmtime(filepath) < five_hours_ago:
                    continue
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        data = json.loads(line)
                        if data.get("type") != "PLANNER_RESPONSE":
                            continue
                        created_at = data.get("created_at")
                        if created_at:
                            # Convert ISO string e.g. 2026-08-07T14:50:00Z to epoch time
                            try:
                                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                                if dt.timestamp() >= five_hours_ago:
                                    total_steps += 1
                            except Exception:
                                pass
            except Exception:
                pass

    remaining = max(0, quota_limit - total_steps)
    return {
        "limit": quota_limit,
        "used": total_steps,
        "remaining": remaining,
        "period": "5h"
    }

# --- Real Antigravity Quota (via local Connect RPC) ---
# The heuristic above was a workaround for not having real quota data. It
# turns out Antigravity's own language_server process exposes it locally:
# each running instance (one per signed-in account -- e.g. the desktop app
# and the IDE extension can be signed into different accounts) listens on a
# loopback HTTPS port and serves GetUserStatus over Connect RPC, protected by
# a CSRF token that's just a command-line argument on the same process.
# Credit: https://github.com/tanaikech/antigravity-cli-check-usage-plugin
# and https://github.com/skainguyen1412/antigravity-usage for reverse
# engineering the endpoint, payload shape, and the X-Codeium-Csrf-Token header
# name (Antigravity's backend is Codeium/Windsurf-derived).
import re
import ssl
import urllib.request
import urllib.error

_antigravity_accounts_cache = {"data": [], "timestamp": 0}
_ANTIGRAVITY_ACCOUNTS_CACHE_TTL_SECONDS = 30

def _find_antigravity_language_servers():
    """Find running Antigravity language_server processes, their CSRF token
    (a plain command-line arg), and their loopback listening ports."""
    servers = []

    if sys.platform.startswith("win"):
        try:
            ps_cmd = 'Get-CimInstance Win32_Process | Where-Object Name -like "*language_server*" | Select-Object ProcessId, CommandLine | ConvertTo-Json'
            output = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True)
            if not output.strip():
                return servers
            data = json.loads(output)
            procs = [data] if isinstance(data, dict) else data

            netstat_out = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], text=True, stderr=subprocess.DEVNULL)
            for p in procs:
                cmd = p.get("CommandLine") or ""
                pid = p.get("ProcessId")
                if not pid or not cmd:
                    continue
                token_match = re.search(r"--csrf_token[= ]([a-zA-Z0-9-]+)", cmd)
                if not token_match:
                    continue
                csrf_token = token_match.group(1)

                ports = []
                for line in netstat_out.splitlines():
                    if "LISTENING" in line and str(pid) == line.strip().split()[-1]:
                        m = re.search(r"(?:127\.0\.0\.1|0\.0\.0\.0|\[::\]|\[::1\]):(\d+)", line)
                        if m:
                            ports.append(int(m.group(1)))
                ports = sorted(set(ports))
                if ports:
                    servers.append({"pid": str(pid), "csrf_token": csrf_token, "ports": ports})
        except Exception:
            pass
        return servers

    try:
        ps_output = subprocess.check_output(["ps", "aux"], text=True)
    except Exception:
        return servers

    for line in ps_output.splitlines():
        if "language_server" not in line:
            continue
        parts = line.split(None, 10)
        if len(parts) < 2:
            continue
        pid = parts[1]
        token_match = re.search(r"--csrf_token[= ]([a-zA-Z0-9-]+)", line)
        if not token_match:
            continue
        csrf_token = token_match.group(1)

        try:
            lsof_output = subprocess.check_output(
                ["lsof", "-a", "-p", pid, "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
                text=True, stderr=subprocess.DEVNULL
            )
            ports = sorted(set(
                int(m.group(1))
                for m in re.finditer(r":(\d+)\s*\(LISTEN\)", lsof_output)
            ))
        except Exception:
            ports = []

        if ports:
            servers.append({"pid": pid, "csrf_token": csrf_token, "ports": ports})

    return servers

def _fetch_antigravity_user_status(port, csrf_token, timeout=3):
    url = f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
    headers = {
        "Content-Type": "application/json",
        "Connect-Protocol-Version": "1",
        "User-Agent": "antigravity",
        "X-Codeium-Csrf-Token": csrf_token,
    }
    payload = json.dumps({
        "metadata": {"ideName": "antigravity", "extensionName": "antigravity", "locale": "en"}
    }).encode("utf-8")

    # The language server's HTTPS listener uses a self-signed cert (it's
    # loopback-only, protected by the CSRF token instead of TLS trust).
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_antigravity_accounts(use_cache=True):
    """Returns one entry per signed-in Antigravity account currently running
    locally: {"email", "remaining_fraction", "reset_time"}. remaining_fraction
    is the Gemini model family's quota (what this project's OLED calls
    "Antigravity quota") since that's the family Antigravity itself is built
    around; Claude/GPT quotas inside Antigravity are tracked separately and
    aren't what this metric means here."""
    now = time.time()
    if use_cache and (now - _antigravity_accounts_cache["timestamp"]) < _ANTIGRAVITY_ACCOUNTS_CACHE_TTL_SECONDS:
        return _antigravity_accounts_cache["data"]

    accounts = []
    seen_emails = set()
    for server in _find_antigravity_language_servers():
        for port in server["ports"]:
            try:
                data = _fetch_antigravity_user_status(port, server["csrf_token"])
            except Exception:
                continue
            user_status = (data or {}).get("userStatus")
            if not user_status:
                continue
            email = user_status.get("email", "unknown")
            if email in seen_emails:
                break
            seen_emails.add(email)

            gemini_quota = None
            for m in user_status.get("cascadeModelConfigData", {}).get("clientModelConfigs", []):
                if "gemini" in (m.get("label") or "").lower():
                    gemini_quota = m.get("quotaInfo")
                    break

            accounts.append({
                "email": email,
                "remaining_fraction": (gemini_quota or {}).get("remainingFraction", 1.0),
                "reset_time": (gemini_quota or {}).get("resetTime"),
            })
            break  # this server's account is identified; skip its other port

    _antigravity_accounts_cache["data"] = accounts
    _antigravity_accounts_cache["timestamp"] = now
    return accounts

def get_antigravity_quota():
    """Real quota when Antigravity is running locally (any signed-in
    account); falls back to the local-log heuristic otherwise."""
    accounts = get_antigravity_accounts()
    if not accounts:
        return scan_antigravity_5h_limits()

    selected_email = config.get("antigravity_account_email")
    account = next((a for a in accounts if a["email"] == selected_email), None) or accounts[0]

    remaining_pct = round((account.get("remaining_fraction") or 1.0) * 100)
    remaining_pct = max(0, min(100, remaining_pct))
    return {
        "limit": 100,
        "used": 100 - remaining_pct,
        "remaining": remaining_pct,
        "period": "5h",
        "email": account.get("email"),
        "reset_time": account.get("reset_time"),
    }

# --- Flask Endpoints ---
test_alert_override = False
test_alert_prompt = "APPROVE PLAN"
test_complete_override = False
test_complete_prompt = "WORK COMPLETE"

@app.route('/api/test_alert', methods=['GET', 'POST'])
def handle_test_alert():
    global test_alert_override, test_alert_prompt, test_complete_override, test_complete_prompt
    data = request.json or request.args or {}
    mode = data.get("mode") or data.get("type") or ""
    
    if mode == "complete" or "complete" in data or "completed" in data:
        val = data.get("complete") if "complete" in data else data.get("completed")
        if val is not None:
            test_complete_override = str(val).lower() in ["true", "1", "yes", "active", "on"]
        else:
            test_complete_override = not test_complete_override
        if test_complete_override:
            test_alert_override = False
    else:
        if "active" in data or "enabled" in data:
            val = data.get("active") or data.get("enabled")
            test_alert_override = str(val).lower() in ["true", "1", "yes", "active", "on"]
        else:
            test_alert_override = not test_alert_override
        if test_alert_override:
            test_complete_override = False

    if "prompt" in data and data["prompt"]:
        if test_complete_override:
            test_complete_prompt = str(data["prompt"])
        else:
            test_alert_prompt = str(data["prompt"])

    return jsonify({
        "status": "ok",
        "test_alert_active": test_alert_override,
        "test_complete_active": test_complete_override,
        "prompt_text": test_complete_prompt if test_complete_override else test_alert_prompt
    })

@app.route('/data', methods=['GET'])
def get_data():
    try:
        antigravity_data = get_antigravity_quota()
    except Exception as e:
        print(f"Antigravity scan error: {e}")
        antigravity_data = {"limit": 200, "used": 0, "remaining": 200, "period": "5h"}
    
    try:
        claude_data = {"tokens_today": scan_claude_tokens_today()}
    except Exception as e:
        print(f"Claude token scan error: {e}")
        claude_data = {"tokens_today": 0}
        
    weather_data = get_weather()
    
    waiting_for_input = False
    work_completed = False
    prompt_text = "INPUT REQ"
    completion_text = "WORK COMPLETE"

    if test_alert_override:
        waiting_for_input = True
        prompt_text = test_alert_prompt
    elif test_complete_override:
        work_completed = True
        completion_text = test_complete_prompt
    else:
        try:
            # Multiple Antigravity sessions -- including across different
            # products (GUI app, CLI, IDE extension) -- can run concurrently.
            now_ts = time.time()
            for brain_dir in _antigravity_brain_dirs():
                if waiting_for_input:
                    break
                for root, dirs, files in os.walk(brain_dir):
                    if "transcript.jsonl" not in files:
                        continue
                    fp = os.path.join(root, "transcript.jsonl")
                    mtime = os.path.getmtime(fp)

                    # 30 minutes of slack accounts for realistic human reaction time
                    if now_ts - mtime >= 1800:
                        continue

                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            lines = [l for l in f.readlines() if l.strip()]
                    except Exception:
                        continue
                    if not lines:
                        continue

                    # Find index of last user input to define the current turn
                    last_user_idx = -1
                    for idx in range(len(lines) - 1, -1, -1):
                        try:
                            entry = json.loads(lines[idx])
                            if entry.get("type") == "USER_INPUT" or entry.get("source") == "USER_EXPLICIT":
                                last_user_idx = idx
                                break
                        except Exception:
                            pass

                    # Steps in current turn (after last USER_INPUT)
                    turn_lines = lines[last_user_idx + 1:] if last_user_idx != -1 else lines
                    if not turn_lines:
                        continue

                    # Scan current turn for tools asking for approval / input
                    found_pending = False
                    turn_pending_prompt = "INPUT REQ"

                    for l in turn_lines:
                        try:
                            entry = json.loads(l)
                            for tc in entry.get("tool_calls", []) or []:
                                name = tc.get("name")
                                args = tc.get("args", {}) or {}
                                if name == "ask_question":
                                    found_pending = True
                                    turn_pending_prompt = "ANSWER Q"
                                    break
                                elif name == "ask_permission":
                                    found_pending = True
                                    turn_pending_prompt = "GRANT PERM"
                                    break

                                meta_raw = args.get("ArtifactMetadata") if isinstance(args, dict) else None
                                if isinstance(meta_raw, str):
                                    try: meta = json.loads(meta_raw)
                                    except Exception: meta = {}
                                elif isinstance(meta_raw, dict):
                                    meta = meta_raw
                                else:
                                    meta = {}

                                target_file = str(args.get("TargetFile", "")).lower() if isinstance(args, dict) else ""
                                if meta.get("RequestFeedback") is True or "implementation_plan" in target_file:
                                    if meta.get("RequestFeedback") is not False:
                                        found_pending = True
                                        turn_pending_prompt = "APPROVE PLAN"
                                        break
                            if found_pending:
                                break
                        except Exception:
                            pass

                    # Also check if implementation_plan.md in conversation dir was modified in current turn
                    conv_dir = os.path.dirname(os.path.dirname(fp))
                    plan_path = os.path.join(conv_dir, "implementation_plan.md")
                    if not found_pending and os.path.exists(plan_path):
                        plan_mtime = os.path.getmtime(plan_path)
                        # If plan was created/updated within last 30m and after or around the last turn began
                        if (now_ts - plan_mtime < 1800) and (last_user_idx == -1 or plan_mtime >= mtime - 180):
                            found_pending = True
                            turn_pending_prompt = "APPROVE PLAN"

                    if found_pending:
                        waiting_for_input = True
                        prompt_text = turn_pending_prompt
                        break
                    elif (now_ts - mtime) < 30:
                        # Turn finished recently without requiring feedback -> Work Completed!
                        work_completed = True
                        completion_text = "WORK COMPLETE"
        except Exception as e:
            print(f"Agent check error: {e}")

    now = datetime.now()
    agent_state = "waiting_approval" if waiting_for_input else ("completed" if work_completed else "idle")

    return jsonify({
        "claude": claude_data,
        "antigravity": antigravity_data,
        "weather": weather_data,
        "time": {
            "hours": now.hour,
            "minutes": now.minute,
            "seconds": now.second,
            "time_string": now.strftime("%H:%M:%S")
        },
        "agent": {
            "waiting_for_input": waiting_for_input,
            "work_completed": work_completed,
            "completion_flash": work_completed,
            "state": agent_state,
            "prompt_text": prompt_text,
            "completion_text": completion_text
        },
        "device": {
            "screen_type": config.get("screen_type", "auto")
        }
    })

@app.route('/api/screen', methods=['GET', 'POST'])
def handle_screen_api():
    global config
    if request.method == 'POST':
        data = request.json or request.form or {}
        mode = data.get("mode") or data.get("screen_type") or request.args.get("mode") or "auto"
        mode = str(mode).lower()
        if mode in ["auto", "round", "gc9a01", "oled", "128x64"]:
            config["screen_type"] = "round" if mode in ["round", "gc9a01"] else ("oled" if mode in ["oled", "128x64"] else "auto")
            save_config(config)
            return jsonify({"status": "ok", "screen_type": config["screen_type"]})
        return jsonify({"status": "error", "message": f"Invalid screen mode '{mode}'"}), 400
    return jsonify({
        "screen_type": config.get("screen_type", "auto"),
        "options": ["auto", "round", "oled"]
    })

@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    global config
    if request.method == 'POST':
        data = request.json or {}
        if "auto_location" in data:
            config["auto_location"] = bool(data["auto_location"])
        if "screen_type" in data:
            val = str(data["screen_type"]).lower()
            if val in ["auto", "round", "gc9a01", "oled", "128x64"]:
                config["screen_type"] = "round" if val in ["round", "gc9a01"] else ("oled" if val in ["oled", "128x64"] else "auto")
        if "antigravity_5h_quota" in data:
            try:
                config["antigravity_5h_quota"] = int(data["antigravity_5h_quota"])
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "antigravity_5h_quota must be an integer"}), 400
        if "antigravity_account_email" in data:
            # Empty string/null means "auto, use whichever account is found first"
            config["antigravity_account_email"] = data["antigravity_account_email"] or None
        if "city" in data and data["city"]:
            lat, lon, full_name = geocode_city(data["city"])
            if lat and lon:
                config["lat"] = lat
                config["lon"] = lon
                config["manual_location_name"] = full_name
            else:
                return jsonify({"status": "error", "message": f"Could not find city '{data['city']}'"}), 400
        save_config(config)
        return jsonify({"status": "ok", "config": config})
    response = dict(config)
    response["available_antigravity_accounts"] = [a["email"] for a in get_antigravity_accounts()]
    return jsonify(response)

# --- mDNS Service Advertisement (so the ESP32 can find us on any network,
#     for any user, with zero hardcoded hostname/IP configuration) ---
_zeroconf_instance = None

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))  # doesn't actually send anything
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

def find_available_port(preferred_port=5000):
    for p in [preferred_port, 5001, 5050, 8080]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', p))
                return p
        except OSError:
            continue
    return preferred_port

PORT = find_available_port(5000)

def register_mdns_service(port=PORT):
    global _zeroconf_instance
    try:
        local_ip = get_local_ip()
        info = ServiceInfo(
            "_tinyscreen._tcp.local.",
            "Tiny AI Screen Companion._tinyscreen._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
        )
        _zeroconf_instance = Zeroconf()
        _zeroconf_instance.register_service(info)
        print(f"[mDNS] Advertising _tinyscreen._tcp.local at {local_ip}:{port}")
    except Exception as e:
        print(f"[mDNS] Failed to register service: {e}")

def start_flask():
    register_mdns_service(port=PORT)
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def create_gui_window():
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("Tiny AI Screen Companion")
    root.geometry("420x540")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    title_label = tk.Label(root, text="TINY AI SCREEN COMPANION", font=("Helvetica", 14, "bold"), fg="#f9e2af", bg="#1e1e2e")
    title_label.pack(pady=(15, 5))

    subtitle_label = tk.Label(root, text="ESP32 Backend & Configuration Utility", font=("Helvetica", 9), fg="#a6adc8", bg="#1e1e2e")
    subtitle_label.pack(pady=(0, 15))

    # --- Location Section ---
    loc_frame = tk.LabelFrame(root, text=" Location Settings ", font=("Helvetica", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e", bd=1, relief="solid")
    loc_frame.pack(fill="x", padx=20, pady=5)

    auto_loc_var = tk.BooleanVar(value=config.get("auto_location", True))

    def toggle_auto_loc():
        city_entry.config(state="disabled" if auto_loc_var.get() else "normal")

    auto_check = tk.Checkbutton(loc_frame, text="Auto-detect location via IP", variable=auto_loc_var, command=toggle_auto_loc, fg="#cdd6f4", bg="#1e1e2e", selectcolor="#313244", activebackground="#1e1e2e", activeforeground="#cdd6f4")
    auto_check.pack(anchor="w", padx=10, pady=5)

    city_frame = tk.Frame(loc_frame, bg="#1e1e2e")
    city_frame.pack(fill="x", padx=10, pady=5)
    
    tk.Label(city_frame, text="Manual City:", fg="#cdd6f4", bg="#1e1e2e").pack(side="left")
    city_entry = tk.Entry(city_frame, bg="#313244", fg="#cdd6f4", insertbackground="white", bd=1, relief="flat")
    city_entry.insert(0, config.get("manual_location_name", "Berlin"))
    city_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
    if auto_loc_var.get():
        city_entry.config(state="disabled")

    def save_location():
        city = city_entry.get().strip()
        is_auto = auto_loc_var.get()
        if not is_auto and city:
            lat, lon, full_name = geocode_city(city)
            if lat and lon:
                config["auto_location"] = False
                config["lat"] = lat
                config["lon"] = lon
                config["manual_location_name"] = full_name
                save_config(config)
                messagebox.showinfo("Success", f"Location set to {full_name}")
            else:
                messagebox.showerror("Error", f"Could not find city: '{city}'")
        else:
            config["auto_location"] = True
            save_config(config)
            messagebox.showinfo("Success", "Location set to Auto-detect (IP)")

    save_btn = tk.Button(loc_frame, text="Save Location", command=save_location, bg="#89b4fa", fg="#11111b", activebackground="#b4befe", font=("Helvetica", 9, "bold"), bd=0, padx=10, pady=4)
    save_btn.pack(anchor="e", padx=10, pady=5)

    # --- OTA & Updates Section ---
    ota_frame = tk.LabelFrame(root, text=" Firmware & Updates ", font=("Helvetica", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e", bd=1, relief="solid")
    ota_frame.pack(fill="x", padx=20, pady=10)

    def check_firmware_updates():
        try:
            res = requests.get("https://api.github.com/repos/YOUR_GITHUB_USERNAME/Desktop-Tiny-Screen/releases/latest", timeout=5)
            if res.status_code == 200:
                data = res.json()
                tag = data.get("tag_name", "Unknown")
                messagebox.showinfo("GitHub Firmware Update", f"Latest Release Tag on GitHub: {tag}\n\nYour ESP32 will auto-update on next boot if a new tag is available!")
            else:
                messagebox.showwarning("Update Check", "No GitHub release tags found or repository is private.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check GitHub updates: {e}")

    ota_btn = tk.Button(ota_frame, text="Check for ESP32 Firmware Updates", command=check_firmware_updates, bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5", font=("Helvetica", 9, "bold"), bd=0, padx=10, pady=6)
    ota_btn.pack(fill="x", padx=10, pady=8)

    # --- Emulator Section ---
    emu_frame = tk.LabelFrame(root, text=" Screen Emulator ", font=("Helvetica", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e", bd=1, relief="solid")
    emu_frame.pack(fill="x", padx=20, pady=5)

    def open_emulator():
        webbrowser.open(f"http://localhost:{PORT}/emulator")

    emu_btn = tk.Button(emu_frame, text="🖥️ Launch Display Emulator", command=open_emulator, bg="#f9e2af", fg="#11111b", activebackground="#f5e0dc", font=("Helvetica", 9, "bold"), bd=0, padx=10, pady=6)
    emu_btn.pack(fill="x", padx=10, pady=8)

    # --- Device Setup Section ---
    setup_frame = tk.LabelFrame(root, text=" New Device Setup ", font=("Helvetica", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e", bd=1, relief="solid")
    setup_frame.pack(fill="x", padx=20, pady=5)

    def open_setup():
        webbrowser.open(f"http://localhost:{PORT}/setup")

    setup_btn = tk.Button(setup_frame, text="🔌 Set Up New Device (WiFi)", command=open_setup, bg="#89b4fa", fg="#11111b", activebackground="#b4befe", font=("Helvetica", 9, "bold"), bd=0, padx=10, pady=6)
    setup_btn.pack(fill="x", padx=10, pady=8)

    # --- Antigravity Account Section ---
    # If you're signed into more than one Antigravity account at once (e.g.
    # the desktop app and the IDE extension on different accounts), pick
    # which one's quota the screen should display.
    ag_frame = tk.LabelFrame(root, text=" Antigravity Account ", font=("Helvetica", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e", bd=1, relief="solid")
    ag_frame.pack(fill="x", padx=20, pady=5)

    AUTO_LABEL = "Auto (first account found)"
    detected_accounts = [a["email"] for a in get_antigravity_accounts()]
    menu_options = [AUTO_LABEL] + detected_accounts
    current_email = config.get("antigravity_account_email")
    current_value = current_email if current_email in detected_accounts else AUTO_LABEL

    ag_var = tk.StringVar(value=current_value)

    def on_account_selected(selected):
        config["antigravity_account_email"] = None if selected == AUTO_LABEL else selected
        save_config(config)

    ag_menu = tk.OptionMenu(ag_frame, ag_var, *menu_options, command=on_account_selected)
    ag_menu.config(bg="#313244", fg="#cdd6f4", activebackground="#45475a", highlightthickness=0, bd=0)
    ag_menu["menu"].config(bg="#313244", fg="#cdd6f4")
    ag_menu.pack(fill="x", padx=10, pady=8)

    if not detected_accounts:
        ag_hint = tk.Label(ag_frame, text="No running Antigravity account detected right now.", font=("Helvetica", 8, "italic"), fg="#a6adc8", bg="#1e1e2e")
        ag_hint.pack(anchor="w", padx=10, pady=(0, 6))

    # Status Footer
    status_lbl = tk.Label(root, text=f"Server running at http://0.0.0.0:{PORT} | Emulator at /emulator", font=("Helvetica", 8, "italic"), fg="#a6adc8", bg="#1e1e2e")
    status_lbl.pack(side="bottom", pady=5)

    return root

class TinyScreenMacStatusBarApp(object):
    def run(self):
        try:
            import rumps
        except ImportError:
            # Fallback if rumps not installed
            root = create_gui_window()
            root.mainloop()
            return

        class StatusBarApp(rumps.App):
            def __init__(self):
                super(StatusBarApp, self).__init__("🖥️", quit_button=None)

            @rumps.clicked("🖥️ Open Display Emulator")
            def open_emulator(self, _):
                webbrowser.open(f"http://localhost:{PORT}/emulator")

            @rumps.clicked("🔌 Set Up New Device (WiFi)")
            def open_setup(self, _):
                webbrowser.open(f"http://localhost:{PORT}/setup")

            @rumps.clicked("🔀 Switch Antigravity Account...")
            def switch_antigravity_account(self, _):
                accounts = [a["email"] for a in get_antigravity_accounts()]
                current = config.get("antigravity_account_email") or "AUTO"
                hint = ", ".join(accounts) if accounts else "(none detected running right now)"
                response = rumps.Window(
                    message=f"Detected accounts: {hint}\n\nType an email to pin that account, or 'AUTO' to use whichever is found first:",
                    title="Antigravity Account",
                    default_text=current,
                    ok="Save",
                    cancel="Cancel"
                ).run()

                if response.clicked:
                    value = response.text.strip()
                    config["antigravity_account_email"] = None if (not value or value.upper() == "AUTO") else value
                    save_config(config)
                    rumps.alert("Saved", f"Antigravity account set to: {config['antigravity_account_email'] or 'Auto'}")

            @rumps.clicked("⚙️ Set Location...")
            def set_location(self, _):
                current_loc = config.get("manual_location_name", "Berlin")
                response = rumps.Window(
                    message="Enter city name (e.g. 'Rome', 'New York') or type 'AUTO' for IP detection:",
                    title="Location Settings",
                    default_text=current_loc,
                    ok="Save",
                    cancel="Cancel"
                ).run()

                if response.clicked:
                    city = response.text.strip()
                    if not city or city.upper() == "AUTO":
                        config["auto_location"] = True
                        save_config(config)
                        rumps.alert("Location Saved", "Location set to Auto-detect via IP.")
                    else:
                        lat, lon, full_name = geocode_city(city)
                        if lat and lon:
                            config["auto_location"] = False
                            config["lat"] = lat
                            config["lon"] = lon
                            config["manual_location_name"] = full_name
                            save_config(config)
                            rumps.alert("Location Saved", f"Successfully set location to {full_name} ({lat:.2f}, {lon:.2f})")
                        else:
                            rumps.alert("Location Error", f"Could not find coordinates for city: '{city}'")

            @rumps.clicked("🔄 Check Firmware Updates")
            def check_updates(self, _):
                try:
                    res = requests.get("https://api.github.com/repos/YOUR_GITHUB_USERNAME/Desktop-Tiny-Screen/releases/latest", timeout=5)
                    if res.status_code == 200:
                        tag = res.json().get("tag_name", "Unknown")
                        rumps.alert("Firmware Updates", f"Latest Release Tag on GitHub: {tag}\n\nYour ESP32 will auto-update on next boot if a new tag is available!")
                    else:
                        rumps.alert("Firmware Updates", "No GitHub releases found or repository is private.")
                except Exception as e:
                    rumps.alert("Update Check Failed", f"Error: {e}")

            @rumps.clicked("🌐 View Live API (/data)")
            def open_api(self, _):
                webbrowser.open(f"http://localhost:{PORT}/data")

            @rumps.clicked("Quit")
            def quit_app(self, _):
                rumps.quit_application()

        app = StatusBarApp()
        app.run()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "--server-only":
        print(f"[INFO] Running in server-only mode at http://localhost:{PORT}")
        start_flask()
    else:
        # Start Flask server in background thread
        t = Thread(target=start_flask, daemon=True)
        t.start()
        # Launch macOS Status Bar App or Windows GUI
        statusBarApp = TinyScreenMacStatusBarApp()
        statusBarApp.run()
