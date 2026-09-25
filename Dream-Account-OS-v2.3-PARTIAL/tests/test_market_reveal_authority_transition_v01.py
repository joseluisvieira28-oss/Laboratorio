import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from authority_transition import (
    H02_DESIGN_FREEZE,
    TARGET_OBSERVATION_OPEN,
    receipt_fingerprint,
    validate_authority_receipt,
)

TEMPLATE = json.loads(
    (MODULE_DIR / "AUTHORITY_TRANSITION_TEMPLATE_V01.json").read_text(encoding="utf-8")
)


class AuthorityTransitionTests(unittest.TestCase):
    def test_canonical_template_is_unissued(self):
        result = validate_authority_receipt(TEMPLATE)
        self.assertFalse(result.ready)
        self.assertIn("AUTHORITY_NOT_ACTIVE", result.blockers)
        self.assertIn("AUTHORITY_TYPE_INVALID_OR_MISSING", result.blockers)

    def _base_active(self):
        r = copy.deepcopy(TEMPLATE)
        r["status"] = "ACTIVE"
        r["issued_at_utc"] = "2099-01-01T00:00:00Z"
        return r

    def test_h02_design_freeze_authority_keeps_target_locked(self):
        r = self._base_active()
        r["authority_type"] = H02_DESIGN_FREEZE
        r["scope"]["h02_design_and_freeze"] = True
        r["scope"]["target_observation"] = False
        r["receipt_sha256"] = receipt_fingerprint(r)
        result = validate_authority_receipt(r)
        self.assertTrue(result.ready, result.blockers)

    def test_h02_authority_cannot_open_target(self):
        r = self._base_active()
        r["authority_type"] = H02_DESIGN_FREEZE
        r["scope"]["h02_design_and_freeze"] = True
        r["scope"]["target_observation"] = True
        r["receipt_sha256"] = receipt_fingerprint(r)
        result = validate_authority_receipt(r)
        self.assertFalse(result.ready)
        self.assertIn("TARGET_OBSERVATION_MUST_REMAIN_LOCKED", result.blockers)

    def test_target_open_requires_exact_fingerprint_bindings(self):
        r = self._base_active()
        r["authority_type"] = TARGET_OBSERVATION_OPEN
        r["scope"]["target_observation"] = True
        r["bindings"] = {
            "protocol_fingerprint_sha256": "a" * 64,
            "calendar_source_manifest_sha256": "b" * 64,
            "implementation_manifest_sha256": "c" * 64,
            "earliest_target_utc": "2099-01-02T00:00:00Z",
        }
        r["receipt_sha256"] = receipt_fingerprint(r)
        result = validate_authority_receipt(r)
        self.assertTrue(result.ready, result.blockers)

    def test_mutation_after_receipt_hash_fails(self):
        r = self._base_active()
        r["authority_type"] = H02_DESIGN_FREEZE
        r["scope"]["h02_design_and_freeze"] = True
        r["receipt_sha256"] = receipt_fingerprint(r)
        r["scope"]["live_trading"] = True
        result = validate_authority_receipt(r)
        self.assertFalse(result.ready)
        self.assertIn("FORBIDDEN_SCOPE_LIVE_TRADING", result.blockers)
        self.assertIn("RECEIPT_SHA256_MISMATCH", result.blockers)


if __name__ == "__main__":
    unittest.main()
