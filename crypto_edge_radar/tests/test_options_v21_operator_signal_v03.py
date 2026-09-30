from __future__ import annotations

from datetime import datetime, timezone
import unittest

from radar.options_v21_operator_signal_v03 import (
    ENTRY_TTL_SECONDS,
    build_operator_signal,
)


class OptionsV21OperatorSignalV03Tests(unittest.TestCase):
    def entry(self, position=1, weight=1.0):
        return {
            "event_key": "OPTIONS-SPOTPERP-001:V2.1:2026-09-29",
            "signal_date": "2026-09-29",
            "entry_date": "2026-09-30",
            "entry_price": 100000.0,
            "position": position,
            "weight": weight,
        }

    def test_long_maps_to_5x_isolated_operator_futures(self):
        signal = build_operator_signal(
            self.entry(position=1, weight=1.0),
            watcher_status="OK",
            now_utc=datetime(2026, 9, 30, 0, 0, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(signal["symbol"], "BTC_USDT")
        self.assertEqual(signal["direction"], "LONG")
        self.assertEqual(signal["leverage"], 5)
        self.assertEqual(signal["margin_mode"], "ISOLATED")
        self.assertEqual(signal["max_initial_margin_usdt"], 10.0)
        self.assertEqual(signal["max_notional_usdt"], 50.0)
        self.assertFalse(signal["scientific_credit"])
        self.assertFalse(signal["promotion_credit_to_spot_parent"])

    def test_parent_weight_scales_operator_envelope_down_only(self):
        signal = build_operator_signal(
            self.entry(position=-1, weight=0.4),
            watcher_status="OK",
            now_utc=datetime(2026, 9, 30, 0, 0, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(signal["direction"], "SHORT")
        self.assertEqual(signal["max_initial_margin_usdt"], 4.0)
        self.assertEqual(signal["max_notional_usdt"], 20.0)

    def test_no_chase_after_frozen_300_second_window(self):
        signal = build_operator_signal(
            self.entry(),
            watcher_status="OK",
            now_utc=datetime(2026, 9, 30, 0, 5, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(signal["max_late_seconds"], ENTRY_TTL_SECONDS)
        self.assertFalse(signal["entry_window_open"])
        self.assertFalse(signal["late_chase_allowed"])


if __name__ == "__main__":
    unittest.main()
