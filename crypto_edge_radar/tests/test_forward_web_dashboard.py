import unittest

from radar.forward_web import (
    CED1D_ARCHIVE_RETRY_MS,
    ced1d_runtime_check_due,
    dashboard_html,
    normalized_poll_interval_seconds,
)


class ForwardWebDashboardTests(unittest.TestCase):
    def test_poll_interval_floor_is_30_seconds(self):
        self.assertEqual(normalized_poll_interval_seconds(1), 30.0)
        self.assertEqual(normalized_poll_interval_seconds(30), 30.0)
        self.assertEqual(normalized_poll_interval_seconds(45), 45.0)
        with self.assertRaises(ValueError):
            normalized_poll_interval_seconds(0)

    def test_ced1d_archive_pending_retries_same_day_without_hammering(self):
        now_ms = 1_800_000_000_000
        self.assertFalse(
            ced1d_runtime_check_due(
                current_day="2026-09-25",
                last_check_day="2026-09-25",
                last_check_ms=now_ms - CED1D_ARCHIVE_RETRY_MS + 1,
                state_status="WAITING_SOURCE_ARCHIVE",
                now_ms=now_ms,
            )
        )
        self.assertTrue(
            ced1d_runtime_check_due(
                current_day="2026-09-25",
                last_check_day="2026-09-25",
                last_check_ms=now_ms - CED1D_ARCHIVE_RETRY_MS,
                state_status="WAITING_SOURCE_ARCHIVE",
                now_ms=now_ms,
            )
        )
        self.assertFalse(
            ced1d_runtime_check_due(
                current_day="2026-09-25",
                last_check_day="2026-09-25",
                last_check_ms=now_ms - CED1D_ARCHIVE_RETRY_MS,
                state_status="FAIL_CLOSED",
                now_ms=now_ms,
            )
        )
        self.assertTrue(
            ced1d_runtime_check_due(
                current_day="2026-09-26",
                last_check_day="2026-09-25",
                last_check_ms=now_ms,
                state_status="FAIL_CLOSED",
                now_ms=now_ms,
            )
        )

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
