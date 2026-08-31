import os
import sys
import unittest
import json
import threading

# Ensure both backend directory and repository root are in sys.path
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_repo_dir = os.path.abspath(os.path.join(_backend_dir, ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
if _repo_dir not in sys.path:
    sys.path.insert(0, _repo_dir)

try:
    import app
    from providers.base import read_sqlite_kv_safe
except ImportError:
    from backend import app
    from backend.providers.base import read_sqlite_kv_safe

class TestPhase1Hardening(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_mask_key(self):
        self.assertEqual(app.mask_key(""), "")
        self.assertEqual(app.mask_key("short"), "***")
        self.assertEqual(app.mask_key("sk-ant-api03-123456789"), "sk-a...6789")

    def test_concurrent_session_label_assignment(self):
        """Ensure thread safety when assigning stable agent labels concurrently."""
        def worker(thread_id):
            for i in range(20):
                app.get_stable_agent_label("antigravity", f"session_{thread_id}_{i}")
                app.get_stable_agent_label("claude", f"session_{thread_id}_{i}")

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with app._session_registry_lock:
            self.assertGreater(len(app._session_registry), 0)
            self.assertGreater(app._session_counters["antigravity"], 0)
            self.assertGreater(app._session_counters["claude"], 0)

    def test_config_access_security(self):
        """Local callers (127.0.0.1) can access and POST /api/config."""
        res = self.client.get('/api/config', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(res.status_code, 200)
        res.close()

        res_post = self.client.post(
            '/api/config',
            data=json.dumps({"antigravity_5h_quota": 250}),
            content_type='application/json',
            environ_base={'REMOTE_ADDR': '127.0.0.1'}
        )
        self.assertEqual(res_post.status_code, 200)
        res_post.close()

    def test_unpaired_external_access_denied(self):
        """Unpaired external IP callers cannot POST /api/config or /api/ota/trigger."""
        # Unpaired external call without pair_id query
        res_post = self.client.post(
            '/api/config',
            data=json.dumps({"antigravity_5h_quota": 999}),
            content_type='application/json',
            environ_base={'REMOTE_ADDR': '192.168.1.100'}
        )
        self.assertEqual(res_post.status_code, 403)
        res_post.close()

        res_ota = self.client.post(
            '/api/ota/trigger',
            environ_base={'REMOTE_ADDR': '192.168.1.100'}
        )
        self.assertEqual(res_ota.status_code, 403)
        res_ota.close()

    def test_paired_external_access_granted(self):
        """Paired external IP callers with valid pair_id can access protected routes."""
        cfg = app.load_config()
        pair_id = cfg.get("pair_id")
        self.assertIsNotNone(pair_id)

        res_post = self.client.post(
            f'/api/config?pair_id={pair_id}',
            data=json.dumps({"antigravity_5h_quota": 200}),
            content_type='application/json',
            environ_base={'REMOTE_ADDR': '192.168.1.100'}
        )
        self.assertEqual(res_post.status_code, 200)
        res_post.close()

    def test_concurrent_save_config(self):
        """Ensure concurrent save_config calls with unique temp files execute safely."""
        def saver(val):
            cfg = app.load_config()
            cfg["test_val"] = val
            app.save_config(cfg)

        threads = [threading.Thread(target=saver, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final_cfg = app.load_config()
        self.assertIn("test_val", final_cfg)

    def test_read_sqlite_kv_safe_nonexistent(self):
        """Ensure read_sqlite_kv_safe returns None gracefully for nonexistent DBs."""
        val = read_sqlite_kv_safe("/non/existent/path/state.vscdb", "ItemTable", "key", "value", "target")
        self.assertIsNone(val)

if __name__ == "__main__":
    unittest.main()
