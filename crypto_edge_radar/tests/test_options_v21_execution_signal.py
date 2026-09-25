from __future__ import annotations

from datetime import datetime, timezone
import unittest

from radar.options_v21_execution_signal import (
    ENTRY_TTL_SECONDS,
    build_execution_signal,
)


class SignalBridgeTests(unittest.TestCase):
    def _entry(self, position=1, weight=0.6):
        return {
            "event_key": "OPTIONS-SPOTPERP-001:V2.1:2026-09-25",
            "signal_date": "2026-09-25",
            "entry_date": "2026-09-26",
            "entry_price": 100000.0,
            "position": position,
            "weight": weight,
        }

    def test_long_route_and_24h_exit(self):
        now = datetime(2026, 9, 26, 0, 1, tzinfo=timezone.utc)
        s = build_execution_signal(self._entry(1, 0.6), watcher_status="OK", now_utc=now)
        self.assertEqual(s["signal_direction"], "LONG")
        self.assertEqual(s["route"], "MEXC_SPOT_BTCUSDT")
        self.assertEqual(s["planned_notional_usdt"], 6.0)
        self.assertEqual(s["exit_target_utc"], "2026-09-27T00:00:00Z")
        self.assertTrue(s["entry_window_open"])

    def test_short_route(self):
        now = datetime(2026, 9, 26, 0, 0, 30, tzinfo=timezone.utc)
        s = build_execution_signal(self._entry(-1, 1.0), watcher_status="OK", now_utc=now)
        self.assertEqual(s["signal_direction"], "SHORT")
        self.assertEqual(s["route"], "MEXC_USDT_PERP_BTC_USDT")
        self.assertEqual(s["planned_notional_usdt"], 10.0)

    def test_no_chase_after_ttl(self):
        now = datetime(2026, 9, 26, 0, 0, int(ENTRY_TTL_SECONDS) + 1, tzinfo=timezone.utc)
        s = build_execution_signal(self._entry(), watcher_status="OK", now_utc=now)
        self.assertFalse(s["entry_window_open"])
        self.assertFalse(s["late_chase_allowed"])

    def test_source_failure_does_not_open_execution(self):
        now = datetime(2026, 9, 26, 0, 1, tzinfo=timezone.utc)
        s = build_execution_signal(self._entry(), watcher_status="FAIL_CLOSED", now_utc=now)
        self.assertFalse(s["source_healthy"])


if __name__ == "__main__":
    unittest.main()
