import unittest

from radar.forward_web import dashboard_html


class ForwardWebDashboardTests(unittest.TestCase):
    def test_dashboard_is_read_only_and_exposes_shadow_state(self):
        html = dashboard_html()
        self.assertIn("Crypto Edge Radar V1.0", html)
        self.assertIn("Persistent public shadow", html)
        self.assertIn("/api/state", html)
        self.assertIn("TFG Donchian Regime", html)
        self.assertIn("BNB Launchpool", html)
        self.assertIn("DH03 12H Standalone", html)
        self.assertIn("FAIL-CLOSED", html)
        self.assertNotIn("Place Order", html)
        self.assertNotIn("API Key", html)
        self.assertNotIn("Secret", html)


if __name__ == "__main__":
    unittest.main()
