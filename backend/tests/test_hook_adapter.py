import os
import sys
import json
import time
import unittest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app
from app import (
    handle_hook_event,
    get_hook_sessions,
    install_claude_hooks,
    uninstall_claude_hooks,
    get_multi_agent_status,
    _hook_sessions,
    _hook_lock,
    _is_pid_alive
)

class TestHookAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.orig_hook_file = app._HOOK_STATE_FILE
        app._HOOK_STATE_FILE = os.path.join(self.tmp_dir.name, "tinyscreen_hook_state.json")
        with _hook_lock:
            _hook_sessions.clear()
        app._session_registry.clear()
        app._session_counters = {"claude": 0, "antigravity": 0}

    def tearDown(self):
        with _hook_lock:
            _hook_sessions.clear()
        app._session_registry.clear()
        app._session_counters = {"claude": 0, "antigravity": 0}
        app._HOOK_STATE_FILE = self.orig_hook_file
        self.tmp_dir.cleanup()

    def test_handle_hook_event_notification_perm(self):
        now = time.time()
        res = handle_hook_event({
            "session_id": "ses_test1",
            "hook_event_name": "Notification",
            "notification_type": "permission_prompt",
            "cwd": "/path/to/repo",
            "owner_pid": os.getpid()
        }, now_ts=now)
        
        self.assertIsNotNone(res)
        self.assertEqual(res["state"], "WAITING")
        self.assertEqual(res["detail"], "GRANT PERM")
        self.assertEqual(res["color"], "#FFB800")
        
        sessions = get_hook_sessions(now_ts=now)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["state"], "WAITING")

    def test_handle_hook_event_idle_notification_ignored(self):
        now = time.time()
        res = handle_hook_event({
            "session_id": "ses_test_idle",
            "hook_event_name": "Notification",
            "notification_type": "idle_prompt",
            "cwd": "/path/to/repo"
        }, now_ts=now)
        
        self.assertEqual(res, {"status": "ignored", "session_id": "ses_test_idle"})
        sessions = get_hook_sessions(now_ts=now)
        self.assertEqual(len(sessions), 0)

    def test_handle_hook_event_user_prompt_and_tool(self):
        now = time.time()
        res1 = handle_hook_event({
            "session_id": "ses_test2",
            "hook_event_name": "UserPromptSubmit",
            "cwd": "/path/to/repo",
            "owner_pid": os.getpid()
        }, now_ts=now)
        
        self.assertEqual(res1["state"], "WORKING")
        self.assertEqual(res1["detail"], "EXECUTING...")
        self.assertEqual(res1["color"], "#00E5FF")

        res2 = handle_hook_event({
            "session_id": "ses_test2",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash"
        }, now_ts=now)
        
        self.assertEqual(res2["state"], "WAITING")
        self.assertEqual(res2["detail"], "GRANT PERM")
        self.assertEqual(res2["color"], "#FFB800")

        res3 = handle_hook_event({
            "session_id": "ses_test2",
            "hook_event_name": "PreToolUse",
            "tool_name": "Grep"
        }, now_ts=now)
        
        self.assertEqual(res3["state"], "WORKING")
        self.assertEqual(res3["detail"], "EXECUTING...")
        self.assertEqual(res3["color"], "#00E5FF")

    def test_handle_hook_event_stop_complete(self):
        now = time.time()
        res = handle_hook_event({
            "session_id": "ses_test3",
            "hook_event_name": "Stop",
            "cwd": "/path/to/repo",
            "owner_pid": os.getpid()
        }, now_ts=now)
        
        self.assertEqual(res["state"], "COMPLETE")
        self.assertEqual(res["detail"], "WORK COMPLETE")
        self.assertEqual(res["color"], "#00FF88")

    def test_handle_hook_event_session_end(self):
        now = time.time()
        handle_hook_event({
            "session_id": "ses_test4",
            "hook_event_name": "SessionStart",
            "owner_pid": os.getpid()
        }, now_ts=now)
        
        self.assertEqual(len(get_hook_sessions(now_ts=now)), 1)
        
        res = handle_hook_event({
            "session_id": "ses_test4",
            "hook_event_name": "SessionEnd"
        }, now_ts=now)
        
        self.assertEqual(res, {"status": "removed", "session_id": "ses_test4"})
        self.assertEqual(len(get_hook_sessions(now_ts=now)), 0)

    def test_dead_pid_reaping(self):
        now = time.time()
        # Register session with PID 999999999 (non-existent process)
        handle_hook_event({
            "session_id": "ses_dead",
            "hook_event_name": "SessionStart",
            "owner_pid": 999999999
        }, now_ts=now)
        
        # get_hook_sessions should automatically reap dead PID
        sessions = get_hook_sessions(now_ts=now)
        self.assertEqual(len(sessions), 0)

    def test_multi_agent_status_with_hooks(self):
        now = time.time()
        handle_hook_event({
            "session_id": "ses_hook1",
            "hook_event_name": "Notification",
            "notification_type": "permission_prompt",
            "owner_pid": os.getpid()
        }, now_ts=now)

        with tempfile.TemporaryDirectory() as tmp_dir:
            ag_dir = os.path.join(tmp_dir, "brain")
            sess = os.path.join(ag_dir, "s1", ".system_generated", "logs")
            os.makedirs(sess, exist_ok=True)
            with open(os.path.join(sess, "transcript.jsonl"), "w") as f:
                f.write(json.dumps({"type": "PLANNER_RESPONSE", "content": "Working on it"}) + "\n")

            status = get_multi_agent_status(antigravity_dirs=[ag_dir], claude_dirs=[], now_ts=now)
            self.assertTrue(status["has_active_agents"])
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "GRANT PERM")
            self.assertEqual(status["active_agents"][0]["name"], "Claude 1")
            self.assertEqual(status["active_agents"][0]["state"], "WAITING")

    def test_api_hook_endpoint(self):
        with app.app.test_client() as client:
            res = client.post("/api/hook", json={
                "session_id": "ses_api_test",
                "hook_event_name": "UserPromptSubmit",
                "owner_pid": os.getpid()
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["state"], "WORKING")
            self.assertEqual(data["detail"], "EXECUTING...")

    def test_install_and_uninstall_hooks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_settings = os.path.join(tmp_dir, "settings.json")
            
            # Monkeypatch expanduser
            original_expanduser = os.path.expanduser
            app.os.path.expanduser = lambda p: mock_settings if "settings.json" in p else original_expanduser(p)
            try:
                # 1. Install
                self.assertTrue(install_claude_hooks(app_path="/fake/app.py"))
                with open(mock_settings, "r") as f:
                    data = json.load(f)
                self.assertIn("hooks", data)
                self.assertIn("SessionStart", data["hooks"])
                self.assertIn("Notification", data["hooks"])
                
                # 2. Uninstall
                self.assertTrue(uninstall_claude_hooks(app_path="/fake/app.py"))
                with open(mock_settings, "r") as f:
                    data_uninstalled = json.load(f)
                self.assertEqual(len(data_uninstalled["hooks"]["SessionStart"]), 0)
            finally:
                app.os.path.expanduser = original_expanduser

if __name__ == "__main__":
    unittest.main()
