from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from radar.options_v21_execution_economics import (
    analyze_session,
    observed_fill_fee_summary,
    oos_net_at_full_notional_cost,
    oos_reference,
)


class ExecutionEconomicsTruthGateTests(unittest.TestCase):
    def test_oos_reference_is_consistent_with_frozen_net10_net20(self):
        ref = oos_reference()
        self.assertAlmostEqual(ref["average_executed_weight_implied"], 0.97187041717, places=9)
        self.assertAlmostEqual(oos_net_at_full_notional_cost(10.0), 5.0427663334, places=9)
        self.assertAlmostEqual(oos_net_at_full_notional_cost(20.0), -4.6759378383, places=9)
        self.assertLess(oos_net_at_full_notional_cost(16.0), 0.0)

    def test_observed_mexc_five_fill_fee_rate(self):
        rows = [
            {"notional_usdt": 8.4410, "fee_usdt": 0.0067},
            {"notional_usdt": 8.4433, "fee_usdt": 0.0067},
            {"notional_usdt": 8.4403, "fee_usdt": 0.0067},
            {"notional_usdt": 8.4396, "fee_usdt": 0.0067},
            {"notional_usdt": 8.4049, "fee_usdt": 0.0067},
        ]
        out = observed_fill_fee_summary(rows)
        self.assertGreater(out["weighted_fill_fee_bps"], 7.9)
        self.assertLess(out["weighted_fill_fee_bps"], 8.0)
        self.assertGreater(out["two_fill_round_trip_equivalent_bps"], 15.8)

    def test_incomplete_session_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            out = analyze_session(td)
            self.assertEqual(out["status"], "EVIDENCE_INCOMPLETE")
            self.assertFalse(out["economic_verdict_allowed"])

    def test_complete_session_decomposes_fees_and_net(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ident = "sig-1"
            payloads = {
                "CANONICAL_EXECUTION_SIGNAL.json": {"immutable_signal_key": ident},
                "ORDER_INTENT.json": {"signal_identity": ident, "external_oid": "entry-1"},
                "PRE_ORDER_GATE.json": {"bid": 100.0, "ask": 100.1},
                "FILL_RECEIPT.json": {"order": {"orderId": "e1", "dealAvgPrice": 100.2, "dealVol": 100, "totalFee": 0.08016}},
                "ACTIVE_TRADE_STATE.json": {"signal_identity": ident, "direction": "LONG"},
                "EXIT_INTENT.json": {"signal_identity": ident, "external_oid": "exit-1"},
                "PRE_EXIT_MARKET_SNAPSHOT.json": {"bid": 101.0, "ask": 101.1},
                "EXIT_FILL_RECEIPT.json": {"order": {"orderId": "x1", "dealAvgPrice": 100.9, "dealVol": 100, "totalFee": 0.08072}},
                "POST_TRADE_RECONCILIATION.json": {
                    "signal_identity": ident,
                    "funding_hold_fee_usdt": -0.01,
                    "gross_close_profit_usdt": 0.07,
                    "realized_net_pnl_usdt": -0.10088,
                },
            }
            for name, payload in payloads.items():
                (root / name).write_text(json.dumps(payload), encoding="utf-8")
            out = analyze_session(root, contract_size_btc=0.01)
            self.assertEqual(out["status"], "COMPLETE_EXECUTION_ECONOMICS")
            self.assertGreater(out["round_trip_fee_bps_on_position"], 15.0)
            self.assertEqual(out["fee_bucket"], "FEE_ONLY_BETWEEN_BASE10_AND_STRESS20")


if __name__ == "__main__":
    unittest.main()
