import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from authority_transition import receipt_fingerprint
from calendar_manifest import manifest_sha256
from pretarget_gate import protocol_fingerprint
from freeze_manifest import manifest_sha256 as implementation_manifest_sha256
from h02_ruleset import EXPECTED_RULESET_HASH
from target_open_runtime_guard import validate_target_capture_open


def synthetic_artifacts():
    calendar = {
        "document_type": "MRCR_OFFICIAL_CALENDAR_MANIFEST_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "calendar_year": 2099,
        "complete_official_calendar": True,
        "event_families": ["SYNTHETIC_EVENT"],
        "official_sources": [{
            "authority": "SYNTHETIC",
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

    protocol = {
        "document_type": "MRCR_PRETARGET_PROTOCOL_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "status": "FROZEN_PRETARGET_PROTOCOL__TARGET_LOCKED",
        "protocol_version": "0.1",
        "governance": {
            "h02_authorized": True,
            "target_observation_authorized": False,
            "historical_contaminated_data_allowed_for_selection": False,
            "earliest_target_period": "2099",
        },
        "calendar": {
            "complete_official_calendar": True,
            "calendar_source_manifest_sha256": calendar["manifest_sha256"],
            "calendar_frozen_at_utc": "2099-01-01T00:00:00Z",
            "event_families": ["SYNTHETIC_EVENT"],
        },
        "market_scope": {
            "venues": ["SYNTHETIC_VENUE"],
            "native_symbols": ["SYNTHETIC_SYMBOL"],
            "cross_venue_merge_allowed": False,
        },
        "decision_state": {
            "anchor_definition": "SYNTHETIC",
            "decision_clock_seconds": 1,
            "availability_rule": "SOURCE_AND_COLLECTOR_ARRIVAL",
            "depth_definition": {"mode": "TOP_N", "value": 1},
            "measurement_catalog_sha256": "b" * 64,
            "implementation_head_sha": "c" * 40,
        },
        "hypothesis": {
            "causal_statement": "SYNTHETIC",
            "classifier_definition": "SYNTHETIC",
            "classifier_sha256": "d" * 64,
            "abstention_rule": "SYNTHETIC",
        },
        "outcome": {
            "future_horizon_seconds": 1,
            "outcome_definition": "SYNTHETIC",
            "benchmark_definition": "SYNTHETIC",
        },
        "economics": {
            "tested": False,
            "fee_model": None,
            "slippage_model": None,
            "latency_model": None,
        },
        "freeze": {
            "protocol_fingerprint_sha256": None,
            "ruleset_sha256": EXPECTED_RULESET_HASH,
            "frozen_at_utc": "2099-01-01T00:00:01Z",
            "operator_authority_receipt": "f" * 64,
        },
    }
    protocol["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(protocol)

    implementation = {
        "document_type": "MRCR_IMPLEMENTATION_MANIFEST_V01",
        "implementation_head_sha": "c" * 40,
        "files": [{"path": "synthetic.py", "bytes": 1, "sha256": "a" * 64}],
    }
    implementation["manifest_sha256"] = implementation_manifest_sha256(
        implementation
    )

    authority = {
        "document_type": "MRCR_AUTHORITY_TRANSITION_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "status": "ACTIVE",
        "authority_type": "TARGET_OBSERVATION_OPEN",
        "issued_at_utc": "2099-01-01T00:00:02Z",
        "governance_policy_id": "CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN",
        "scope": {
            "h02_design_and_freeze": False,
            "target_observation": True,
            "historical_contaminated_outcome_inspection": False,
            "live_trading": False,
            "paper_trading": False,
            "exchange_mutation": False,
            "paid_data_purchase": False,
            "render_deployment": False,
            "main_merge": False,
        },
        "bindings": {
            "protocol_fingerprint_sha256": protocol["freeze"]["protocol_fingerprint_sha256"],
            "calendar_source_manifest_sha256": calendar["manifest_sha256"],
            "implementation_manifest_sha256": implementation["manifest_sha256"],
            "earliest_target_utc": "2099-01-02T00:00:00Z",
        },
        "chronology": {
            "requires_freeze_before_target_open": True,
            "authority_may_not_inherit_promotion_credit": True,
            "contaminated_history_may_not_select_parameters": True,
        },
        "receipt_sha256": None,
    }
    authority["receipt_sha256"] = receipt_fingerprint(authority)
    return protocol, calendar, implementation, authority


class TargetOpenRuntimeGuardTests(unittest.TestCase):
    def test_complete_bound_artifacts_pass_after_start(self):
        p, c, i, a = synthetic_artifacts()
        result = validate_target_capture_open(
            protocol=p,
            calendar_manifest=c,
            implementation_manifest=i,
            authority_receipt=a,
            now_utc="2099-01-02T00:00:00Z",
        )
        self.assertTrue(result.ready, result.blockers)

    def test_runtime_before_earliest_target_fails(self):
        p, c, i, a = synthetic_artifacts()
        result = validate_target_capture_open(
            protocol=p,
            calendar_manifest=c,
            implementation_manifest=i,
            authority_receipt=a,
            now_utc="2099-01-01T23:59:59Z",
        )
        self.assertFalse(result.ready)
        self.assertIn("TARGET_WINDOW_NOT_STARTED", result.blockers)

    def test_wrong_implementation_head_fails(self):
        p, c, i, a = synthetic_artifacts()
        i["implementation_head_sha"] = "9" * 40
        result = validate_target_capture_open(
            protocol=p,
            calendar_manifest=c,
            implementation_manifest=i,
            authority_receipt=a,
            now_utc="2099-01-02T00:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn("IMPLEMENTATION_HEAD_PROTOCOL_BINDING_MISMATCH", result.blockers)

    def test_protocol_cannot_self_open_target(self):
        p, c, i, a = synthetic_artifacts()
        p["governance"]["target_observation_authorized"] = True
        p["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(p)
        a["bindings"]["protocol_fingerprint_sha256"] = p["freeze"]["protocol_fingerprint_sha256"]
        a["receipt_sha256"] = receipt_fingerprint(a)
        result = validate_target_capture_open(
            protocol=p,
            calendar_manifest=c,
            implementation_manifest=i,
            authority_receipt=a,
            now_utc="2099-01-02T00:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn("PROTOCOL_MUST_REMAIN_TARGET_LOCKED", result.blockers)

    def test_missing_target_open_authority_fails(self):
        p, c, i, a = synthetic_artifacts()
        a["authority_type"] = "H02_DESIGN_FREEZE"
        a["scope"]["target_observation"] = False
        a["scope"]["h02_design_and_freeze"] = True
        a["bindings"]["earliest_target_utc"] = None
        a["receipt_sha256"] = receipt_fingerprint(a)
        result = validate_target_capture_open(
            protocol=p,
            calendar_manifest=c,
            implementation_manifest=i,
            authority_receipt=a,
            now_utc="2099-01-02T00:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn("TARGET_OBSERVATION_OPEN_AUTHORITY_REQUIRED", result.blockers)

    def test_mutated_implementation_manifest_fails(self):
        p, c, i, a = synthetic_artifacts()
        i["files"][0]["bytes"] = 2
        result = validate_target_capture_open(
            protocol=p,
            calendar_manifest=c,
            implementation_manifest=i,
            authority_receipt=a,
            now_utc="2099-01-02T00:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn("IMPLEMENTATION:MANIFEST_SHA256_MISMATCH", result.blockers)

    def test_wrong_ruleset_hash_fails(self):
        p, c, i, a = synthetic_artifacts()
        p["freeze"]["ruleset_sha256"] = "9" * 64
        p["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(p)
        a["bindings"]["protocol_fingerprint_sha256"] = p["freeze"]["protocol_fingerprint_sha256"]
        a["receipt_sha256"] = receipt_fingerprint(a)
        result = validate_target_capture_open(
            protocol=p,
            calendar_manifest=c,
            implementation_manifest=i,
            authority_receipt=a,
            now_utc="2099-01-02T00:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn("PROTOCOL_RULESET_HASH_MISMATCH", result.blockers)


if __name__ == "__main__":
    unittest.main()
