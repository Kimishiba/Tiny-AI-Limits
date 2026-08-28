import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir, resolve_app_data_path

class ClaudeProvider(BaseProvider):
    provider_id = "claude"
    provider_name = "Anthropic Claude"
    badge = "CLD"
    color = "0x00E5FF"  # Cyan
    ttl_seconds = 60

    def _read_oauth_token(self) -> Optional[Dict[str, Any]]:
        home = get_home_dir()
        candidates = [
            os.path.join(home, ".claude", ".credentials.json"),
            os.path.join(home, ".claude", "credentials.json"),
            os.path.join(home, ".config", "claude", "credentials.json"),
            resolve_app_data_path("credentials.json", "claude"),
        ]

        for p in candidates:
            if not p or not os.path.exists(p):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "claudeAiOauth" in data and isinstance(data["claudeAiOauth"], dict):
                        return data["claudeAiOauth"]
                    if "access_token" in data or "token" in data or "accessToken" in data:
                        return data
            except Exception:
                continue
        return None

    def _scan_claude_dirs(self) -> List[str]:
        dirs = []
        home = get_home_dir()
        dirs.append(os.path.join(home, ".claude"))
        dirs.append(os.path.join(home, ".config", "claude"))
        dirs.append(resolve_app_data_path("", "claude-code"))
        return [d for d in dirs if d and os.path.exists(d)]

    def _scan_tokens_today(self) -> int:
        total_tokens = 0
        today_local = datetime.now().date()
        two_days_ago = time.time() - (2 * 86400)
        skip_dirs = {"cache", "gpucache", "code cache", "blob_storage", "node_modules", "logs", "session storage", "dist", ".git"}

        for c_dir in self._scan_claude_dirs():
            base_depth = c_dir.rstrip(os.sep).count(os.sep)
            for root, dirs, files in os.walk(c_dir):
                if root.rstrip(os.sep).count(os.sep) - base_depth > 4:
                    dirs.clear()
                    continue
                dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
                for file in files:
                    if not file.endswith(".jsonl"):
                        continue
                    filepath = os.path.join(root, file)
                    try:
                        if os.path.getmtime(filepath) < two_days_ago:
                            continue
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    entry = json.loads(line)
                                except Exception:
                                    continue
                                if entry.get("type") != "assistant":
                                    continue
                                ts = entry.get("timestamp")
                                if not ts:
                                    continue
                                try:
                                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
                                except Exception:
                                    continue
                                if dt.date() != today_local:
                                    continue
                                usage = (entry.get("message") or {}).get("usage") or {}
                                total_tokens += usage.get("input_tokens", 0) or 0
                                total_tokens += usage.get("output_tokens", 0) or 0
                                total_tokens += usage.get("cache_creation_input_tokens", 0) or 0
                    except Exception:
                        pass
        return total_tokens

    def _local_fallback_snapshot(self, tokens_today: int, error_message: str) -> UsageSnapshot:
        return UsageSnapshot(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            badge=self.badge,
            color=self.color,
            primary_window=RateWindow(
                limit=500000,
                used=tokens_today,
                remaining=max(0, 500000 - tokens_today),
                percent_left=max(0.0, min(100.0, 100.0 - (tokens_today / 5000))),
                period_desc="today (local)"
            ),
            credits={"tokens_today": tokens_today},
            plan="Claude Local",
            status="degraded" if tokens_today > 0 else "ok",
            error_message=error_message
        )

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        oauth = self._read_oauth_token()
        token = (oauth.get("accessToken") or oauth.get("access_token") or oauth.get("token")) if oauth else None

        if not token:
            token = config.get("claude_api_key") or os.environ.get("ANTHROPIC_API_KEY")

        tokens_today = self._scan_tokens_today()

        if not token:
            return self._local_fallback_snapshot(tokens_today, "OAuth credentials not found, showing local transcript tokens")

        headers = {
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
        }

        url = "https://api.anthropic.com/api/oauth/usage"
        data, err = self.request_json("GET", url, headers)
        if err:
            return self._local_fallback_snapshot(tokens_today, f"API error: {err.error_message}; showing local tokens")

        try:
            pw_raw = data.get("five_hour") or {}
            pw_used = float(pw_raw.get("utilization", 0.0)) * 100.0 if "utilization" in pw_raw else float(pw_raw.get("used_percent", 0.0))
            pw_pct_left = max(0.0, min(100.0, 100.0 - pw_used))

            primary_window = RateWindow(
                limit=100,
                used=round(pw_used),
                remaining=round(pw_pct_left),
                percent_left=pw_pct_left,
                resets_at=pw_raw.get("resets_at") or pw_raw.get("reset_at"),
                window_minutes=300,
                period_desc="5h"
            )

            secondary_window = None
            sw_raw = data.get("seven_day")
            if sw_raw:
                sw_used = float(sw_raw.get("utilization", 0.0)) * 100.0 if "utilization" in sw_raw else float(sw_raw.get("used_percent", 0.0))
                sw_pct_left = max(0.0, min(100.0, 100.0 - sw_used))
                secondary_window = RateWindow(
                    limit=100,
                    used=round(sw_used),
                    remaining=round(sw_pct_left),
                    percent_left=sw_pct_left,
                    resets_at=sw_raw.get("resets_at") or sw_raw.get("reset_at"),
                    window_minutes=10080,
                    period_desc="weekly"
                )

            plan_str = data.get("subscriptionType") or data.get("rate_limit_tier") or "Pro"

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                secondary_window=secondary_window,
                credits={"tokens_today": tokens_today},
                plan=str(plan_str).capitalize(),
                status="ok"
            )

        except Exception as e:
            return self._local_fallback_snapshot(tokens_today, str(e))
