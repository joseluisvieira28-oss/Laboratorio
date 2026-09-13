from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from research.phase_b_h02_us_eu_overlap_session_gate_v01 import (
    SESSION_END_HOUR_UTC_EXCLUSIVE,
    SESSION_START_HOUR_UTC,
)
from research.phase_b_h03_binance_daily_manifest_v01 import (
    EXPECTED_ARCHIVE_COUNT,
    EXPECTED_DAY_COUNT,
    FREEZE_FINGERPRINT,
    UNIVERSE,
    build_h03_manifest_receipt,
    expected_h03_daily_objects,
)


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
FREEZE_PATH = RESEARCH / "PHASE_B_H03_BINANCE_CROSS_VENUE_US_EU_OVERLAP_REPLICATION_PROSPECTIVE_FREEZE_V0.1.json"
AUTH_TEMPLATE_PATH = RESEARCH / "PHASE_B_H03_BINANCE_DATA_ACCESS_AUTHORIZATION_TEMPLATE_V0.1.json"
EXPECTED_FREEZE_FINGERPRINT = "0c7c931bd48d4cd696e4a8f3188db64e497716dbc7020eb63db100aecca49fa7"


class PhaseBH03BinanceCrossVenueReplicationTests(unittest.TestCase):
    def test_freeze_fingerprint_is_deterministic(self):
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        body = dict(payload)
        expected = body.pop("fingerprint")
        actual = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(expected, EXPECTED_FREEZE_FINGERPRINT)
        self.assertEqual(actual, EXPECTED_FREEZE_FINGERPRINT)
        self.assertEqual(FREEZE_FINGERPRINT, EXPECTED_FREEZE_FINGERPRINT)

    def test_h03_changes_only_confirmatory_venue_dimension(self):
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        dimension = payload["single_new_dimension"]
        self.assertEqual(dimension["name"], "INDEPENDENT_CROSS_VENUE_REPLICATION")
        self.assertEqual(dimension["generation_target_venue"], "MEXC Spot")
        self.assertEqual(dimension["confirmatory_replication_venue"], "Binance Spot")
        self.assertFalse(dimension["changes_signal_geometry"])
        self.assertFalse(dimension["changes_management"])
        self.assertFalse(dimension["changes_session_rule"])
        self.assertFalse(dimension["changes_symbol_universe"])
        self.assertFalse(dimension["changes_scoring"])
        self.assertTrue(payload["origin"]["h03_is_not_cross_exchange_backfill_for_h01_or_h02"])

    def test_h02_session_rule_is_inherited_exactly(self):
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        session = payload["session_rule"]
        self.assertTrue(session["inherit_h02_session_rule_exactly"])
        self.assertEqual(session["start_inclusive"], "13:00:00")
        self.assertEqual(session["end_exclusive"], "17:00:00")
        self.assertEqual(session["eligible_utc_hours"], [13, 14, 15, 16])
        self.assertEqual(SESSION_START_HOUR_UTC, 13)
        self.assertEqual(SESSION_END_HOUR_UTC_EXCLUSIVE, 17)
        self.assertFalse(session["dst_adjustment"])

    def test_exact_six_symbol_24_month_binance_discovery_is_frozen(self):
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(tuple(payload["symbol_universe"]), UNIVERSE)
        data = payload["data_contract"]
        self.assertEqual(data["source"], "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY")
        self.assertEqual(data["market_type"], "SPOT")
        self.assertEqual(data["timeframe"], "15m")
        self.assertEqual(data["archive_granularity"], "DAILY_ZIP_FILES")
        self.assertTrue(data["checksum_required"])
        discovery = data["confirmatory_discovery"]
        self.assertEqual(discovery["start_utc_inclusive"], "2021-02-01T00:00:00.000Z")
        self.assertEqual(discovery["end_utc_exclusive"], "2023-02-01T00:00:00.000Z")
        self.assertEqual(discovery["calendar_months"], 24)
        self.assertEqual(discovery["minimum_resolved_trades"], 100)

    def test_existing_phase_b_base_and_stress_costs_are_unchanged(self):
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        costs = payload["cost_policy"]
        self.assertTrue(costs["use_existing_phase_b_cost_scenarios_unchanged"])
        self.assertEqual(costs["base_selection"]["round_trip_cost_pct"], 0.20)
        self.assertEqual(costs["fixed_cohort_stress"]["round_trip_cost_pct"], 0.30)
        self.assertEqual(costs["base_selection"]["name"], "BASE_SENSITIVITY")
        self.assertEqual(costs["fixed_cohort_stress"]["name"], "STRESS")

    def test_daily_manifest_is_exactly_730_days_times_six_without_network_access(self):
        objects = expected_h03_daily_objects()
        self.assertEqual(EXPECTED_DAY_COUNT, 730)
        self.assertEqual(EXPECTED_ARCHIVE_COUNT, 4380)
        self.assertEqual(len(objects), 4380)
        self.assertEqual(objects[0]["symbol"], "BTCUSDT")
        self.assertEqual(objects[0]["date_utc"], "2021-02-01")
        self.assertTrue(objects[0]["archive_url"].endswith("/BTCUSDT/15m/BTCUSDT-15m-2021-02-01.zip"))
        self.assertTrue(objects[0]["checksum_url"].endswith(".zip.CHECKSUM"))
        self.assertEqual(objects[-1]["symbol"], "DOGEUSDT")
        self.assertEqual(objects[-1]["date_utc"], "2023-01-31")
        receipt = build_h03_manifest_receipt()
        self.assertEqual(receipt["expected_archive_count"], 4380)
        self.assertEqual(receipt["expected_checksum_count"], 4380)
        self.assertFalse(receipt["market_data_access_authorized"])
        self.assertFalse(receipt["network_download_authorized"])

    def test_all_unopened_mexc_and_2026_routes_remain_locked(self):
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        authority = payload["authority_boundary"]
        self.assertFalse(authority["this_file_authorizes_h03_market_data_access"])
        self.assertFalse(authority["this_file_authorizes_network_download"])
        self.assertFalse(authority["this_file_authorizes_mexc_2025_09_through_2025_12"])
        self.assertFalse(authority["this_file_authorizes_2026"])
        self.assertFalse(authority["exchange_mutation_authorized"])
        self.assertFalse(authority["live_trading_authorized"])
        self.assertTrue(authority["gate_k_phase_a_unchanged"])
        self.assertEqual(
            payload["future_target_venue_validation"]["mexc_2025_09_through_2025_12"],
            "REMAINS_LOCKED_DURING_H03_BINANCE_DISCOVERY",
        )

    def test_survival_policy_and_sample_floor_cannot_be_weakened(self):
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        policy = payload["decision_policy"]
        self.assertEqual(policy["minimum_resolved_trades"], 100)
        self.assertEqual(policy["if_below_100"], "INSUFFICIENT_SAMPLE_STOP")
        self.assertEqual(policy["if_any_survival_gate_fails"], "NO_EDGE_STOP")
        self.assertTrue(policy["no_sensitivity_rescue"])
        self.assertTrue(policy["no_parameter_edits_after_h03_data_access"])
        self.assertEqual(
            policy["survives_requires_all"],
            [
                "minimum_resolved_trade_count_met",
                "base_net_expectancy_r_gt_0",
                "base_profit_factor_r_gt_1",
                "bootstrap_lower_95_gt_0",
                "fixed_cohort_stress_net_expectancy_r_gt_0",
            ],
        )

    def test_authorization_template_is_explicitly_non_authorizing(self):
        payload = json.loads(AUTH_TEMPLATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "TEMPLATE_NOT_AUTHORIZATION")
        self.assertEqual(
            payload["required_bindings"]["h03_prospective_freeze_fingerprint"],
            EXPECTED_FREEZE_FINGERPRINT,
        )
        self.assertIsNone(payload["required_bindings"]["manifest_fingerprint"])
        self.assertFalse(payload["market_data_access_authorized"])
        self.assertFalse(payload["network_download_authorized"])
        self.assertFalse(payload["mexc_validation_2025_09_through_2025_12_authorized"])
        self.assertFalse(payload["holdout_2026_authorized"])
        self.assertFalse(payload["exchange_mutation_authorized"])
        self.assertFalse(payload["live_trading_authorized"])


if __name__ == "__main__":
    unittest.main()
