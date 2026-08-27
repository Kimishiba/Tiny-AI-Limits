import os
import json
import time
import unittest
from app import check_agent_status, scan_antigravity_sessions, scan_claude_sessions, get_multi_agent_status

class TestAgentStatus(unittest.TestCase):
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

    def test_priority_waiting_for_input_over_completed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            ag_dir = os.path.join(tmp_dir, "brain")
            ag_session = os.path.join(ag_dir, "session1", ".system_generated", "logs")
            os.makedirs(ag_session, exist_ok=True)
            ag_file = os.path.join(ag_session, "transcript.jsonl")
            # Finished turn recently
            with open(ag_file, "w") as f:
                f.write(json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": []}) + "\n")

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
        from app import get_multi_agent_status
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
                    "message": {"content": [{"type": "tool_use", "name": "Bash"}]}
                }) + "\n")

            now = time.time()
            res = get_multi_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[claude_dir], now_ts=now)
            self.assertTrue(res["waiting_for_input"])
            self.assertTrue(res["has_active_agents"])
            self.assertEqual(len(res["active_agents"]), 2)
            # The waiting AGY agent must be sorted first
            self.assertEqual(res["active_agents"][0]["state"], "WAITING")
            self.assertEqual(res["active_agents"][0]["source"], "antigravity")

if __name__ == "__main__":
    unittest.main()


