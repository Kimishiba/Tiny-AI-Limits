import os
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from .base import BaseProvider, RateWindow, UsageSnapshot, get_home_dir, resolve_app_data_path

# Anthropic Pricing per 1M tokens ($)
CLAUDE_MODEL_PRICING = {
    "sonnet": {"in": 3.00, "out": 15.00, "cache_write": 3.75, "cache_read": 0.30},
    "haiku":  {"in": 0.80, "out": 4.00,  "cache_write": 1.00, "cache_read": 0.08},
    "opus":   {"in": 15.00, "out": 75.00, "cache_write": 18.75, "cache_read": 1.50},
}

def resolve_model_pricing(model_name: Optional[str]) -> Dict[str, float]:
    if not model_name:
        return CLAUDE_MODEL_PRICING["sonnet"]
    m_lower = model_name.lower()
    if "haiku" in m_lower:
        return CLAUDE_MODEL_PRICING["haiku"]
    elif "opus" in m_lower:
        return CLAUDE_MODEL_PRICING["opus"]
    else:
        return CLAUDE_MODEL_PRICING["sonnet"]

def format_token_count(tokens: int) -> str:
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M".replace(".0M", "M")
    elif tokens >= 1_000:
        return f"{tokens / 1_000:.1f}k".replace(".0k", "k")
    else:
        return str(tokens)

class ClaudeProvider(BaseProvider):
    provider_id = "claude"
    provider_name = "Anthropic Claude"
    badge = "CLD"
    color = "0x00E5FF"  # Cyan
    ttl_seconds = 30

    def _read_oauth_token(self) -> Optional[Dict[str, Any]]:
        home = get_home_dir()
        candidates = [
            os.path.join(home, ".claude", ".credentials.json"),
            os.path.join(home, ".claude", "credentials.json"),
            os.path.join(home, ".config", "claude", "credentials.json"),
            resolve_app_data_path("credentials.json", "claude"),
        ]

        for p in candidates:
            if not p or not os.path.exists(p):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "claudeAiOauth" in data and isinstance(data["claudeAiOauth"], dict):
                        return data["claudeAiOauth"]
                    if "access_token" in data or "token" in data or "accessToken" in data:
                        return data
            except Exception:
                continue
        return None

    def _scan_claude_dirs(self) -> List[str]:
        dirs = []
        home = get_home_dir()
        dirs.append(os.path.join(home, ".claude"))
        dirs.append(os.path.join(home, ".config", "claude"))
        dirs.append(resolve_app_data_path("", "claude-code"))
        return [d for d in dirs if d and os.path.exists(d)]

    def scan_usage_detailed(self) -> Dict[str, Any]:
        """Scan local Claude transcripts for 24h and today's token volume and USD cost."""
        now_ts = time.time()
        five_hours_ago = now_ts - (5 * 3600)
        twenty_four_hours_ago = now_ts - 86400
        two_days_ago = now_ts - (2 * 86400)
        today_local = datetime.now().date()

        tokens_today = 0
        tokens_24h = 0
        cost_today = 0.0
        cost_24h = 0.0
        earliest_5h_ts = None

        skip_dirs = {"cache", "gpucache", "code cache", "blob_storage", "node_modules", "logs", "session storage", "dist", ".git"}

        for c_dir in self._scan_claude_dirs():
            base_depth = c_dir.rstrip(os.sep).count(os.sep)
            for root, dirs, files in os.walk(c_dir):
                if root.rstrip(os.sep).count(os.sep) - base_depth > 4:
                    dirs.clear()
                    continue
                dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
                for file in files:
                    if not file.endswith(".jsonl"):
                        continue
                    filepath = os.path.join(root, file)
                    try:
                        if os.path.getmtime(filepath) < two_days_ago:
                            continue
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    entry = json.loads(line)
                                except Exception:
                                    continue
                                if entry.get("type") != "assistant":
                                    continue
                                ts = entry.get("timestamp")
                                if not ts:
                                    continue
                                try:
                                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                    step_ts = dt.timestamp()
                                except Exception:
                                    continue

                                msg = entry.get("message") or {}
                                model = msg.get("model") or entry.get("model")
                                usage = msg.get("usage") or {}
                                inp = usage.get("input_tokens", 0) or 0
                                out = usage.get("output_tokens", 0) or 0
                                cw = usage.get("cache_creation_input_tokens", 0) or 0
                                cr = usage.get("cache_read_input_tokens", 0) or 0

                                rates = resolve_model_pricing(model)
                                step_cost = (inp * rates["in"] + out * rates["out"] + cw * rates["cache_write"] + cr * rates["cache_read"]) / 1_000_000.0
                                step_toks = inp + out + cw

                                if step_ts >= five_hours_ago:
                                    if earliest_5h_ts is None or step_ts < earliest_5h_ts:
                                        earliest_5h_ts = step_ts

                                if step_ts >= twenty_four_hours_ago:
                                    tokens_24h += step_toks
                                    cost_24h += step_cost

                                if dt.astimezone().date() == today_local:
                                    tokens_today += step_toks
                                    cost_today += step_cost
                    except Exception:
                        pass

        resets_at = None
        if earliest_5h_ts is not None:
            reset_ts = earliest_5h_ts + (5 * 3600)
            resets_at = datetime.fromtimestamp(reset_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "tokens_today": tokens_today,
            "tokens_24h": tokens_24h,
            "cost_today_usd": round(cost_today, 2),
            "cost_24h_usd": round(cost_24h, 2),
            "cost_str": f"${cost_today:.2f}",
            "tokens_str": format_token_count(tokens_today),
            "resets_at": resets_at,
            "earliest_5h_ts": earliest_5h_ts
        }

    def _scan_tokens_today(self) -> int:
        return self.scan_usage_detailed()["tokens_today"]

    def _local_fallback_snapshot(self, detailed: Dict[str, Any], config: Dict[str, Any], error_message: str) -> UsageSnapshot:
        plan_mode = config.get("claude_plan", "standard") if isinstance(config, dict) else "standard"
        if plan_mode == "enterprise":
            daily_budget = float(config.get("claude_daily_budget_usd", 10.0))
            cost_today = detailed["cost_today_usd"]
            pct_used = min(100.0, (cost_today / max(0.01, daily_budget)) * 100.0)
            pct_left = max(0.0, 100.0 - pct_used)
            tokens_str = detailed["tokens_str"]
            cost_str = detailed["cost_str"]

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=RateWindow(
                    limit=round(daily_budget),
                    used=round(cost_today),
                    remaining=round(max(0.0, daily_budget - cost_today)),
                    percent_left=pct_left,
                    period_desc=f"{tokens_str} TOK"
                ),
                credits={
                    "plan": "enterprise",
                    "cost_today_usd": cost_today,
                    "cost_24h_usd": detailed["cost_24h_usd"],
                    "cost_str": cost_str,
                    "tokens_today": detailed["tokens_today"],
                    "tokens_24h": detailed["tokens_24h"],
                    "tokens_str": tokens_str,
                    "daily_budget_usd": daily_budget,
                    "curved_text": f"{cost_str} SPENT"
                },
                plan="Enterprise",
                status="ok",
                error_message=error_message
            )

        # Standard quota fallback
        tokens_today = detailed["tokens_today"]
        return UsageSnapshot(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            badge=self.badge,
            color=self.color,
            primary_window=RateWindow(
                limit=500000,
                used=tokens_today,
                remaining=max(0, 500000 - tokens_today),
                percent_left=max(0.0, min(100.0, 100.0 - (tokens_today / 5000))),
                resets_at=detailed.get("resets_at"),
                period_desc="today (local)"
            ),
            credits={"tokens_today": tokens_today},
            plan="Claude Local",
            status="degraded" if tokens_today > 0 else "ok",
            error_message=error_message
        )

    def fetch_usage(self, config: Dict[str, Any]) -> UsageSnapshot:
        detailed = self.scan_usage_detailed()
        plan_mode = config.get("claude_plan", "standard") if isinstance(config, dict) else "standard"

        # In Enterprise Mode, prioritize local transcript-derived USD and token metrics
        if plan_mode == "enterprise":
            return self._local_fallback_snapshot(detailed, config, "")

        oauth = self._read_oauth_token()
        token = (oauth.get("accessToken") or oauth.get("access_token") or oauth.get("token")) if oauth else None

        if not token:
            token = config.get("claude_api_key") or config.get("claude_session_cookie") or os.environ.get("ANTHROPIC_API_KEY")

        if not token:
            return self._local_fallback_snapshot(detailed, config, "OAuth credentials not found, showing local transcript tokens")

        headers = {
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
        }

        url = "https://api.anthropic.com/api/oauth/usage"
        data, err = self.request_json("GET", url, headers)
        if err:
            return self._local_fallback_snapshot(detailed, config, f"API error: {err.error_message}; showing local tokens")

        try:
            pw_raw = data.get("five_hour") or {}
            u_val = pw_raw.get("utilization")
            if u_val is not None:
                pw_used = float(u_val) * 100.0
            else:
                up_val = pw_raw.get("used_percent")
                pw_used = float(up_val) if up_val is not None else 0.0
            pw_pct_left = max(0.0, min(100.0, 100.0 - pw_used))

            primary_window = RateWindow(
                limit=100,
                used=round(pw_used),
                remaining=round(pw_pct_left),
                percent_left=pw_pct_left,
                resets_at=pw_raw.get("resets_at") or pw_raw.get("reset_at") or detailed.get("resets_at"),
                window_minutes=300,
                period_desc="5h"
            )

            secondary_window = None
            sw_raw = data.get("seven_day")
            if sw_raw:
                su_val = sw_raw.get("utilization")
                if su_val is not None:
                    sw_used = float(su_val) * 100.0
                else:
                    sup_val = sw_raw.get("used_percent")
                    sw_used = float(sup_val) if sup_val is not None else 0.0
                sw_pct_left = max(0.0, min(100.0, 100.0 - sw_used))
                secondary_window = RateWindow(
                    limit=100,
                    used=round(sw_used),
                    remaining=round(sw_pct_left),
                    percent_left=sw_pct_left,
                    resets_at=sw_raw.get("resets_at") or sw_raw.get("reset_at"),
                    window_minutes=10080,
                    period_desc="weekly"
                )

            plan_str = data.get("subscriptionType") or data.get("rate_limit_tier") or "Pro"

            return UsageSnapshot(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                badge=self.badge,
                color=self.color,
                primary_window=primary_window,
                secondary_window=secondary_window,
                credits={"tokens_today": detailed["tokens_today"], "tokens_24h": detailed["tokens_24h"], "cost_today_usd": detailed["cost_today_usd"]},
                plan=str(plan_str).capitalize(),
                status="ok"
            )

        except Exception as e:
            return self._local_fallback_snapshot(detailed, config, str(e))
