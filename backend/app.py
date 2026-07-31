import json
import glob
import os
import platform
import time
import subprocess
import requests
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# --- Weather Data Logic ---
def get_location():
    try:
        # Auto-detect location via IP
        res = requests.get('http://ip-api.com/json/', timeout=5)
        data = res.json()
        return data['lat'], data['lon']
    except:
        # Fallback to London if detection fails
        return 51.5074, -0.1278

def get_weather():
    lat, lon = get_location()
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation"
        res = requests.get(url, timeout=5)
        data = res.json()
        
        current_temp = data['current_weather']['temperature']
        
        # Calculate hours until next rain
        hours_until_rain = -1
        hourly_precip = data['hourly']['precipitation']
        
        # Open-Meteo returns hourly data starting from midnight today, we need to find the current hour index
        # A simple hack without parsing the ISO timestamp exactly is to assume we just look for the first non-zero precip 
        # in the next 24 hours. (For a robust implementation, you'd match the current_weather time).
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
            "date_string": datetime.now().strftime("%a %d %b").upper()
        }
    except Exception as e:
        print(f"Weather error: {e}")
        return {
            "temperature": 0.0,
            "hours_until_rain": -1,
            "date_string": "ERR"
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

@app.route('/data', methods=['GET'])
def get_data():
    # Fetch Antigravity Data
    try:
        result = subprocess.run(
            ['agy', '--print', 'What is my current usage and quota limit? Return ONLY a JSON object with "remaining" and "limit" integer keys.'],
            capture_output=True, 
            text=True
        )
        raw_output = result.stdout.strip()
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:-3].strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:-3].strip()
        antigravity_data = json.loads(raw_output)
    except Exception as e:
        antigravity_data = {"limit": 100, "remaining": 0}
    
    # Fetch Claude Data
    try:
        used_tokens = scan_claude_tokens()
        claude_data = {"limit": 500000, "remaining": max(0, 500000 - used_tokens)}
    except Exception as e:
        claude_data = {"limit": 500000, "remaining": 500000}
        
    # Fetch Weather
    weather_data = get_weather()
    
    return jsonify({
        "claude": claude_data,
        "antigravity": antigravity_data,
        "weather": weather_data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
