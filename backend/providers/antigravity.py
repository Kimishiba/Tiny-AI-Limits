import os
import glob
import json
import time
import subprocess
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir

class AntigravityProvider(BaseProvider):
    provider_id = "antigravity"
    provider_name = "Google Antigravity"
    badge = "AGY"
    color = "0xFF9100"  # Orange
    ttl_seconds = 30

    def _find_language_servers(self) -> List[Tuple[int, str]]:
        """Find running Antigravity Language Server processes and their CSRF tokens."""
        results = []
        try:
            cmd = ["ps", "auxww"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            lines = res.stdout.splitlines()

            for line in lines:
                if "language_server" in line and ("--csrf_token=" in line or "--csrf_token" in line):
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    try:
                        pid = int(parts[1])
                    except ValueError:
                        continue

                    token = None
                    for token_part in line.split():
                        if token_part.startswith("--csrf_token="):
                            token = token_part.split("=", 1)[1]
                            break

                    if token:
                        results.append((pid, token))
        except Exception:
            pass

        return results

    def _get_listening_ports_for_pid(self, pid: int) -> List[int]:
        """Find TCP listening ports for the given PID using lsof or netstat."""
        ports = []
        try:
            cmd = ["lsof", "-aPi", "-p", str(pid), "-sTCP:LISTEN", "-Fn"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            for line in res.stdout.splitlines():
                if line.startswith("n*:") or line.startswith("n127.0.0.1:") or line.startswith("nlocalhost:"):
                    port_str = line.split(":")[-1]
                    try:
                        ports.append(int(port_str))
                    except ValueError:
                        pass
        except Exception:
            pass
        return ports

    def _query_live_rpc(self) -> Optional[Dict[str, Any]]:
        """Connect to local Language Server Connect RPC to query live quota & user status."""
        servers = self._find_language_servers()
        if not servers:
            return None

        for pid, token in servers:
            ports = self._get_listening_ports_for_pid(pid)
            for port in ports:
                try:
                    url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
                    headers = {
                        "Content-Type": "application/json",
                        "X-Csrf-Token": token,
                        "Connect-Protocol-Version": "1"
                    }
                    resp = requests.post(url, headers=headers, json={}, timeout=1.5)
                    if resp.status_code == 200:
                        return resp.json()
                except Exception:
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
                except Exception:
                    continue
        except Exception:
            pass

        return total_steps, total_sessions

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        # 1. Try real-time Connect RPC
        live_data = self._query_live_rpc()
        if live_data:
            user_status = live_data.get("userStatus", {})
            user_email = user_status.get("userEmail")
            models = live_data.get("models", [])
            
            gemini_quota = None
            for m in models:
                mid = m.get("modelId", "")
                if "gemini" in mid.lower():
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
