import unittest

from radar.forward_web import (
    BINANCE_RATE_LIMIT_COOLDOWN_MS,
    CED1D_ARCHIVE_RETRY_MS,
    ced1d_runtime_check_due,
    is_binance_public_rate_limit_error,
    source_rate_limit_retry_due,
    source_rate_limit_wait_state,
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

    def test_binance_rate_limit_detector_is_narrow(self):
        self.assertTrue(is_binance_public_rate_limit_error("HTTP Error 418: I'm a teapot"))
        self.assertTrue(is_binance_public_rate_limit_error("Binance HTTP 429"))
        self.assertFalse(is_binance_public_rate_limit_error("HTTP Error 451"))
        self.assertFalse(is_binance_public_rate_limit_error("timeout"))

    def test_rate_limit_cooldown_retries_only_at_expiry(self):
        now_ms = 1_800_000_000_000
        self.assertFalse(
            source_rate_limit_retry_due(
                state_status="WAITING_SOURCE_RATE_LIMIT",
                retry_not_before_ms=now_ms + 1,
                now_ms=now_ms,
            )
        )
        self.assertTrue(
            source_rate_limit_retry_due(
                state_status="WAITING_SOURCE_RATE_LIMIT",
                retry_not_before_ms=now_ms,
                now_ms=now_ms,
            )
        )
        self.assertTrue(
            source_rate_limit_retry_due(
                state_status="FAIL_CLOSED",
                retry_not_before_ms=now_ms + BINANCE_RATE_LIMIT_COOLDOWN_MS,
                now_ms=now_ms,
            )
        )

    def test_rate_limit_wait_state_never_claims_evidence_or_capital(self):
        now_ms = 1_800_000_000_000
        state = source_rate_limit_wait_state(
            watcher_id="OPTIONS-SPOTPERP-001-V2.1-FORWARD-SHADOW",
            now_ms=now_ms,
            error="HTTP Error 418: I'm a teapot",
        )
        self.assertEqual(state["status"], "WAITING_SOURCE_RATE_LIMIT")
        self.assertEqual(state["source"], "BINANCE_PUBLIC")
        self.assertEqual(state["http_class"], "418_OR_429")
        self.assertEqual(state["cooldown_seconds"], 3600)
        self.assertFalse(state["evidence_advanced"])
        self.assertFalse(state["authenticated_exchange_api_used"])
        self.assertFalse(state["orders_created"])
        self.assertFalse(state["exchange_mutation_performed"])
        self.assertFalse(state["live_capital_enabled"])

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
