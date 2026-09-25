import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from science_lock import evaluate_science_lock

PROTOCOL = json.loads(
    (MODULE_DIR / "PRETARGET_PROTOCOL_TEMPLATE_V01.json").read_text(encoding="utf-8")
)
CALENDAR = json.loads(
    (MODULE_DIR / "OFFICIAL_CALENDAR_MANIFEST_TEMPLATE_V01.json").read_text(encoding="utf-8")
)
READINESS = json.loads(
    (MODULE_DIR / "PRETARGET_READINESS_MATRIX_2026-09-24.json").read_text(encoding="utf-8")
)
AUTHORITY = json.loads(
    (MODULE_DIR / "H02_DESIGN_FREEZE_AUTHORITY_V01.json").read_text(encoding="utf-8")
)
RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)
CLASSIFIER = json.loads(
    (MODULE_DIR / "H02_CLASSIFIER_SPEC_V01.json").read_text(encoding="utf-8")
)
CATALOG = (MODULE_DIR / "MEASUREMENT_CATALOG_V01.md").read_bytes()


class ScienceLockTests(unittest.TestCase):
    def test_current_design_frozen_target_locked_state_is_valid(self):
        locked, violations = evaluate_science_lock(
            PROTOCOL,
            CALENDAR,
            READINESS,
            AUTHORITY,
            RULESET,
            CLASSIFIER,
            CATALOG,
        )
        self.assertTrue(locked, violations)

    def test_arming_h02_breaks_lock(self):
        p = copy.deepcopy(PROTOCOL)
        p["governance"]["h02_authorized"] = True
        locked, violations = evaluate_science_lock(
            p, CALENDAR, READINESS, AUTHORITY, RULESET, CLASSIFIER, CATALOG
        )
        self.assertFalse(locked)
        self.assertIn("H02_ARMED_WITHOUT_AUTHORITY_TRANSITION", violations)

    def test_selecting_depth_breaks_lock(self):
        p = copy.deepcopy(PROTOCOL)
        p["decision_state"]["depth_definition"] = {"mode": "TOP_N", "value": 10}
        locked, violations = evaluate_science_lock(p, CALENDAR, READINESS)
        self.assertFalse(locked)
        self.assertIn("DEPTH_RULE_PRESELECTED", violations)

    def test_selecting_availability_rule_breaks_lock_before_transition(self):
        p = copy.deepcopy(PROTOCOL)
        p["decision_state"]["availability_rule"] = "SOURCE_AND_COLLECTOR_ARRIVAL"
        locked, violations = evaluate_science_lock(p, CALENDAR, READINESS)
        self.assertFalse(locked)
        self.assertIn("AVAILABILITY_RULE_PRESELECTED", violations)

    def test_populating_calendar_breaks_lock(self):
        c = copy.deepcopy(CALENDAR)
        c["complete_official_calendar"] = True
        c["event_families"] = ["SYNTHETIC"]
        locked, violations = evaluate_science_lock(
            PROTOCOL, c, READINESS, AUTHORITY, RULESET, CLASSIFIER, CATALOG
        )
        self.assertFalse(locked)
        self.assertIn("CALENDAR_TEMPLATE_MARKED_COMPLETE", violations)

    def test_readiness_cannot_silently_promote_h02(self):
        r = copy.deepcopy(READINESS)
        for row in r["gates"]:
            if row["gate"] == "H02":
                row["status"] = "NOT_AUTHORIZED"
        locked, violations = evaluate_science_lock(
            PROTOCOL, CALENDAR, r, AUTHORITY, RULESET, CLASSIFIER, CATALOG
        )
        self.assertFalse(locked)
        self.assertIn("READINESS_H02_STATUS_CHANGED", violations)


if __name__ == "__main__":
    unittest.main()
