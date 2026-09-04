import re
import hmac
from flask import Blueprint, jsonify, request, current_app
from backend.services.geocoding import geocode_city
from backend.services.agent_tracker import get_antigravity_accounts

bp = Blueprint("config", __name__)

def mask_key(val):
    if not val or not isinstance(val, str):
        return ""
    if len(val) <= 8:
        return "***"
    return f"{val[:4]}...{val[-4:]}"

def client_is_local():
    if request.remote_addr not in ("127.0.0.1", "::1", "localhost"):
        return False
    origin = request.headers.get("Origin")
    if origin and not any(h in origin for h in ("localhost", "127.0.0.1", "chrome-extension://")):
        return False
    return True

def caller_is_paired(allow_unpaired=True):
    cfg = current_app.config.get("COMPANION_CONFIG", {})
    if allow_unpaired and cfg.get("allow_unpaired_clients", False):
        return True
    
    pair_id = cfg.get("pair_id")
    if not pair_id:
        return True
    
    caller_pair = request.args.get("pair_id") or request.headers.get("X-Pair-ID", "")
    return hmac.compare_digest(str(caller_pair or ""), str(pair_id or ""))

@bp.route('/config', methods=['GET', 'POST'])
@bp.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    save_fn = current_app.config.get("SAVE_CONFIG_FN")
    config_lock = current_app.config.get("CONFIG_LOCK")
    cfg = current_app.config.get("COMPANION_CONFIG", {})

    if request.method == 'POST':
        if not (client_is_local() or caller_is_paired(allow_unpaired=False)):
            return jsonify({"status": "error", "message": "Access restricted to local callers or paired companion devices"}), 403
        data = request.json or {}
        
        if config_lock:
            config_lock.acquire()
        try:
            if "auto_location" in data:
                cfg["auto_location"] = bool(data["auto_location"])
            if "antigravity_5h_quota" in data:
                try:
                    cfg["antigravity_5h_quota"] = int(data["antigravity_5h_quota"])
                except (TypeError, ValueError):
                    return jsonify({"status": "error", "message": "antigravity_5h_quota must be an integer"}), 400
            if "antigravity_account_email" in data:
                cfg["antigravity_account_email"] = data["antigravity_account_email"] or None
            if "selected_gauges" in data and isinstance(data["selected_gauges"], dict):
                cfg.setdefault("selected_gauges", {})
                if "left" in data["selected_gauges"]:
                    cfg["selected_gauges"]["left"] = str(data["selected_gauges"]["left"])
                if "right" in data["selected_gauges"]:
                    cfg["selected_gauges"]["right"] = str(data["selected_gauges"]["right"])
            if "provider_keys" in data and isinstance(data["provider_keys"], dict):
                cfg.setdefault("provider_keys", {})
                for k, v in data["provider_keys"].items():
                    if v and re.match(r"^[a-zA-Z0-9_]{1,32}$", str(k)):
                        cfg["provider_keys"][str(k)] = str(v)[:256]
                        cfg[f"{k}_api_key"] = str(v)[:256]
            if "provider_plans" in data and isinstance(data["provider_plans"], dict):
                cfg.setdefault("provider_plans", {})
                for k, v in data["provider_plans"].items():
                    if re.match(r"^[a-zA-Z0-9_]{1,32}$", str(k)):
                        cfg["provider_plans"][str(k)] = str(v)[:64]
                        cfg[f"{k}_plan"] = str(v)[:64]
            if "claude_plan" in data:
                cfg["claude_plan"] = str(data["claude_plan"])
                cfg.setdefault("provider_plans", {})["claude"] = str(data["claude_plan"])
            if "antigravity_plan" in data:
                cfg["antigravity_plan"] = str(data["antigravity_plan"])
                cfg.setdefault("provider_plans", {})["antigravity"] = str(data["antigravity_plan"])

            if "provider_daily_budgets" in data and isinstance(data["provider_daily_budgets"], dict):
                cfg.setdefault("provider_daily_budgets", {})
                for k, v in data["provider_daily_budgets"].items():
                    try:
                        cfg["provider_daily_budgets"][str(k)] = float(v)
                        cfg[f"{k}_daily_budget_usd"] = float(v)
                    except (TypeError, ValueError):
                        pass
            if "claude_daily_budget_usd" in data:
                try:
                    cfg["claude_daily_budget_usd"] = float(data["claude_daily_budget_usd"])
                    cfg.setdefault("provider_daily_budgets", {})["claude"] = float(data["claude_daily_budget_usd"])
                except (TypeError, ValueError):
                    pass
            if "antigravity_daily_budget_usd" in data:
                try:
                    cfg["antigravity_daily_budget_usd"] = float(data["antigravity_daily_budget_usd"])
                    cfg.setdefault("provider_daily_budgets", {})["antigravity"] = float(data["antigravity_daily_budget_usd"])
                except (TypeError, ValueError):
                    pass

            if "led_waiting_anim" in data:
                anim = str(data["led_waiting_anim"]).lower().strip()
                if anim in {"breathe", "radar", "heartbeat", "hazard", "solid", "off"}:
                    cfg["led_waiting_anim"] = anim

            if "led_brightness" in data:
                try:
                    b = int(data["led_brightness"])
                    cfg["led_brightness"] = max(0, min(100, b))
                except (TypeError, ValueError):
                    return jsonify({"status": "error", "message": "led_brightness must be an integer between 0 and 100"}), 400

            if "led_active_count" in data:
                try:
                    c = int(data["led_active_count"])
                    cfg["led_active_count"] = max(1, min(32, c))
                except (TypeError, ValueError):
                    pass

            if "city" in data and data["city"]:
                lat, lon, full_name = geocode_city(data["city"])
                if lat and lon:
                    cfg["lat"] = lat
                    cfg["lon"] = lon
                    cfg["manual_location_name"] = full_name
                else:
                    return jsonify({"status": "error", "message": f"Could not find city '{data['city']}'"}), 400
            
            if save_fn:
                save_fn(cfg)

            masked_cfg = dict(cfg)
            if "provider_keys" in masked_cfg:
                masked_cfg["provider_keys"] = {k: mask_key(v) for k, v in masked_cfg["provider_keys"].items()}
            return jsonify({"status": "ok", "config": masked_cfg})
        finally:
            if config_lock:
                config_lock.release()

    if config_lock:
        config_lock.acquire()
    try:
        response = dict(cfg)
        if "provider_keys" in response:
            response["provider_keys"] = {k: mask_key(v) for k, v in response["provider_keys"].items()}
        response["available_antigravity_accounts"] = [a["email"] for a in get_antigravity_accounts()]
        return jsonify(response)
    finally:
        if config_lock:
            config_lock.release()
