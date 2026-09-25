from __future__ import annotations

from datetime import datetime, timezone
import unittest

from radar.options_v21_futures_execution_signal import build_futures_execution_signal


class FuturesSignalForkTests(unittest.TestCase):
    def _entry(self, position=1, weight=0.7):
        return {
            "event_key": "OPTIONS-SPOTPERP-001:V2.1:2026-09-25",
            "signal_date": "2026-09-25",
            "entry_date": "2026-09-26",
            "entry_price": 100000.0,
            "position": position,
            "weight": weight,
        }

    def test_long_becomes_btc_perpetual_long_without_spot_route(self):
        s = build_futures_execution_signal(
            self._entry(1, 0.7),
            watcher_status="OK",
            now_utc=datetime(2026, 9, 26, 0, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(s["signal_direction"], "LONG")
        self.assertEqual(s["route"], "MEXC_USDT_PERP_BTC_USDT")
        self.assertEqual(s["symbol"], "BTC_USDT")
        self.assertEqual(s["instrument_type"], "USDT_PERPETUAL")
        self.assertEqual(s["planned_notional_usdt"], 7.0)
        self.assertFalse(s["promotion_credit_to_spot_parent"])

    def test_short_becomes_btc_perpetual_short(self):
        s = build_futures_execution_signal(
            self._entry(-1, 1.0),
            watcher_status="OK",
            now_utc=datetime(2026, 9, 26, 0, 0, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(s["signal_direction"], "SHORT")
        self.assertEqual(s["route"], "MEXC_USDT_PERP_BTC_USDT")
        self.assertEqual(s["exit_target_utc"], "2026-09-27T00:00:00Z")

    def test_no_chase_after_300_seconds(self):
        s = build_futures_execution_signal(
            self._entry(1, 1.0),
            watcher_status="OK",
            now_utc=datetime(2026, 9, 26, 0, 5, 1, tzinfo=timezone.utc),
        )
        self.assertFalse(s["entry_window_open"])
        self.assertFalse(s["late_chase_allowed"])


if __name__ == "__main__":
    unittest.main()
