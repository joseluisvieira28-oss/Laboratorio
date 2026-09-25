import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from h02_ruleset import validate_h02_ruleset

RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)
AUTHORITY = json.loads(
    (MODULE_DIR / "H02_DESIGN_FREEZE_AUTHORITY_V01.json").read_text(encoding="utf-8")
)
CLASSIFIER = json.loads(
    (MODULE_DIR / "H02_CLASSIFIER_SPEC_V01.json").read_text(encoding="utf-8")
)
CATALOG = (MODULE_DIR / "MEASUREMENT_CATALOG_V01.md").read_bytes()


class H02RulesetTests(unittest.TestCase):
    def test_frozen_ruleset_is_internally_valid(self):
        ready, blockers = validate_h02_ruleset(
            RULESET, AUTHORITY, CLASSIFIER, CATALOG
        )
        self.assertTrue(ready, blockers)

    def test_decision_clock_mutation_fails(self):
        r = copy.deepcopy(RULESET)
        r["decision_state"]["decision_clock_seconds"] = 300
        ready, blockers = validate_h02_ruleset(
            r, AUTHORITY, CLASSIFIER, CATALOG
        )
        self.assertFalse(ready)
        self.assertIn("DECISION_CLOCK_MUTATION", blockers)
        self.assertIn("RULESET_FINGERPRINT_MISMATCH", blockers)

    def test_target_authority_cannot_leak_into_design_freeze(self):
        a = copy.deepcopy(AUTHORITY)
        a["scope"]["target_observation"] = True
        ready, blockers = validate_h02_ruleset(
            RULESET, a, CLASSIFIER, CATALOG
        )
        self.assertFalse(ready)
        self.assertIn("TARGET_OBSERVATION_MUST_REMAIN_LOCKED", blockers)

    def test_measurement_catalog_mutation_fails(self):
        ready, blockers = validate_h02_ruleset(
            RULESET,
            AUTHORITY,
            CLASSIFIER,
            CATALOG + b"mutation",
        )
        self.assertFalse(ready)
        self.assertIn("MEASUREMENT_CATALOG_FINGERPRINT_MISMATCH", blockers)


if __name__ == "__main__":
    unittest.main()
