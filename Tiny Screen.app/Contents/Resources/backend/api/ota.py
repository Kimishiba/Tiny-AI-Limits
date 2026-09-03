import os
from flask import Blueprint, jsonify, send_file, request, current_app
from backend.services.firmware_cache import get_latest_firmware, arm_ota_trigger
from backend.api.config import client_is_local, caller_is_paired

bp = Blueprint("ota", __name__)

@bp.route('/firmware/version', methods=['GET'])
def firmware_version():
    fw_info = get_latest_firmware()
    return jsonify(fw_info)

@bp.route('/firmware/latest.bin', methods=['GET'])
def firmware_binary():
    fw_info = get_latest_firmware()
    bin_path = fw_info.get("path")
    if not bin_path or not os.path.exists(bin_path):
        return "Firmware binary not available", 404
    return send_file(
        bin_path,
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="firmware.bin"
    )

@bp.route('/api/ota/trigger', methods=['POST'])
def trigger_ota():
    if not (client_is_local() or caller_is_paired(allow_unpaired=False)):
        return jsonify({"status": "error", "message": "Access restricted to local callers or paired companion devices"}), 403
    arm_ota_trigger()
    fw_info = get_latest_firmware(force_check=True)
    return jsonify({
        "status": "ok",
        "message": "OTA update trigger armed for connected device",
        "target_version": fw_info.get("version", "0.5"),
        "target_tag": fw_info.get("tag", "firmware-v0.5")
    })
