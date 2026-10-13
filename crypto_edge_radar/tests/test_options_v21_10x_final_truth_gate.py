from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.options_v21_10x_final_truth_gate import economic_bridge, verdict


class TenXFinalTruthGateTests(unittest.TestCase):
    def test_historical_cost_bridge_reproduces_frozen_result(self):
        p = Path(__file__).resolve().parents[2] / "receipts/OPTIONS_SPOTPERP_001_V21_EXECUTION_ECONOMICS_FINAL_CANONICAL_2026-09-28.json"
        x = economic_bridge(json.loads(p.read_text(encoding="utf-8")))
        self.assertAlmostEqual(x["historical_implied_break_even_cost_bps"], 15.188722945270918, places=7)
        self.assertAlmostEqual(x["historical_net_sensitivity_at_api_fee_floor_bps"], -0.78845616962, places=7)
        self.assertEqual(x["market_market_fee_only_bps_full_notional"], 16.0)
        self.assertTrue(x["fee_floor_exceeds_historical_implied_break_even"])

    def test_10x_leverage_does_not_scale_fee_fraction(self):
        fixed = {"economics": {
            "frozen_oos_net10_bps_per_opportunity": 5.0427663334,
            "frozen_oos_net20_bps_per_opportunity": -4.6759378383,
            "mexc_api_market_taker_bps_per_fill": 8,
        }}
        normal = economic_bridge(fixed)
        self.assertEqual(normal["market_market_fee_only_bps_full_notional"], 16)
        self.assertLess(normal["historical_net_sensitivity_at_api_fee_floor_bps"], 0)

    def test_missing_stop_signal_forces_no_go(self):
        f = {"status": "WAITING_LOCAL_READ_ONLY_AUDIT", "economics": {
            "frozen_oos_net10_bps_per_opportunity": 5.0427663334,
            "frozen_oos_net20_bps_per_opportunity": -4.6759378383,
            "mexc_api_market_taker_bps_per_fill": 8,
        }}
        v = verdict(
            economic_evidence=f,
            canonical_signal_source='{"leverage": 10, "margin_mode": "ISOLATED"}',
            execution_engine_source='int(signal.get("leverage") or 0) != 10\ndef _broker_stop_proven(',
            transport_source='if symbol != "BTC_USDT":\n    payload = {"leverage": 10}',
            prospective_policy="PRE-OUTCOME ENGINEERING PROTOTYPE",
        )
        self.assertFalse(v["live_go"])
        self.assertIn("NO_PRECOMMITTED_STOP_PRICE_FROM_CANONICAL_SIGNAL", v["blockers"])
        self.assertIn("TAKER_TAKER_FEES_ALONE_EXCEED_FROZEN_HISTORICAL_BREAK_EVEN", v["blockers"])

    def test_even_fake_stop_key_does_not_prove_exchange_or_edge(self):
        f = {"status": "WAITING_LOCAL_READ_ONLY_AUDIT", "economics": {
            "frozen_oos_net10_bps_per_opportunity": 5.0427663334,
            "frozen_oos_net20_bps_per_opportunity": -4.6759378383,
            "mexc_api_market_taker_bps_per_fill": 8,
        }}
        v = verdict(
            economic_evidence=f,
            canonical_signal_source='{"leverage": 10, "margin_mode": "ISOLATED", "protective_stop_loss_price": 80000}',
            execution_engine_source='int(signal.get("leverage") or 0) != 10\ndef _broker_stop_proven(',
            transport_source='if symbol != "BTC_USDT":\n    payload = {"leverage": 10}',
            prospective_policy="PRE-OUTCOME ENGINEERING PROTOTYPE",
        )
        self.assertFalse(v["live_go"])
        self.assertIn("NO_INDEPENDENT_MEXC_STOP_LIFECYCLE_PROOF", v["blockers"])
        self.assertIn("NO_PROSPECTIVE_NET_EDGE_FOR_10X_STOPPED_FORK", v["blockers"])


if __name__ == "__main__":
    unittest.main()
