import os
from typing import Dict, Any, Optional
from .base import BaseProvider, RateWindow, UsageSnapshot

class DeepSeekProvider(BaseProvider):
    provider_id = "deepseek"
    provider_name = "DeepSeek"
    badge = "DSK"
    color = "0x0288D1"  # Sky Blue
    ttl_seconds = 300

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        token = config.get("deepseek_api_key") or os.environ.get("DEEPSEEK_API_KEY")
        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unconfigured",
                error_message="No deepseek_api_key found in config or DEEPSEEK_API_KEY env"
            )

        headers = {
            "Authorization": f"Bearer {token}",
        }

        url = "https://api.deepseek.com/user/balance"
        data, err = self.request_json("GET", url, headers)
        if err:
            return err

        try:
            is_available = data.get("is_available", True)
            balance_infos = data.get("balance_infos", [])
            total_balance = 0.0
            currency = "USD"

            for info in balance_infos:
                currency = info.get("currency", "USD")
                total_balance += float(info.get("total_balance", 0.0))

            # Scale display: 100% if available and balance > $5, percentage down to 0 if $0
            pct_left = 100.0 if total_balance >= 5.0 else max(0.0, float(round((total_balance / 5.0) * 100.0, 1)))

            primary_window = RateWindow(
                limit=100,
                used=round(100.0 - pct_left),
                remaining=round(pct_left),
                percent_left=pct_left,
                period_desc=f"{total_balance:.2f} {currency}"
            )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                credits={"total_balance": total_balance, "currency": currency},
                plan="Prepaid",
                status="ok" if is_available else "degraded"
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
