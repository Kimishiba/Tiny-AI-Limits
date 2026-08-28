import os
import sys
import json
import time
import unittest

import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app
from app import check_agent_status, check_antigravity_status, check_claude_status, scan_antigravity_sessions, scan_claude_sessions, get_multi_agent_status, _hook_lock, _hook_sessions

class TestAgentStatus(unittest.TestCase):
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

    def test_antigravity_ask_question(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            session_dir = os.path.join(brain_dir, "session1", ".system_generated", "logs")
            os.makedirs(session_dir, exist_ok=True)
            transcript_file = os.path.join(session_dir, "transcript.jsonl")
            
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "type": "ASK_QUESTION",
                    "created_at": "2026-08-27T10:00:00Z"
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "ANSWER Q")
            self.assertEqual(status["source"], "antigravity")

    def test_claude_ask_user_question(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = os.path.join(tmp_dir, "projects", "project1")
            os.makedirs(projects_dir, exist_ok=True)
            session_file = os.path.join(projects_dir, "session1.jsonl")
            
            with open(session_file, "w") as f:
                f.write(json.dumps({
                    "type": "assistant",
                    "timestamp": "2026-08-27T10:00:00Z",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "AskUserQuestion",
                                "input": {"questions": ["Proceed?"]}
                            }
                        ]
                    }
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[], claude_dirs=[tmp_dir], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "ANSWER Q")
            self.assertEqual(status["source"], "claude")

    def test_antigravity_request_feedback_metadata(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            session_dir = os.path.join(brain_dir, "session1", ".system_generated", "logs")
            os.makedirs(session_dir, exist_ok=True)
            transcript_file = os.path.join(session_dir, "transcript.jsonl")
            
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-08-27T10:00:00Z",
                    "tool_calls": [
                        {
                            "name": "write_to_file",
                            "args": {
                                "ArtifactMetadata": {"RequestFeedback": True}
                            }
                        }
                    ]
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "APPROVE PLAN")
            self.assertEqual(status["source"], "antigravity")

    def test_antigravity_ask_permission_pending(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            session_dir = os.path.join(brain_dir, "session1", ".system_generated", "logs")
            os.makedirs(session_dir, exist_ok=True)
            transcript_file = os.path.join(session_dir, "transcript.jsonl")
            
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-08-27T10:00:00Z",
                    "tool_calls": [
                        {
                            "name": "ask_permission",
                            "args": {"permission": "Execute deployment"}
                        }
                    ]
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "GRANT PERM")
            self.assertEqual(status["source"], "antigravity")

    def test_antigravity_autonomous_tool_does_not_alert(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            session_dir = os.path.join(brain_dir, "session1", ".system_generated", "logs")
            os.makedirs(session_dir, exist_ok=True)
            transcript_file = os.path.join(session_dir, "transcript.jsonl")
            
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-08-27T10:00:00Z",
                    "tool_calls": [
                        {
                            "name": "view_file",
                            "args": {"AbsolutePath": "/path/to/file.py"}
                        }
                    ]
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertFalse(status["waiting_for_input"])

    def test_antigravity_run_command_working_state(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            session_dir = os.path.join(brain_dir, "session1", ".system_generated", "logs")
            os.makedirs(session_dir, exist_ok=True)
            transcript_file = os.path.join(session_dir, "transcript.jsonl")
            
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-08-27T10:00:00Z",
                    "tool_calls": [
                        {
                            "name": "run_command",
                            "args": {"CommandLine": "swift test"}
                        }
                    ]
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertFalse(status["waiting_for_input"])
            
            sessions = scan_antigravity_sessions(brain_dirs=[brain_dir], now_ts=time.time())
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["state"], "WORKING")

    def test_antigravity_ask_permission_waiting_state(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            session_dir = os.path.join(brain_dir, "session1", ".system_generated", "logs")
            os.makedirs(session_dir, exist_ok=True)
            transcript_file = os.path.join(session_dir, "transcript.jsonl")
            
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-08-27T10:00:00Z",
                    "tool_calls": [
                        {
                            "name": "ask_permission",
                            "args": {"Action": "Deploy to production"}
                        }
                    ]
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "GRANT PERM")

    def test_claude_permission_prompt(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = os.path.join(tmp_dir, "projects", "project1")
            os.makedirs(projects_dir, exist_ok=True)
            session_file = os.path.join(projects_dir, "session1.jsonl")
            
            with open(session_file, "w") as f:
                f.write(json.dumps({
                    "type": "assistant",
                    "timestamp": "2026-08-27T10:00:00Z",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "request_permission",
                                "input": {"action": "sudo rm"}
                            }
                        ]
                    }
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[], claude_dirs=[tmp_dir], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "GRANT PERM")
            self.assertEqual(status["source"], "claude")

    def test_priority_waiting_for_input_over_completed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            ag_dir = os.path.join(tmp_dir, "brain")
            ag_session = os.path.join(ag_dir, "session1", ".system_generated", "logs")
            os.makedirs(ag_session, exist_ok=True)
            ag_file = os.path.join(ag_session, "transcript.jsonl")
            # Finished turn recently
            with open(ag_file, "w") as f:
                f.write(json.dumps({"type": "PLANNER_RESPONSE", "content": "Done!"}) + "\n")

            cl_dir = os.path.join(tmp_dir, "claude")
            cl_project = os.path.join(cl_dir, "proj")
            os.makedirs(cl_project, exist_ok=True)
            cl_file = os.path.join(cl_project, "sess.jsonl")
            # Waiting for input
            with open(cl_file, "w") as f:
                f.write(json.dumps({
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "tool_use", "name": "AskUserQuestion"}]
                    }
                }) + "\n")

            status = check_agent_status(antigravity_dirs=[ag_dir], claude_dirs=[cl_dir], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["source"], "claude")

    def test_multi_agent_status_aggregation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            ag_sess1 = os.path.join(brain_dir, "sess1", ".system_generated", "logs")
            os.makedirs(ag_sess1, exist_ok=True)
            with open(os.path.join(ag_sess1, "transcript.jsonl"), "w") as f:
                f.write(json.dumps({"type": "ASK_QUESTION"}) + "\n")

            claude_dir = os.path.join(tmp_dir, "claude")
            cl_proj = os.path.join(claude_dir, "p1")
            os.makedirs(cl_proj, exist_ok=True)
            with open(os.path.join(cl_proj, "s1.jsonl"), "w") as f:
                f.write(json.dumps({
                    "type": "assistant",
                    "message": {"content": [{"type": "tool_use", "name": "AskUserQuestion"}]}
                }) + "\n")

            now = time.time()
            res = get_multi_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[claude_dir], now_ts=now)
            self.assertTrue(res["waiting_for_input"])
            self.assertTrue(res["has_active_agents"])
            self.assertEqual(len(res["active_agents"]), 2)
            self.assertEqual(res["active_agents"][0]["state"], "WAITING")

    def test_antigravity_run_command_waiting(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            brain_dir = os.path.join(tmp_dir, "brain")
            session_dir = os.path.join(brain_dir, "session1", ".system_generated", "logs")
            os.makedirs(session_dir, exist_ok=True)
            transcript_file = os.path.join(session_dir, "transcript.jsonl")
            
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-08-27T10:00:00Z",
                    "tool_calls": [
                        {
                            "name": "run_command",
                            "args": {"CommandLine": "curl -s http://127.0.0.1:5000/whoami"}
                        }
                    ]
                }) + "\n")
            
            sessions = scan_antigravity_sessions(brain_dirs=[brain_dir], now_ts=time.time())
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["state"], "WORKING")
            self.assertEqual(sessions[0]["color"], "#FF7A00")

    def test_claude_bash_working(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = os.path.join(tmp_dir, "projects", "project1")
            os.makedirs(projects_dir, exist_ok=True)
            session_file = os.path.join(projects_dir, "session1.jsonl")
            
            with open(session_file, "w") as f:
                f.write(json.dumps({
                    "type": "assistant",
                    "timestamp": "2026-08-27T10:00:00Z",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Bash",
                                "input": {"command": "ls -la"}
                            }
                        ]
                    }
                }) + "\n")
            
            sessions = scan_claude_sessions(claude_dirs=[tmp_dir], now_ts=time.time())
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["state"], "WORKING")
            self.assertEqual(sessions[0]["color"], "#00E5FF")

    def test_format_reset_time_variations(self):
        from app import format_reset_time
        now = 1787830000.0
        
        # 3h 12m in future
        future_iso = "2026-08-27T14:40:00Z"
        # 11520 seconds = 3h 12m
        secs, s = format_reset_time(future_iso, now_ts=1787800000.0)
        self.assertIsNotNone(secs)
        
        # Exact calculation test
        from datetime import datetime, timezone
        now_dt = datetime.now(timezone.utc)
        now_ts = float(int(now_dt.timestamp()))
        
        # 2h 15m in future
        future_iso_2h = datetime.fromtimestamp(now_ts + 8100, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        secs_2h, reset_str_2h = format_reset_time(future_iso_2h, now_ts=now_ts)
        self.assertEqual(secs_2h, 8100)
        self.assertEqual(reset_str_2h, "2h 15m")
        
        # 42 mins in future
        future_iso_42m = datetime.fromtimestamp(now_ts + 2520, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        secs_42m, reset_str_42m = format_reset_time(future_iso_42m, now_ts=now_ts)
        self.assertEqual(secs_42m, 2520)
        self.assertEqual(reset_str_42m, "42m")
        
        # Past timestamp
        past_iso = datetime.fromtimestamp(now_ts - 100, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        secs_past, reset_str_past = format_reset_time(past_iso, now_ts=now_ts)
        self.assertEqual(secs_past, 0)
        self.assertEqual(reset_str_past, "READY")

    def test_get_antigravity_quota_fields(self):
        from app import get_antigravity_quota
        quota = get_antigravity_quota()
        self.assertIn("limit", quota)
        self.assertIn("used", quota)
        self.assertIn("remaining", quota)
        self.assertIn("period", quota)
        self.assertIn("reset_time", quota)
        self.assertIn("reset_in_seconds", quota)
        self.assertIn("reset_str", quota)

    def test_scan_claude_usage_fields(self):
        from app import scan_claude_usage
        usage = scan_claude_usage()
        self.assertIn("tokens_today", usage)
        self.assertIn("limit", usage)
        self.assertIn("remaining", usage)
        self.assertIn("reset_time", usage)
        self.assertIn("reset_in_seconds", usage)
        self.assertIn("reset_str", usage)

    def test_firmware_version_endpoint(self):
        client = app.app.test_client()
        res = client.get("/firmware/version")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode("utf-8"))
        self.assertIn("version", data)
        self.assertIn("available", data)
        self.assertIn("companion_version", data)

    def test_ota_trigger_and_data_payload(self):
        client = app.app.test_client()
        # Trigger OTA
        res = client.post("/api/ota/trigger")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode("utf-8"))
        self.assertEqual(data["status"], "ok")

        # Now get /data with paired query (or allow_unpaired)
        app.config["allow_unpaired_clients"] = True
        data_res = client.get("/data")
        self.assertEqual(data_res.status_code, 200)
        payload = json.loads(data_res.data.decode("utf-8"))
        self.assertIn("ota", payload)
        self.assertTrue(payload["ota"]["trigger"])
        self.assertIn("url", payload["ota"])
        self.assertIn("version", payload["ota"])

        # Second get /data should have trigger == False (one-shot consumption)
        data_res2 = client.get("/data")
        payload2 = json.loads(data_res2.data.decode("utf-8"))
        self.assertFalse(payload2["ota"]["trigger"])

    def test_contextual_agent_label_agy_objective(self):
        lines = [
            json.dumps({"type": "CHECKPOINT", "content": "{{ CHECKPOINT 0 }}\n# USER Objective:\nMulti-Service Quota Display Ticket\n"})
        ]
        label = app.get_stable_agent_label("antigravity", "sess_obj_1", transcript_lines=lines)
        self.assertEqual(label, "Quota")
        self.assertLessEqual(len(label), 12)

    def test_contextual_agent_label_agy_user_request(self):
        lines = [
            json.dumps({
                "type": "USER_INPUT",
                "source": "USER_EXPLICIT",
                "content": "<USER_REQUEST>\ncan we design the enclosure CAD model for the device?\n</USER_REQUEST>"
            })
        ]
        label = app.get_stable_agent_label("antigravity", "sess_prompt_1", transcript_lines=lines)
        self.assertEqual(label, "Design")
        self.assertLessEqual(len(label), 12)

    def test_contextual_agent_label_agy_subagent_role(self):
        label = app.get_stable_agent_label("antigravity", "sess_role_1", role="Thermal CAD Modeler")
        self.assertEqual(label, "Thermal")
        self.assertLessEqual(len(label), 12)

    def test_contextual_agent_label_claude_cwd(self):
        label = app.get_stable_agent_label("claude", "sess_cl_1", cwd="/Users/dev/Documents/Tiny AI Limits")
        self.assertEqual(label, "Limits")
        self.assertLessEqual(len(label), 12)

    def test_contextual_agent_label_length_limit(self):
        # Long objective or words must never exceed 12 characters
        lines = [
            json.dumps({"type": "CHECKPOINT", "content": "# USER Objective:\nSupercalifragilisticexpialidocious"})
        ]
        label = app.get_stable_agent_label("antigravity", "sess_long_1", transcript_lines=lines)
        self.assertLessEqual(len(label), 12)
        self.assertEqual(label, "Supercalifra")

    def test_session_name_stability_and_collision(self):
        # Same session returns same label on subsequent calls
        lines = [json.dumps({"type": "CHECKPOINT", "content": "# USER Objective:\nFirmware Build\n"})]
        lbl1 = app.get_stable_agent_label("antigravity", "sess_stable_1", transcript_lines=lines)
        lbl2 = app.get_stable_agent_label("antigravity", "sess_stable_1", transcript_lines=lines)
        self.assertEqual(lbl1, lbl2)

        # Another session with identical context gets disambiguated
        lbl3 = app.get_stable_agent_label("antigravity", "sess_stable_2", transcript_lines=lines)
        self.assertNotEqual(lbl1, lbl3)
        self.assertLessEqual(len(lbl3), 12)

if __name__ == "__main__":
    unittest.main()



