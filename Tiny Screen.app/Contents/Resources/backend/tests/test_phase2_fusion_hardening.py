import unittest
from unittest import mock
import os
import re
import tempfile
import json
from providers.base import read_sqlite_kv_safe
from services.firmware_cache import get_latest_firmware, FIRMWARE_CACHE_DIR
from services.geocoding import _sanitize_coord, get_weather
from providers.cursor import CursorProvider
from providers.claude import ClaudeProvider
from providers.codex import CodexProvider
from providers.groq import GroqProvider
from services.agent_tracker import install_claude_hooks

class TestFusionLoopHardening(unittest.TestCase):
    def test_sql_identifier_validation(self):
        # Malicious table / column identifiers must be rejected
        res = read_sqlite_kv_safe("/tmp/dummy.db", "users; DROP TABLE users;--", "key", "val", "test")
        self.assertIsNone(res)
        res2 = read_sqlite_kv_safe("/tmp/dummy.db", "users", "key' OR 1=1--", "val", "test")
        self.assertIsNone(res2)

    def test_cursor_zero_quota_handling(self):
        provider = CursorProvider()
        mock_resp = {
            "gpt-4": {"numRequests": 0, "maxRequestUsage": 0},
            "startOfMonth": "2026-08-01"
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snapshot = provider.fetch_usage({"cursor_token": "token"})
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.primary_window.limit, 0)
        self.assertEqual(snapshot.primary_window.remaining, 0)
        self.assertEqual(snapshot.primary_window.percent_left, 0.0)

    def test_claude_none_utilization_handling(self):
        provider = ClaudeProvider()
        mock_resp = {
            "five_hour": {"utilization": None, "used_percent": None, "resets_at": "2026-09-03T12:00:00Z"},
            "seven_day": {"utilization": None, "used_percent": None, "resets_at": None},
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        snapshot = provider.fetch_usage({"claude_session_cookie": "dummy"})
        self.assertEqual(snapshot.status, "ok")
        self.assertEqual(snapshot.primary_window.percent_left, 100.0)

    def test_codex_none_used_percent_handling(self):
        provider = CodexProvider()
        mock_resp = {
            "rate_limit": {
                "primary_window": {"percent_left": None, "used_percent": None},
                "secondary_window": {"percent_left": None, "used_percent": None}
            }
        }
        provider.request_json = lambda *args, **kwargs: (mock_resp, None)
        with mock.patch.object(provider, "_read_auth_credentials", return_value={"access_token": "tok"}):
            snapshot = provider.fetch_usage({})
            self.assertEqual(snapshot.status, "ok")
            self.assertEqual(snapshot.primary_window.percent_left, 100.0)

    def test_coord_sanitization(self):
        self.assertEqual(_sanitize_coord(45.0, -90.0, 90.0, 0.0), 45.0)
        self.assertEqual(_sanitize_coord("invalid", -90.0, 90.0, 10.0), 10.0)
        self.assertEqual(_sanitize_coord(100.0, -90.0, 90.0, 0.0), 0.0)  # out of bounds
        self.assertEqual(_sanitize_coord(-190.0, -180.0, 180.0, 0.0), 0.0)  # out of bounds

    def test_claude_hooks_shell_escaping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = os.path.join(tmpdir, "settings.json")
            with mock.patch("os.path.expanduser", return_value=settings_file):
                path_with_spaces = os.path.join(tmpdir, "my custom app dir", "app.py")
                os.makedirs(os.path.dirname(path_with_spaces), exist_ok=True)
                with open(path_with_spaces, "w") as f:
                    f.write("# dummy")
                
                res = install_claude_hooks(path_with_spaces)
                self.assertTrue(res)
                with open(settings_file, "r") as sf:
                    data = json.load(sf)
                    cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
                    self.assertTrue(cmd.startswith("python3 "))
                    self.assertIn("my custom app dir", cmd)

if __name__ == "__main__":
    unittest.main()
