import unittest
from datetime import datetime, timezone

from radar.bnb_microlive_readiness import (
    BNBMicroLiveInputs,
    evaluate_bnb_microlive_readiness,
    projected_round_trip_bps,
)


class BNBMicroLiveReadinessTests(unittest.TestCase):
    def _base(self, **changes):
        data = dict(
            signal_eligible=True,
            prospective_event=True,
            source_timestamp_unambiguous=True,
            bnbbtc_market_binding_ok=True,
            duplicate_or_cluster_violation=False,
            overlapping_active_trade=False,
            account_fee_verified_read_only=True,
            venue_min_notional_chf=5.0,
            observed_full_spread_bps=1.0,
            simulated_market_impact_bps=1.0,
            taker_fee_bps_per_side=5.0,
            execution_authority_present=False,
        )
        data.update(changes)
        return BNBMicroLiveInputs(**data)

    def test_friction_formula_is_conservative_round_trip(self):
        self.assertEqual(
            projected_round_trip_bps(
                observed_full_spread_bps=2.0,
                simulated_market_impact_bps=1.0,
                taker_fee_bps_per_side=5.0,
            ),
            16.0,
        )

    def test_readiness_can_pass_without_authorizing_execution(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 11, 59, 30, tzinfo=timezone.utc)
        receipt = evaluate_bnb_microlive_readiness(self._base(), now=now, entry_target=target)
        self.assertTrue(receipt["ready_for_execution_authority"])
        self.assertFalse(receipt["micro_live_allowed"])
        self.assertIn("SEPARATE_EXECUTION_AUTHORITY_ABSENT", receipt["blockers"])
        self.assertFalse(receipt["late_chase_allowed"])

    def test_missed_entry_is_fail_closed_no_chase(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 3, tzinfo=timezone.utc)
        receipt = evaluate_bnb_microlive_readiness(
            self._base(execution_authority_present=True),
            now=now,
            entry_target=target,
        )
        self.assertFalse(receipt["micro_live_allowed"])
        self.assertIn("MISSED_ENTRY_NO_CHASE", receipt["blockers"])

    def test_stress30_cost_gate_blocks(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
        receipt = evaluate_bnb_microlive_readiness(
            self._base(
                execution_authority_present=True,
                taker_fee_bps_per_side=10.0,
                observed_full_spread_bps=4.0,
                simulated_market_impact_bps=2.0,
            ),
            now=now,
            entry_target=target,
        )
        self.assertGreater(receipt["projected_round_trip_bps"], 30.0)
        self.assertIn("PROJECTED_FRICTION_EXCEEDS_STRESS30", receipt["blockers"])
        self.assertFalse(receipt["micro_live_allowed"])

    def test_venue_minimum_above_chf25_blocks(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
        receipt = evaluate_bnb_microlive_readiness(
            self._base(
                execution_authority_present=True,
                venue_min_notional_chf=25.01,
            ),
            now=now,
            entry_target=target,
        )
        self.assertIn("VENUE_MIN_NOTIONAL_EXCEEDS_CHF25_CAP", receipt["blockers"])
        self.assertFalse(receipt["micro_live_allowed"])

    def test_exact_due_window_only_allows_when_authority_exists(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
        receipt = evaluate_bnb_microlive_readiness(
            self._base(execution_authority_present=True),
            now=now,
            entry_target=target,
        )
        self.assertTrue(receipt["micro_live_allowed"])
        self.assertEqual(receipt["entry_timing"]["max_late_seconds"], 2.0)
        self.assertFalse(receipt["authenticated_exchange_api_used_by_this_evaluator"])
        self.assertFalse(receipt["order_created_by_this_evaluator"])


if __name__ == "__main__":
    unittest.main()
