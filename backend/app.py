import json
import re
import glob
import getpass
import os
import platform
import socket
import time
import subprocess
import requests
import sys
import uuid
import threading
from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread
from zeroconf import ServiceInfo, Zeroconf

# Providers and background poller
try:
    from providers import poller, ALL_PROVIDERS
except ImportError:
    from .providers import poller, ALL_PROVIDERS

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
        "selected_gauges": {
            "left": "claude",
            "right": "antigravity"
        },
        "provider_keys": {}
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
    global config
    try:
        config = cfg
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            pass
    except Exception as e:
        print(f"Error saving config: {e}")

COMPANION_VERSION = "0.5.0"
FIRMWARE_CACHE_DIR = os.path.join(CONFIG_DIR, "firmware_cache")
os.makedirs(FIRMWARE_CACHE_DIR, exist_ok=True)
_ota_trigger_lock = threading.Lock()
_ota_trigger_requested = False
_firmware_cache = {"version": "0.5", "tag": "firmware-v0.5", "path": None, "size": 0, "checked_at": 0}

def get_latest_firmware(force_check=False):
    global _firmware_cache
    now = time.time()
    if not force_check and _firmware_cache.get("path") and os.path.exists(_firmware_cache["path"]) and (now - _firmware_cache.get("checked_at", 0) < 600):
        return _firmware_cache

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    local_bin = os.path.join(repo_root, ".pio", "build", "esp32c3", "firmware.bin")

    try:
        res = requests.get("https://api.github.com/repos/Kimishiba/Tiny-AI-Limits/releases", timeout=5)
        if res.status_code == 200:
            releases = res.json()
            for r in releases:
                tag = r.get("tag_name", "")
                if tag.startswith("firmware-v") or tag.startswith("v"):
                    ver_clean = tag.replace("firmware-v", "").replace("v", "")
                    for asset in r.get("assets", []):
                        if asset.get("name") == "firmware.bin":
                            download_url = asset.get("browser_download_url")
                            dest_path = os.path.join(FIRMWARE_CACHE_DIR, f"firmware_{tag}.bin")
                            if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
                                d_res = requests.get(download_url, timeout=30)
                                if d_res.status_code == 200:
                                    with open(dest_path, "wb") as f:
                                        f.write(d_res.content)
                            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                                _firmware_cache = {
                                    "version": ver_clean,
                                    "tag": tag,
                                    "path": dest_path,
                                    "size": os.path.getsize(dest_path),
                                    "checked_at": now
                                }
                                return _firmware_cache
    except Exception as e:
        print(f"GitHub release check warning: {e}")

    if os.path.exists(local_bin) and os.path.getsize(local_bin) > 0:
        _firmware_cache = {
            "version": "0.5",
            "tag": "firmware-v0.5",
            "path": local_bin,
            "size": os.path.getsize(local_bin),
            "checked_at": now
        }
        return _firmware_cache

    return _firmware_cache

def get_pair_id(cfg):
    """Stable per-install identifier used to pair a board to *this* companion.

    Deliberately not the OS username or hostname: two machines on the same LAN
    can easily share either one (both "admin", both "MacBook-Pro"), which would
    let a board re-pair with the wrong computer after a DHCP lease change.
    Generated once and persisted, so it survives restarts and IP changes.
    """
    pair_id = cfg.get("pair_id")
    if not pair_id:
        pair_id = uuid.uuid4().hex[:12]
        cfg["pair_id"] = pair_id
        save_config(cfg)
    return pair_id

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

@app.route('/setup')
def serve_setup_page():
    setup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emulator", "setup.html")
    if os.path.exists(setup_path):
        return send_file(setup_path, max_age=0)
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
# "location not found" style all-zero fallback on the display). Weather doesn't
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
            "temp": current_temp,
            "hours_until_rain": hours_until_rain,
            "date_string": datetime.now().strftime("%a %d %b").upper(),
            "location_name": loc_name,
            "location": loc_name
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
            "temp": 0.0,
            "hours_until_rain": -1,
            "date_string": "ERR",
            "location_name": loc_name,
            "location": loc_name
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
def scan_claude_usage(now_ts=None):
    """Scan Claude transcript logs for 24h tokens, USD cost, and 5h rolling reset window."""
    from providers.claude import ClaudeProvider
    detailed = ClaudeProvider().scan_usage_detailed()
    plan_mode = config.get("claude_plan", "enterprise")
    daily_budget = float(config.get("claude_daily_budget_usd", 10.0))

    cost_today = detailed["cost_today_usd"]
    cost_str = detailed["cost_str"]
    tokens_str = detailed["tokens_str"]

    if plan_mode == "enterprise":
        pct_used = min(100.0, (cost_today / max(0.01, daily_budget)) * 100.0)
        pct_left = max(0.0, 100.0 - pct_used)
        return {
            "plan": "enterprise",
            "tokens_today": detailed["tokens_today"],
            "tokens_24h": detailed["tokens_24h"],
            "cost_today_usd": cost_today,
            "cost_24h_usd": detailed["cost_24h_usd"],
            "cost_str": cost_str,
            "tokens_str": tokens_str,
            "limit": round(daily_budget),
            "remaining": round(pct_left),
            "percent": round(pct_used),
            "reset_time": detailed.get("resets_at"),
            "reset_in_seconds": 0,
            "reset_str": f"{tokens_str} TOK",
            "curved_text": f"{cost_str} SPENT"
        }

    # Standard quota mode
    reset_time = detailed.get("resets_at")
    reset_in_seconds, reset_str = (0, "READY")
    if reset_time:
        reset_in_seconds, reset_str = format_reset_time(reset_time, now_ts)

    return {
        "plan": "standard",
        "tokens_today": detailed["tokens_today"],
        "tokens_24h": detailed["tokens_24h"],
        "cost_today_usd": cost_today,
        "cost_24h_usd": detailed["cost_24h_usd"],
        "cost_str": cost_str,
        "tokens_str": tokens_str,
        "limit": 100,
        "remaining": 100,
        "percent": 100,
        "reset_time": reset_time,
        "reset_in_seconds": reset_in_seconds,
        "reset_str": reset_str,
        "curved_text": "CLD 100%"
    }

def scan_claude_tokens_today():
    return scan_claude_usage()["tokens_today"]

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
    earliest_step_ts = None

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
                                step_ts = dt.timestamp()
                                if step_ts >= five_hours_ago:
                                    total_steps += 1
                                    if earliest_step_ts is None or step_ts < earliest_step_ts:
                                        earliest_step_ts = step_ts
                            except Exception:
                                pass
            except Exception:
                pass

    remaining = max(0, quota_limit - total_steps)
    if earliest_step_ts is not None:
        reset_ts = earliest_step_ts + (5 * 3600)
        from datetime import timezone
        reset_time = datetime.fromtimestamp(reset_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        reset_in_seconds, reset_str = format_reset_time(reset_time, now)
    else:
        reset_time = None
        reset_in_seconds = 0
        reset_str = "READY"

    return {
        "limit": quota_limit,
        "used": total_steps,
        "remaining": remaining,
        "period": "5h",
        "reset_time": reset_time,
        "reset_in_seconds": reset_in_seconds,
        "reset_str": reset_str
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
    is the Gemini model family's quota (what this project's display calls
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

def format_reset_time(reset_time_str, now_ts=None):
    """Compute countdown seconds and human-readable string (e.g. '3h 12m', '45m') from ISO timestamp."""
    if not reset_time_str:
        return None, ""
    if now_ts is None:
        now_ts = time.time()
    try:
        dt = datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))
        reset_ts = dt.timestamp()
        secs_left = max(0, int(round(reset_ts - now_ts)))
        hours = secs_left // 3600
        mins = (secs_left % 3600) // 60
        if hours > 0:
            reset_str = f"{hours}h {mins:02d}m"
        elif mins > 0:
            reset_str = f"{mins}m"
        elif secs_left > 0:
            reset_str = f"{secs_left}s"
        else:
            reset_str = "READY"
        return secs_left, reset_str
    except Exception:
        return None, ""

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
    reset_time = account.get("reset_time")
    reset_in_seconds, reset_str = format_reset_time(reset_time)
    return {
        "limit": 100,
        "used": 100 - remaining_pct,
        "remaining": remaining_pct,
        "period": "5h",
        "email": account.get("email"),
        "reset_time": reset_time,
        "reset_in_seconds": reset_in_seconds,
        "reset_str": reset_str,
    }

# --- Flask Endpoints ---
test_alert_override = False
test_alert_prompt = "APPROVE PLAN"
test_complete_override = False
test_complete_prompt = "WORK COMPLETE"
test_idle_override = False
test_agents_override = None

@app.route('/api/test_agents', methods=['GET', 'POST'])
def handle_test_agents():
    global test_agents_override, test_idle_override, test_alert_override, test_complete_override
    data = request.json or request.args or {}
    if "clear" in data or data.get("active") is False or data.get("agents") is None:
        test_agents_override = None
    elif "agents" in data:
        test_agents_override = data["agents"]
        test_idle_override = False
        test_alert_override = False
        test_complete_override = False
    return jsonify({"status": "ok", "test_agents_override": test_agents_override})

@app.route('/api/test_idle', methods=['GET', 'POST'])
def handle_test_idle():
    global test_idle_override, test_alert_override, test_complete_override, test_agents_override
    data = request.json or request.args or {}
    val = data.get("idle") if "idle" in data else data.get("active")
    if val is not None:
        test_idle_override = str(val).lower() in ["true", "1", "yes", "active", "on"]
    else:
        test_idle_override = not test_idle_override
    if test_idle_override:
        test_alert_override = False
        test_complete_override = False
        test_agents_override = None
    return jsonify({"status": "ok", "test_idle_active": test_idle_override})

@app.route('/api/test_alert', methods=['GET', 'POST'])
@app.route('/api/test_complete', methods=['GET', 'POST'])
def handle_test_alert():
    global test_alert_override, test_alert_prompt, test_complete_override, test_complete_prompt, test_idle_override, test_agents_override
    test_idle_override = False
    test_agents_override = None
    data = request.json or request.args or {}
    mode = data.get("mode") or data.get("type") or ""
    if request.path == '/api/test_complete':
        mode = "complete"
    
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

@app.route('/api/hook', methods=['POST'])
def api_hook():
    """Hook ingestion endpoint for Claude Code and compatible agent lifecycle events."""
    payload = request.get_json(force=True, silent=True) or {}
    result = handle_hook_event(payload)
    if result is None:
        return jsonify({"status": "error", "message": "missing session_id"}), 400
    return jsonify(result), 200

def client_is_local():
    """Requests from this machine: the emulator, the setup page, local curl.

    These fetch /data same-origin and have no pair_id to send, so they are
    exempt from the pairing check.
    """
    return request.remote_addr in ("127.0.0.1", "::1")


def caller_is_paired():
    """Whether the caller proved it belongs to this companion.

    /data carries a personal email address, working hours, token volume and
    location. Without this check any board on the LAN that finds us over mDNS
    reads all of it -- which is exactly what was happening in the wild (#38):
    a colleague's board on older firmware had been polling every 3 seconds.
    """
    if client_is_local():
        return True
    if config.get("allow_unpaired_clients", False):
        return True
    return request.args.get("pair_id", "") == get_pair_id(config)


# Persistent/In-memory Registry for stable agent naming
_session_registry = {}
_session_counters = {"claude": 0, "antigravity": 0}

IN_FLIGHT_TIMEOUT_SECONDS = 45

def _format_context_phrase(words, max_len=12):
    """Combine 1-2 meaningful context words into a clear, descriptive label <= max_len."""
    if not words:
        return ""

    acronyms = {"3D", "CAD", "UI", "UX", "QA", "API", "RPC", "OTA", "LCD", "ESP", "PCB", "CLI", "AGY", "CLD", "AI"}
    cleaned_words = []
    for w in words:
        clean = re.sub(r"[^A-Za-z0-9]", "", w)
        if not clean:
            continue
        if clean.upper() in acronyms or (len(clean) <= 3 and clean.isupper()):
            cleaned_words.append(clean.upper())
        elif len(clean) <= 2:
            cleaned_words.append(clean.upper())
        else:
            cleaned_words.append(clean.capitalize())

    if not cleaned_words:
        return ""

    # Try combining two words if they fit comfortably (e.g. "3D CAD", "Firmware QA", "AI Limits")
    if len(cleaned_words) >= 2:
        combined = f"{cleaned_words[0]} {cleaned_words[1]}"
        if len(combined) <= max_len:
            return combined

    # If first word is very short (<= 3 chars, e.g. "3D", "UI", "QA") and we have a 2nd word,
    # combine with truncated 2nd word so it's not a lonely cryptic acronym
    if len(cleaned_words) >= 2 and len(cleaned_words[0]) <= 3:
        combined = f"{cleaned_words[0]} {cleaned_words[1]}"
        return combined[:max_len].strip()

    # Otherwise return the first word
    return cleaned_words[0][:max_len]

def _clean_context_word(word, max_len=12):
    """Legacy helper fallback."""
    return _format_context_phrase([word] if word else [], max_len=max_len)

def _extract_antigravity_context(transcript_lines=None, role=None, objective=None):
    """Extract a concise, meaningful context tag for Antigravity."""
    generic_words = {
        "agent", "worker", "specialist", "engineer", "subagent", "reviewer",
        "tester", "ticket", "task", "user", "objective", "display", "multi",
        "service", "system", "request", "tool", "call", "please", "help"
    }
    acronyms = {"3d", "cad", "ui", "ux", "qa", "api", "rpc", "ota", "lcd", "esp", "pcb", "cli", "ai"}

    if role:
        words = re.findall(r"[A-Za-z0-9]+", role)
        filtered = [w for w in words if w.lower() not in generic_words]
        phrase = _format_context_phrase(filtered or words, max_len=12)
        if phrase:
            return phrase

    if objective:
        words = re.findall(r"[A-Za-z0-9]+", objective)
        filtered = [w for w in words if w.lower() not in generic_words]
        phrase = _format_context_phrase(filtered or words, max_len=12)
        if phrase:
            return phrase

    if transcript_lines:
        for line in transcript_lines:
            entry = {}
            if isinstance(line, dict):
                entry = line
            elif isinstance(line, str):
                try:
                    entry = json.loads(line)
                except Exception:
                    entry = {}

            if not isinstance(entry, dict):
                continue

            content = entry.get("content", "")
            if isinstance(content, str) and "# USER Objective:" in content:
                m = re.search(r"# USER Objective:\s*([^\n\r]+)", content)
                if m:
                    words = re.findall(r"[A-Za-z0-9]+", m.group(1))
                    filtered = [w for w in words if w.lower() not in generic_words]
                    phrase = _format_context_phrase(filtered or words, max_len=12)
                    if phrase:
                        return phrase

            tool_calls = entry.get("tool_calls", [])
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    args = tc.get("args", {}) if isinstance(tc, dict) else {}
                    subagents = args.get("Subagents", []) if isinstance(args, dict) else []
                    if isinstance(subagents, list):
                        for sa in subagents:
                            if isinstance(sa, dict) and sa.get("Role"):
                                words = re.findall(r"[A-Za-z0-9]+", sa["Role"])
                                filtered = [w for w in words if w.lower() not in generic_words]
                                phrase = _format_context_phrase(filtered or words, max_len=12)
                                if phrase:
                                    return phrase

        stop_words = {
            "can", "we", "the", "a", "an", "to", "for", "in", "of", "and", "is", "it",
            "you", "i", "me", "my", "our", "have", "has", "do", "does", "did", "please",
            "make", "write", "create", "update", "fix", "add", "show", "get", "let", "lets",
            "why", "what", "how", "when", "where", "this", "that", "there", "with", "instead"
        }
        for line in transcript_lines:
            entry = {}
            if isinstance(line, dict):
                entry = line
            elif isinstance(line, str):
                try:
                    entry = json.loads(line)
                except Exception:
                    entry = {}

            if not isinstance(entry, dict):
                continue

            if entry.get("type") in ("USER_INPUT", "user") or entry.get("source") == "USER_EXPLICIT":
                raw_content = entry.get("content", "")
                if isinstance(raw_content, str):
                    stripped = re.sub(r"<[^>]+>", " ", raw_content)
                    words = re.findall(r"[A-Za-z0-9]+", stripped)
                    filtered = [w for w in words if w.lower() not in stop_words and w.lower() not in generic_words and (len(w) >= 3 or w.lower() in acronyms)]
                    if filtered:
                        phrase = _format_context_phrase(filtered, max_len=12)
                        if phrase:
                            return phrase
    return ""

def _extract_claude_context(cwd=None, transcript_lines=None):
    """Extract a concise context tag for Claude."""
    if cwd:
        base = os.path.basename(os.path.normpath(cwd))
        words = re.findall(r"[A-Za-z0-9]+", base)
        if words:
            phrase = _format_context_phrase(words, max_len=12)
            if phrase:
                return phrase
    return ""

def get_stable_agent_label(source, session_key, transcript_lines=None, cwd=None, role=None, objective=None):
    """Assign stable, clean contextual names (e.g. 'Customizing', 'Limits', 'Backend') strictly clamped to <= 12 chars."""
    reg_key = f"{source}:{session_key}"
    if reg_key in _session_registry:
        return _session_registry[reg_key]

    _session_counters[source] = _session_counters.get(source, 0) + 1
    seq_num = _session_counters[source]

    label = ""
    if source == "antigravity":
        ctx = _extract_antigravity_context(transcript_lines, role=role, objective=objective)
        if ctx:
            label = ctx[:12]
        else:
            label = f"Agent {seq_num}"[:12]
    else:  # claude
        ctx = _extract_claude_context(cwd=cwd, transcript_lines=transcript_lines)
        if ctx:
            label = ctx[:12]
        else:
            label = f"Claude {seq_num}"[:12]

    # Handle collision with other existing labels in registry
    assigned_values = set(_session_registry.values())
    if label in assigned_values:
        if len(label) <= 10:
            label = f"{label} {seq_num}"[:12]
        else:
            label = f"{label[:10]} {seq_num}"[:12]

    _session_registry[reg_key] = label
    return label

def resolve_session_state(found_pending, turn_pending_prompt, has_in_flight_tools, is_final_turn_response, age, cfg=None, source="claude"):
    """Deterministic state resolution: WAITING > COMPLETE/IDLE > WORKING > IDLE."""
    completion_duration = (cfg.get("completion_duration_seconds", 10) if isinstance(cfg, dict) else 10) if cfg else 10
    working_color = "#FF7A00" if source == "antigravity" else "#00E5FF"

    if found_pending:
        return "WAITING", "waiting_approval", turn_pending_prompt, "#FFB800"
    elif is_final_turn_response:
        if age < completion_duration:
            return "COMPLETE", "work_complete", "WORK COMPLETE", "#00FF88"
        else:
            return "IDLE", "idle", "IDLE", "#94A3B8"
    elif has_in_flight_tools or age < IN_FLIGHT_TIMEOUT_SECONDS:
        return "WORKING", "working", "EXECUTING...", working_color
    else:
        return "IDLE", "idle", "IDLE", "#94A3B8"

# -----------------------------------------------------------------------------
# Hook-Driven Lifecycle Adapter (inspired by clawlight-cli)
# -----------------------------------------------------------------------------
_HOOK_STATE_FILE = os.path.expanduser("~/.claude/tinyscreen_hook_state.json")
_hook_sessions = {}
_hook_lock = threading.Lock()

def _load_hook_state():
    global _hook_sessions
    if not os.path.exists(_HOOK_STATE_FILE):
        _hook_sessions = {}
        return
    try:
        with open(_HOOK_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _hook_sessions = data
            else:
                _hook_sessions = {}
    except Exception:
        _hook_sessions = {}

def _save_hook_state():
    try:
        os.makedirs(os.path.dirname(_HOOK_STATE_FILE), exist_ok=True)
        tmp = _HOOK_STATE_FILE + f".tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_hook_sessions, f)
        os.replace(tmp, _HOOK_STATE_FILE)
    except Exception:
        pass

def _is_pid_alive(pid):
    if not pid or not isinstance(pid, int) or pid <= 0:
        return True
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (ProcessLookupError, OSError):
        return False

def handle_hook_event(data, now_ts=None):
    """Process a raw lifecycle hook payload from Claude Code or compatible agent."""
    if now_ts is None:
        now_ts = time.time()
    
    if not isinstance(data, dict):
        return None

    session_id = data.get("session_id")
    if not session_id:
        return None
    
    hook_event = data.get("hook_event_name") or data.get("event") or ""
    notification_type = data.get("notification_type", "")
    cwd = data.get("cwd") or data.get("directory") or ""
    owner_pid = data.get("owner_pid") or data.get("pid")
    if owner_pid is not None:
        try:
            owner_pid = int(owner_pid)
        except Exception:
            owner_pid = None

    with _hook_lock:
        _load_hook_state()
        if hook_event == "SessionEnd":
            _hook_sessions.pop(session_id, None)
            _save_hook_state()
            return {"status": "removed", "session_id": session_id}
        
        if hook_event == "Notification":
            # Informational idle notifications should not flip yellow
            if notification_type == "idle_prompt":
                return {"status": "ignored", "session_id": session_id}
            state = "WAITING"
            code = "waiting_approval"
            detail = "GRANT PERM"
            color = "#FFB800"
        elif hook_event == "PreToolUse":
            tool_name = (data.get("tool_name") or "").lower()
            if tool_name in ("askuserquestion", "ask_user_question"):
                state = "WAITING"
                code = "waiting_approval"
                detail = "ANSWER Q"
                color = "#FFB800"
            elif tool_name in ("ask_permission", "request_permission") or "permission" in tool_name or "confirm" in tool_name:
                state = "WAITING"
                code = "waiting_approval"
                detail = "GRANT PERM"
                color = "#FFB800"
            else:
                state = "WORKING"
                code = "working"
                detail = "EXECUTING..."
                color = "#00E5FF"
        elif hook_event in ("SessionStart", "UserPromptSubmit", "working", "resumed"):
            state = "WORKING"
            code = "working"
            detail = "EXECUTING..."
            color = "#00E5FF"
        elif hook_event in ("Stop", "idle", "ended"):
            state = "COMPLETE"
            code = "work_complete"
            detail = "WORK COMPLETE"
            color = "#00FF88"
        else:
            return {"status": "ignored", "session_id": session_id}
        
        existing = _hook_sessions.get(session_id, {})
        label = get_stable_agent_label("claude", session_id, cwd=cwd or existing.get("cwd", ""))
        
        entry = {
            "id": session_id,
            "name": label,
            "source": "claude",
            "state": state,
            "code": code,
            "detail": detail,
            "color": color,
            "mtime": now_ts,
            "cwd": cwd or existing.get("cwd", ""),
            "owner_pid": owner_pid or existing.get("owner_pid"),
            "hook_event": hook_event
        }
        _hook_sessions[session_id] = entry
        _save_hook_state()
        return entry

def get_hook_sessions(now_ts=None, cfg=None):
    """Return active hook sessions, reaping zombie PIDs and stale entries."""
    if now_ts is None:
        now_ts = time.time()
    if cfg is None:
        cfg = config
    
    with _hook_lock:
        _load_hook_state()
        active = []
        to_delete = []
        completion_duration = cfg.get("completion_duration_seconds", 10) if isinstance(cfg, dict) else 10
        
        for s_id, s in list(_hook_sessions.items()):
            pid = s.get("owner_pid")
            if pid and not _is_pid_alive(pid):
                to_delete.append(s_id)
                continue
            
            mtime = s.get("mtime", now_ts)
            age = now_ts - mtime
            if age >= 1800:
                to_delete.append(s_id)
                continue
            
            state = s.get("state", "IDLE")
            code = s.get("code", "idle")
            detail = s.get("detail", "IDLE")
            color = s.get("color", "#94A3B8")
            
            # Transition COMPLETE -> IDLE after completion_duration
            if state == "COMPLETE" and age >= completion_duration:
                state = "IDLE"
                code = "idle"
                detail = "IDLE"
                color = "#94A3B8"
            
            active.append({
                "id": s["id"],
                "name": s["name"],
                "source": "claude",
                "state": state,
                "code": code,
                "detail": detail,
                "color": color,
                "age_seconds": int(age),
                "mtime": mtime
            })
        
        if to_delete:
            for s_id in to_delete:
                _hook_sessions.pop(s_id, None)
            _save_hook_state()
            
        return active

def install_claude_hooks(app_path=None):
    """Idempotently register Tiny AI Limits hook command in ~/.claude/settings.json."""
    if app_path is None:
        app_path = os.path.abspath(__file__)
    settings_path = os.path.expanduser("~/.claude/settings.json")
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}
    
    if not isinstance(settings, dict):
        settings = {}
    
    hooks = settings.setdefault("hooks", {})
    hook_events = ["SessionStart", "UserPromptSubmit", "PreToolUse", "Stop", "Notification", "SessionEnd"]
    hook_cmd = f"python3 \"{app_path}\" --hook"
    
    for event in hook_events:
        event_hooks = hooks.setdefault(event, [])
        already_registered = False
        for h in event_hooks:
            for item in h.get("hooks", []):
                cmd = item.get("command", "")
                if "--hook" in cmd and (app_path in cmd or "app.py" in cmd or "tinyscreen" in cmd.lower()):
                    already_registered = True
                    break
        if not already_registered:
            event_hooks.append({
                "hooks": [{
                    "type": "command",
                    "command": hook_cmd
                }]
            })
            
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    return True

def uninstall_claude_hooks(app_path=None):
    """Remove Tiny AI Limits hook entries from ~/.claude/settings.json."""
    if app_path is None:
        app_path = os.path.abspath(__file__)
    settings_path = os.path.expanduser("~/.claude/settings.json")
    if not os.path.exists(settings_path):
        return True
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        if not isinstance(settings, dict):
            return True
        hooks = settings.get("hooks", {})
        for event, event_hooks in list(hooks.items()):
            if isinstance(event_hooks, list):
                new_list = []
                for h in event_hooks:
                    keep = True
                    for item in h.get("hooks", []):
                        cmd = item.get("command", "")
                        if "--hook" in cmd and (app_path in cmd or "app.py" in cmd or "tinyscreen" in cmd.lower()):
                            keep = False
                    if keep:
                        new_list.append(h)
                hooks[event] = new_list
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False

def scan_antigravity_sessions(brain_dirs=None, now_ts=None):
    if brain_dirs is None:
        brain_dirs = _antigravity_brain_dirs()
    if now_ts is None:
        now_ts = time.time()

    sessions = []
    for brain_dir in brain_dirs:
        for root, dirs, files in os.walk(brain_dir):
            if "transcript.jsonl" not in files:
                continue
            fp = os.path.join(root, "transcript.jsonl")
            try:
                mtime = os.path.getmtime(fp)
            except Exception:
                continue

            # 30 minutes of slack accounts for realistic human reaction time
            age = now_ts - mtime
            if age >= 1800:
                continue

            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l for l in f.readlines() if l.strip()]
            except Exception:
                continue
            if not lines:
                continue

            last_user_idx = -1
            for idx in range(len(lines) - 1, -1, -1):
                try:
                    entry = json.loads(lines[idx])
                    if entry.get("type") == "USER_INPUT" or entry.get("source") == "USER_EXPLICIT":
                        last_user_idx = idx
                        break
                except Exception:
                    pass

            # Session identification (parent folder of .system_generated)
            parts = os.path.normpath(fp).split(os.sep)
            session_id = parts[-4] if len(parts) >= 4 and parts[-3] == ".system_generated" else os.path.basename(root)
            label = get_stable_agent_label("antigravity", session_id, transcript_lines=lines)

            if last_user_idx == len(lines) - 1:
                # User just sent a prompt; assistant is currently thinking/executing
                if age < 45:
                    sessions.append({
                        "id": session_id,
                        "name": label,
                        "source": "antigravity",
                        "state": "WORKING",
                        "code": "working",
                        "detail": "EXECUTING...",
                        "color": "#00E5FF",
                        "age_seconds": int(age),
                        "mtime": mtime
                    })
                continue

            turn_lines = lines[last_user_idx + 1:] if last_user_idx != -1 else lines
            if not turn_lines:
                continue

            last_step_entry = {}
            try:
                last_step_entry = json.loads(turn_lines[-1])
            except Exception:
                pass

            found_pending = False
            turn_pending_prompt = "INPUT REQ"

            step_type = last_step_entry.get("type")
            is_final_turn_response = False
            has_in_flight_tools = False

            if step_type in ("ASK_QUESTION", "ASK_PERMISSION"):
                found_pending = True
                turn_pending_prompt = "ANSWER Q" if step_type == "ASK_QUESTION" else "GRANT PERM"
            elif step_type == "PLANNER_RESPONSE":
                tool_calls = last_step_entry.get("tool_calls", []) or []
                if tool_calls:
                    # Tool call generated: check if it is an explicit user prompt/approval modal
                    for tc in tool_calls:
                        name = tc.get("name")
                        args = tc.get("args", {}) or {}

                        meta_raw = args.get("ArtifactMetadata") if isinstance(args, dict) else None
                        if isinstance(meta_raw, str):
                            try: meta = json.loads(meta_raw)
                            except Exception: meta = {}
                        elif isinstance(meta_raw, dict):
                            meta = meta_raw
                        else:
                            meta = {}

                        name_str = (name or "")
                        name_lower = name_str.lower()
                        if meta.get("RequestFeedback") is True:
                            found_pending = True
                            turn_pending_prompt = "APPROVE PLAN"
                            break
                        elif name_lower in ("ask_question", "ask_user_question"):
                            found_pending = True
                            turn_pending_prompt = "ANSWER Q"
                            break
                        elif name_lower in ("ask_permission", "request_permission") or "permission" in name_lower or "confirm" in name_lower:
                            found_pending = True
                            turn_pending_prompt = "GRANT PERM"
                            break
                        else:
                            # Autonomous tool execution (run_command, write_to_file, replace_file_content, etc.)
                            has_in_flight_tools = True
                elif last_step_entry.get("content"):
                    # Final text response delivered to user
                    is_final_turn_response = True
                else:
                    # Thinking or reasoning step with no tools and no text content yet
                    has_in_flight_tools = True
            elif step_type == "GENERIC":
                # Intermediate tool output step: turn is still executing
                has_in_flight_tools = True

            state, code, detail, color = resolve_session_state(
                found_pending, turn_pending_prompt, has_in_flight_tools, is_final_turn_response, age, config, source="antigravity"
            )

            sessions.append({
                "id": session_id,
                "name": label,
                "source": "antigravity",
                "state": state,
                "code": code,
                "detail": detail,
                "color": color,
                "age_seconds": int(age),
                "mtime": mtime
            })
    return sessions

def check_antigravity_status(brain_dirs=None, now_ts=None):
    sessions = scan_antigravity_sessions(brain_dirs, now_ts)
    waiting = next((s for s in sessions if s["state"] == "WAITING"), None)
    if waiting:
        return {
            "waiting_for_input": True,
            "work_completed": False,
            "prompt_text": waiting["detail"],
            "source": "antigravity"
        }
    complete = next((s for s in sessions if s["state"] == "COMPLETE"), None)
    if complete:
        return {
            "waiting_for_input": False,
            "work_completed": True,
            "prompt_text": "INPUT REQ",
            "source": "antigravity"
        }
    return {
        "waiting_for_input": False,
        "work_completed": False,
        "prompt_text": "INPUT REQ",
        "source": "antigravity"
    }

def scan_claude_sessions(claude_dirs=None, now_ts=None):
    if claude_dirs is None:
        claude_dirs = get_claude_dirs()
    if now_ts is None:
        now_ts = time.time()

    sessions = []
    for c_dir in claude_dirs:
        pattern = os.path.join(c_dir, "**", "*.jsonl")
        for fp in glob.glob(pattern, recursive=True):
            try:
                mtime = os.path.getmtime(fp)
            except Exception:
                continue

            age = now_ts - mtime
            if age >= 1800:
                continue

            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip()]
            except Exception:
                continue
            if not lines:
                continue

            last_user_idx = -1
            for idx in range(len(lines) - 1, -1, -1):
                try:
                    entry = json.loads(lines[idx])
                    if entry.get("type") == "user":
                        msg = entry.get("message", {})
                        content = msg.get("content")
                        if isinstance(content, str):
                            last_user_idx = idx
                            break
                        elif isinstance(content, list):
                            has_text = any(isinstance(c, dict) and c.get("type") == "text" for c in content)
                            if has_text:
                                last_user_idx = idx
                                break
                except Exception:
                    pass

            session_id = os.path.splitext(os.path.basename(fp))[0]
            label = get_stable_agent_label("claude", session_id, cwd=os.path.dirname(fp), transcript_lines=lines)

            if last_user_idx == len(lines) - 1:
                # User just sent a prompt; Claude is currently thinking/executing
                if age < 45:
                    sessions.append({
                        "id": session_id,
                        "name": label,
                        "source": "claude",
                        "state": "WORKING",
                        "code": "working",
                        "detail": "EXECUTING...",
                        "color": "#00E5FF",
                        "age_seconds": int(age),
                        "mtime": mtime
                    })
                continue

            turn_lines = lines[last_user_idx + 1:] if last_user_idx != -1 else lines
            if not turn_lines:
                continue

            last_entry = {}
            try:
                last_entry = json.loads(turn_lines[-1])
            except Exception:
                pass

            found_pending = False
            turn_pending_prompt = "CLAUDE PROMPT"
            has_in_flight_tools = False
            is_final_turn_response = False

            if last_entry.get("type") == "assistant":
                msg = last_entry.get("message", {})
                content = msg.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            t_name = (item.get("name") or "").lower()
                            if t_name in ("askuserquestion", "ask_user_question"):
                                found_pending = True
                                turn_pending_prompt = "ANSWER Q"
                                break
                            elif t_name in ("ask_permission", "request_permission") or "permission" in t_name or "confirm" in t_name:
                                found_pending = True
                                turn_pending_prompt = "GRANT PERM"
                                break
                            else:
                                # Autonomous tools (bash, edit, write, fileedit, etc.)
                                has_in_flight_tools = True
                    if not found_pending and not has_in_flight_tools:
                        is_final_turn_response = any(isinstance(item, dict) and item.get("type") == "text" for item in content)
                elif isinstance(content, str) and content.strip():
                    is_final_turn_response = True

            state, code, detail, color = resolve_session_state(
                found_pending, turn_pending_prompt, has_in_flight_tools, is_final_turn_response, age, config, source="claude"
            )

            sessions.append({
                "id": session_id,
                "name": label,
                "source": "claude",
                "state": state,
                "code": code,
                "detail": detail,
                "color": color,
                "age_seconds": int(age),
                "mtime": mtime
            })
    return sessions

def check_claude_status(claude_dirs=None, now_ts=None):
    if now_ts is None:
        now_ts = time.time()
    hook_sessions = get_hook_sessions(now_ts)
    hooked_ids = {s["id"] for s in hook_sessions}
    scanned_sessions = [s for s in scan_claude_sessions(claude_dirs, now_ts) if s["id"] not in hooked_ids]
    sessions = hook_sessions + scanned_sessions
    waiting = next((s for s in sessions if s["state"] == "WAITING"), None)
    if waiting:
        return {
            "waiting_for_input": True,
            "work_completed": False,
            "prompt_text": waiting["detail"],
            "source": "claude"
        }
    complete = next((s for s in sessions if s["state"] == "COMPLETE"), None)
    if complete:
        return {
            "waiting_for_input": False,
            "work_completed": True,
            "prompt_text": "INPUT REQ",
            "source": "claude"
        }
    return {
        "waiting_for_input": False,
        "work_completed": False,
        "prompt_text": "INPUT REQ",
        "source": "claude"
    }

def get_multi_agent_status(antigravity_dirs=None, claude_dirs=None, now_ts=None):
    if now_ts is None:
        now_ts = time.time()

    hook_sessions = get_hook_sessions(now_ts)
    hooked_ids = {s["id"] for s in hook_sessions}

    ag_sessions = scan_antigravity_sessions(brain_dirs=antigravity_dirs, now_ts=now_ts)
    cl_sessions = [s for s in scan_claude_sessions(claude_dirs=claude_dirs, now_ts=now_ts) if s["id"] not in hooked_ids]
    all_sessions = hook_sessions + ag_sessions + cl_sessions

    # State sorting priority: WAITING > WORKING > COMPLETE > IDLE
    priority_map = {"WAITING": 0, "WORKING": 1, "COMPLETE": 2, "IDLE": 3}
    all_sessions.sort(key=lambda s: (priority_map.get(s["state"], 4), s["age_seconds"]))

    # Only show active sessions (WAITING, WORKING, COMPLETE). If none are active, active_agents is empty.
    active = [s for s in all_sessions if s["state"] in ("WAITING", "WORKING", "COMPLETE")]

    waiting_session = next((s for s in all_sessions if s["state"] == "WAITING"), None)
    complete_session = next((s for s in all_sessions if s["state"] == "COMPLETE"), None)

    waiting_for_input = waiting_session is not None
    work_completed = complete_session is not None and not waiting_for_input
    prompt_text = waiting_session["detail"] if waiting_session else "INPUT REQ"
    completion_text = complete_session["detail"] if complete_session else "WORK COMPLETE"
    source = waiting_session["source"] if waiting_session else (complete_session["source"] if complete_session else "none")

    return {
        "waiting_for_input": waiting_for_input,
        "work_completed": work_completed,
        "prompt_text": prompt_text,
        "completion_text": completion_text,
        "source": source,
        "active_agents": active[:3],
        "has_active_agents": len(active) > 0
    }

def check_agent_status(antigravity_dirs=None, claude_dirs=None, now_ts=None):
    res = get_multi_agent_status(antigravity_dirs, claude_dirs, now_ts)
    return {
        "waiting_for_input": res["waiting_for_input"],
        "work_completed": res["work_completed"],
        "prompt_text": res["prompt_text"],
        "source": res["source"]
    }


@app.route('/data', methods=['GET'])
def get_data():
    if not caller_is_paired():
        return jsonify({
            "error": "not_paired",
            "message": "This board is not paired with this companion app. "
                       "Run setup, or set allow_unpaired_clients in config.json.",
        }), 403

    try:
        antigravity_data = get_antigravity_quota()
    except Exception as e:
        print(f"Antigravity scan error: {e}")
        antigravity_data = {"limit": 200, "used": 0, "remaining": 200, "period": "5h"}
    
    try:
        claude_data = scan_claude_usage()
    except Exception as e:
        print(f"Claude token scan error: {e}")
        claude_data = {"tokens_today": 0, "limit": 100, "remaining": 100, "reset_str": "READY"}
        
    weather_data = get_weather()
    
    waiting_for_input = False
    work_completed = False
    prompt_text = "INPUT REQ"
    completion_text = "WORK COMPLETE"
    source = "none"

    if test_idle_override:
        waiting_for_input = False
        work_completed = False
        active_agents_payload = []
        has_active = False
        agent_state = "idle"
        source = "none"
    elif test_agents_override is not None:
        active_agents_payload = test_agents_override
        has_active = len(test_agents_override) > 0
        waiting_for_input = any(a.get("state") == "WAITING" for a in test_agents_override)
        work_completed = any(a.get("state") == "COMPLETE" for a in test_agents_override) and not waiting_for_input
        prompt_text = next((a.get("detail") for a in test_agents_override if a.get("state") == "WAITING"), "INPUT REQ")
        completion_text = next((a.get("detail") for a in test_agents_override if a.get("state") == "COMPLETE"), "WORK COMPLETE")
        agent_state = "waiting_approval" if waiting_for_input else ("completed" if work_completed else "working" if has_active else "idle")
        source = "test"
    elif test_alert_override:
        waiting_for_input = True
        prompt_text = test_alert_prompt
        source = "test"
    elif test_complete_override:
        work_completed = True
        completion_text = test_complete_prompt
        source = "test"
    else:
        try:
            status = check_agent_status()
            waiting_for_input = status["waiting_for_input"]
            work_completed = status["work_completed"]
            prompt_text = status["prompt_text"]
            source = status["source"]
        except Exception as e:
            print(f"Agent check error: {e}")

    now = datetime.now()
    if not test_idle_override and test_agents_override is None:
        agent_state = "waiting_approval" if waiting_for_input else ("completed" if work_completed else "idle")
        multi_status = get_multi_agent_status()

        # If test overrides are active, synthesize an active agent entry
        if test_alert_override:
            active_agents_payload = [{
                "id": "test-alert",
                "name": "Claude 1",
                "source": "claude",
                "state": "WAITING",
                "code": "waiting_approval",
                "detail": test_alert_prompt,
                "color": "#FFB800"
            }]
            has_active = True
        elif test_complete_override:
            active_agents_payload = [{
                "id": "test-complete",
                "name": "AGY 1",
                "source": "antigravity",
                "state": "COMPLETE",
                "code": "work_complete",
                "detail": test_complete_prompt,
                "color": "#00FF88"
            }]
            has_active = True
        else:
            active_agents_payload = multi_status["active_agents"]
            has_active = multi_status["has_active_agents"]

    global _ota_trigger_requested
    with _ota_trigger_lock:
        trigger_ota = _ota_trigger_requested
        _ota_trigger_requested = False

    fw_info = get_latest_firmware()
    ota_payload = {
        "available": bool(fw_info.get("path") and fw_info.get("size", 0) > 0),
        "version": fw_info.get("version", "0.5"),
        "tag": fw_info.get("tag", "firmware-v0.5"),
        "trigger": trigger_ota,
        "url": "/firmware/latest.bin"
    }

    # Dynamic Gauge Mapping for Left and Right HUD Arcs
    cfg = config
    selected = cfg.get("selected_gauges", {"left": "claude", "right": "antigravity"})
    left_id = selected.get("left", "claude")
    right_id = selected.get("right", "antigravity")

    # Fast in-memory lookup from background poller (non-blocking)
    left_snap = poller.get_snapshot(left_id)
    right_snap = poller.get_snapshot(right_id)

    # Left gauge properties
    left_curved = ""
    left_mode = "standard"
    if left_id == "claude":
        plan_mode = config.get("claude_plan", "enterprise")
        left_label = "CLD"
        left_name = "Claude"
        left_color = "0x00E5FF"
        left_mode = plan_mode
        if plan_mode == "enterprise":
            cost_today = claude_data.get("cost_today_usd", 0.0)
            daily_budget = float(config.get("claude_daily_budget_usd", 10.0))
            left_pct = int(min(100, round((cost_today / max(0.01, daily_budget)) * 100)))
            left_reset = claude_data.get("reset_str", f"{claude_data.get('tokens_str', '0')} TOK")
            left_curved = claude_data.get("curved_text", f"{claude_data.get('cost_str', '$0.00')} SPENT")
        else:
            left_pct = claude_data.get("remaining", 100)
            left_reset = claude_data.get("reset_str", "READY")
            left_curved = f"{left_label} {left_pct}%"
    elif left_snap and left_snap.primary_window:
        left_pct = int(round(left_snap.primary_window.percent_left))
        left_label = left_snap.badge or left_id[:3].upper()
        left_name = left_snap.provider_name
        left_color = left_snap.color
        if left_snap.primary_window.resets_at:
            _, left_reset = format_reset_time(left_snap.primary_window.resets_at)
        else:
            left_reset = left_snap.primary_window.period_desc or "READY"
        left_curved = f"{left_label} {left_pct}%"
    else:
        left_pct = 100
        left_label = left_id[:3].upper()
        left_name = left_id.capitalize()
        left_color = "0x00E5FF"
        left_reset = "READY"
        left_curved = f"{left_label} 100%"

    # Right gauge properties
    if right_id == "antigravity":
        lim = max(1, antigravity_data.get("limit", 100))
        rem = antigravity_data.get("remaining", 100)
        right_pct = int(round((rem / lim) * 100))
        right_label = "AGY"
        right_name = "Antigravity"
        right_color = "0xFF9100"
        right_reset = antigravity_data.get("reset_str") or antigravity_data.get("period", "5h")
    elif right_snap and right_snap.primary_window:
        right_pct = int(round(right_snap.primary_window.percent_left))
        right_label = right_snap.badge or right_id[:3].upper()
        right_name = right_snap.provider_name
        right_color = right_snap.color
        if right_snap.primary_window.resets_at:
            _, right_reset = format_reset_time(right_snap.primary_window.resets_at)
        else:
            right_reset = right_snap.primary_window.period_desc or "5h"
    else:
        right_pct = 100
        right_label = right_id[:3].upper()
        right_name = right_id.capitalize()
        right_color = "0xFF9100"
        right_reset = "READY"

    left_gauge = {
        "id": left_id,
        "label": left_label,
        "name": left_name,
        "mode": left_mode,
        "percent": left_pct,
        "color": left_color,
        "reset_str": left_reset,
        "curved_text": left_curved,
        "cost_usd": claude_data.get("cost_today_usd", 0.0) if left_id == "claude" else 0.0,
        "cost_str": claude_data.get("cost_str", "$0.00") if left_id == "claude" else "$0.00",
        "tokens_str": claude_data.get("tokens_str", "0") if left_id == "claude" else "0",
        "daily_budget_usd": float(config.get("claude_daily_budget_usd", 10.0)) if left_id == "claude" else 0.0
    }

    right_gauge = {
        "id": right_id,
        "label": right_label,
        "name": right_name,
        "percent": right_pct,
        "color": right_color,
        "reset_str": right_reset
    }

    return jsonify({
        "left_gauge": left_gauge,
        "right_gauge": right_gauge,
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
            "completion_text": completion_text,
            "source": source,
            "has_active_agents": has_active,
            "active_agents": active_agents_payload
        },
        "ota": ota_payload
    })

@app.route('/api/providers', methods=['GET'])
def get_providers_api():
    cfg = load_config()
    selected = cfg.get("selected_gauges", {"left": "claude", "right": "antigravity"})
    providers_data = []
    for p in poller.providers.values():
        snap = poller.get_snapshot(p.provider_id)
        if not snap:
            try:
                snap = p.fetch_usage(cfg)
            except Exception as e:
                snap = None
        pct = round(snap.primary_window.percent_left) if (snap and snap.primary_window) else 100
        providers_data.append({
            "id": p.provider_id,
            "name": p.provider_name,
            "badge": p.badge,
            "color": p.color,
            "status": snap.status if snap else "unconfigured",
            "percent": pct,
            "reset_str": (snap.primary_window.period_desc if snap and snap.primary_window else ""),
            "plan": snap.plan if snap else None,
            "is_selected_left": (selected.get("left") == p.provider_id),
            "is_selected_right": (selected.get("right") == p.provider_id),
            "has_key": bool(cfg.get("provider_keys", {}).get(p.provider_id) or cfg.get(f"{p.provider_id}_api_key")),
            "error_message": snap.error_message if snap else None
        })
    return jsonify({"providers": providers_data, "selected_gauges": selected})

@app.route('/api/agents', methods=['GET'])
def get_agents():
    return jsonify(get_multi_agent_status())

@app.route('/firmware/version', methods=['GET'])
def get_firmware_version():
    force = request.args.get("refresh", "0") == "1"
    fw_info = get_latest_firmware(force_check=force)
    return jsonify({
        "version": fw_info.get("version", "0.5"),
        "tag": fw_info.get("tag", "firmware-v0.5"),
        "available": bool(fw_info.get("path") and fw_info.get("size", 0) > 0),
        "size": fw_info.get("size", 0),
        "companion_version": COMPANION_VERSION
    })

@app.route('/firmware/latest.bin', methods=['GET'])
def download_latest_firmware():
    fw_info = get_latest_firmware()
    fw_path = fw_info.get("path")
    if not fw_path or not os.path.exists(fw_path):
        return jsonify({"error": "firmware_not_found", "message": "No firmware binary available"}), 404
    return send_file(
        fw_path,
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="firmware.bin"
    )

@app.route('/api/ota/trigger', methods=['POST'])
def trigger_ota():
    global _ota_trigger_requested
    with _ota_trigger_lock:
        _ota_trigger_requested = True
    fw_info = get_latest_firmware(force_check=True)
    return jsonify({
        "status": "ok",
        "message": "OTA update trigger armed for connected device",
        "target_version": fw_info.get("version", "0.5"),
        "target_tag": fw_info.get("tag", "firmware-v0.5")
    })

@app.route('/config', methods=['GET', 'POST'])
@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    global config
    if request.method == 'POST':
        data = request.json or {}
        if "auto_location" in data:
            config["auto_location"] = bool(data["auto_location"])
        if "antigravity_5h_quota" in data:
            try:
                config["antigravity_5h_quota"] = int(data["antigravity_5h_quota"])
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "antigravity_5h_quota must be an integer"}), 400
        if "antigravity_account_email" in data:
            # Empty string/null means "auto, use whichever account is found first"
            config["antigravity_account_email"] = data["antigravity_account_email"] or None
        if "selected_gauges" in data and isinstance(data["selected_gauges"], dict):
            config.setdefault("selected_gauges", {})
            if "left" in data["selected_gauges"]:
                config["selected_gauges"]["left"] = str(data["selected_gauges"]["left"])
            if "right" in data["selected_gauges"]:
                config["selected_gauges"]["right"] = str(data["selected_gauges"]["right"])
        if "provider_keys" in data and isinstance(data["provider_keys"], dict):
            config.setdefault("provider_keys", {})
            for k, v in data["provider_keys"].items():
                if v:
                    config["provider_keys"][k] = str(v)
                    config[f"{k}_api_key"] = str(v)
        if "city" in data and data["city"]:
            lat, lon, full_name = geocode_city(data["city"])
            if lat and lon:
                config["lat"] = lat
                config["lon"] = lon
                config["manual_location_name"] = full_name
            else:
                return jsonify({"status": "error", "message": f"Could not find city '{data['city']}'"}), 400
        save_config(config)
        
        # Mask sensitive keys in response
        masked_cfg = dict(config)
        if "provider_keys" in masked_cfg:
            masked_cfg["provider_keys"] = {k: (v[:4] + "..." + v[-4:] if len(v) > 8 else "***") for k, v in masked_cfg["provider_keys"].items()}
        return jsonify({"status": "ok", "config": masked_cfg})
        
    response = dict(config)
    if "provider_keys" in response:
        response["provider_keys"] = {k: (v[:4] + "..." + v[-4:] if len(v) > 8 else "***") for k, v in response["provider_keys"].items()}
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

PORT = 5000

def get_host_label():
    return socket.gethostname().split('.')[0].replace(' ', '-') or "tinyscreen-host"

@app.route('/whoami', methods=['GET'])
def whoami():
    """Identity of this companion, read by the setup page before it provisions
    a board over Web Serial. The browser has no API for the machine's own LAN
    IP, so the setup page asks us for it and passes it straight to the board."""
    return jsonify({
        "ip": get_local_ip(),
        "port": PORT,
        "pair_id": get_pair_id(config),
        "hostname": get_host_label(),
        "user": getpass.getuser(),
        "version": COMPANION_VERSION,
    })

def register_mdns_service(port=PORT):
    global _zeroconf_instance
    try:
        local_ip = get_local_ip()
        host_label = get_host_label()
        pair_id = get_pair_id(config)
        properties = {
            "pair_id": pair_id,
            "hostname": host_label,
            "user": getpass.getuser(),
            "version": COMPANION_VERSION,
        }
        info = ServiceInfo(
            "_tinyscreen._tcp.local.",
            # Instance name includes the host label: two companions on one LAN
            # would otherwise register the identical name and conflict.
            f"Tiny AI Screen Companion ({host_label})._tinyscreen._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties=properties,
            server=f"{host_label}.local.",
        )
        _zeroconf_instance = Zeroconf()
        _zeroconf_instance.register_service(info)
        print(f"[mDNS] Advertising _tinyscreen._tcp.local at {local_ip}:{port} (server: {host_label}.local., pair_id: {pair_id})")
    except Exception as e:
        print(f"[mDNS] Failed to register service: {e}")

def start_flask():
    poller.start(load_config)
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
            fw = get_latest_firmware(force_check=True)
            if fw.get("path") and fw.get("size", 0) > 0:
                tag = fw.get("tag", "Unknown")
                size_kb = fw.get("size", 0) // 1024
                if messagebox.askyesno("Firmware Update", f"Latest Release: {tag} ({size_kb} KB)\n\nDo you want to flash this firmware to your ESP32 over-the-air now?"):
                    global _ota_trigger_requested
                    with _ota_trigger_lock:
                        _ota_trigger_requested = True
                    messagebox.showinfo("OTA Triggered", "OTA Update trigger sent to device!\nYour screen will show the update progress ring shortly.")
            else:
                messagebox.showwarning("Update Check", "No firmware release found on GitHub or repository is private.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check GitHub updates: {e}")

    ota_btn = tk.Button(ota_frame, text="⚡ Flash Latest Firmware (OTA)", command=check_firmware_updates, bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5", font=("Helvetica", 9, "bold"), bd=0, padx=10, pady=6)
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

            @rumps.clicked("⚡ Flash Latest Firmware (OTA)")
            def check_updates(self, _):
                try:
                    fw = get_latest_firmware(force_check=True)
                    if fw.get("path") and fw.get("size", 0) > 0:
                        tag = fw.get("tag", "Unknown")
                        size_kb = fw.get("size", 0) // 1024
                        response = rumps.alert(
                            title="Firmware OTA Update",
                            message=f"Latest Release: {tag} ({size_kb} KB)\n\nFlash this firmware over-the-air to your ESP32 companion device now?",
                            ok="Flash Device (OTA)",
                            cancel="Cancel"
                        )
                        if response == 1:
                            global _ota_trigger_requested
                            with _ota_trigger_lock:
                                _ota_trigger_requested = True
                            rumps.alert("OTA Triggered", "OTA Update signal sent to device!\nYour screen will begin flashing shortly.")
                    else:
                        rumps.alert("Firmware Updates", "No firmware release found on GitHub or repository is private.")
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
    if "--hook" in sys.argv:
        # Read JSON from stdin or argument
        raw_input = ""
        try:
            if not sys.stdin.isatty():
                raw_input = sys.stdin.read().strip()
        except Exception:
            pass
        
        event_data = {}
        if raw_input:
            try:
                event_data = json.loads(raw_input)
            except Exception:
                pass
        
        hook_idx = sys.argv.index("--hook")
        if not event_data and len(sys.argv) > hook_idx + 1 and not sys.argv[hook_idx + 1].startswith("-"):
            try:
                event_data = json.loads(sys.argv[hook_idx + 1])
            except Exception:
                pass
        
        if "owner_pid" not in event_data and "pid" not in event_data:
            event_data["owner_pid"] = os.getppid()
        
        posted = False
        try:
            r = requests.post(f"http://127.0.0.1:{PORT}/api/hook", json=event_data, timeout=0.5)
            if r.status_code == 200:
                posted = True
        except Exception:
            pass
        
        if not posted:
            handle_hook_event(event_data)
        sys.exit(0)

    if "--install-hooks" in sys.argv:
        install_claude_hooks()
        print("[OK] Tiny AI Limits lifecycle hooks installed into ~/.claude/settings.json")
        sys.exit(0)

    if "--uninstall-hooks" in sys.argv:
        uninstall_claude_hooks()
        print("[OK] Tiny AI Limits lifecycle hooks uninstalled from ~/.claude/settings.json")
        sys.exit(0)

    if "--server-only" in sys.argv or "--headless" in sys.argv:
        print(f"[INFO] Running in headless server-only mode at http://localhost:{PORT}")
        start_flask()
    else:
        # Start Flask server in background thread
        t = Thread(target=start_flask, daemon=True)
        t.start()
        # Launch macOS Status Bar App or Windows GUI
        statusBarApp = TinyScreenMacStatusBarApp()
        statusBarApp.run()
