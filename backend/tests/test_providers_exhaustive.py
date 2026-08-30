import os
import sys
import json
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.base import RateWindow, UsageSnapshot, BaseProvider, resolve_app_data_path, read_sqlite_kv_safe
from providers import (
    ALL_PROVIDERS,
    ProviderPoller,
    AntigravityProvider,
    ClaudeProvider,
    CodexProvider,
    CopilotProvider,
    CursorProvider,
    DeepSeekProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OpenRouterProvider,
)

class TestRateWindowAndUsageSnapshot(unittest.TestCase):
    def test_rate_window_defaults_and_to_dict(self):
        rw = RateWindow(limit=200, used=50, remaining=150, percent_left=75.0, resets_at="2026-09-01T00:00:00Z", window_minutes=300, period_desc="5h")
        d = rw.to_dict()
        self.assertEqual(d["limit"], 200)
        self.assertEqual(d["used"], 50)
        self.assertEqual(d["remaining"], 150)
        self.assertEqual(d["percent_left"], 75.0)
        self.assertEqual(d["period_desc"], "5h")

    def test_usage_snapshot_nested_to_dict(self):
        p_win = RateWindow(limit=100, used=10, remaining=90, percent_left=90.0)
        s_win = RateWindow(limit=500, used=100, remaining=400, percent_left=80.0)
        m_win = {"gpt-4": RateWindow(limit=50, used=25, remaining=25, percent_left=50.0)}

        snap = UsageSnapshot(
            provider_id="test_prov",
            provider_name="Test Provider",
            badge="TST",
            color="0xFF00FF",
            primary_window=p_win,
            secondary_window=s_win,
            model_windows=m_win,
            plan="pro",
            status="ok"
        )
        d = snap.to_dict()
        self.assertEqual(d["provider_id"], "test_prov")
        self.assertEqual(d["primary_window"]["percent_left"], 90.0)
        self.assertEqual(d["secondary_window"]["percent_left"], 80.0)
        self.assertEqual(d["model_windows"]["gpt-4"]["limit"], 50)

class TestBaseUtilities(unittest.TestCase):
    def test_resolve_app_data_path_missing(self):
        with patch("os.path.exists", return_value=False):
            res = resolve_app_data_path("nonexistent_path.json", app_name="testapp")
            self.assertIsNone(res)

    def test_resolve_app_data_path_found(self):
        with patch("os.path.exists", return_value=True):
            res = resolve_app_data_path("config.json", app_name="testapp")
            self.assertIsNotNone(res)

    def test_read_sqlite_kv_safe_valid_and_errors(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "state.vscdb")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT INTO ItemTable VALUES ('cursorAuth/accessToken', 'token-12345')")
            conn.commit()
            conn.close()

            # Read existing key
            val = read_sqlite_kv_safe(db_file, "ItemTable", "key", "value", "cursorAuth/accessToken")
            self.assertEqual(val, "token-12345")

            # Read nonexistent key
            val_missing = read_sqlite_kv_safe(db_file, "ItemTable", "key", "value", "nonexistent")
            self.assertIsNone(val_missing)

            # Read nonexistent db file
            val_no_file = read_sqlite_kv_safe(os.path.join(tmp_dir, "missing.db"), "ItemTable", "key", "value", "k")
            self.assertIsNone(val_no_file)

            # Corrupted db file
            corrupt_file = os.path.join(tmp_dir, "corrupt.db")
            with open(corrupt_file, "w") as f:
                f.write("not a sqlite database")
            val_corrupt = read_sqlite_kv_safe(corrupt_file, "ItemTable", "key", "value", "k")
            self.assertIsNone(val_corrupt)

class TestExhaustiveProviders(unittest.TestCase):
    def test_antigravity_provider_live_rpc_and_transcript_fallback(self):
        provider = AntigravityProvider()

        # 1. Live RPC found with quota
        mock_rpc_data = {
            "userStatus": {"userEmail": "engineer@google.com"},
            "models": [
                {
                    "modelId": "gemini-3.1-pro",
                    "quotaInfo": {
                        "remainingFraction": 0.45,
                        "resetTime": "2026-09-01T12:00:00Z"
                    }
                }
            ]
        }
        with patch.object(provider, "_query_live_rpc", return_value=mock_rpc_data):
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "ok")
            self.assertEqual(snap.provider_id, "antigravity")
            self.assertEqual(snap.account_email, "engineer@google.com")
            self.assertEqual(snap.primary_window.remaining, 45)
            self.assertEqual(snap.primary_window.used, 55)

        # 2. Live RPC None -> Fallback to transcript heuristic (status is 'degraded' when steps > 0)
        with patch.object(provider, "_query_live_rpc", return_value=None), \
             patch.object(provider, "_scan_antigravity_transcripts", return_value=(10, 2)):
            snap_fb = provider.fetch_usage({"antigravity_5h_quota": 200})
            self.assertEqual(snap_fb.status, "degraded")
            self.assertEqual(snap_fb.primary_window.used, 10)
            self.assertEqual(snap_fb.primary_window.limit, 200)
            self.assertEqual(snap_fb.primary_window.remaining, 190)

    def test_claude_provider_oauth_and_local_fallback(self):
        provider = ClaudeProvider()

        # 1. OAuth API success with utilization
        mock_oauth_resp = {
            "five_hour": {"utilization": 0.25, "resets_at": "2026-09-01T15:00:00Z"},
            "seven_day": {"utilization": 0.10, "resets_at": "2026-09-07T00:00:00Z"}
        }
        with patch.object(provider, "_read_oauth_token", return_value={"accessToken": "oauth_token_123"}):
            provider.request_json = lambda *args, **kwargs: (mock_oauth_resp, None)
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "ok")
            self.assertEqual(snap.primary_window.percent_left, 75.0)
            self.assertEqual(snap.secondary_window.percent_left, 90.0)

        # 2. Local fallback when no token and enterprise plan
        with patch.object(provider, "_read_oauth_token", return_value=None), \
             patch.object(provider, "scan_usage_detailed", return_value={
                 "tokens_today": 12000,
                 "tokens_24h": 25000,
                 "tokens_str": "12.0k",
                 "cost_today_usd": 1.25,
                 "cost_24h_usd": 2.50,
                 "cost_str": "$1.25"
             }):
            snap_ent = provider.fetch_usage({"claude_plan": "enterprise", "claude_daily_budget_usd": 10.0})
            self.assertEqual(snap_ent.status, "ok")
            self.assertEqual(snap_ent.primary_window.used, 1)

    def test_codex_provider_missing_auth_and_expired_token(self):
        provider = CodexProvider()

        # Missing auth credentials -> unauthenticated
        with patch.object(provider, "_read_auth_credentials", return_value=None):
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "unauthenticated")

        # 401 unauthorized response from API
        with patch.object(provider, "_read_auth_credentials", return_value={"access_token": "expired_token"}):
            err_snap = UsageSnapshot(
                provider_id="codex",
                provider_name="OpenAI Codex",
                status="unauthenticated",
                error_message="HTTP 401: Unauthorized"
            )
            provider.request_json = lambda *args, **kwargs: (None, err_snap)
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "unauthenticated")

    def test_copilot_provider_missing_hosts_and_success(self):
        provider = CopilotProvider()

        # Missing hosts.json -> unauthenticated
        with patch.object(provider, "_find_copilot_token", return_value=None):
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "unauthenticated")

        # Valid Copilot internal quota response
        with patch.object(provider, "_find_copilot_token", return_value="gho_mocktoken123"):
            mock_copilot_resp = {
                "copilot_plan": "individual",
                "login": "octocat"
            }
            provider.request_json = lambda *args, **kwargs: (mock_copilot_resp, None)
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "ok")
            self.assertEqual(snap.account_email, "octocat")
            self.assertEqual(snap.plan, "Individual")
            self.assertEqual(snap.primary_window.percent_left, 100.0)

    def test_cursor_provider_missing_and_valid_db(self):
        provider = CursorProvider()

        # Missing DB / token
        with patch.object(provider, "_find_cursor_state_db", return_value=None):
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "unauthenticated")

        # Valid token and usage response
        with patch.object(provider, "_find_cursor_state_db", return_value="/mock/state.vscdb"), \
             patch("providers.cursor.read_sqlite_kv_safe", return_value="cur_token_xyz"):
            mock_cursor_resp = {
                "membershipType": "pro",
                "email": "developer@cursor.com",
                "gpt-4": {
                    "numRequests": 80,
                    "maxRequestUsage": 500
                }
            }
            provider.request_json = lambda *args, **kwargs: (mock_cursor_resp, None)
            snap = provider.fetch_usage({})
            self.assertEqual(snap.status, "ok")
            self.assertEqual(snap.plan, "Pro")
            self.assertEqual(snap.primary_window.used, 80)
            self.assertEqual(snap.primary_window.limit, 500)
            self.assertEqual(snap.primary_window.remaining, 420)

    def test_deepseek_provider_missing_key_and_error(self):
        provider = DeepSeekProvider()

        # Missing API key
        snap = provider.fetch_usage({})
        self.assertEqual(snap.status, "unconfigured")

        # API error (500)
        err_snap = UsageSnapshot(
            provider_id="deepseek",
            provider_name="DeepSeek",
            status="error",
            error_message="HTTP 500 Internal Server Error"
        )
        provider.request_json = lambda *args, **kwargs: (None, err_snap)
        snap_err = provider.fetch_usage({"deepseek_api_key": "sk-test"})
        self.assertEqual(snap_err.status, "error")

    def test_gemini_provider_missing_key_and_valid_response(self):
        provider = GeminiProvider()

        # Missing API key -> unauthenticated
        snap = provider.fetch_usage({})
        self.assertEqual(snap.status, "unauthenticated")

        # Valid API key
        mock_resp = {
            "models": [
                {"name": "models/gemini-2.5-flash", "supportedGenerationMethods": ["generateContent"]}
            ]
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snap_ok = provider.fetch_usage({"gemini_api_key": "AIzaSyTestKey"})
        self.assertEqual(snap_ok.status, "ok")
        self.assertEqual(snap_ok.primary_window.percent_left, 100.0)

    def test_groq_provider_missing_key_and_headers_parsing(self):
        provider = GroqProvider()

        # Missing API key
        snap = provider.fetch_usage({})
        self.assertEqual(snap.status, "unconfigured")

        # Mock API request returning rate limit headers
        mock_headers = {
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-remaining-requests": "750",
            "x-ratelimit-limit-tokens": "100000",
            "x-ratelimit-remaining-tokens": "75000"
        }
        with patch("requests.get") as mock_get:
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.headers = mock_headers
            mock_res.json.return_value = {"data": []}
            mock_get.return_value = mock_res

            snap_ok = provider.fetch_usage({"groq_api_key": "gsk_testgroqkey"})
            self.assertEqual(snap_ok.status, "ok")
            self.assertEqual(snap_ok.primary_window.limit, 1000)
            self.assertEqual(snap_ok.primary_window.remaining, 750)
            self.assertEqual(snap_ok.primary_window.used, 250)
            self.assertEqual(snap_ok.primary_window.percent_left, 75.0)

    def test_mistral_provider_missing_key_and_rate_limit(self):
        provider = MistralProvider()

        # Missing API key
        snap = provider.fetch_usage({})
        self.assertEqual(snap.status, "unconfigured")

        # 429 Rate Limit
        err_snap = UsageSnapshot(
            provider_id="mistral",
            provider_name="Mistral AI",
            status="degraded",
            error_message="HTTP 429: Rate limit exceeded"
        )
        provider.request_json = lambda *args, **kwargs: (None, err_snap)
        snap_429 = provider.fetch_usage({"mistral_api_key": "mis_key_123"})
        self.assertEqual(snap_429.status, "degraded")
        self.assertIn("Rate limit", snap_429.error_message)

    def test_openrouter_provider_zero_limit_boundary(self):
        provider = OpenRouterProvider()

        # Zero limit / unlimited boundary condition
        mock_resp = {
            "data": {
                "label": "Free Tier Key",
                "usage": 0.0,
                "limit": 0.0,
                "is_free_tier": True
            }
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snap = provider.fetch_usage({"openrouter_api_key": "sk-or-free"})
        self.assertEqual(snap.status, "ok")
        self.assertEqual(snap.primary_window.limit, 100)
        self.assertEqual(snap.primary_window.remaining, 100)
        self.assertEqual(snap.primary_window.percent_left, 100.0)

class TestProviderPollerExhaustive(unittest.TestCase):
    def test_poller_lifecycle_and_compact_summary(self):
        mock_provider = MagicMock(spec=BaseProvider)
        mock_provider.provider_id = "mock_p"
        mock_provider.provider_name = "Mock Provider"
        mock_provider.badge = "MCK"
        mock_provider.color = "0x00FF88"
        mock_provider.ttl_seconds = 0.2

        mock_snap = UsageSnapshot(
            provider_id="mock_p",
            provider_name="Mock Provider",
            badge="MCK",
            color="0x00FF88",
            primary_window=RateWindow(limit=100, used=20, remaining=80, percent_left=80.0),
            status="ok"
        )
        mock_provider.fetch_usage.return_value = mock_snap

        poller = ProviderPoller(providers=[mock_provider])
        self.assertFalse(poller._running)

        poller.start(config_getter=lambda: {})
        self.assertTrue(poller._running)

        # Wait briefly for poller loop to execute
        time.sleep(0.8)

        snap = poller.get_snapshot("mock_p")
        self.assertIsNotNone(snap)
        self.assertEqual(snap.provider_id, "mock_p")

        all_snaps = poller.get_all_snapshots()
        self.assertIn("mock_p", all_snaps)

        summary = poller.get_compact_summary()
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["id"], "mock_p")
        self.assertEqual(summary[0]["pct"], 80)
        self.assertEqual(summary[0]["st"], "ok")

        poller.stop(timeout=2.0)
        self.assertFalse(poller._running)

    def test_poller_resilience_on_exception(self):
        mock_faulty = MagicMock(spec=BaseProvider)
        mock_faulty.provider_id = "faulty_p"
        mock_faulty.provider_name = "Faulty Provider"
        mock_faulty.badge = "FLT"
        mock_faulty.color = "0xFF0000"
        mock_faulty.ttl_seconds = 0.1
        mock_faulty.fetch_usage.side_effect = RuntimeError("Network timeout")

        poller = ProviderPoller(providers=[mock_faulty])
        poller.start(config_getter=lambda: {})
        time.sleep(0.8)

        snap = poller.get_snapshot("faulty_p")
        self.assertIsNotNone(snap)
        self.assertEqual(snap.status, "error")
        self.assertIn("Network timeout", snap.error_message)

        poller.stop(timeout=2.0)

if __name__ == "__main__":
    unittest.main()
