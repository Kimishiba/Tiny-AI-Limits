import json
import glob
import os
import platform
import time
import subprocess
import requests
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread

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
        "antigravity_5h_quota": 200
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

def get_weather():
    lat, lon, loc_name = get_location()
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation"
        res = requests.get(url, timeout=5)
        data = res.json()
        
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

        return {
            "temperature": current_temp,
            "hours_until_rain": hours_until_rain,
            "date_string": datetime.now().strftime("%a %d %b").upper(),
            "location_name": loc_name
        }
    except Exception as e:
        print(f"Weather error: {e}")
        return {
            "temperature": 0.0,
            "hours_until_rain": -1,
            "date_string": "ERR",
            "location_name": "UNKNOWN"
        }

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

def scan_claude_tokens():
    total_tokens = 0
    now = time.time()
    for c_dir in get_claude_dirs():
        patterns = [
            os.path.join(c_dir, "*.jsonl"),
            os.path.join(c_dir, "**", "*.jsonl"),
            os.path.join(c_dir, "**", "*.json"),
        ]
        for pattern in patterns:
            for filepath in glob.glob(pattern, recursive=True):
                try:
                    if os.path.getmtime(filepath) < (now - 7 * 86400):
                        continue
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if "tokens" in line.lower() or "outputTokens" in line:
                                try:
                                    data = json.loads(line)
                                    if isinstance(data, dict):
                                        usage = data.get("usage", {}) or data.get("token_usage", {})
                                        in_tok = usage.get("input_tokens", 0) or data.get("input_tokens", 0) or data.get("inputTokens", 0)
                                        out_tok = usage.get("output_tokens", 0) or data.get("output_tokens", 0) or data.get("outputTokens", 0)
                                        total_tokens += (in_tok + out_tok)
                                except Exception:
                                    pass
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
    five_hours_ago = now - (5 * 3600)

    brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    if os.path.exists(brain_dir):
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

# --- Flask Endpoints ---
@app.route('/data', methods=['GET'])
def get_data():
    try:
        antigravity_data = scan_antigravity_5h_limits()
    except Exception as e:
        print(f"Antigravity scan error: {e}")
        antigravity_data = {"limit": 200, "used": 0, "remaining": 200, "period": "5h"}
    
    try:
        used_tokens = scan_claude_tokens()
        claude_data = {"limit": 500000, "remaining": max(0, 500000 - used_tokens)}
    except Exception:
        claude_data = {"limit": 500000, "remaining": 500000}
        
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

            if latest_transcript and (time.time() - latest_mod) < 180:
                with open(latest_transcript, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    if lines:
                        last_steps = [json.loads(l) for l in lines[-3:] if l.strip()]
                        for step in reversed(last_steps):
                            for tc in step.get("tool_calls", []):
                                if tc.get("name") == "ask_question":
                                    waiting_for_input = True
                                    prompt_text = "ANSWER Q"
                                    break
                                args = tc.get("arguments", {})
                                if isinstance(args, dict):
                                    meta = args.get("ArtifactMetadata", {})
                                    if meta.get("RequestFeedback") is True:
                                        waiting_for_input = True
                                        prompt_text = "APPROVE PLAN"
                                        break
                            if waiting_for_input:
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

def start_flask():
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
