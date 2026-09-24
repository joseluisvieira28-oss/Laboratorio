import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from pretarget_gate import protocol_fingerprint, validate_for_freeze


TEMPLATE = MODULE_DIR / "PRETARGET_PROTOCOL_TEMPLATE_V01.json"


class PretargetGateTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_template_is_intentionally_unarmed(self):
        result = validate_for_freeze(self.template)
        self.assertFalse(result.ready)
        self.assertIn("H02_NOT_AUTHORIZED", result.blockers)
        self.assertIn("TARGET_OBSERVATION_NOT_AUTHORIZED", result.blockers)
        self.assertIn("OFFICIAL_CALENDAR_INCOMPLETE", result.blockers)
        self.assertIn("DEPTH_MODE_INVALID_OR_MISSING", result.blockers)
        self.assertIn("AVAILABILITY_RULE_INVALID_OR_MISSING", result.blockers)
        self.assertIn("OUTCOME_FUTURE_HORIZON_SECONDS_MISSING", result.blockers)

    def _synthetic_complete_protocol(self):
        p = copy.deepcopy(self.template)
        p["status"] = "SYNTHETIC_TEST_ONLY"
        p["governance"]["h02_authorized"] = True
        p["governance"]["target_observation_authorized"] = True
        p["calendar"] = {
            "complete_official_calendar": True,
            "calendar_source_manifest_sha256": "a" * 64,
            "calendar_frozen_at_utc": "2099-01-01T00:00:00Z",
            "event_families": ["SYNTHETIC_EVENT"],
        }
        p["market_scope"] = {
            "venues": ["SYNTHETIC_VENUE"],
            "native_symbols": ["SYNTHETIC_SYMBOL"],
            "cross_venue_merge_allowed": False,
        }
        p["decision_state"] = {
            "anchor_definition": "SYNTHETIC_ANCHOR",
            "decision_clock_seconds": [1],
            "availability_rule": "SOURCE_AND_COLLECTOR_ARRIVAL",
            "depth_definition": {"mode": "TOP_N", "value": 1},
            "measurement_catalog_sha256": "b" * 64,
            "implementation_head_sha": "c" * 40,
        }
        p["hypothesis"] = {
            "causal_statement": "SYNTHETIC_ONLY",
            "classifier_definition": "SYNTHETIC_ONLY",
            "classifier_sha256": "d" * 64,
            "abstention_rule": "SYNTHETIC_ONLY",
        }
        p["outcome"] = {
            "future_horizon_seconds": 1,
            "outcome_definition": "SYNTHETIC_ONLY",
            "benchmark_definition": "SYNTHETIC_ONLY",
        }
        p["economics"] = {
            "tested": False,
            "fee_model": None,
            "slippage_model": None,
            "latency_model": None,
        }
        p["freeze"] = {
            "protocol_fingerprint_sha256": None,
            "frozen_at_utc": "2099-01-01T00:00:00Z",
            "operator_authority_receipt": "SYNTHETIC_ONLY",
        }
        p["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(p)
        return p

    def test_structurally_complete_synthetic_protocol_can_pass(self):
        p = self._synthetic_complete_protocol()
        result = validate_for_freeze(p)
        self.assertTrue(result.ready, result.blockers)

    def test_mutation_after_fingerprint_is_detected(self):
        p = self._synthetic_complete_protocol()
        p["decision_state"]["depth_definition"]["value"] = 2
        result = validate_for_freeze(p)
        self.assertFalse(result.ready)
        self.assertIn("PROTOCOL_FINGERPRINT_MISMATCH", result.blockers)

    def test_cross_venue_merge_is_rejected(self):
        p = self._synthetic_complete_protocol()
        p["market_scope"]["cross_venue_merge_allowed"] = True
        p["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(p)
        result = validate_for_freeze(p)
        self.assertFalse(result.ready)
        self.assertIn("CROSS_VENUE_MERGE_POLICY_INVALID", result.blockers)

    def test_source_only_availability_rule_is_rejected(self):
        p = self._synthetic_complete_protocol()
        p["decision_state"]["availability_rule"] = "SOURCE_TIME_ONLY"
        p["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(p)
        result = validate_for_freeze(p)
        self.assertFalse(result.ready)
        self.assertIn("AVAILABILITY_RULE_INVALID_OR_MISSING", result.blockers)


if __name__ == "__main__":
    unittest.main()
