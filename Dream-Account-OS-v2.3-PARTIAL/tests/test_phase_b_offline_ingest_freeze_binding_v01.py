import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_FREEZE = ROOT / "research" / "PHASE_B_PRE_DATA_RESEARCH_FREEZE_V0.1.json"
INGEST_FREEZE = ROOT / "research" / "PHASE_B_OFFLINE_DATA_INGEST_FREEZE_V0.1.json"


class PhaseBOfflineIngestFreezeBindingTests(unittest.TestCase):
    def test_main_freeze_binds_to_exact_offline_ingest_contract(self):
        main = json.loads(MAIN_FREEZE.read_text(encoding="utf-8"))
        ingest = json.loads(INGEST_FREEZE.read_text(encoding="utf-8"))
        binding = main["offline_ingest_contract"]

        self.assertEqual(binding["contract_file"], INGEST_FREEZE.name)
        self.assertEqual(binding["status"], ingest["status"])
        self.assertEqual(binding["canonical_schema"], ingest["canonical_schema"]["schema_id"])
        self.assertEqual(
            binding["raw_mexc_adapter_status"],
            ingest["source_policy"]["raw_mexc_adapter_status"],
        )
        self.assertEqual(
            binding["first_real_file_action"],
            ingest["handoff_rule"]["first_real_file_action"],
        )

    def test_locked_stages_and_p00_wiring_remain_false_in_both_contracts(self):
        main = json.loads(MAIN_FREEZE.read_text(encoding="utf-8"))
        ingest = json.loads(INGEST_FREEZE.read_text(encoding="utf-8"))
        binding = main["offline_ingest_contract"]

        self.assertFalse(binding["validation_2025_market_data_access"])
        self.assertFalse(binding["holdout_2026_market_data_access"])
        self.assertFalse(binding["p00_evaluator_wiring"])
        self.assertFalse(ingest["handoff_rule"]["p00_evaluator_wiring_in_this_release"])
        self.assertIn("PHYSICALLY_LOCKED", ingest["stage_lock"]["validation_2025_status"])
        self.assertIn("PHYSICALLY_LOCKED", ingest["stage_lock"]["holdout_2026_status"])

    def test_main_freeze_and_ingest_contract_both_forbid_irregular_spacing(self):
        main = json.loads(MAIN_FREEZE.read_text(encoding="utf-8"))
        ingest = json.loads(INGEST_FREEZE.read_text(encoding="utf-8"))
        self.assertFalse(main["offline_ingest_contract"]["irregular_interval_spacing_allowed"])
        self.assertFalse(ingest["integrity_audit"]["irregular_interval_spacing_allowed"])

    def test_unknown_raw_mexc_schema_still_cannot_be_guessed(self):
        main = json.loads(MAIN_FREEZE.read_text(encoding="utf-8"))
        ingest = json.loads(INGEST_FREEZE.read_text(encoding="utf-8"))
        self.assertIn("Unknown raw MEXC schemas fail closed", main["offline_ingest_contract"]["rule"])
        self.assertEqual(ingest["source_policy"]["raw_source_format_assumption"], "NONE")
        self.assertEqual(ingest["source_policy"]["unknown_raw_schema_action"], "BLOCKED_UNKNOWN_SCHEMA")


if __name__ == "__main__":
    unittest.main()
