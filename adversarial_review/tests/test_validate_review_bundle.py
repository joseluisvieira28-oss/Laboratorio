import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "tools" / "validate_review_bundle.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

MATRIX = json.loads((ROOT / "adversarial_matrix_v0_1.json").read_text(encoding="utf-8"))

def valid_bundle():
    attacks = []
    for item in MATRIX["red_attacks"]:
        if item["mandatory"]:
            attacks.append({
                "id": item["id"],
                "result": "PASS",
                "evidence_ref": "commit:deadbeef"
            })
    return {
        "candidate": {"id": "TEST-001", "version": "V1"},
        "freeze": {
            "complete": True,
            "mechanism": "frozen mechanism",
            "failure_mode": "frozen failure mode",
            "controlling_authority": "AUTH-001",
            "source_manifest": {"source": "SOURCE-001"},
            "code_commit": "deadbeef",
            "parameters": {"p": 1},
            "entry_exit_rules": {"entry": "frozen", "exit": "frozen"},
            "cost_model": {"bps": 10},
            "protected_periods": ["HOLDOUT"],
            "promotion_gates": ["GATE-1"],
            "scientific_identity_changed_after_outcome_access": False
        },
        "blue": {"verdict": "PASS", "checks": [{"id": "BT-001", "result": "PASS"}]},
        "red": {
            "verdict": "SURVIVES",
            "attack_plan_prepared_before_blue_conclusion_review": True,
            "attacks": attacks
        },
        "referee": {
            "verdict": "PROCESS_PASS",
            "higher_precedence_authority_reconciled": True
        },
        "boundaries": {
            "live_trading_authorized": False,
            "main_merge_authorized": False,
            "exchange_mutation_authorized": False,
            "sealed_holdout_open_authorized": False
        },
        "evidence": ["commit:deadbeef"]
    }

class TestValidator(unittest.TestCase):
    def test_valid_bundle_passes(self):
        self.assertEqual([], validator.validate(valid_bundle(), MATRIX))

    def test_missing_mandatory_attack_fails_closed(self):
        b = valid_bundle()
        b["red"]["attacks"] = b["red"]["attacks"][1:]
        errors = validator.validate(b, MATRIX)
        self.assertTrue(any("missing mandatory red attack" in x for x in errors))

    def test_live_authority_cannot_be_granted(self):
        b = valid_bundle()
        b["boundaries"]["live_trading_authorized"] = True
        errors = validator.validate(b, MATRIX)
        self.assertTrue(any("live_trading_authorized must be false" in x for x in errors))

    def test_post_outcome_change_requires_new_version(self):
        b = valid_bundle()
        b["freeze"]["scientific_identity_changed_after_outcome_access"] = True
        errors = validator.validate(b, MATRIX)
        self.assertTrue(any("NEW_VERSION_REQUIRED" in x for x in errors))

    def test_frozen_gate_failure_blocks_process_pass(self):
        b = valid_bundle()
        b["red"]["attacks"][0]["result"] = "FAIL"
        b["red"]["attacks"][0]["hits_frozen_failure_gate"] = True
        errors = validator.validate(b, MATRIX)
        self.assertTrue(any("frozen-gate failure" in x for x in errors))

if __name__ == "__main__":
    unittest.main()
