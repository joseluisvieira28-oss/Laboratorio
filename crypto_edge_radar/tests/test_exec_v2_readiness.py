import unittest
from datetime import datetime, timezone

from radar.exec_v2_readiness import ExecV2Inputs, evaluate_exec_v2_readiness


class ExecV2ReadinessTests(unittest.TestCase):
    def _base(self, direction="LONG", **changes):
        data = dict(
            direction=direction,
            account_fee_verified_read_only=True,
            venue_min_notional_quote=1.0,
            account_equity_quote=10000.0,
            public_market_binding_ok=True,
            observed_full_spread_bps=0.5,
            simulated_market_impact_bps=0.5,
            taker_fee_bps_per_side=4.0,
            conservative_funding_burden_bps=0.0,
            isolated_margin_confirmed=(direction == "SHORT"),
            auto_margin_add_off_confirmed=(direction == "SHORT"),
            leverage_1x_confirmed=(direction == "SHORT"),
            conflicting_position_or_order=False,
            execution_authority_present=False,
        )
        data.update(changes)
        return ExecV2Inputs(**data)

    def test_long_spot_can_be_readiness_ready_without_authority(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 11, 59, 30, tzinfo=timezone.utc)
        r = evaluate_exec_v2_readiness(self._base("LONG"), now=now, entry_target=target)
        self.assertTrue(r["ready_for_execution_authority"])
        self.assertFalse(r["micro_live_allowed"])
        self.assertEqual(r["mapping"]["market"], "MEXC_SPOT")
        self.assertEqual(r["max_initial_allocation_quote"], 10.0)
        self.assertIn("SEPARATE_EXECUTION_AUTHORITY_ABSENT", r["blockers"])

    def test_short_requires_isolated_auto_margin_off_and_one_x(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
        r = evaluate_exec_v2_readiness(
            self._base(
                "SHORT",
                isolated_margin_confirmed=False,
                auto_margin_add_off_confirmed=False,
                leverage_1x_confirmed=False,
                execution_authority_present=True,
            ),
            now=now,
            entry_target=target,
        )
        self.assertIn("SHORT_ISOLATED_MARGIN_NOT_CONFIRMED", r["blockers"])
        self.assertIn("SHORT_AUTO_MARGIN_ADD_NOT_CONFIRMED_OFF", r["blockers"])
        self.assertIn("SHORT_LEVERAGE_NOT_CONFIRMED_1X", r["blockers"])
        self.assertFalse(r["micro_live_allowed"])

    def test_stress20_friction_gate_blocks(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
        r = evaluate_exec_v2_readiness(
            self._base(
                "SHORT",
                taker_fee_bps_per_side=7.0,
                observed_full_spread_bps=2.0,
                simulated_market_impact_bps=1.0,
                conservative_funding_burden_bps=2.0,
                execution_authority_present=True,
            ),
            now=now,
            entry_target=target,
        )
        self.assertGreater(r["projected_round_trip_bps"], 20)
        self.assertIn("PROJECTED_FRICTION_EXCEEDS_STRESS20", r["blockers"])
        self.assertFalse(r["micro_live_allowed"])

    def test_minimum_notional_above_point_one_percent_equity_blocks(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
        r = evaluate_exec_v2_readiness(
            self._base(
                "LONG",
                venue_min_notional_quote=10.01,
                execution_authority_present=True,
            ),
            now=now,
            entry_target=target,
        )
        self.assertIn("VENUE_MIN_NOTIONAL_EXCEEDS_VALIDATION_BUDGET", r["blockers"])
        self.assertFalse(r["micro_live_allowed"])

    def test_missed_entry_never_chases(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 3, tzinfo=timezone.utc)
        r = evaluate_exec_v2_readiness(
            self._base("LONG", execution_authority_present=True),
            now=now,
            entry_target=target,
        )
        self.assertIn("MISSED_ENTRY_NO_CHASE", r["blockers"])
        self.assertFalse(r["late_chase_allowed"])
        self.assertFalse(r["micro_live_allowed"])

    def test_exact_due_short_can_open_only_with_all_gates_and_authority(self):
        target = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
        r = evaluate_exec_v2_readiness(
            self._base("SHORT", execution_authority_present=True),
            now=now,
            entry_target=target,
        )
        self.assertTrue(r["micro_live_allowed"])
        self.assertEqual(r["mapping"]["leverage"], 1)
        self.assertEqual(r["mapping"]["margin_mode"], "ISOLATED")
        self.assertFalse(r["authenticated_exchange_api_used_by_this_evaluator"])
        self.assertFalse(r["order_created_by_this_evaluator"])


if __name__ == "__main__":
    unittest.main()
