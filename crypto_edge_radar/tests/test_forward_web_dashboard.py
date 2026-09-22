import unittest

from radar.forward_web import dashboard_html, normalized_poll_interval_seconds


class ForwardWebDashboardTests(unittest.TestCase):
    def test_dls_probe_endpoint_is_read_only_surface(self):
        source = __import__("inspect").getsource(__import__(
            "radar.forward_web", fromlist=["_Handler"]
        )._Handler.do_GET)
        self.assertIn("/api/dls-solanafm-source-probe", source)
        self.assertNotIn("POST", source)

    def test_poll_interval_floor_is_30_seconds(self):
        self.assertEqual(normalized_poll_interval_seconds(1), 30.0)
        self.assertEqual(normalized_poll_interval_seconds(30), 30.0)
        self.assertEqual(normalized_poll_interval_seconds(45), 45.0)
        with self.assertRaises(ValueError):
            normalized_poll_interval_seconds(0)

    def test_dashboard_is_read_only_and_exposes_shadow_state(self):
        html = dashboard_html()
        self.assertIn("Crypto Edge Radar V0.9", html)
        self.assertIn("Persistent public shadow", html)
        self.assertIn("/api/state", html)
        self.assertIn("TFG Donchian Regime", html)
        self.assertIn("BNB Launchpool", html)
        self.assertIn("ETF-CME Signal Watcher", html)
        self.assertIn("External Collectors", html)
        self.assertIn("FAIL-CLOSED", html)
        self.assertNotIn("Place Order", html)
        self.assertNotIn("API Key", html)
        self.assertNotIn("Secret", html)


if __name__ == "__main__":
    unittest.main()
