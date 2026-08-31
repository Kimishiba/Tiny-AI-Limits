import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir, resolve_app_data_path, read_sqlite_kv_safe

class CursorProvider(BaseProvider):
    provider_id = "cursor"
    provider_name = "Cursor"
    badge = "CUR"
    color = "0x8A2BE2"  # Blue Violet
    ttl_seconds = 180

    def _find_cursor_state_db(self) -> Optional[str]:
        candidates = [
            resolve_app_data_path(os.path.join("User", "globalStorage", "state.vscdb"), "Cursor"),
            os.path.join(get_home_dir(), "Library", "Application Support", "Cursor", "User", "globalStorage", "state.vscdb"),
            os.path.join(get_home_dir(), ".config", "Cursor", "User", "globalStorage", "state.vscdb"),
        ]
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(os.path.join(appdata, "Cursor", "User", "globalStorage", "state.vscdb"))

        for c in candidates:
            if c and os.path.exists(c):
                return c
        return None

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        db_path = self._find_cursor_state_db()
        token = None
        if db_path:
            token = read_sqlite_kv_safe(db_path, "ItemTable", "key", "value", "cursorAuth/accessToken")

        if not token:
            token = config.get("cursor_token")

        if not token:
            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                status="unauthenticated",
                error_message="Cursor token not found in state.vscdb or config"
            )

        headers = {
            "Authorization": f"Bearer {token}",
        }

        url = "https://api2.cursor.sh/auth/usage"
        data, err = self.request_json("GET", url, headers)
        if err:
            return err

        try:
            gpt4 = data.get("gpt-4") or data.get("premiumUsage") or {}
            num_requests = gpt4.get("numRequests", 0)
            max_requests = gpt4.get("maxRequestUsage") or gpt4.get("limit") or 500

            remaining = max(0, max_requests - num_requests)
            pct_left = float(round((remaining / max_requests) * 100.0)) if max_requests > 0 else 0.0

            primary_window = RateWindow(
                limit=max_requests,
                used=num_requests,
                remaining=remaining,
                percent_left=pct_left,
                period_desc="monthly"
            )

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                plan="Pro" if max_requests >= 500 else "Free",
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
