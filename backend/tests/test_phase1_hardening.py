import unittest
import json
import threading
from backend.app import (
    app,
    save_config,
    load_config,
    get_stable_agent_label,
    mask_key,
    _session_registry,
    _session_counters,
    _session_registry_lock,
)
from backend.providers.base import read_sqlite_kv_safe

class TestPhase1Hardening(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_mask_key(self):
        self.assertEqual(mask_key(""), "")
        self.assertEqual(mask_key("short"), "***")
        self.assertEqual(mask_key("sk-ant-api03-123456789"), "sk-a...6789")

    def test_concurrent_session_label_assignment(self):
        """Ensure thread safety when assigning stable agent labels concurrently."""
        def worker(thread_id):
            for i in range(20):
                get_stable_agent_label("antigravity", f"session_{thread_id}_{i}")
                get_stable_agent_label("claude", f"session_{thread_id}_{i}")

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with _session_registry_lock:
            self.assertGreater(len(_session_registry), 0)
            self.assertGreater(_session_counters["antigravity"], 0)
            self.assertGreater(_session_counters["claude"], 0)

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

    def test_read_sqlite_kv_safe_nonexistent(self):
        """Ensure read_sqlite_kv_safe returns None gracefully for nonexistent DBs."""
        val = read_sqlite_kv_safe("/non/existent/path/state.vscdb", "ItemTable", "key", "value", "target")
        self.assertIsNone(val)

if __name__ == "__main__":
    unittest.main()
