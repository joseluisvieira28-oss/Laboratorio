from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from research.phase_b_h02_confirmatory_sample_planner_v01 import (
    load_h02_sample_contract,
    plan_h02_confirmatory_window,
)


UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
PREFLIGHT_PATH = Path(__file__).resolve().parents[1] / "research" / "PHASE_B_H02_CONFIRMATORY_DATA_ADEQUACY_PREFLIGHT_V0.1.json"


def months(start: str, end: str) -> list[str]:
    sy, sm = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out = []
    cursor = sy * 12 + sm - 1
    final = ey * 12 + em - 1
    while cursor <= final:
        y, m0 = divmod(cursor, 12)
        out.append(f"{y:04d}-{m0 + 1:02d}")
        cursor += 1
    return out


class PhaseBH02ConfirmatorySamplePlannerTests(unittest.TestCase):
    def test_contract_fingerprint_is_deterministic_and_market_data_locked(self):
        payload = load_h02_sample_contract()
        body = dict(payload)
        expected = body.pop("fingerprint")
        actual = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(expected, actual)
        self.assertEqual(
            expected,
            "8d374ad946e2f7c6124c911fff61a76df9d0195ebe01b4c12b7b56a7640f3bb5",
        )
        self.assertFalse(payload["authority_boundary"]["this_file_authorizes_market_candle_bytes"])
        self.assertFalse(payload["authority_boundary"]["this_file_authorizes_2026"])

    def test_exact_24_month_common_suffix_is_catalog_adequate_but_not_authorized(self):
        available = {symbol: months("2021-02", "2023-01") for symbol in UNIVERSE}
        result = plan_h02_confirmatory_window(available)
        self.assertEqual(result["common_contiguous_source_month_count"], 24)
        self.assertEqual(result["proposed_source_month_start"], "2021-02")
        self.assertEqual(result["proposed_source_month_end"], "2023-01")
        self.assertEqual(
            result["status"],
            "CATALOG_ADEQUATE_FREEZE_EXACT_WINDOW_BEFORE_DATA_ACCESS",
        )
        self.assertTrue(result["eligible_for_separate_data_access_authorization"])
        self.assertFalse(result["validation_2025_09_through_2025_12_authorized"])
        self.assertFalse(result["holdout_2026_authorized"])

    def test_23_month_common_suffix_fails_closed_before_candle_access(self):
        available = {symbol: months("2021-03", "2023-01") for symbol in UNIVERSE}
        result = plan_h02_confirmatory_window(available)
        self.assertEqual(result["common_contiguous_source_month_count"], 23)
        self.assertEqual(
            result["status"],
            "CATALOG_INADEQUATE_DO_NOT_OPEN_CONFIRMATORY_CANDLES",
        )
        self.assertFalse(result["eligible_for_separate_data_access_authorization"])
        self.assertFalse(result["market_candle_values_read"])

    def test_internal_common_gap_shortens_suffix_instead_of_backfilling(self):
        available = {symbol: months("2020-01", "2023-01") for symbol in UNIVERSE}
        available["SOLUSDT"].remove("2022-06")
        result = plan_h02_confirmatory_window(available)
        self.assertEqual(result["proposed_source_month_start"], "2022-07")
        self.assertEqual(result["common_contiguous_source_month_count"], 7)
        self.assertFalse(result["eligible_for_separate_data_access_authorization"])

    def test_missing_2023_01_for_one_symbol_blocks_common_suffix(self):
        available = {symbol: months("2020-01", "2023-01") for symbol in UNIVERSE}
        available["DOGEUSDT"].remove("2023-01")
        result = plan_h02_confirmatory_window(available)
        self.assertEqual(result["common_contiguous_source_month_count"], 0)
        self.assertIsNone(result["proposed_source_month_start"])
        self.assertFalse(result["eligible_for_separate_data_access_authorization"])

    def test_manifest_must_preserve_exact_six_symbol_universe(self):
        available = {symbol: months("2021-02", "2023-01") for symbol in UNIVERSE[:-1]}
        with self.assertRaisesRegex(ValueError, "exactly the frozen H02 universe"):
            plan_h02_confirmatory_window(available)

    def test_later_month_metadata_cannot_move_cutoff_past_2023_01(self):
        available = {symbol: months("2021-01", "2025-12") for symbol in UNIVERSE}
        result = plan_h02_confirmatory_window(available)
        self.assertEqual(result["proposed_source_month_end"], "2023-01")
        self.assertEqual(result["common_contiguous_source_month_count"], 25)

    def test_contract_preserves_100_trade_floor_and_q4_2025_as_later_validation(self):
        payload = load_h02_sample_contract()
        self.assertEqual(
            payload["primary_confirmatory_discovery_route"]["realized_sample_gate"]["minimum_resolved_trades"],
            100,
        )
        self.assertEqual(
            payload["later_temporal_validation_route"]["minimum_resolved_trades"],
            30,
        )
        self.assertEqual(
            payload["contamination_boundary"]["unopened_2025_09_through_2025_12"],
            "RESERVED_FOR_LATER_TEMPORAL_VALIDATION_ONLY",
        )
        self.assertTrue(
            payload["sample_adequacy_fail_closed_policy"]["never_use_2026_to_rescue_sample_size"]
        )

    def test_metadata_only_preflight_closes_primary_h02_route_without_outcome_classification(self):
        payload = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "DATA_INADEQUATE_UNDER_FROZEN_H02_SOURCE_UNIVERSE")
        self.assertEqual(payload["frozen_primary_route_test"]["current_visible_common_contiguous_months_ending_2023_01"], 0)
        self.assertFalse(payload["frozen_primary_route_test"]["calendar_coverage_gate_met"])
        self.assertEqual(
            payload["frozen_primary_route_test"]["result"],
            "DO_NOT_OPEN_CONFIRMATORY_CANDLES_H02_DATA_INADEQUATE",
        )
        self.assertTrue(payload["interpretation"]["this_is_not_no_edge"])
        self.assertFalse(payload["interpretation"]["h02_confirmatory_edge_test_performed"])
        self.assertFalse(payload["authority_boundary"]["2025_09_through_2025_12_access_performed"])
        self.assertFalse(payload["authority_boundary"]["2026_access_performed"])
        self.assertTrue(payload["forbidden_rescues"]["lower_minimum_trade_threshold"])
        self.assertTrue(payload["forbidden_rescues"]["expand_symbol_universe_inside_h02"])


if __name__ == "__main__":
    unittest.main()
