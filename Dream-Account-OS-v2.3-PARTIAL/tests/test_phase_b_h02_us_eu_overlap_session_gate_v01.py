from __future__ import annotations

import hashlib
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research.phase_b_h02_us_eu_overlap_session_gate_v01 import (
    FAMILY_ID,
    FREEZE_FINGERPRINT,
    HOLDOUT_2026_AUTHORIZED,
    HYPOTHESIS_ID,
    LIVE_AUTHORIZED,
    NEW_MARKET_DATA_ACCESS_AUTHORIZED,
    NETWORK_DOWNLOAD_AUTHORIZED,
    SESSION_END_HOUR_UTC_EXCLUSIVE,
    SESSION_START_HOUR_UTC,
    VALIDATION_2025_09_THROUGH_2025_12_AUTHORIZED,
    EXCHANGE_MUTATION_AUTHORIZED,
    is_h02_entry_open_time_eligible,
)


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "PHASE_B_H02_US_EU_OVERLAP_SESSION_GATE_PROSPECTIVE_FREEZE_V0.1.json"
H01_FREEZE_PATH = ROOT / "research" / "PHASE_B_H01_PROTECT_AFTER_TP1_PROSPECTIVE_FREEZE_V0.1.json"


def ms(year: int, month: int, day: int, hour: int, minute: int = 0) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=timezone.utc).timestamp() * 1000)


class PhaseBH02SessionGateTests(unittest.TestCase):
    def test_identity_and_exact_session_are_frozen(self) -> None:
        self.assertEqual(HYPOTHESIS_ID, "H02_US_EU_OVERLAP_SESSION_GATE")
        self.assertEqual(FAMILY_ID, "PBR03_SESSION_GATED_MANAGED_BREAKOUT_RETEST_LONG")
        self.assertEqual(SESSION_START_HOUR_UTC, 13)
        self.assertEqual(SESSION_END_HOUR_UTC_EXCLUSIVE, 17)

    def test_exact_start_is_included_and_exact_end_is_excluded(self) -> None:
        self.assertTrue(is_h02_entry_open_time_eligible(ms(2026, 1, 5, 13, 0)))
        self.assertTrue(is_h02_entry_open_time_eligible(ms(2026, 1, 5, 16, 45)))
        self.assertFalse(is_h02_entry_open_time_eligible(ms(2026, 1, 5, 12, 45)))
        self.assertFalse(is_h02_entry_open_time_eligible(ms(2026, 1, 5, 17, 0)))

    def test_fixed_utc_gate_does_not_change_with_dst_season(self) -> None:
        self.assertTrue(is_h02_entry_open_time_eligible(ms(2026, 1, 15, 14, 30)))
        self.assertTrue(is_h02_entry_open_time_eligible(ms(2026, 7, 15, 14, 30)))
        self.assertFalse(is_h02_entry_open_time_eligible(ms(2026, 1, 15, 18, 0)))
        self.assertFalse(is_h02_entry_open_time_eligible(ms(2026, 7, 15, 18, 0)))

    def test_timestamp_must_be_nonnegative_integer_and_15m_aligned(self) -> None:
        with self.assertRaises(TypeError):
            is_h02_entry_open_time_eligible(True)
        with self.assertRaises(TypeError):
            is_h02_entry_open_time_eligible(1.5)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            is_h02_entry_open_time_eligible(-900000)
        with self.assertRaises(ValueError):
            is_h02_entry_open_time_eligible(ms(2026, 1, 5, 13, 0) + 1)

    def test_freeze_fingerprint_is_deterministic(self) -> None:
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        fingerprint = payload.pop("fingerprint")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.assertEqual(fingerprint, FREEZE_FINGERPRINT)
        self.assertEqual(recomputed, FREEZE_FINGERPRINT)

    def test_freeze_keeps_all_unopened_data_and_live_routes_locked(self) -> None:
        payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FROZEN_RULES_ONLY_DATA_CONTRACT_NOT_YET_AUTHORIZED")
        self.assertFalse(payload["origin"]["generation_data_eligible_for_h02_classification"])
        self.assertEqual(
            payload["data_contract"]["unopened_2025_09_through_2025_12"]["status"],
            "LOCKED_NOT_AUTHORIZED_FOR_H02_BY_THIS_FREEZE",
        )
        self.assertEqual(payload["data_contract"]["final_holdout_2026"]["status"], "LOCKED")
        self.assertEqual(
            payload["data_contract"]["h02_confirmatory_window"]["status"],
            "NOT_YET_FROZEN_PENDING_SAMPLE_ADEQUACY_DESIGN",
        )
        authority = payload["authority_boundary"]
        self.assertFalse(authority["this_file_authorizes_any_new_market_data_access"])
        self.assertFalse(authority["validation_2025_09_through_2025_12_authorized"])
        self.assertFalse(authority["holdout_2026_authorized"])
        self.assertFalse(authority["network_download_authorized"])
        self.assertFalse(authority["real_trading_authorized"])
        self.assertFalse(authority["exchange_mutation_authorized"])
        self.assertFalse(authority["main_merge_authorized"])
        self.assertFalse(authority["render_deploy_authorized"])
        self.assertTrue(payload["decision_governance"]["minimum_sample_not_reduced_to_fit_available_data"])

    def test_module_level_authority_flags_are_all_fail_closed(self) -> None:
        self.assertFalse(NEW_MARKET_DATA_ACCESS_AUTHORIZED)
        self.assertFalse(VALIDATION_2025_09_THROUGH_2025_12_AUTHORIZED)
        self.assertFalse(HOLDOUT_2026_AUTHORIZED)
        self.assertFalse(NETWORK_DOWNLOAD_AUTHORIZED)
        self.assertFalse(LIVE_AUTHORIZED)
        self.assertFalse(EXCHANGE_MUTATION_AUTHORIZED)

    def test_h01_freeze_is_unchanged_and_bound_by_exact_fingerprint(self) -> None:
        h01 = json.loads(H01_FREEZE_PATH.read_text(encoding="utf-8"))
        h02 = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(h01["fingerprint"], "5229b820df2fc40036fe064e2b25361f3905b63345732f960eb7d9e457033d0b")
        self.assertEqual(h02["inherited_signal_and_management"]["h01_freeze_fingerprint"], h01["fingerprint"])
        self.assertFalse(h02["single_new_rule"]["changes_signal_geometry"])
        self.assertFalse(h02["single_new_rule"]["changes_h01_management"])
        self.assertFalse(h02["single_new_rule"]["changes_scoring"])


if __name__ == "__main__":
    unittest.main()
