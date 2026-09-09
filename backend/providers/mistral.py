from typing import Dict, Any
from .base import GenericHttpProvider, RateWindow, UsageSnapshot

class MistralProvider(GenericHttpProvider):
    provider_id = "mistral"
    provider_name = "Mistral AI / Codestral"
    badge = "MST"
    color = "0xFF7043"  # Deep Orange
    ttl_seconds = 300
    token_key = "mistral_api_key"
    env_var = "MISTRAL_API_KEY"
    url = "https://api.mistral.ai/v1/models"

    def parse_payload(self, data: Dict[str, Any]) -> UsageSnapshot:
        return UsageSnapshot(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            badge=self.badge,
            color=self.color,
            primary_window=RateWindow(
                limit=100,
                used=0,
                remaining=100,
                percent_left=100.0,
                period_desc="active plan"
            ),
            plan="Mistral API",
            status="ok"
        )

