from flask import Blueprint, jsonify, request, current_app
import backend.services.agent_tracker as tracker

bp = Blueprint("agents", __name__)

@bp.route('/api/agents', methods=['GET'])
def api_agents():
    cfg = current_app.config.get("COMPANION_CONFIG", {})
    return jsonify(tracker.get_multi_agent_status(cfg))

@bp.route('/api/hook', methods=['POST'])
def api_hook():
    payload = request.get_json(force=True, silent=True) or {}
    result = tracker.handle_hook_event(payload)
    if result is None:
        return jsonify({"status": "error", "message": "missing session_id"}), 400
    return jsonify(result), 200

@bp.route('/api/test_agents', methods=['POST'])
def api_test_agents():
    data = request.get_json(force=True, silent=True) or {}
    if data.get("reset"):
        tracker.test_agents_override = None
        return jsonify({"status": "ok", "message": "test_agents reset to live discovery"})

    agents_list = data.get("agents")
    if isinstance(agents_list, list):
        tracker.test_agents_override = agents_list
        return jsonify({"status": "ok", "message": f"test_agents set ({len(agents_list)} agents)", "agents": agents_list})

    return jsonify({"status": "error", "message": "provide {agents: [...]} or {reset: true}"}), 400

@bp.route('/api/test_idle', methods=['POST'])
def api_test_idle():
    data = request.get_json(force=True, silent=True) or {}
    tracker.test_idle_override = bool(data.get("active", False))
    return jsonify({"status": "ok", "test_idle_active": tracker.test_idle_override})

@bp.route('/api/test_alert', methods=['POST'])
def api_test_alert():
    data = request.get_json(force=True, silent=True) or {}
    tracker.test_alert_override = bool(data.get("active", False))
    if data.get("prompt"):
        tracker.test_alert_prompt = str(data.get("prompt"))
    return jsonify({
        "status": "ok",
        "test_alert_active": tracker.test_alert_override,
        "prompt": tracker.test_alert_prompt
    })

@bp.route('/api/test_complete', methods=['POST'])
def api_test_complete():
    data = request.get_json(force=True, silent=True) or {}
    tracker.test_complete_override = bool(data.get("active", False))
    if data.get("prompt"):
        tracker.test_complete_prompt = str(data.get("prompt"))
    return jsonify({
        "status": "ok",
        "test_complete_active": tracker.test_complete_override,
        "prompt": tracker.test_complete_prompt
    })
