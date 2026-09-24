from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from radar.bnb_launchpool_diamond_v02 import (
    BLOCKED_EVENT,
    MEASUREMENT_EVENT,
    MinuteBar,
    evaluate_bnb_diamond_v02,
    first_minute_open_strictly_after,
    measure_causal_event,
)
from radar.evidence import EvidenceStore


MINUTE = 60_000


class FakeMinuteFeed:
    provider = "BINANCE_SPOT_DATA_API_PUBLIC"

    def __init__(self, event_start_ms: int) -> None:
        self.event_start_ms = event_start_ms

    def exact_window(self, *, symbol: str, start_ms: int, minutes: int, now_ms: int):
        rows = []
        event = start_ms == self.event_start_ms
        for i in range(minutes):
            if symbol == "BNBBTC":
                op = 1.0
                if event:
                    close = 1.01 if i < 15 else 1.02
                else:
                    close = 1.0
                qv = 50.0
            elif symbol == "BNBUSDT":
                op = 200.0
                close = 202.0 if event else 200.0
                qv = 200.0 if event else 100.0
            else:
                op = 50_000.0
                close = 50_000.0
                qv = 1000.0
            rows.append(
                MinuteBar(
                    open_time=start_ms + i * MINUTE,
                    open=op,
                    close=close,
                    quote_volume=qv,
                    close_time=start_ms + (i + 1) * MINUTE - 1,
                )
            )
        return rows


class BNBDiamondV02Tests(unittest.TestCase):
    def test_causal_measurement_is_deterministic_and_uses_prior20_baseline(self):
        signal = 1_800_000_012_345
        start = first_minute_open_strictly_after(signal)
        feed = FakeMinuteFeed(start)
        result = measure_causal_event(
            feed,
            signal_timestamp_ms=signal,
            now_ms=start + 61 * MINUTE,
        )
        self.assertEqual(result["status"], "COMPLETE")
        self.assertAlmostEqual(result["bnbbtc_return_15m"], 0.01, places=12)
        self.assertAlmostEqual(result["bnbbtc_return_60m"], 0.02, places=12)
        self.assertAlmostEqual(result["bnbusdt_volume_shock_ratio"], 2.0, places=12)
        self.assertEqual(len(result["baseline_dates_utc"]), 20)
        self.assertEqual(len(result["measurement_sha256"]), 64)
        self.assertFalse(result["authenticated_exchange_api_used"])
        self.assertFalse(result["orders_created"])

    def test_causal_window_never_peeks_before_full_60_minutes(self):
        signal = 1_800_000_012_345
        start = first_minute_open_strictly_after(signal)
        result = measure_causal_event(
            FakeMinuteFeed(start),
            signal_timestamp_ms=signal,
            now_ms=start + 30 * MINUTE,
        )
        self.assertEqual(result["status"], "WAITING_CAUSAL_WINDOW")

    def _store(self):
        td = tempfile.TemporaryDirectory()
        store = EvidenceStore(str(Path(td.name) / "evidence.sqlite3"))
        return td, store

    def _seed_positive_25(self, store: EvidenceStore):
        for i in range(25):
            key = f"BNB-DIAMOND:{i:02d}"
            store.append_once(
                MEASUREMENT_EVENT,
                key,
                {
                    "event_key": key,
                    "signal_timestamp_ms": 1_800_000_000_000 + i * 1000,
                    "bnbbtc_return_60m": 0.01,
                    "bnbusdt_volume_shock_ratio": 1.5,
                },
            )
            store.append_once(
                "BNB_FORWARD_RESOLUTION",
                key,
                {
                    "event_key": key,
                    "base_net_bps": 10.0,
                    "stress_net_bps": 1.0,
                },
            )

    def test_exact_first_25_positive_events_survive_for_review(self):
        td, store = self._store()
        try:
            self._seed_positive_25(store)
            result = evaluate_bnb_diamond_v02(store)
            self.assertEqual(
                result["classification"],
                "DIAMOND_TEST_SURVIVES__REVIEW_REQUIRED",
            )
            self.assertEqual(result["evaluated_events"], 25)
            self.assertEqual(result["positive_bnbbtc_60m_events"], 25)
            self.assertEqual(result["volume_shock_gt_one_events"], 25)
            self.assertTrue(all(result["gates"].values()))
            self.assertFalse(result["automatic_promotion"])
            self.assertFalse(result["live_trading_authorized"])
        finally:
            td.cleanup()

    def test_missed_eligible_event_forces_fail_at_25_no_rescue(self):
        td, store = self._store()
        try:
            self._seed_positive_25(store)
            store.append_once(
                "BNB_FORWARD_MISSED_PROSPECTIVE_OBSERVATION",
                "missed-1",
                {
                    "event_key": "missed-1",
                    "used_as_forward_trade_evidence": False,
                },
            )
            result = evaluate_bnb_diamond_v02(store)
            self.assertEqual(
                result["classification"],
                "DIAMOND_TEST_FAIL__EXACT_CANDIDATE_NO_RESCUE",
            )
            self.assertFalse(result["gates"]["missed_eligible_events_eq_0"])
        finally:
            td.cleanup()

    def test_less_than_25_never_gets_early_verdict(self):
        td, store = self._store()
        try:
            for i in range(4):
                key = f"small:{i}"
                store.append_once(
                    MEASUREMENT_EVENT,
                    key,
                    {
                        "event_key": key,
                        "signal_timestamp_ms": 1_800_000_000_000 + i,
                        "bnbbtc_return_60m": -0.10,
                        "bnbusdt_volume_shock_ratio": 0.5,
                    },
                )
                store.append_once(
                    "BNB_FORWARD_RESOLUTION",
                    key,
                    {"event_key": key, "base_net_bps": -100.0},
                )
            result = evaluate_bnb_diamond_v02(store)
            self.assertEqual(result["classification"], "DIAMOND_TEST_COLLECTING")
            self.assertEqual(result["evaluated_events"], 4)
        finally:
            td.cleanup()

    def test_blocked_measurement_is_visible_but_not_silently_counted(self):
        td, store = self._store()
        try:
            store.append_once(
                BLOCKED_EVENT,
                "blocked-1",
                {"event_key": "blocked-1", "status": "MECHANISM_DATA_BLOCKED"},
            )
            result = evaluate_bnb_diamond_v02(store)
            self.assertEqual(result["mechanism_data_blocked_events"], 1)
            self.assertEqual(result["matched_resolved_events"], 0)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
