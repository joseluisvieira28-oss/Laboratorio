from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from radar.options_v21_execution_economics import (
    _order_fee,
    analyze_receipt_root,
    analyze_session,
    observed_fill_fee_summary,
    oos_net_at_full_notional_cost,
    oos_reference,
)


def dump(path: Path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def complete_session(root: Path, ident: str, *, unequal_exit_notional: bool = False) -> None:
    entry_px = 100.2
    exit_px = 110.0 if unequal_exit_notional else 100.9
    entry_fee = 0.08016
    exit_fee = 0.088 if unequal_exit_notional else 0.08072
    gross = 0.07
    funding = -0.01
    net = gross + funding - entry_fee - exit_fee
    payloads = {
        "CANONICAL_EXECUTION_SIGNAL.json": {"immutable_signal_key": ident},
        "ORDER_INTENT.json": {"signal_identity": ident, "external_oid": "entry-" + ident},
        "PRE_ORDER_GATE.json": {"bid": 100.0, "ask": 100.1, "contract_size": 0.01},
        "PRE_ENTRY_MARKET_SNAPSHOT.json": {"bid": 100.05, "ask": 100.10},
        "FILL_RECEIPT.json": {"order": {"orderId": "e-" + ident, "dealAvgPrice": entry_px, "dealVol": 100, "totalFee": entry_fee}},
        "ACTIVE_TRADE_STATE.json": {"signal_identity": ident, "direction": "LONG", "contract_size": 0.01},
        "EXIT_INTENT.json": {"signal_identity": ident, "external_oid": "exit-" + ident},
        "PRE_EXIT_MARKET_SNAPSHOT.json": {"bid": exit_px + 0.1, "ask": exit_px + 0.2},
        "EXIT_FILL_RECEIPT.json": {"order": {"orderId": "x-" + ident, "dealAvgPrice": exit_px, "dealVol": 100, "totalFee": exit_fee}},
        "POST_TRADE_RECONCILIATION.json": {
            "signal_identity": ident,
            "funding_hold_fee_usdt": funding,
            "gross_close_profit_usdt": gross,
            "entry_fee_usdt": entry_fee,
            "exit_fee_usdt": exit_fee,
            "realized_net_pnl_usdt": net,
        },
    }
    for name, payload in payloads.items():
        dump(root / name, payload)


class ExecutionEconomicsTruthGateTests(unittest.TestCase):
    def test_oos_reference_is_consistent_with_frozen_net10_net20(self):
        ref = oos_reference()
        self.assertAlmostEqual(ref["average_executed_weight_implied"], 0.97187041717, places=9)
        self.assertAlmostEqual(oos_net_at_full_notional_cost(10.0), 5.0427663334, places=9)
        self.assertAlmostEqual(oos_net_at_full_notional_cost(20.0), -4.6759378383, places=9)
        self.assertLess(oos_net_at_full_notional_cost(16.0), 0.0)

    def test_zero_total_fee_falls_back_to_taker_component(self):
        order = {"totalFee": 0, "takerFee": 0.00675284, "makerFee": 0}
        self.assertAlmostEqual(_order_fee(order), 0.00675284, places=10)

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
            self.assertFalse(out["per_trade_economic_decomposition_allowed"])

    def test_exact_round_trip_fee_is_sum_of_leg_bps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            complete_session(root, "sig-1", unequal_exit_notional=True)
            out = analyze_session(root)
            self.assertEqual(out["status"], "COMPLETE_EXECUTION_ECONOMICS")
            expected = out["entry_fee_usdt"] / out["entry_notional_usdt"] * 10000.0
            expected += out["exit_fee_usdt"] / out["exit_notional_usdt"] * 10000.0
            self.assertAlmostEqual(out["round_trip_fee_bps_on_position"], expected, places=10)
            self.assertAlmostEqual(out["pnl_reference_notional_usdt"], out["entry_notional_usdt"], places=10)

    def test_pre_entry_snapshot_is_preferred_to_gate_for_slippage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            complete_session(root, "sig-2")
            out = analyze_session(root)
            self.assertEqual(out["entry_reference_source"], "PRE_ENTRY_MARKET_SNAPSHOT")
            self.assertTrue(out["accounting_identity_pass"])

    def test_accounting_identity_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            complete_session(root, "sig-3")
            recon = json.loads((root / "POST_TRADE_RECONCILIATION.json").read_text())
            recon["realized_net_pnl_usdt"] += 0.01
            dump(root / "POST_TRADE_RECONCILIATION.json", recon)
            out = analyze_session(root)
            self.assertEqual(out["status"], "ACCOUNTING_IDENTITY_MISMATCH")
            self.assertFalse(out["per_trade_economic_decomposition_allowed"])

    def test_root_requires_ten_complete_trades_for_review(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(2):
                session = root / f"s{i}"
                session.mkdir()
                complete_session(session, f"sig-{i}")
            out = analyze_receipt_root(root)
            self.assertEqual(out["status"], "INSUFFICIENT_EXECUTION_ECONOMICS_SAMPLE")
            self.assertEqual(out["complete_trade_count"], 2)
            self.assertFalse(out["strategy_economic_verdict_allowed"])


if __name__ == "__main__":
    unittest.main()
