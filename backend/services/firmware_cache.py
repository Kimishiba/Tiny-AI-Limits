import os
import re
import time
import copy
import requests
import threading
import logging

logger = logging.getLogger("tinyscreen.services.firmware")

COMPANION_VERSION = "0.5.0"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".tiny_ai_screen")
FIRMWARE_CACHE_DIR = os.path.join(CONFIG_DIR, "firmware_cache")
os.makedirs(FIRMWARE_CACHE_DIR, exist_ok=True)

_ota_trigger_lock = threading.Lock()
_ota_trigger_requested = False
_firmware_cache_lock = threading.RLock()
_firmware_cache = {"version": "0.5", "tag": "firmware-v0.5", "path": None, "size": 0, "checked_at": 0}

def get_latest_firmware(force_check=False):
    global _firmware_cache
    with _firmware_cache_lock:
        now = time.time()
        if not force_check and _firmware_cache.get("path") and os.path.exists(_firmware_cache["path"]) and (now - _firmware_cache.get("checked_at", 0) < 600):
            return copy.deepcopy(_firmware_cache)

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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
                                safe_tag = re.sub(r"[^a-zA-Z0-9_.-]", "", tag)
                                if not safe_tag or ".." in safe_tag:
                                    continue
                                dest_path = os.path.abspath(os.path.join(FIRMWARE_CACHE_DIR, f"firmware_{safe_tag}.bin"))
                                if os.path.commonpath([FIRMWARE_CACHE_DIR, dest_path]) != FIRMWARE_CACHE_DIR:
                                    continue

                                if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
                                    tmp_dest = dest_path + f".tmp.{os.getpid()}"
                                    try:
                                        with requests.get(download_url, stream=True, timeout=20) as d_res:
                                            if d_res.status_code == 200:
                                                downloaded = 0
                                                with open(tmp_dest, "wb") as f:
                                                    for chunk in d_res.iter_content(chunk_size=65536):
                                                        if not chunk:
                                                            continue
                                                        downloaded += len(chunk)
                                                        if downloaded > 4 * 1024 * 1024:  # 4MB flash limit
                                                            raise ValueError("Firmware exceeds 4MB limit")
                                                        f.write(chunk)
                                                os.replace(tmp_dest, dest_path)
                                    except Exception as dl_err:
                                        logger.debug("Failed downloading firmware: %s", dl_err)
                                        if os.path.exists(tmp_dest):
                                            try:
                                                os.remove(tmp_dest)
                                            except Exception:
                                                pass
                                if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                                    _firmware_cache = {
                                        "version": ver_clean,
                                        "tag": tag,
                                        "path": dest_path,
                                        "size": os.path.getsize(dest_path),
                                        "checked_at": now
                                    }
                                    return copy.deepcopy(_firmware_cache)
        except Exception as e:
            logger.debug("GitHub release check warning: %s", e)

        if os.path.exists(local_bin) and os.path.getsize(local_bin) > 0:
            _firmware_cache = {
                "version": "0.5",
                "tag": "firmware-v0.5",
                "path": local_bin,
                "size": os.path.getsize(local_bin),
                "checked_at": now
            }
            return copy.deepcopy(_firmware_cache)

        return copy.deepcopy(_firmware_cache)

def arm_ota_trigger():
    global _ota_trigger_requested
    with _ota_trigger_lock:
        _ota_trigger_requested = True

def pop_ota_trigger():
    global _ota_trigger_requested
    with _ota_trigger_lock:
        triggered = _ota_trigger_requested
        _ota_trigger_requested = False
        return triggered
