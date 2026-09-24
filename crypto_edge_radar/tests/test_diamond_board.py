from __future__ import annotations

import unittest

from radar.diamond_board import build_diamond_board


class DiamondBoardTests(unittest.TestCase):
    def test_options_does_not_early_fail_before_first_50(self):
        board = build_diamond_board({
            "options_v21_metrics": {
                "resolved_forward_trades": 4,
                "base_net_mean_bps": -106.15,
                "base_profit_factor": 0.356,
                "stress_net_mean_bps": -116.06,
                "integrity": {"pass": True},
                "tier1_forward_gate": {
                    "minimum_resolved_forward_trades": 50,
                    "first_50_window_locked": False,
                    "statistical_gate_pass": False,
                },
            }
        })
        row = board["candidates"]["OPTIONS-SPOTPERP-001-V2.1"]
        self.assertEqual(row["state"], "COLLECTING__NO_EARLY_VERDICT")
        self.assertEqual(row["progress"], "4/50")
        self.assertFalse(row["verdict_allowed_now"])

    def test_etf_never_surfaces_interim_outcome_metrics(self):
        board = build_diamond_board({
            "etf_cme_signal": {
                "source_status": "OK",
                "status": "MISSED_EXPECTED_OBSERVATION_NO_CHASE",
                "missed_expected_observation_count": 1,
            },
            "etf_cme_exact_scheduler": {
                "status": "WAITING_NEW_CFTC_AS_OF_AFTER_BOUNDARY",
            },
        })
        row = board["candidates"]["ETF-CME-INSTFLOW-001"]
        self.assertEqual(row["state"], "Q4_OUTCOMES_SEALED__SOURCE_ONLY")
        self.assertEqual(row["outcomes_sealed_until_utc"], "2027-01-01T00:00:00Z")
        self.assertFalse(row["interim_pnl_allowed"])
        self.assertNotIn("base_mean_bps_descriptive", row)

    def test_ced_routes_only_when_existing_gate_says_eligible(self):
        board = build_diamond_board({
            "ced1d_render_shadow": {
                "status": "SHADOW_COLLECTION_COMPLETE",
                "metrics": {
                    "resolved_trade_events": 60,
                    "complete_utc_signal_weeks": 8,
                    "routing": "TIER1_ADJUDICATION_ELIGIBLE",
                },
            }
        })
        row = board["candidates"]["CED1D-0031"]
        self.assertEqual(
            row["state"],
            "PROSPECTIVE_GATE_PASS__DIAMOND_RECONCILIATION_ELIGIBLE",
        )
        self.assertTrue(row["verdict_allowed_now"])

    def test_bnb_sidecar_never_creates_full_verdict_by_itself(self):
        board = build_diamond_board({
            "bnb_launchpool": {
                "status": "OK",
                "eligible_events_visible": 1,
            },
            "bnb_diamond_v02": {
                "status": "OK",
                "complete_causal_measurements": 25,
                "blocked_causal_measurements": 0,
                "summary": {
                    "verdict_allowed_now": True,
                    "causal_gate_pass": True,
                },
            },
        })
        row = board["candidates"]["BNB-LAUNCHPOOL-DEMAND-001"]
        self.assertEqual(
            row["state"],
            "CAUSAL_GATE_READY_FOR_PARENT_RECONCILIATION",
        )
        self.assertTrue(row["diamond_contract_canonical"])
        self.assertTrue(row["parent_reconciliation_required"])
        self.assertFalse(row["verdict_allowed_now"])

    def test_safety_is_read_only(self):
        board = build_diamond_board({
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        })
        self.assertEqual(
            board["safety"],
            {
                "authenticated_exchange_api_used": False,
                "orders_created": False,
                "exchange_mutation_performed": False,
                "live_capital_enabled": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
