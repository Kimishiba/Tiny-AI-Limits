import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir

class CodexProvider(BaseProvider):
    provider_id = "codex"
    provider_name = "OpenAI Codex"
    badge = "CDX"
    color = "0x10A37F"  # OpenAI Emerald Green
    ttl_seconds = 120

    def _get_auth_file_path(self) -> Optional[str]:
        codex_home = os.environ.get("CODEX_HOME")
        if codex_home and os.path.exists(os.path.join(codex_home, "auth.json")):
            return os.path.join(codex_home, "auth.json")

        home = get_home_dir()
        candidates = [
            os.path.join(home, ".codex", "auth.json"),
            os.path.join(home, ".config", "codex", "auth.json"),
            os.path.join(os.environ.get("APPDATA", ""), "codex", "auth.json") if os.environ.get("APPDATA") else None,
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return None

    def _read_auth_credentials(self) -> Optional[Dict[str, Any]]:
        auth_file = self._get_auth_file_path()
        if not auth_file:
            return None
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        creds = self._read_auth_credentials()
        token = None
        account_id = None
        email = None

        if creds:
            token = creds.get("access_token") or creds.get("token") or creds.get("apiKey")
            account_id = creds.get("account_id") or creds.get("accountId")
            email = creds.get("email") or creds.get("user", {}).get("email")

        if not token:
            token = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")

        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unauthenticated",
                error_message="No auth.json found in ~/.codex or CODEX_HOME"
            )

        headers = {
            "Authorization": f"Bearer {token}",
        }
        if account_id:
            headers["ChatGPT-Account-Id"] = str(account_id)

        url = "https://chatgpt.com/backend-api/wham/usage"
        data, err = self.request_json("GET", url, headers, account_email=email)
        if err:
            return err

        try:
            rate_limit = data.get("rate_limit", {})
            plan_type = data.get("plan_type") or data.get("account_plan") or "Plus"

            pw_raw = rate_limit.get("primary_window") or {}
            pw_pct_left = pw_raw.get("percent_left")
            if pw_pct_left is None and "used_percent" in pw_raw:
                pw_pct_left = max(0, 100 - pw_raw["used_percent"])
            pw_pct_left = 100.0 if pw_pct_left is None else float(pw_pct_left)

            primary_window = RateWindow(
                limit=100,
                used=round(100.0 - pw_pct_left),
                remaining=round(pw_pct_left),
                percent_left=pw_pct_left,
                resets_at=pw_raw.get("reset_at") or pw_raw.get("resets_at"),
                window_minutes=pw_raw.get("window_minutes", 300),
                period_desc="5h"
            )

            secondary_window = None
            sw_raw = rate_limit.get("secondary_window")
            if sw_raw:
                sw_pct_left = sw_raw.get("percent_left")
                if sw_pct_left is None and "used_percent" in sw_raw:
                    sw_pct_left = max(0, 100 - sw_raw["used_percent"])
                sw_pct_left = 100.0 if sw_pct_left is None else float(sw_pct_left)

                secondary_window = RateWindow(
                    limit=100,
                    used=round(100.0 - sw_pct_left),
                    remaining=round(sw_pct_left),
                    percent_left=sw_pct_left,
                    resets_at=sw_raw.get("reset_at") or sw_raw.get("resets_at"),
                    window_minutes=sw_raw.get("window_minutes", 10080),
                    period_desc="weekly"
                )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                secondary_window=secondary_window,
                plan=str(plan_type).capitalize(),
                account_email=email,
                status="ok"
            )

        except Exception as e:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                account_email=email,
                status="error",
                error_message=str(e)
            )
