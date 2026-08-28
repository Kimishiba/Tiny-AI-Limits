import unittest
import json
import time
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.base import RateWindow, UsageSnapshot, BaseProvider
from providers.antigravity import AntigravityProvider
from providers.claude import ClaudeProvider
from providers.codex import CodexProvider
from providers.cursor import CursorProvider
from providers.copilot import CopilotProvider
from providers.gemini import GeminiProvider
from providers.openrouter import OpenRouterProvider
from providers.deepseek import DeepSeekProvider
from providers.mistral import MistralProvider
from providers.groq import GroqProvider
from providers import poller, ALL_PROVIDERS, ProviderPoller

from app import app, load_config, save_config

class TestProviders(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.orig_config = dict(load_config())

    def tearDown(self):
        save_config(self.orig_config)

    def test_provider_registry(self):
        self.assertEqual(len(ALL_PROVIDERS), 10)
        p_ids = {p.provider_id for p in ALL_PROVIDERS}
        expected_ids = {"antigravity", "claude", "codex", "cursor", "copilot", "gemini", "openrouter", "deepseek", "mistral", "groq"}
        self.assertEqual(p_ids, expected_ids)

    def test_openrouter_mock_parsing(self):
        provider = OpenRouterProvider()
        # Mock request_json returning a valid OpenRouter response
        mock_response = {
            "data": {
                "label": "Test Key",
                "usage": 4.50,
                "limit": 20.00,
                "is_free_tier": False
            }
        }
        provider.request_json = lambda *args, **kwargs: (mock_response, None)
        snapshot = provider.fetch_usage({"openrouter_api_key": "sk-or-test-key"})
        
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "openrouter")
        self.assertEqual(snapshot.badge, "OPR")
        self.assertIsNotNone(snapshot.primary_window)
        self.assertEqual(snapshot.primary_window.limit, 20)
        self.assertEqual(snapshot.primary_window.used, 4)
        self.assertEqual(snapshot.primary_window.remaining, 16)
        self.assertAlmostEqual(snapshot.primary_window.percent_left, 77.5, delta=0.5)

    def test_deepseek_mock_parsing(self):
        provider = DeepSeekProvider()
        mock_response = {
            "is_available": True,
            "balance_infos": [
                {"currency": "USD", "total_balance": "15.50"}
            ]
        }
        provider.request_json = lambda *args, **kwargs: (mock_response, None)
        snapshot = provider.fetch_usage({"deepseek_api_key": "sk-test-deepseek"})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "deepseek")
        self.assertEqual(snapshot.badge, "DSK")
        self.assertEqual(snapshot.primary_window.percent_left, 100.0)

    def test_codex_mock_parsing(self):
        provider = CodexProvider()
        mock_response = {
            "plan_type": "pro",
            "rate_limit": {
                "primary_window": {
                    "used_percent": 35.0,
                    "window_minutes": 300,
                    "reset_at": "2026-08-28T14:00:00Z"
                },
                "secondary_window": {
                    "used_percent": 15.0,
                    "window_minutes": 10080
                }
            }
        }
        provider._read_auth_credentials = lambda: {"access_token": "mock-token", "email": "dev@test.com"}
        provider.request_json = lambda *args, **kwargs: (mock_response, None)
        snapshot = provider.fetch_usage({})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "codex")
        self.assertEqual(snapshot.badge, "CDX")
        self.assertEqual(snapshot.primary_window.percent_left, 65.0)

    def test_cursor_mock_parsing(self):
        provider = CursorProvider()
        mock_resp = {
            "gpt-4": {"numRequests": 150, "maxRequestUsage": 500},
            "startOfMonth": "2026-08-01"
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snapshot = provider.fetch_usage({"cursor_token": "mock-cursor-token"})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "cursor")
        self.assertEqual(snapshot.badge, "CUR")
        self.assertEqual(snapshot.primary_window.used, 150)
        self.assertEqual(snapshot.primary_window.remaining, 350)
        self.assertEqual(snapshot.primary_window.percent_left, 70.0)

    def test_copilot_mock_parsing(self):
        provider = CopilotProvider()
        mock_resp = {
            "copilot_plan": "individual",
            "login": "octocat"
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snapshot = provider.fetch_usage({"copilot_token": "ghu_mock_token"})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "copilot")
        self.assertEqual(snapshot.badge, "COP")
        self.assertEqual(snapshot.plan, "Individual")
        self.assertEqual(snapshot.account_email, "octocat")

    def test_gemini_mock_parsing(self):
        provider = GeminiProvider()
        mock_resp = {
            "models": [{
                "modelId": "gemini-2.5-pro",
                "quotaInfo": {
                    "remainingFraction": 0.85,
                    "resetTime": "2026-08-28T23:59:59Z"
                }
            }]
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snapshot = provider.fetch_usage({"gemini_api_key": "mock-gemini-key"})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "gemini")
        self.assertEqual(snapshot.badge, "GEM")
        self.assertEqual(snapshot.primary_window.percent_left, 85.0)

    def test_mistral_mock_parsing(self):
        provider = MistralProvider()
        mock_resp = {"data": [{"id": "codestral-latest"}]}
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snapshot = provider.fetch_usage({"mistral_api_key": "mock-mistral-key"})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "mistral")
        self.assertEqual(snapshot.badge, "MST")
        self.assertEqual(snapshot.primary_window.percent_left, 100.0)

    def test_groq_mock_parsing(self):
        provider = GroqProvider()
        # Mock requests.get with rate limit headers
        class MockResponse:
            status_code = 200
            headers = {
                "x-ratelimit-remaining-requests": "80",
                "x-ratelimit-limit-requests": "100",
                "x-ratelimit-remaining-tokens": "45000",
                "x-ratelimit-limit-tokens": "50000"
            }
        
        import requests
        orig_get = requests.get
        try:
            requests.get = lambda *args, **kwargs: MockResponse()
            snapshot = provider.fetch_usage({"groq_api_key": "gsk_mock_key"})
            self.assertEqual(snapshot.status, "ok")
            self.assertEqual(snapshot.provider_id, "groq")
            self.assertEqual(snapshot.badge, "GRQ")
            self.assertEqual(snapshot.primary_window.percent_left, 80.0)
        finally:
            requests.get = orig_get

    def test_claude_mock_oauth_parsing(self):
        provider = ClaudeProvider()
        mock_resp = {
            "subscriptionType": "pro",
            "five_hour": {
                "utilization": 0.25,
                "resets_at": "2026-08-28T14:30:00Z"
            },
            "seven_day": {
                "utilization": 0.40
            }
        }
        provider._read_oauth_token = lambda: {"accessToken": "mock-token"}
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snapshot = provider.fetch_usage({})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "claude")
        self.assertEqual(snapshot.badge, "CLD")
        self.assertEqual(snapshot.primary_window.percent_left, 75.0)
        self.assertEqual(snapshot.secondary_window.percent_left, 60.0)

    def test_antigravity_mock_live_rpc(self):
        provider = AntigravityProvider()
        mock_live = {
            "userStatus": {"userEmail": "engineer@deepmind.com"},
            "models": [{
                "modelId": "gemini-2.5-pro",
                "quotaInfo": {
                    "remainingFraction": 0.92,
                    "resetTime": "2026-08-28T13:00:00Z"
                }
            }]
        }
        provider._query_live_rpc = lambda: mock_live
        snapshot = provider.fetch_usage({})

        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.provider_id, "antigravity")
        self.assertEqual(snapshot.badge, "AGY")
        self.assertEqual(snapshot.primary_window.percent_left, 92.0)
        self.assertEqual(snapshot.account_email, "engineer@deepmind.com")

    def test_poller_cache_and_lifecycle(self):
        test_poller = ProviderPoller()
        test_poller.start(lambda: {})
        self.assertTrue(test_poller._running)
        time.sleep(0.6)
        summary = test_poller.get_compact_summary()
        self.assertIsInstance(summary, list)
        test_poller.stop(timeout=2.0)
        self.assertFalse(test_poller._running)

    def test_api_providers_endpoint(self):
        res = self.client.get('/api/providers')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("providers", data)
        self.assertIn("selected_gauges", data)
        self.assertEqual(len(data["providers"]), 10)
        
        provider_ids = [p["id"] for p in data["providers"]]
        self.assertIn("antigravity", provider_ids)
        self.assertIn("claude", provider_ids)
        self.assertIn("codex", provider_ids)

    def test_config_gauge_selection(self):
        update_payload = {
            "selected_gauges": {
                "left": "codex",
                "right": "cursor"
            },
            "provider_keys": {
                "openrouter": "sk-or-v1-secret-key-12345"
            }
        }
        post_res = self.client.post('/api/config', json=update_payload)
        self.assertEqual(post_res.status_code, 200)
        post_data = json.loads(post_res.data)
        self.assertEqual(post_data["status"], "ok")
        self.assertEqual(post_data["config"]["selected_gauges"]["left"], "codex")
        self.assertEqual(post_data["config"]["selected_gauges"]["right"], "cursor")
        
        # Verify API key is masked in response
        self.assertTrue(post_data["config"]["provider_keys"]["openrouter"].endswith("2345"))
        self.assertIn("...", post_data["config"]["provider_keys"]["openrouter"])

    def test_data_endpoint_dynamic_gauges_and_size_budget(self):
        res = self.client.get('/data', headers={"Host": "localhost:5000"})
        self.assertEqual(res.status_code, 200)
        payload_bytes = len(res.data)
        
        # Ensure payload size constraint (<1800 bytes) for ESP32 StaticJsonDocument<2560>
        self.assertLess(payload_bytes, 1800, f"Payload size {payload_bytes}B exceeds 1800B budget")

        data = json.loads(res.data)
        self.assertIn("left_gauge", data)
        self.assertIn("right_gauge", data)
        self.assertIn("claude", data)
        self.assertIn("antigravity", data)
        self.assertIn("weather", data)
        self.assertIn("agent", data)
        self.assertIn("time", data)

        # Check left gauge and right gauge schema
        self.assertIn("label", data["left_gauge"])
        self.assertIn("percent", data["left_gauge"])
        self.assertIn("color", data["left_gauge"])
        self.assertIn("label", data["right_gauge"])
        self.assertIn("percent", data["right_gauge"])
        self.assertIn("color", data["right_gauge"])

if __name__ == '__main__':
    unittest.main()
