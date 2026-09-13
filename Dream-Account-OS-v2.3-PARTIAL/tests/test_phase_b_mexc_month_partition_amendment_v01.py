from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / "research" / "PHASE_B_MEXC_MONTH_PARTITION_AMENDMENT_V0.1.json"


class PhaseBMEXCMonthPartitionAmendmentTests(unittest.TestCase):
    def test_two_real_months_freeze_utc_plus_8_partition(self):
        doc = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        self.assertEqual(doc["status"], "FROZEN_AFTER_TWO_REAL_OFFICIAL_MONTH_OBSERVATIONS")
        evidence = doc["observed_official_mexc_evidence"]
        self.assertEqual(len(evidence), 2)
        self.assertEqual([item["row_count"] for item in evidence], [2688, 2976])
        self.assertTrue(all(item["first_open_offset_from_utc_calendar_month_hours"] == -8 for item in evidence))
        self.assertTrue(all(item["last_open_offset_from_utc_calendar_month_hours"] == -8 for item in evidence))
        rule = doc["frozen_source_partition_rule"]
        self.assertEqual(rule["timezone"], "UTC+08:00")
        self.assertEqual(rule["offset_hours"], 8)
        self.assertEqual(rule["scope"], "CORPUS_INTEGRITY_AUDIT_ONLY")

    def test_partition_freeze_does_not_unlock_p00_or_2025_boundary_file(self):
        doc = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        authority = doc["authority_boundary"]
        self.assertFalse(authority["p00_evaluation_authorized"])
        self.assertFalse(authority["validation_2025_access_authorized"])
        self.assertFalse(authority["holdout_2026_access_authorized"])
        self.assertFalse(authority["cross_exchange_backfill_authorized"])
        self.assertFalse(authority["interpolation_authorized"])
        conflict = doc["discovery_boundary_conflict"]
        self.assertTrue(conflict["source_partition_and_research_utc_window_are_not_identical"])
        self.assertEqual(conflict["remaining_2024_utc_tail_hours"], 8)
        self.assertEqual(conflict["remaining_2024_utc_tail_would_reside_in_vendor_file_label"], "2025-01")
        self.assertFalse(conflict["access_to_2025_labeled_source_is_authorized"])
        self.assertTrue(conflict["utc_discovery_boundary_reconciliation_required_before_p00"])
        self.assertEqual(doc["required_pre_p00_decision"]["status"], "BLOCKED_PENDING_SEPARATE_FREEZE")


if __name__ == "__main__":
    unittest.main()
