import time
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from backend.services.geocoding import get_weather
from backend.services.firmware_cache import get_latest_firmware, pop_ota_trigger
from backend.api.config import caller_is_paired
import backend.services.agent_tracker as tracker
from backend.providers.base import format_reset_time

bp = Blueprint("telemetry", __name__)

@bp.route('/data', methods=['GET'])
def get_data():
    if not caller_is_paired():
        return jsonify({
            "error": "not_paired",
            "message": "This board is not paired with this companion app. "
                       "Run setup, or set allow_unpaired_clients in config.json.",
        }), 403

    poller = current_app.config.get("POLLER")
    cfg = current_app.config.get("COMPANION_CONFIG", {})

    antigravity_data = {"limit": 200, "used": 0, "remaining": 200, "period": "5h"}
    claude_data = {"tokens_today": 0, "limit": 100, "remaining": 100, "reset_str": "READY"}

    if poller:
        ag_provider = poller.providers.get("antigravity")
        if ag_provider and hasattr(ag_provider, "get_quota_dict"):
            try:
                antigravity_data = ag_provider.get_quota_dict(cfg)
            except Exception:
                pass
        
        cl_provider = poller.providers.get("claude")
        if cl_provider and hasattr(cl_provider, "scan_usage_dict"):
            try:
                claude_data = cl_provider.scan_usage_dict(cfg)
            except Exception:
                pass

    weather_data = get_weather(cfg)

    waiting_for_input = False
    work_completed = False
    prompt_text = "INPUT REQ"
    completion_text = "WORK COMPLETE"
    source = "none"

    if tracker.test_idle_override:
        waiting_for_input = False
        work_completed = False
        active_agents_payload = []
        has_active = False
        agent_state = "idle"
        source = "none"
    elif tracker.test_agents_override is not None:
        active_agents_payload = tracker.test_agents_override
        has_active = len(tracker.test_agents_override) > 0
        waiting_for_input = any(a.get("state") == "WAITING" for a in tracker.test_agents_override)
        work_completed = any(a.get("state") == "COMPLETE" for a in tracker.test_agents_override) and not waiting_for_input
        prompt_text = next((a.get("detail") for a in tracker.test_agents_override if a.get("state") == "WAITING"), "INPUT REQ")
        completion_text = next((a.get("detail") for a in tracker.test_agents_override if a.get("state") == "COMPLETE"), "WORK COMPLETE")
        agent_state = "waiting_approval" if waiting_for_input else ("completed" if work_completed else "working" if has_active else "idle")
        source = "test"
    elif tracker.test_alert_override:
        waiting_for_input = True
        prompt_text = tracker.test_alert_prompt
        source = "test"
    elif tracker.test_complete_override:
        work_completed = True
        completion_text = tracker.test_complete_prompt
        source = "test"
    else:
        multi_status = tracker.get_multi_agent_status(cfg)
        active_agents_payload = multi_status["agents"][:8]
        has_active = len(active_agents_payload) > 0
        waiting_session = next((s for s in multi_status["agents"] if s["state"] == "WAITING"), None)
        complete_session = next((s for s in multi_status["agents"] if s["state"] == "COMPLETE"), None)
        waiting_for_input = waiting_session is not None
        work_completed = complete_session is not None and not waiting_for_input
        prompt_text = waiting_session["detail"] if waiting_session else "INPUT REQ"
        completion_text = complete_session["detail"] if complete_session else "WORK COMPLETE"
        source = waiting_session["source"] if waiting_session else (complete_session["source"] if complete_session else "none")
        agent_state = "waiting_approval" if waiting_for_input else ("completed" if work_completed else ("working" if has_active else "idle"))

    now = datetime.now()
    trigger_ota = pop_ota_trigger()

    fw_info = get_latest_firmware()
    ota_payload = {
        "available": bool(fw_info.get("path") and fw_info.get("size", 0) > 0),
        "version": fw_info.get("version", "0.5"),
        "tag": fw_info.get("tag", "firmware-v0.5"),
        "trigger": trigger_ota,
        "url": "/firmware/latest.bin"
    }

    selected = cfg.get("selected_gauges", {"left": "claude", "right": "antigravity"})
    left_id = selected.get("left", "claude")
    right_id = selected.get("right", "antigravity")

    left_snap = poller.get_snapshot(left_id) if poller else None
    right_snap = poller.get_snapshot(right_id) if poller else None

    def build_gauge_payload(provider_id, snap, custom_data, default_color, default_label, default_name):
        provider_plans = cfg.get("provider_plans", {})
        plan = provider_plans.get(provider_id, cfg.get(f"{provider_id}_plan", "standard"))
        daily_budgets = cfg.get("provider_daily_budgets", {})
        daily_budget = float(daily_budgets.get(provider_id, cfg.get(f"{provider_id}_daily_budget_usd", 10.0)))

        label = default_label
        name = default_name
        color = default_color
        mode = "enterprise" if plan == "enterprise" else "standard"
        cost_str = ""
        tokens_str = ""
        cost_usd = 0.0
        percent = 100
        reset_str = "READY"

        if snap and snap.primary_window:
            label = snap.badge or default_label
            name = snap.provider_name or default_name
            color = snap.color or default_color
            if snap.primary_window.resets_at:
                _, reset_str = format_reset_time(snap.primary_window.resets_at)
            else:
                reset_str = snap.primary_window.period_desc or "READY"
            percent = int(round(snap.primary_window.percent_left))

        if custom_data:
            if "label" in custom_data: label = custom_data["label"]
            if "name" in custom_data: name = custom_data["name"]
            if "color" in custom_data: color = custom_data["color"]
            if "reset_str" in custom_data: reset_str = custom_data["reset_str"]
            if "percent" in custom_data: percent = custom_data["percent"]
            elif "remaining" in custom_data and "limit" in custom_data:
                lim = max(1, custom_data["limit"])
                rem = custom_data["remaining"]
                percent = int(round((rem / lim) * 100))
            if "cost_str" in custom_data: cost_str = custom_data["cost_str"]
            if "tokens_str" in custom_data: tokens_str = custom_data["tokens_str"]
            if "cost_today_usd" in custom_data: cost_usd = float(custom_data["cost_today_usd"])
            elif "cost_usd" in custom_data: cost_usd = float(custom_data["cost_usd"])

        if mode == "enterprise":
            if not cost_str:
                if custom_data and "cost_today_usd" in custom_data:
                    cost_usd = float(custom_data["cost_today_usd"])
                    cost_str = f"${cost_usd:.2f}"
                elif snap and hasattr(snap, "metadata") and snap.metadata and "cost_today_usd" in snap.metadata:
                    cost_usd = float(snap.metadata["cost_today_usd"])
                    cost_str = f"${cost_usd:.2f}"
                elif custom_data and "cost_usd" in custom_data:
                    cost_usd = float(custom_data["cost_usd"])
                    cost_str = f"${cost_usd:.2f}"
                else:
                    cost_str = "$0.00"

            if not tokens_str:
                if custom_data and "tokens_today" in custom_data:
                    tok = custom_data["tokens_today"]
                    tokens_str = f"{tok/1000:.1f}k" if tok >= 1000 else str(tok)
                elif snap and hasattr(snap, "metadata") and snap.metadata and "tokens_today" in snap.metadata:
                    tok = snap.metadata["tokens_today"]
                    tokens_str = f"{tok/1000:.1f}k" if tok >= 1000 else str(tok)
                else:
                    tokens_str = "0"

            if daily_budget > 0:
                pct_used = min(100, int(round((cost_usd / daily_budget) * 100)))
                percent = max(1, pct_used)
            else:
                percent = 100

            reset_str = f"{tokens_str} TOK"

        return {
            "id": provider_id,
            "label": label,
            "name": name,
            "color": color,
            "mode": mode,
            "cost_str": cost_str,
            "tokens_str": tokens_str,
            "cost_usd": cost_usd,
            "daily_budget_usd": daily_budget,
            "curved_text": f"{cost_str} SPENT" if cost_str else "",
            "percent": percent,
            "reset_str": reset_str
        }

    left_custom = claude_data if left_id == "claude" else (antigravity_data if left_id == "antigravity" else None)
    right_custom = antigravity_data if right_id == "antigravity" else (claude_data if right_id == "claude" else None)

    left_gauge = build_gauge_payload(left_id, left_snap, left_custom, "0x00E5FF", "CLD", "Claude")
    right_gauge = build_gauge_payload(right_id, right_snap, right_custom, "0xFF9100", "AGY", "Antigravity")

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

@bp.route('/api/providers', methods=['GET'])
def get_providers_api():
    cfg = current_app.config.get("COMPANION_CONFIG", {})
    poller = current_app.config.get("POLLER")
    selected = cfg.get("selected_gauges", {"left": "claude", "right": "antigravity"})
    providers_data = []
    if poller:
        for p in poller.providers.values():
            snap = poller.get_snapshot(p.provider_id)
            if not snap:
                try:
                    snap = p.fetch_usage(cfg)
                except Exception:
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
