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
        "antigravity_cycle_start": None
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

@app.route('/emulator')
@app.route('/simulator')
def serve_emulator():
    emulator_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emulator", "index.html")
    if os.path.exists(emulator_path):
        return send_file(emulator_path)
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

# --- Antigravity Data Extraction Logic ---
# NOTE: Google does not expose Antigravity's real 5h quota anywhere (locally or
# via API) -- it's an undisclosed, dynamic "amount of agent work done" measure,
# not a fixed request count. This counts PLANNER_RESPONSE entries (one per
# agent/model turn) as the closest available proxy for "work done", since a
# single prompt can trigger many turns. `antigravity_5h_quota` in config.json
# is a guessed ceiling -- tune it against when the real app actually locks you
# out to calibrate the displayed percentage.
def scan_antigravity_5h_limits(quota_limit=None):
    if quota_limit is None:
        quota_limit = config.get("antigravity_5h_quota", 200)
    total_steps = 0
    now = time.time()

    # Google's 5h quota is (almost certainly) a fixed-duration window anchored
    # to first use, like Claude's own rate limit -- it resets sharply back to
    # 100%, it doesn't continuously erode/regenerate. A plain trailing "last
    # 5 real-time hours" window doesn't behave that way: right after a real
    # reset, it still includes turns from *before* the reset (they're still
    # within the last 5h), so used% looks far higher than reality until those
    # age out -- which is exactly the pattern behind our repeated recalibration
    # (750 -> 1033 -> 3800) as the window slowly caught up rather than the
    # true limit actually changing. Track our own fixed 5h cycle instead:
    # once it's been running >=5h, snap to a fresh one starting now.
    cycle_start = config.get("antigravity_cycle_start")
    if cycle_start is None or (now - cycle_start) >= 5 * 3600:
        cycle_start = now
        config["antigravity_cycle_start"] = cycle_start
        save_config(config)

    brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    if os.path.exists(brain_dir):
        pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
        for filepath in glob.glob(pattern):
            try:
                if os.path.getmtime(filepath) < cycle_start:
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
                                if dt.timestamp() >= cycle_start:
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

# --- Flask Endpoints ---
@app.route('/data', methods=['GET'])
def get_data():
    try:
        antigravity_data = scan_antigravity_5h_limits()
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
    prompt_text = "INPUT REQ"
    try:
        brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
        if os.path.exists(brain_dir):
            latest_mod = 0
            latest_transcript = None
            for root, dirs, files in os.walk(brain_dir):
                if "transcript.jsonl" in files:
                    fp = os.path.join(root, "transcript.jsonl")
                    mtime = os.path.getmtime(fp)
                    if mtime > latest_mod:
                        latest_mod = mtime
                        latest_transcript = fp

            # A pending question/permission/plan-approval is only ever the
            # LAST line of the transcript -- once answered, the agent appends
            # a new step (e.g. type ASK_QUESTION) right after it. 30 minutes
            # of slack accounts for realistic human reaction time; the file
            # simply stops being written while a question is outstanding.
            if latest_transcript and (time.time() - latest_mod) < 1800:
                with open(latest_transcript, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l for l in f.readlines() if l.strip()]
                if lines:
                    try:
                        last_step = json.loads(lines[-1])
                    except Exception:
                        last_step = None
                    if last_step and last_step.get("type") == "PLANNER_RESPONSE":
                        for tc in last_step.get("tool_calls", []) or []:
                            name = tc.get("name")
                            args = tc.get("args", {}) or {}
                            if name == "ask_question":
                                waiting_for_input = True
                                prompt_text = "ANSWER Q"
                                break
                            if name == "ask_permission":
                                waiting_for_input = True
                                prompt_text = "GRANT PERM"
                                break
                            meta_raw = args.get("ArtifactMetadata") if isinstance(args, dict) else None
                            if isinstance(meta_raw, str):
                                try:
                                    meta = json.loads(meta_raw)
                                except Exception:
                                    meta = {}
                            elif isinstance(meta_raw, dict):
                                meta = meta_raw
                            else:
                                meta = {}
                            if meta.get("RequestFeedback") is True:
                                waiting_for_input = True
                                prompt_text = "APPROVE PLAN"
                                break
    except Exception as e:
        print(f"Agent check error: {e}")


    now = datetime.now()
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
            "prompt_text": prompt_text
        }
    })

@app.route('/config', methods=['GET', 'POST'])
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
    return jsonify(config)

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

def register_mdns_service():
    global _zeroconf_instance
    try:
        local_ip = get_local_ip()
        info = ServiceInfo(
            "_tinyscreen._tcp.local.",
            "Tiny AI Screen Companion._tinyscreen._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=5000,
        )
        _zeroconf_instance = Zeroconf()
        _zeroconf_instance.register_service(info)
        print(f"[mDNS] Advertising _tinyscreen._tcp.local at {local_ip}:5000")
    except Exception as e:
        print(f"[mDNS] Failed to register service: {e}")

def start_flask():
    register_mdns_service()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def create_gui_window():
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("Tiny AI Screen Companion")
    root.geometry("420x460")
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
        webbrowser.open("http://localhost:5000/emulator")

    emu_btn = tk.Button(emu_frame, text="🖥️ Launch Display Emulator", command=open_emulator, bg="#f9e2af", fg="#11111b", activebackground="#f5e0dc", font=("Helvetica", 9, "bold"), bd=0, padx=10, pady=6)
    emu_btn.pack(fill="x", padx=10, pady=8)

    # --- Device Setup Section ---
    setup_frame = tk.LabelFrame(root, text=" New Device Setup ", font=("Helvetica", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e", bd=1, relief="solid")
    setup_frame.pack(fill="x", padx=20, pady=5)

    def open_setup():
        webbrowser.open("http://localhost:5000/setup")

    setup_btn = tk.Button(setup_frame, text="🔌 Set Up New Device (WiFi)", command=open_setup, bg="#89b4fa", fg="#11111b", activebackground="#b4befe", font=("Helvetica", 9, "bold"), bd=0, padx=10, pady=6)
    setup_btn.pack(fill="x", padx=10, pady=8)

    # Status Footer
    status_lbl = tk.Label(root, text="Server running at http://0.0.0.0:5000 | Emulator at /emulator", font=("Helvetica", 8, "italic"), fg="#a6adc8", bg="#1e1e2e")
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
                webbrowser.open("http://localhost:5000/emulator")

            @rumps.clicked("🔌 Set Up New Device (WiFi)")
            def open_setup(self, _):
                webbrowser.open("http://localhost:5000/setup")

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
                webbrowser.open("http://localhost:5000/data")

            @rumps.clicked("Quit")
            def quit_app(self, _):
                rumps.quit_application()

        app = StatusBarApp()
        app.run()

if __name__ == '__main__':
    # Start Flask server in background thread
    t = Thread(target=start_flask, daemon=True)
    t.start()

    if len(sys.argv) > 1 and sys.argv[1] == "--server-only":
        print("[INFO] Running in server-only mode at http://localhost:5000")
        while True:
            time.sleep(1)
    else:
        # Launch macOS Status Bar App
        statusBarApp = TinyScreenMacStatusBarApp()
        statusBarApp.run()
