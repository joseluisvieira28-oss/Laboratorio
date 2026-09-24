import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from state_receipt import build_state_receipt, verify_state_receipt


class StateReceiptTests(unittest.TestCase):
    def _build(self):
        return build_state_receipt(
            lab_id="MARKET-REVEAL-CONFIRMATION-REACTION-001",
            venue="SYNTHETIC_VENUE",
            native_symbol="SYNTHETIC_SYMBOL",
            event_or_impulse_id="SYNTHETIC-001",
            anchor_ns=100,
            decision_ns=200,
            state={
                "flow_imbalance": 0.5,
                "decision_return_bps": 10.0,
                "retracement_fraction": 0.25,
            },
            raw_segment_sha256=["a" * 64, "b" * 64],
            timestamp_semantics={
                "trade": "SYNTHETIC",
                "book": "SYNTHETIC",
            },
            sequence_diagnostics={"status": "PASS"},
            implementation_head_sha="c" * 40,
            measurement_catalog_sha256="d" * 64,
        )

    def test_receipt_is_deterministic_and_verifiable(self):
        a = self._build()
        b = self._build()
        self.assertEqual(a["receipt_sha256"], b["receipt_sha256"])
        self.assertTrue(verify_state_receipt(a))

    def test_tampering_breaks_verification(self):
        receipt = self._build()
        receipt["state"]["flow_imbalance"] = 0.9
        self.assertFalse(verify_state_receipt(receipt))

    def test_missing_raw_hash_fails(self):
        with self.assertRaises(ValueError):
            build_state_receipt(
                lab_id="X",
                venue="X",
                native_symbol="X",
                event_or_impulse_id="X",
                anchor_ns=1,
                decision_ns=2,
                state={},
                raw_segment_sha256=[],
                timestamp_semantics={},
                sequence_diagnostics={},
                implementation_head_sha="c" * 40,
                measurement_catalog_sha256="d" * 64,
            )

    def test_future_target_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            build_state_receipt(
                lab_id="X",
                venue="X",
                native_symbol="X",
                event_or_impulse_id="X",
                anchor_ns=1,
                decision_ns=2,
                state={"future_return": 0.1},
                raw_segment_sha256=["a" * 64],
                timestamp_semantics={},
                sequence_diagnostics={},
                implementation_head_sha="c" * 40,
                measurement_catalog_sha256="d" * 64,
            )


if __name__ == "__main__":
    unittest.main()
