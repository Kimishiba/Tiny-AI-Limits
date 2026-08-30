import os
import sys
import json
import socket
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

class TestAppEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.orig_config = dict(app.config)
        # Reset test overrides
        app.test_agents_override = None
        app.test_idle_override = False
        app.test_alert_override = False
        app.test_complete_override = False

    def tearDown(self):
        app.config = dict(self.orig_config)
        app.test_agents_override = None
        app.test_idle_override = False
        app.test_alert_override = False
        app.test_complete_override = False

    def test_cors_headers_on_all_responses(self):
        res = self.client.get('/whoami')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get('Access-Control-Allow-Origin'), '*')
        self.assertIn('Content-Type', res.headers.get('Access-Control-Allow-Headers', ''))
        self.assertIn('GET', res.headers.get('Access-Control-Allow-Methods', ''))

    def test_static_ui_endpoints(self):
        endpoints = ['/', '/emulator', '/simulator', '/round']
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"<!DOCTYPE html>", res.data)

    def test_static_ui_endpoint_missing_file_404(self):
        with patch('os.path.exists', return_value=False):
            res = self.client.get('/emulator')
            self.assertEqual(res.status_code, 404)
            self.assertIn(b"Emulator file not found", res.data)

    def test_setup_page_endpoint(self):
        res = self.client.get('/setup')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"<!DOCTYPE html>", res.data)

    def test_setup_page_missing_file_404(self):
        with patch('os.path.exists', return_value=False):
            res = self.client.get('/setup')
            self.assertEqual(res.status_code, 404)
            self.assertIn(b"Setup page not found", res.data)

    def test_setup_vendor_endpoint_and_path_traversal(self):
        # Valid vendor file
        res = self.client.get('/setup/vendor/improv-wifi-serial-launch-button.bundle.js')
        self.assertEqual(res.status_code, 200)

        # Missing vendor file
        res_404 = self.client.get('/setup/vendor/nonexistent-file.js')
        self.assertEqual(res_404.status_code, 404)

        # Path traversal attack
        res_traversal = self.client.get('/setup/vendor/../../backend/app.py')
        self.assertEqual(res_traversal.status_code, 404)

    def test_simulation_test_agents_override(self):
        # Set agents override
        agents_payload = [
            {"id": "a1", "name": "Agent 1", "state": "WORKING", "detail": "Building", "color": "#00E5FF"}
        ]
        res = self.client.post('/api/test_agents', json={"agents": agents_payload})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["test_agents_override"], agents_payload)
        self.assertFalse(app.test_idle_override)

        # Clear agents override via {"clear": True}
        res_clear = self.client.post('/api/test_agents', json={"clear": True})
        self.assertEqual(res_clear.status_code, 200)
        self.assertIsNone(res_clear.get_json()["test_agents_override"])

    def test_simulation_test_idle_override(self):
        # Explicit enable
        res = self.client.post('/api/test_idle', json={"idle": True})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["test_idle_active"])
        self.assertTrue(app.test_idle_override)

        # Explicit disable via "off"
        res_off = self.client.post('/api/test_idle', json={"idle": "off"})
        self.assertEqual(res_off.status_code, 200)
        self.assertFalse(res_off.get_json()["test_idle_active"])
        self.assertFalse(app.test_idle_override)

        # Toggle when no parameters passed
        res_toggle = self.client.post('/api/test_idle', json={})
        self.assertEqual(res_toggle.status_code, 200)
        self.assertTrue(res_toggle.get_json()["test_idle_active"])

    def test_simulation_test_alert_and_complete(self):
        # Test alert with custom prompt
        res_alert = self.client.post('/api/test_alert', json={"prompt": "APPROVE BUILD", "active": True})
        self.assertEqual(res_alert.status_code, 200)
        self.assertTrue(app.test_alert_override)
        self.assertEqual(app.test_alert_prompt, "APPROVE BUILD")

        # Test complete mode
        res_comp = self.client.post('/api/test_complete', json={"prompt": "ALL DONE", "complete": True})
        self.assertEqual(res_comp.status_code, 200)
        self.assertTrue(app.test_complete_override)
        self.assertEqual(app.test_complete_prompt, "ALL DONE")
        self.assertFalse(app.test_alert_override)

    def test_data_endpoint_remote_unpaired_rejected(self):
        app.config["allow_unpaired_clients"] = False
        app.config["pair_id"] = "secret_pair_123"

        # Remote IP without pair_id query param
        res = self.client.get('/data', environ_base={'REMOTE_ADDR': '192.168.1.100'})
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertEqual(data["error"], "not_paired")

    def test_data_endpoint_remote_paired_accepted(self):
        app.config["allow_unpaired_clients"] = False
        pair_id = app.get_pair_id(app.config)

        # Remote IP with correct pair_id query param
        res = self.client.get(f'/data?pair_id={pair_id}', environ_base={'REMOTE_ADDR': '192.168.1.100'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("left_gauge", data)
        self.assertIn("right_gauge", data)
        self.assertIn("weather", data)
        self.assertIn("agent", data)
        self.assertIn("ota", data)

    def test_data_endpoint_local_always_allowed(self):
        app.config["allow_unpaired_clients"] = False
        res = self.client.get('/data', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("left_gauge", data)
        self.assertIn("right_gauge", data)

    def test_data_endpoint_safe_error_handling_when_scanners_fail(self):
        with patch('app.get_antigravity_quota', side_effect=Exception("Antigravity server down")), \
             patch('app.scan_claude_usage', side_effect=Exception("Claude logs unavailable")):
            res = self.client.get('/data', environ_base={'REMOTE_ADDR': '127.0.0.1'})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn("left_gauge", data)
            self.assertIn("right_gauge", data)
            self.assertEqual(data["antigravity"]["limit"], 200)
            self.assertEqual(data["claude"]["limit"], 100)

    def test_data_endpoint_with_active_test_agents_override(self):
        app.test_agents_override = [
            {"id": "test1", "name": "Agent Waiting", "state": "WAITING", "detail": "GRANT PERM", "color": "#FFB800"}
        ]
        res = self.client.get('/data', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["agent"]["state"], "waiting_approval")
        self.assertEqual(data["agent"]["prompt_text"], "GRANT PERM")
        self.assertTrue(data["agent"]["waiting_for_input"])
        self.assertEqual(len(data["agent"]["active_agents"]), 1)

    def test_config_get_and_post_updates(self):
        # GET config
        app.config["provider_keys"] = {"openrouter": "sk-or-v1-abcdef123456789"}
        res = self.client.get('/config')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        # Ensure API keys are masked
        self.assertEqual(data["provider_keys"]["openrouter"], "sk-o...6789")
        self.assertIn("available_antigravity_accounts", data)

        # POST config updates
        update_payload = {
            "auto_location": False,
            "antigravity_5h_quota": 350,
            "antigravity_account_email": "engineer@google.com",
            "selected_gauges": {"left": "gemini", "right": "deepseek"},
            "provider_keys": {"deepseek": "sk-ds-998877665544"},
            "provider_plans": {"gemini": "pro", "deepseek": "payg"},
            "claude_plan": "max",
            "antigravity_plan": "ultra",
            "claude_daily_budget_usd": 15.0,
            "antigravity_daily_budget_usd": 20.0
        }
        res_post = self.client.post('/api/config', json=update_payload)
        self.assertEqual(res_post.status_code, 200)
        res_data = res_post.get_json()
        self.assertEqual(res_data["status"], "ok")
        self.assertFalse(app.config["auto_location"])
        self.assertEqual(app.config["antigravity_5h_quota"], 350)
        self.assertEqual(app.config["antigravity_account_email"], "engineer@google.com")
        self.assertEqual(app.config["selected_gauges"]["left"], "gemini")
        self.assertEqual(app.config["claude_plan"], "max")
        self.assertEqual(app.config["claude_daily_budget_usd"], 15.0)

    def test_config_post_invalid_quota_type(self):
        res = self.client.post('/api/config', json={"antigravity_5h_quota": "invalid_number"})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("antigravity_5h_quota must be an integer", data["message"])

    def test_config_post_city_geocoding(self):
        # Successful geocode
        with patch('app.geocode_city', return_value=(48.8566, 2.3522, "PARIS, FR")):
            res = self.client.post('/api/config', json={"city": "Paris"})
            self.assertEqual(res.status_code, 200)
            self.assertEqual(app.config["lat"], 48.8566)
            self.assertEqual(app.config["lon"], 2.3522)
            self.assertEqual(app.config["manual_location_name"], "PARIS, FR")

        # Failed geocode
        with patch('app.geocode_city', return_value=(None, None, None)):
            res_fail = self.client.post('/api/config', json={"city": "NonexistentCityNameXYZ"})
            self.assertEqual(res_fail.status_code, 400)
            data = res_fail.get_json()
            self.assertEqual(data["status"], "error")
            self.assertIn("Could not find city", data["message"])

    def test_whoami_endpoint(self):
        res = self.client.get('/whoami')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("ip", data)
        self.assertEqual(data["port"], app.PORT)
        self.assertIn("pair_id", data)
        self.assertIn("hostname", data)
        self.assertIn("user", data)
        self.assertEqual(data["version"], app.COMPANION_VERSION)

    def test_get_local_ip_fallback(self):
        with patch('socket.socket') as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect.side_effect = Exception("No network")
            mock_sock_cls.return_value = mock_sock
            ip = app.get_local_ip()
            self.assertEqual(ip, "127.0.0.1")

    def test_get_host_label_sanitization(self):
        with patch('socket.gethostname', return_value="MacBook Pro.local"):
            label = app.get_host_label()
            self.assertEqual(label, "MacBook-Pro")

    def test_api_providers_endpoint(self):
        res = self.client.get('/api/providers')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("providers", data)
        self.assertIsInstance(data["providers"], list)
        self.assertGreaterEqual(len(data["providers"]), 10)

    def test_api_agents_endpoint(self):
        res = self.client.get('/api/agents')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("active_agents", data)
        self.assertIn("has_active_agents", data)

    def test_firmware_latest_bin_missing_file_404(self):
        with patch('app.get_latest_firmware', return_value={"path": "/nonexistent/firmware.bin"}):
            res = self.client.get('/firmware/latest.bin')
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.get_json()["error"], "firmware_not_found")

if __name__ == '__main__':
    unittest.main()
