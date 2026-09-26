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
    validate_freeze_binding,
    validate_target_open_binding,
)
from calendar_manifest import manifest_sha256
from pretarget_gate import protocol_fingerprint

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

    def _synthetic_protocol_and_calendar(self, authority_hash):
        protocol = {
            "document_type": "MRCR_PRETARGET_PROTOCOL_V01",
            "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
            "status": "SYNTHETIC_TEST_ONLY",
            "protocol_version": "0.1",
            "governance": {
                "h02_authorized": True,
                "target_observation_authorized": False,
                "historical_contaminated_data_allowed_for_selection": False,
                "earliest_target_period": "2099",
            },
            "calendar": {
                "complete_official_calendar": True,
                "calendar_source_manifest_sha256": None,
                "calendar_frozen_at_utc": "2099-01-01T00:00:00Z",
                "event_families": ["SYNTHETIC_EVENT"],
            },
            "market_scope": {
                "venues": ["SYNTHETIC_VENUE"],
                "native_symbols": ["SYNTHETIC_SYMBOL"],
                "cross_venue_merge_allowed": False,
            },
            "decision_state": {
                "anchor_definition": "SYNTHETIC_ANCHOR",
                "decision_clock_seconds": [1],
                "availability_rule": "SOURCE_AND_COLLECTOR_ARRIVAL",
                "depth_definition": {"mode": "TOP_N", "value": 1},
                "measurement_catalog_sha256": "b" * 64,
                "implementation_head_sha": "c" * 40,
            },
            "hypothesis": {
                "causal_statement": "SYNTHETIC_ONLY",
                "classifier_definition": "SYNTHETIC_ONLY",
                "classifier_sha256": "d" * 64,
                "abstention_rule": "SYNTHETIC_ONLY",
            },
            "outcome": {
                "future_horizon_seconds": 1,
                "outcome_definition": "SYNTHETIC_ONLY",
                "benchmark_definition": "SYNTHETIC_ONLY",
            },
            "economics": {
                "tested": False,
                "fee_model": None,
                "slippage_model": None,
                "latency_model": None,
            },
            "freeze": {
                "protocol_fingerprint_sha256": None,
                "frozen_at_utc": "2099-01-01T00:00:01Z",
                "operator_authority_receipt": authority_hash,
            },
        }
        calendar = {
            "document_type": "MRCR_OFFICIAL_CALENDAR_MANIFEST_V01",
            "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
            "calendar_year": 2099,
            "complete_official_calendar": True,
            "event_families": ["SYNTHETIC_EVENT"],
            "official_sources": [{
                "authority": "SYNTHETIC_AUTHORITY",
                "source_url": "https://example.invalid/calendar",
                "retrieved_at_utc": "2098-12-01T00:00:00Z",
            }],
            "events": [{
                "event_id": "SYNTH-2099-01-02",
                "event_family": "SYNTHETIC_EVENT",
                "scheduled_time_utc": "2099-01-02T00:00:00Z",
                "official_source_ref": 0,
            }],
            "manifest_sha256": None,
        }
        calendar["manifest_sha256"] = manifest_sha256(calendar)
        protocol["calendar"]["calendar_source_manifest_sha256"] = calendar["manifest_sha256"]
        protocol["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(protocol)
        return protocol, calendar

    def test_freeze_binding_requires_exact_h02_authority_receipt(self):
        authority = self._base_active()
        authority["authority_type"] = H02_DESIGN_FREEZE
        authority["scope"]["h02_design_and_freeze"] = True
        authority["receipt_sha256"] = receipt_fingerprint(authority)
        protocol, _ = self._synthetic_protocol_and_calendar(authority["receipt_sha256"])
        result = validate_freeze_binding(protocol, authority)
        self.assertTrue(result.ready, result.blockers)

    def test_target_open_binds_exact_frozen_artifacts_and_chronology(self):
        freeze_authority = self._base_active()
        freeze_authority["authority_type"] = H02_DESIGN_FREEZE
        freeze_authority["scope"]["h02_design_and_freeze"] = True
        freeze_authority["receipt_sha256"] = receipt_fingerprint(freeze_authority)
        protocol, calendar = self._synthetic_protocol_and_calendar(
            freeze_authority["receipt_sha256"]
        )
        implementation_hash = "e" * 64

        target = self._base_active()
        target["authority_type"] = TARGET_OBSERVATION_OPEN
        target["issued_at_utc"] = "2099-01-01T00:00:02Z"
        target["scope"]["target_observation"] = True
        target["bindings"] = {
            "protocol_fingerprint_sha256": protocol["freeze"]["protocol_fingerprint_sha256"],
            "calendar_source_manifest_sha256": calendar["manifest_sha256"],
            "implementation_manifest_sha256": implementation_hash,
            "earliest_target_utc": "2099-01-02T00:00:00Z",
        }
        target["receipt_sha256"] = receipt_fingerprint(target)

        result = validate_target_open_binding(
            protocol,
            calendar,
            implementation_hash,
            target,
        )
        self.assertTrue(result.ready, result.blockers)

        target["bindings"]["protocol_fingerprint_sha256"] = "f" * 64
        target["receipt_sha256"] = receipt_fingerprint(target)
        result = validate_target_open_binding(
            protocol,
            calendar,
            implementation_hash,
            target,
        )
        self.assertFalse(result.ready)
        self.assertIn("TARGET_AUTHORITY_PROTOCOL_BINDING_MISMATCH", result.blockers)

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
