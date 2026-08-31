import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir, resolve_app_data_path

class CopilotProvider(BaseProvider):
    provider_id = "copilot"
    provider_name = "GitHub Copilot"
    badge = "COP"
    color = "0x2EA44F"  # GitHub Green
    ttl_seconds = 300

    def _find_copilot_token(self) -> Optional[str]:
        home = get_home_dir()
        candidates = [
            os.path.join(home, ".config", "github-copilot", "hosts.json"),
            os.path.join(home, ".config", "github-copilot", "apps.json"),
            resolve_app_data_path("hosts.json", "github-copilot"),
        ]
        appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if appdata:
            candidates.append(os.path.join(appdata, "github-copilot", "hosts.json"))

        for c in candidates:
            if c and os.path.exists(c):
                try:
                    with open(c, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for host, info in data.items():
                            if isinstance(info, dict) and ("oauth_token" in info or "token" in info):
                                return info.get("oauth_token") or info.get("token")
                except Exception:
                    continue

        return os.environ.get("COPILOT_TOKEN") or os.environ.get("GITHUB_TOKEN")

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        token = self._find_copilot_token() or config.get("copilot_token")
        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unauthenticated",
                error_message="GitHub Copilot token not found in hosts.json or config"
            )

        headers = {
            "Authorization": f"token {token}",
            "Editor-Version": "TinyAILimits/1.0",
        }

        url = "https://api.github.com/copilot_internal/user"
        data, err = self.request_json("GET", url, headers)
        if err:
            return err

        try:
            plan = data.get("copilot_plan") or data.get("access_type_sku") or "Individual"
            login_user = data.get("login") or data.get("user")

            primary_window = RateWindow(
                limit=100,
                used=0,
                remaining=100,
                percent_left=100.0,
                period_desc="active"
            )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                plan=str(plan).replace("copilot_for_", "").capitalize(),
                account_email=login_user,
                status="ok"
            )

        except Exception as e:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="error",
                error_message=str(e)
            )
