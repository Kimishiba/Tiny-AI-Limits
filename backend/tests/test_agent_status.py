import os
import sys
import json
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import check_agent_status, check_antigravity_status, check_claude_status

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

    def test_antigravity_run_command_pending(self):
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
                            "args": {"CommandLine": "gh pr create"}
                        }
                    ]
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "ALLOW CMD")
            self.assertEqual(status["source"], "antigravity")

    def test_antigravity_file_edit_pending(self):
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
                            "name": "replace_file_content",
                            "args": {"TargetFile": "/path/to/file"}
                        }
                    ]
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[brain_dir], claude_dirs=[], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "ALLOW EDIT")
            self.assertEqual(status["source"], "antigravity")

    def test_claude_bash_pending(self):
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
                                "input": {"command": "git push"}
                            }
                        ]
                    }
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[], claude_dirs=[tmp_dir], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "ALLOW BASH")
            self.assertEqual(status["source"], "claude")

    def test_claude_file_edit_pending(self):
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
                                "name": "FileEdit",
                                "input": {"file_path": "main.py"}
                            }
                        ]
                    }
                }) + "\n")
            
            status = check_agent_status(antigravity_dirs=[], claude_dirs=[tmp_dir], now_ts=time.time())
            self.assertTrue(status["waiting_for_input"])
            self.assertEqual(status["prompt_text"], "ALLOW EDIT")
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

if __name__ == "__main__":
    unittest.main()


