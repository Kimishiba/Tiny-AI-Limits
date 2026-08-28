import os
import requests
from typing import Dict, Any, Optional
from .base import BaseProvider, RateWindow, UsageSnapshot

class GroqProvider(BaseProvider):
    provider_id = "groq"
    provider_name = "Groq"
    badge = "GRQ"
    color = "0xF55036"  # Groq Orange-Red
    ttl_seconds = 300

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        token = config.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unconfigured",
                error_message="No groq_api_key found in config or GROQ_API_KEY env"
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "TinyAILimits/1.0 (ESP32-Companion; +https://github.com/Kimishiba/Tiny-AI-Limits)",
        }

        try:
            resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5.0)
            if resp.status_code in (401, 403):
                return UsageSnapshot(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    badge=self.badge,
                    color=self.color,
                    status="unauthenticated",
                    error_message=f"HTTP {resp.status_code}: Invalid Groq API key"
                )

            if resp.status_code == 429:
                return UsageSnapshot(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    badge=self.badge,
                    color=self.color,
                    primary_window=RateWindow(limit=100, used=100, remaining=0, percent_left=0.0, period_desc="rate-limited"),
                    status="degraded",
                    error_message="HTTP 429: Rate limit exceeded"
                )

            if resp.status_code != 200:
                return UsageSnapshot(
                    provider_id=self.provider_id,
                    provider_name=self.provider_name,
                    badge=self.badge,
                    color=self.color,
                    status="error",
                    error_message=f"HTTP {resp.status_code}: {resp.text[:120]}"
                )

            # Check Groq Rate Limit Headers
            rem_req = resp.headers.get("x-ratelimit-remaining-requests")
            lim_req = resp.headers.get("x-ratelimit-limit-requests")
            rem_tok = resp.headers.get("x-ratelimit-remaining-tokens")
            lim_tok = resp.headers.get("x-ratelimit-limit-tokens")

            pct_left = 100.0
            if rem_req and lim_req and float(lim_req) > 0:
                pct_left = float(round((float(rem_req) / float(lim_req)) * 100.0, 1))

            primary_window = RateWindow(
                limit=int(lim_req) if lim_req else 100,
                used=int(lim_req) - int(rem_req) if lim_req and rem_req else 0,
                remaining=int(rem_req) if rem_req else 100,
                percent_left=pct_left,
                period_desc="minute rate limit"
            )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                credits={"remaining_tokens": rem_tok, "limit_tokens": lim_tok},
                plan="Groq Cloud",
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
