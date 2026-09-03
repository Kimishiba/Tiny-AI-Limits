import os
import glob
import json
import time
import re
import ssl
import socket
import subprocess
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir

logger = logging.getLogger("tinyscreen.providers.antigravity")

class AntigravityProvider(BaseProvider):
    provider_id = "antigravity"
    provider_name = "Google Antigravity"
    badge = "AGY"
    color = "0xFF9100"  # Orange
    ttl_seconds = 30

    def _find_language_servers(self) -> List[Dict[str, Any]]:
        """Find running Antigravity Language Server processes and their CSRF tokens and listening ports."""
        servers = []
        import sys
        if sys.platform.startswith("win"):
            try:
                ps_cmd = 'Get-CimInstance Win32_Process | Where-Object Name -like "*language_server*" | Select-Object ProcessId, CommandLine | ConvertTo-Json'
                output = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True, timeout=3)
                if not output.strip():
                    return servers
                data = json.loads(output)
                procs = [data] if isinstance(data, dict) else data

                netstat_out = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], text=True, stderr=subprocess.DEVNULL, timeout=3)
                for p in procs:
                    cmd = p.get("CommandLine") or ""
                    pid = p.get("ProcessId")
                    if not pid or not cmd:
                        continue
                    token_match = re.search(r"--csrf_token[= ]([a-zA-Z0-9-]+)", cmd)
                    if not token_match:
                        continue
                    csrf_token = token_match.group(1)

                    ports = []
                    for line in netstat_out.splitlines():
                        if "LISTENING" in line and str(pid) == line.strip().split()[-1]:
                            m = re.search(r"(?:127\.0\.0\.1|0\.0\.0\.0|\[::\]|\[::1\]):(\d+)", line)
                            if m:
                                ports.append(int(m.group(1)))
                    ports = sorted(set(ports))
                    if ports:
                        servers.append({"pid": str(pid), "csrf_token": csrf_token, "ports": ports})
            except Exception as e:
                logger.debug("Error finding language servers on Windows: %s", e)
            return servers

        try:
            ps_output = subprocess.check_output(
                ["ps", "aux"],
                text=True,
                timeout=2.0,
                stderr=subprocess.DEVNULL
            )
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError) as e:
            logger.debug("Failed executing ps to locate language server: %s", e)
            return servers

        for line in ps_output.splitlines():
            if "language_server" not in line:
                continue
            parts = line.split(None, 10)
            if len(parts) < 2 or not parts[1].isdigit():
                continue
            pid = parts[1]
            token_match = re.search(r"--csrf_token[= ]([a-zA-Z0-9_-]+)", line)
            if not token_match:
                continue
            csrf_token = token_match.group(1)
            if not re.match(r'^[a-zA-Z0-9_-]+$', csrf_token):
                continue

            try:
                lsof_output = subprocess.check_output(
                    ["lsof", "-a", "-p", pid, "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
                    text=True, stderr=subprocess.DEVNULL, timeout=2.0
                )
                ports = sorted(set(
                    int(m.group(1))
                    for m in re.finditer(r":(\d+)\s*\(LISTEN\)", lsof_output)
                    if 1024 <= int(m.group(1)) <= 65535
                ))
            except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError):
                ports = []

            if ports:
                servers.append({"pid": pid, "csrf_token": csrf_token, "ports": ports})

        return servers

    def _query_live_rpc(self) -> Optional[Dict[str, Any]]:
        """Connect to local Language Server Connect RPC to query live quota & user status."""
        servers = self._find_language_servers()
        if not servers:
            return None

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        payload = json.dumps({
            "metadata": {"ideName": "antigravity", "extensionName": "antigravity", "locale": "en"}
        }).encode("utf-8")

        for server in servers:
            token = server["csrf_token"]
            headers = {
                "Content-Type": "application/json",
                "Connect-Protocol-Version": "1",
                "User-Agent": "antigravity",
                "X-Codeium-Csrf-Token": token,
            }
            for port in server["ports"]:
                # Fast socket connectivity probe (200ms) to prevent blocking the poller
                try:
                    with socket.create_connection(('127.0.0.1', int(port)), timeout=0.2):
                        pass
                except (socket.timeout, socket.error, OSError, ConnectionRefusedError):
                    continue

                for scheme in ["https", "http"]:
                    url = f"{scheme}://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
                    try:
                        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                        with urllib.request.urlopen(req, context=ctx if scheme == "https" else None, timeout=2.0) as resp:
                            if resp.status == 200:
                                return json.loads(resp.read().decode("utf-8"))
                    except Exception as e:
                        logger.debug("Connect RPC %s on port %s failed: %s", scheme, port, e)
                        continue
        return None

    def _scan_antigravity_transcripts(self) -> Tuple[int, int]:
        """Scan local gemini/antigravity transcripts for recent 5h step usage."""
        home = get_home_dir()
        base_dir = os.path.join(home, ".gemini", "antigravity", "brain")
        if not os.path.exists(base_dir):
            return 0, 0

        five_hours_ago = time.time() - (5 * 3600)
        total_steps = 0
        total_sessions = 0

        try:
            for conv_dir in os.listdir(base_dir):
                conv_path = os.path.join(base_dir, conv_dir)
                if not os.path.isdir(conv_path):
                    continue
                transcript_file = os.path.join(conv_path, ".system_generated", "logs", "transcript.jsonl")
                if not os.path.exists(transcript_file):
                    continue

                try:
                    mtime = os.path.getmtime(transcript_file)
                    if mtime < five_hours_ago:
                        continue

                    session_has_recent = False
                    with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if '"type":"PLANNER_RESPONSE"' in line:
                                total_steps += 1
                                session_has_recent = True

                    if session_has_recent:
                        total_sessions += 1
                except (OSError, UnicodeDecodeError) as e:
                    logger.debug("Error reading transcript %s: %s", transcript_file, e)
                    continue
                except Exception as e:
                    logger.debug("Unexpected error reading transcript %s: %s", transcript_file, e)
                    continue
        except Exception as e:
            logger.debug("Error scanning transcripts in %s: %s", base_dir, e)

        return total_steps, total_sessions

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        # 1. Try real-time Connect RPC
        live_data = self._query_live_rpc()
        if live_data:
            user_status = live_data.get("userStatus", {})
            user_email = user_status.get("email") or user_status.get("userEmail")
            
            client_models = user_status.get("cascadeModelConfigData", {}).get("clientModelConfigs", [])
            if not client_models:
                client_models = live_data.get("models", [])

            gemini_quota = None
            for m in client_models:
                mid = (m.get("modelId") or m.get("label") or "").lower()
                if "gemini" in mid:
                    gemini_quota = m.get("quotaInfo")
                    if gemini_quota is not None:
                        break

            if gemini_quota is not None:
                rem_frac = gemini_quota.get("remainingFraction", 0.0)
                pct_left = float(round(rem_frac * 100.0, 1))
                reset_time = gemini_quota.get("resetTime")

                window_mins = 300
                period_desc = "5h"
                if reset_time:
                    try:
                        dt = datetime.fromisoformat(reset_time.replace("Z", "+00:00"))
                        secs_left = max(0, int(round(dt.timestamp() - time.time())))
                        hours = secs_left / 3600.0
                        if hours > 48:
                            period_desc = "weekly"
                            window_mins = 10080
                        elif hours > 6:
                            period_desc = "daily"
                            window_mins = 1440
                    except Exception:
                        pass

                primary_window = RateWindow(
                    limit=100,
                    used=round(100.0 - pct_left),
                    remaining=round(pct_left),
                    percent_left=pct_left,
                    resets_at=reset_time,
                    window_minutes=window_mins,
                    period_desc=period_desc
                )

                return UsageSnapshot(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    badge=self.badge,
                    color=self.color,
                    primary_window=primary_window,
                    account_email=user_email,
                    plan="Google Antigravity",
                    status="ok"
                )

        # 2. Fallback to local transcript heuristic
        steps, sessions = self._scan_antigravity_transcripts()
        quota_limit = config.get("antigravity_5h_quota", 200)
        remaining = max(0, quota_limit - steps)
        pct_left = float(round((remaining / quota_limit) * 100.0, 1)) if quota_limit > 0 else 100.0

        primary_window = RateWindow(
            limit=quota_limit,
            used=steps,
            remaining=remaining,
            percent_left=pct_left,
            period_desc="5h (local heuristic)"
        )

        return UsageSnapshot(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            badge=self.badge,
            color=self.color,
            primary_window=primary_window,
            credits={"steps_5h": steps, "active_sessions": sessions},
            plan="Local Transcripts",
            status="degraded" if steps > 0 else "ok"
        )
