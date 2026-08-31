import os
from typing import Dict, Any, Optional
from .base import BaseProvider, RateWindow, UsageSnapshot

class OpenRouterProvider(BaseProvider):
    provider_id = "openrouter"
    provider_name = "OpenRouter"
    badge = "OPR"
    color = "0x6A1B9A"  # Deep Purple
    ttl_seconds = 180

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        token = config.get("openrouter_api_key") or os.environ.get("OPENROUTER_API_KEY")
        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unconfigured",
                error_message="No openrouter_api_key found in config or OPENROUTER_API_KEY env"
            )

        headers = {
            "Authorization": f"Bearer {token}",
        }

        url = "https://openrouter.ai/api/v1/auth/key"
        data, err = self.request_json("GET", url, headers)
        if err:
            return err

        try:
            key_data = data.get("data", {})
            label = key_data.get("label", "Key")
            usage_usd = float(key_data.get("usage", 0.0))
            limit_usd = key_data.get("limit")
            is_free_tier = key_data.get("is_free_tier", False)

            if limit_usd is not None and float(limit_usd) > 0:
                limit_f = float(limit_usd)
                remaining_usd = max(0.0, limit_f - usage_usd)
                pct_left = float(round((remaining_usd / limit_f) * 100.0, 1))
                primary_window = RateWindow(
                    limit=round(limit_f),
                    used=round(usage_usd),
                    remaining=round(remaining_usd),
                    percent_left=pct_left,
                    period_desc="credit limit"
                )
            else:
                pct_left = 100.0
                primary_window = RateWindow(
                    limit=100,
                    used=0,
                    remaining=100,
                    percent_left=100.0,
                    period_desc="unlimited ($" + f"{usage_usd:.2f} spent)"
                )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                credits={"usage_usd": usage_usd, "limit_usd": limit_usd, "is_free_tier": is_free_tier},
                plan="Free Tier" if is_free_tier else "Paid",
                account_email=label,
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
