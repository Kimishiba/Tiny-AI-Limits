import os
import getpass
from flask import Blueprint, jsonify, send_file, request, current_app
from backend.services.zeroconf_svc import get_local_ip, get_host_label
from backend.services.firmware_cache import COMPANION_VERSION

bp = Blueprint("system", __name__)

PORT = 5000

def get_pair_id(cfg):
    """Stable per-install identifier used to pair a board to *this* companion."""
    if not isinstance(cfg, dict):
        return "tinyscreen-host"
    pair_id = cfg.get("pair_id")
    if pair_id:
        return str(pair_id)
    raw = f"{get_host_label()}-{getpass.getuser()}"
    clean = "".join(c if (c.isalnum() or c in "-_") else "_" for c in raw)[:24]
    return clean or "tinyscreen-host"

@bp.route('/setup/vendor/<path:filename>')
def serve_vendor_static(filename):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    vendor_dir = os.path.join(repo_root, "frontend", "vendor")
    safe_path = os.path.abspath(os.path.join(vendor_dir, filename))
    if not safe_path.startswith(vendor_dir) or not os.path.exists(safe_path):
        return "File not found", 404
    return send_file(safe_path)

@bp.route('/setup')
def serve_setup_page():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(repo_root, "frontend", "setup.html")
    if os.path.exists(path):
        return send_file(path)
    return "Setup page not found", 404

@bp.route('/')
@bp.route('/emulator')
@bp.route('/simulator')
@bp.route('/round')
def serve_emulator():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(repo_root, "emulator", "index.html")
    if os.path.exists(path):
        return send_file(path)
    return "Emulator file not found", 404

@bp.route('/whoami', methods=['GET'])
def whoami():
    cfg = current_app.config.get("COMPANION_CONFIG", {})
    return jsonify({
        "ip": get_local_ip(),
        "port": PORT,
        "pair_id": get_pair_id(cfg),
        "hostname": get_host_label(),
        "user": getpass.getuser(),
        "version": COMPANION_VERSION,
    })
