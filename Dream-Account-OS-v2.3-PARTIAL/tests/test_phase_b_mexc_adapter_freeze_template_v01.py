import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "research" / "PHASE_B_MEXC_RAW_ADAPTER_FREEZE_TEMPLATE_V0.1.json"


class PhaseBMEXCRawAdapterFreezeTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_template_is_blocked_and_cannot_execute_or_authorize_p00(self):
        self.assertEqual(self.template["status"], "TEMPLATE_BLOCKED_PENDING_REAL_OFFICIAL_SAMPLE")
        authority = self.template["authority_boundary"]
        self.assertFalse(authority["adapter_executable"])
        self.assertFalse(authority["p00_evaluation_authorized"])
        self.assertFalse(authority["validation_2025_access_authorized"])
        self.assertFalse(authority["holdout_2026_access_authorized"])
        self.assertFalse(authority["live_integration_authorized"])
        self.assertFalse(authority["exchange_network_access_authorized"])
        self.assertFalse(authority["exchange_mutation_authorized"])

    def test_template_requires_real_official_sample_and_hash_before_activation(self):
        rule = self.template["activation_rule"]
        self.assertFalse(rule["may_activate_from_template_alone"])
        self.assertTrue(rule["requires_real_official_mexc_sample"])
        self.assertTrue(rule["requires_structure_probe_pass"])
        self.assertTrue(rule["requires_raw_file_sha256_pin"])
        self.assertTrue(rule["requires_source_provenance_record"])
        self.assertTrue(rule["requires_mapping_review_before_any_row_values_are_interpreted"])
        self.assertTrue(rule["requires_adapter_unit_tests_before_canonical_output"])
        self.assertTrue(rule["requires_full_ci_pass_before_first_discovery_ingest"])

    def test_raw_schema_and_canonical_mapping_are_unfilled_not_guessed(self):
        raw = self.template["raw_schema_observation"]
        mapping = self.template["canonical_mapping"]
        for key, value in raw.items():
            self.assertIsNone(value, key)
        for key in ("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms"):
            self.assertIsNone(mapping[key], key)
        self.assertFalse(mapping["mapping_complete"])
        self.assertFalse(mapping["silent_field_inference_allowed"])
        self.assertFalse(mapping["silent_unit_conversion_allowed"])
        self.assertFalse(mapping["silent_timezone_conversion_allowed"])
        self.assertFalse(mapping["silent_row_drop_allowed"])
        self.assertFalse(mapping["silent_interpolation_allowed"])

    def test_source_channels_are_official_mexc_only_and_cross_exchange_rescue_is_forbidden(self):
        provenance = self.template["source_provenance"]
        self.assertEqual(provenance["exchange"], "MEXC")
        self.assertEqual(provenance["market_type"], "SPOT")
        self.assertEqual(provenance["authority"], "OFFICIAL_MEXC_SOURCE_ONLY")
        self.assertEqual(
            provenance["allowed_source_channels"],
            ["MEXC_MARKET_DATA_DOWNLOAD", "MEXC_PUBLIC_SPOT_REST_KLINES"],
        )
        stage = self.template["stage_scope"]
        self.assertEqual(stage["allowed_stage"], "DISCOVERY")
        self.assertTrue(stage["validation_2025_locked"])
        self.assertTrue(stage["holdout_2026_locked"])
        self.assertFalse(stage["cross_exchange_backfill_allowed"])
        self.assertFalse(stage["synthetic_history_allowed"])


if __name__ == "__main__":
    unittest.main()
