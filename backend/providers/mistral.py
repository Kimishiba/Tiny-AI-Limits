import os
from typing import Dict, Any, Optional
from .base import BaseProvider, RateWindow, UsageSnapshot

class MistralProvider(BaseProvider):
    provider_id = "mistral"
    provider_name = "Mistral AI / Codestral"
    badge = "MST"
    color = "0xFF7043"  # Deep Orange
    ttl_seconds = 300

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        token = config.get("mistral_api_key") or os.environ.get("MISTRAL_API_KEY")
        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unconfigured",
                error_message="No mistral_api_key found in config or MISTRAL_API_KEY env"
            )

        headers = {
            "Authorization": f"Bearer {token}",
        }

        url = "https://api.mistral.ai/v1/models"
        data, err = self.request_json("GET", url, headers)
        if err:
            return err

        try:
            # Mistral API models endpoint confirms authenticated tier
            primary_window = RateWindow(
                limit=100,
                used=0,
                remaining=100,
                percent_left=100.0,
                period_desc="active plan"
            )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                plan="Mistral API",
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
