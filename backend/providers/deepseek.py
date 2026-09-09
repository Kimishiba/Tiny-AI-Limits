from typing import Dict, Any
from .base import GenericHttpProvider, RateWindow, UsageSnapshot

class DeepSeekProvider(GenericHttpProvider):
    provider_id = "deepseek"
    provider_name = "DeepSeek"
    badge = "DSK"
    color = "0x0288D1"  # Sky Blue
    ttl_seconds = 300
    token_key = "deepseek_api_key"
    env_var = "DEEPSEEK_API_KEY"
    url = "https://api.deepseek.com/user/balance"

    def parse_payload(self, data: Dict[str, Any]) -> UsageSnapshot:
        is_available = data.get("is_available", True)
        balance_infos = data.get("balance_infos", [])
        total_balance = 0.0
        currency = "USD"

        for info in balance_infos:
            currency = info.get("currency", "USD")
            total_balance += float(info.get("total_balance", 0.0))

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

