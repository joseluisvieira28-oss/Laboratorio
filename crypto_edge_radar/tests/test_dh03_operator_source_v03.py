from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from radar.dh03_12h_local import OPERATOR_MAX_RECEIPT_LATENCY_MS
from radar.dh03_operator_source_v03 import DH03OperatorSourceV03


class DH03OperatorSourceV03Tests(unittest.TestCase):
    def build(self, td: str) -> DH03OperatorSourceV03:
        root = Path(td)
        return DH03OperatorSourceV03(
            data_db=str(root / "market.sqlite3"),
            evidence_db=str(root / "evidence.sqlite3"),
            state_path=str(root / "state.json"),
        )

    def payload(self, *, eligible=True):
        entry = 100.0
        stop = 95.0
        target = 115.0
        return {
            "event_key": "HTF-DH03-12H-STANDALONE-FORWARD-V1:BTCUSDT:1",
            "symbol": "BTCUSDT",
            "signal": {
                "entry_open_time": 1_800_000_000_000,
                "entry": entry,
                "stop": stop,
                "target": target,
                "initial_risk_fraction": 0.05,
                "fingerprint": "abc",
            },
            "operator_candidate": {
                "eligible": eligible,
                "received_at_ms": 1_800_000_000_900,
                "source_event_time_ms": 1_800_000_000_500,
                "receipt_latency_ms": 900,
                "source_event_latency_ms": 500,
                "max_receipt_latency_ms": OPERATOR_MAX_RECEIPT_LATENCY_MS,
            },
        }

    def test_maps_relative_dh03_geometry_to_protected_mexc_operator_signal(self):
        with tempfile.TemporaryDirectory() as td:
            source = self.build(td)
            signal = source._signal_from_entry(self.payload())
            self.assertIsNotNone(signal)
            self.assertEqual(signal["symbol"], "BTC_USDT")
            self.assertEqual(signal["direction"], "LONG")
            self.assertEqual(signal["max_late_seconds"], 2.0)
            self.assertEqual(signal["leverage"], 5)
            self.assertTrue(signal["protective_exit"]["required"])
            self.assertAlmostEqual(
                signal["protective_exit"]["stop_distance_fraction"], 0.05
            )
            self.assertAlmostEqual(
                signal["protective_exit"]["take_profit_distance_fraction"], 0.15
            )
            self.assertTrue(signal["transaction_cost_ceiling_excludes_funding"])
            self.assertFalse(signal["scientific_credit"])

    def test_late_shadow_entry_never_becomes_operator_signal(self):
        with tempfile.TemporaryDirectory() as td:
            source = self.build(td)
            self.assertIsNone(
                source._signal_from_entry(self.payload(eligible=False))
            )


if __name__ == "__main__":
    unittest.main()
