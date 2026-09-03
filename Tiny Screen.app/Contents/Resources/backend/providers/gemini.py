import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir, resolve_app_data_path

class GeminiProvider(BaseProvider):
    provider_id = "gemini"
    provider_name = "Google Gemini CLI"
    badge = "GEM"
    color = "0x4285F4"  # Google Blue
    ttl_seconds = 180

    def _find_gemini_oauth_creds(self) -> Optional[Dict[str, Any]]:
        home = get_home_dir()
        candidates = [
            os.path.join(home, ".gemini", "oauth_creds.json"),
            os.path.join(home, ".config", "gemini", "oauth_creds.json"),
            resolve_app_data_path("oauth_creds.json", "gemini"),
        ]

        for c in candidates:
            if c and os.path.exists(c):
                try:
                    with open(c, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue
        return None

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        creds = self._find_gemini_oauth_creds()
        token = None
        if creds:
            token = creds.get("access_token") or creds.get("token")

        if not token:
            token = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")

        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unauthenticated",
                error_message="Gemini credentials not found in ~/.gemini or config"
            )

        headers = {
            "Authorization": f"Bearer {token}",
        }

        url = "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota"
        data, err = self.request_json("POST", url, headers, json_data={})
        if err:
            return err

        try:
            models = data.get("models", [])
            primary_model = None
            for m in models:
                if "gemini-2.5" in m.get("modelId", "").lower() or "gemini-1.5" in m.get("modelId", "").lower():
                    primary_model = m
                    break
            if not primary_model and models:
                primary_model = models[0]

            quota_info = (primary_model or {}).get("quotaInfo") or {}
            rem_frac = quota_info.get("remainingFraction")
            rem_frac = 1.0 if rem_frac is None else float(rem_frac)
            pct_left = float(round(rem_frac * 100.0, 1))

            primary_window = RateWindow(
                limit=100,
                used=round(100.0 - pct_left),
                remaining=round(pct_left),
                percent_left=pct_left,
                resets_at=quota_info.get("resetTime"),
                period_desc="daily"
            )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                plan="Google Cloud Code",
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
