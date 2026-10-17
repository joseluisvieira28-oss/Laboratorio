"""Offline synthetic contracts: NO market observations, requests or orders."""
import unittest
from venue_fee_gate import REQUIRED_LIVE_EVIDENCE, evidence_gate, scenario_cost_bps


class FeeGateTests(unittest.TestCase):
    def test_mexc_taker_taker_16bps(self):
        self.assertEqual(scenario_cost_bps("MEXC_FUTURES_API")["fee_bps_roundtrip"], "16")

    def test_kraken_taker_taker_10bps(self):
        self.assertEqual(scenario_cost_bps("KRAKEN_DERIVATIVES")["fee_bps_roundtrip"], "10")

    def test_bybit_taker_taker_11bps(self):
        self.assertEqual(scenario_cost_bps("BYBIT_FUTURES")["fee_bps_roundtrip"], "11.0")

    def test_mexc_maker_taker_14bps(self):
        self.assertEqual(scenario_cost_bps("MEXC_FUTURES_API", entry="maker")["fee_bps_roundtrip"], "14")

    def test_kraken_maker_taker_7bps(self):
        self.assertEqual(scenario_cost_bps("KRAKEN_DERIVATIVES", entry="maker")["fee_bps_roundtrip"], "7")

    def test_original_mexc_base_20bps_excluding_spread(self):
        self.assertEqual(scenario_cost_bps("MEXC_FUTURES_API")["total_cost_bps_roundtrip"], "20")

    def test_sol_observed_old_spread_is_illustrative_only(self):
        x = scenario_cost_bps("MEXC_FUTURES_API", total_spread_impact_bps="0.93127")
        self.assertEqual(x["total_cost_bps_roundtrip"], "20.93127")

    def test_funding_credit_signed(self):
        x = scenario_cost_bps("KRAKEN_DERIVATIVES", net_funding_cost_bps="-3")
        self.assertEqual(x["total_cost_bps_roundtrip"], "11")

    def test_unknown_venue_rejected(self):
        with self.assertRaises(ValueError):
            scenario_cost_bps("FAKE_VENUE")

    def test_negative_slippage_rejected(self):
        with self.assertRaises(ValueError):
            scenario_cost_bps("KRAKEN_DERIVATIVES", total_adverse_slippage_bps="-1")

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            scenario_cost_bps("KRAKEN_DERIVATIVES", total_adverse_slippage_bps="NaN")

    def test_ambiguous_liquidity_rejected(self):
        with self.assertRaises(ValueError):
            scenario_cost_bps("KRAKEN_DERIVATIVES", entry="limit")

    def test_missing_all_evidence_blocks(self):
        r = evidence_gate({})
        self.assertEqual(r["state"], "NO_LIVE_GO")
        self.assertEqual(len(r["missing_evidence"]), len(REQUIRED_LIVE_EVIDENCE))

    def test_string_true_never_passes(self):
        r = evidence_gate({k: "true" for k in REQUIRED_LIVE_EVIDENCE})
        self.assertEqual(len(r["missing_evidence"]), len(REQUIRED_LIVE_EVIDENCE))

    def test_complete_evidence_never_auto_authorizes(self):
        r = evidence_gate({k: True for k in REQUIRED_LIVE_EVIDENCE})
        self.assertEqual(r["state"], "EVIDENCE_COMPLETE_REQUIRES_SEPARATE_HUMAN_AUTHORIZATION")
        self.assertTrue(r["does_not_authorize_trades"])


if __name__ == "__main__":
    unittest.main()
