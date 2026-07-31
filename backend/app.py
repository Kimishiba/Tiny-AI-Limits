import json
import glob
import os
import platform
import time
import subprocess
from flask import Flask, jsonify

app = Flask(__name__)

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
                    # Only look at recent files (last 7 days) to speed up scanning
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

@app.route('/limits', methods=['GET'])
def get_limits():
    # --- Fetch Antigravity Data via CLI ---
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
        print(f"Error fetching Antigravity data: {e}")
        antigravity_data = {
            "limit": 100,
            "remaining": 0
        }
    
    # --- Fetch Claude Data by scanning local logs ---
    try:
        used_tokens = scan_claude_tokens()
        # Since Claude doesn't expose a strict 'limit' without API, we can calculate a percentage
        # or set a fixed max limit that you typically hit (e.g. 500,000 tokens)
        claude_data = {
            "limit": 500000, 
            "remaining": max(0, 500000 - used_tokens)
        }
    except Exception as e:
        print(f"Error fetching Claude data: {e}")
        claude_data = {
            "limit": 500000,
            "remaining": 500000
        }
    
    return jsonify({
        "claude": claude_data,
        "antigravity": antigravity_data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
