import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import claude_statusline

class TestClaudeStatusline(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cache_file = os.path.join(self.tmp_dir.name, "claude_rate_limits.json")
        self.patcher_cache_path = mock.patch("claude_statusline.CACHE_PATH", self.cache_file)
        self.patcher_cache_path.start()

    def tearDown(self):
        self.patcher_cache_path.stop()
        self.tmp_dir.cleanup()

    def _run_main(self, stdin_content: str):
        """Utility to run claude_statusline.main with mocked stdin/stdout."""
        with mock.patch("sys.stdin", new=io.StringIO(stdin_content)), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            claude_statusline.main()
            return mock_stdout.getvalue().strip()

    def _read_cache(self):
        """Read JSON from the temporary cache file, return None if file does not exist."""
        if not os.path.exists(self.cache_file):
            return None
        with open(self.cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_complete_payload_both_limits(self):
        payload = {
            "model": {"display_name": "Claude-2"},
            "workspace": {"current_dir": "/home/user/project"},
            "rate_limits": {
                "five_hour": {"used_percentage": 42.7, "resets_at": "2024-01-01T00:00:00Z"},
                "seven_day": {"used_percentage": 73.2, "resets_at": "2024-01-07T00:00:00Z"},
            },
        }
        stdout = self._run_main(json.dumps(payload))
        self.assertIn("Claude-2 | project | 5h:43% wk:73%", stdout)

        cache = self._read_cache()
        expected_cache = {
            "five_hour_pct": 42.7,
            "five_hour_resets_at": "2024-01-01T00:00:00Z",
            "week_pct": 73.2,
            "week_resets_at": "2024-01-07T00:00:00Z",
        }
        self.assertEqual(cache, expected_cache)

    def test_payload_only_five_hour(self):
        payload = {
            "model": {"display_name": "Claude"},
            "workspace": {"current_dir": "/tmp"},
            "rate_limits": {
                "five_hour": {"used_percentage": 15, "resets_at": "2024-02-01T12:00:00Z"},
                "seven_day": {},
            },
        }
        stdout = self._run_main(json.dumps(payload))
        self.assertIn("Claude | tmp | 5h:15% wk:--", stdout)

        cache = self._read_cache()
        expected_cache = {
            "five_hour_pct": 15,
            "five_hour_resets_at": "2024-02-01T12:00:00Z",
            "week_pct": None,
            "week_resets_at": None,
        }
        self.assertEqual(cache, expected_cache)

    def test_payload_only_seven_day(self):
        payload = {
            "model": {"display_name": "Claude"},
            "workspace": {"current_dir": "/var/log"},
            "rate_limits": {
                "five_hour": {},
                "seven_day": {"used_percentage": 88.9, "resets_at": "2024-03-01T00:00:00Z"},
            },
        }
        stdout = self._run_main(json.dumps(payload))
        self.assertIn("Claude | log | 5h:-- wk:89%", stdout)

        cache = self._read_cache()
        expected_cache = {
            "five_hour_pct": None,
            "five_hour_resets_at": None,
            "week_pct": 88.9,
            "week_resets_at": "2024-03-01T00:00:00Z",
        }
        self.assertEqual(cache, expected_cache)

    def test_payload_missing_rate_limits(self):
        payload = {
            "model": {"display_name": "Claude"},
            "workspace": {"current_dir": "/opt"},
        }
        stdout = self._run_main(json.dumps(payload))
        self.assertIn("Claude | opt | 5h:-- wk:--", stdout)
        self.assertIsNone(self._read_cache())

    def test_invalid_json_on_stdin(self):
        malformed = "{ this is not: valid json"
        stdout = self._run_main(malformed)
        self.assertIn("Claude |  | 5h:-- wk:--", stdout)
        self.assertIsNone(self._read_cache())

    def test_custom_model_and_deep_workspace(self):
        payload = {
            "model": {"display_name": "MyClaude"},
            "workspace": {"current_dir": "/a/b/c/d/e/folder"},
            "rate_limits": {
                "five_hour": {"used_percentage": 5, "resets_at": "2024-04-01T00:00:00Z"},
                "seven_day": {"used_percentage": 10, "resets_at": "2024-04-07T00:00:00Z"},
            },
        }
        stdout = self._run_main(json.dumps(payload))
        self.assertIn("MyClaude | folder | 5h:5% wk:10%", stdout)

    def test_missing_model_and_empty_workspace(self):
        payload = {
            "workspace": {"current_dir": ""},
            "rate_limits": {
                "five_hour": {"used_percentage": 0, "resets_at": None},
                "seven_day": {"used_percentage": None, "resets_at": None},
            },
        }
        stdout = self._run_main(json.dumps(payload))
        self.assertIn("Claude |  | 5h:0% wk:--", stdout)

    def test_cache_write_permission_error(self):
        payload = {
            "model": {"display_name": "Claude"},
            "workspace": {"current_dir": "/tmp"},
            "rate_limits": {
                "five_hour": {"used_percentage": 33, "resets_at": "2024-05-01T00:00:00Z"},
                "seven_day": {"used_percentage": 66, "resets_at": "2024-05-07T00:00:00Z"},
            },
        }

        with mock.patch("builtins.open", side_effect=PermissionError("no write permission")):
            stdout = self._run_main(json.dumps(payload))

        self.assertIn("Claude | tmp | 5h:33% wk:66%", stdout)
        self.assertFalse(os.path.exists(self.cache_file))

if __name__ == "__main__":
    unittest.main()
