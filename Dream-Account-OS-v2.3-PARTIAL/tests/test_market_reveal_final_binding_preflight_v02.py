import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from authority_transition import receipt_fingerprint
from event_capture_runtime_guard_v02 import validate_event_capture_open_v02
from final_binding_preflight_v02 import run_final_binding_preflight_v02
from freeze_manifest import manifest_sha256 as implementation_manifest_sha256
from h02_calendar_binding_v02 import (
    annual_plan_sha256,
    event_activation_sha256,
)
from h02_ruleset import EXPECTED_RULESET_HASH


RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)
H02_AUTHORITY = json.loads(
    (MODULE_DIR / "H02_DESIGN_FREEZE_AUTHORITY_V01.json").read_text(encoding="utf-8")
)


def annual_plan():
    sources = [
        {
            "authority": "BLS",
            "source_url": "https://www.bls.gov/schedule/news_release/cpi.htm",
            "retrieved_at_utc": "2026-12-20T00:00:00Z",
        },
        {
            "authority": "BLS",
            "source_url": "https://www.bls.gov/schedule/news_release/empsit.htm",
            "retrieved_at_utc": "2026-12-20T00:00:00Z",
        },
        {
            "authority": "FEDERAL_RESERVE",
            "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "retrieved_at_utc": "2026-12-20T00:00:00Z",
        },
    ]
    events = []
    for i in range(12):
        month = i + 1
        events.append({
            "event_id": f"CPI-{i+1:02d}",
            "event_family": "US_CPI",
            "scheduled_date": f"2027-{month:02d}-15",
            "official_plan_status": "OFFICIAL_CONFIRMED",
            "official_source_ref": 0,
        })
        events.append({
            "event_id": f"NFP-{i+1:02d}",
            "event_family": "US_EMPLOYMENT_SITUATION",
            "scheduled_date": f"2027-{month:02d}-05",
            "official_plan_status": "OFFICIAL_CONFIRMED",
            "official_source_ref": 1,
        })

    for i, day in enumerate(
        (
            "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09",
            "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08",
        ),
        1,
    ):
        events.append({
            "event_id": f"FOMC-{i:02d}",
            "event_family": "FOMC_STATEMENT",
            "scheduled_date": day,
            "official_plan_status": "OFFICIAL_TENTATIVE",
            "official_source_ref": 2,
        })

    out = {
        "document_type": "MRCR_H02_ANNUAL_PLAN_MANIFEST_V02",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "calendar_year": 2027,
        "complete_official_annual_plan": True,
        "event_families": [
            "US_CPI",
            "US_EMPLOYMENT_SITUATION",
            "FOMC_STATEMENT",
        ],
        "official_sources": sources,
        "events": events,
        "inferred_dates_used": False,
        "target_observation_authorized": False,
        "annual_plan_sha256": None,
    }
    out["annual_plan_sha256"] = annual_plan_sha256(out)
    return out


def implementation():
    out = {
        "document_type": "MRCR_IMPLEMENTATION_MANIFEST_V01",
        "implementation_head_sha": "c" * 40,
        "files": [
            {"path": "a.py", "bytes": 10, "sha256": "a" * 64},
            {"path": "b.py", "bytes": 20, "sha256": "b" * 64},
        ],
    }
    out["manifest_sha256"] = implementation_manifest_sha256(out)
    return out


def target_authority(protocol, plan, impl):
    out = {
        "document_type": "MRCR_AUTHORITY_TRANSITION_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "status": "ACTIVE",
        "authority_type": "TARGET_OBSERVATION_OPEN",
        "issued_at_utc": "2026-12-20T00:00:03Z",
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
            "calendar_source_manifest_sha256": plan["annual_plan_sha256"],
            "implementation_manifest_sha256": impl["manifest_sha256"],
            "earliest_target_utc": "2027-01-01T00:00:00Z",
        },
        "chronology": {
            "requires_freeze_before_target_open": True,
            "authority_may_not_inherit_promotion_credit": True,
            "contaminated_history_may_not_select_parameters": True,
        },
        "receipt_sha256": None,
    }
    out["receipt_sha256"] = receipt_fingerprint(out)
    return out


def activation(event_id="FOMC-01", t0="2027-01-27T19:00:00Z"):
    out = {
        "document_type": "MRCR_H02_EVENT_ACTIVATION_RECEIPT_V02",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "event_id": event_id,
        "event_family": "FOMC_STATEMENT",
        "scheduled_time_utc": t0,
        "confirmed_at_utc": "2026-12-10T15:00:00Z",
        "official_authority": "FEDERAL_RESERVE",
        "official_source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "official_status": "OFFICIAL_CONFIRMED_FOR_CAPTURE",
        "target_observation_authorized": False,
        "outcomes_authorized": False,
        "activation_receipt_sha256": None,
    }
    out["activation_receipt_sha256"] = event_activation_sha256(out)
    return out


class FinalBindingPreflightV02Tests(unittest.TestCase):
    def _preflight(self):
        plan = annual_plan()
        impl = implementation()
        result = run_final_binding_preflight_v02(
            ruleset=RULESET,
            annual_plan=plan,
            implementation_manifest=impl,
            h02_authority_receipt=H02_AUTHORITY,
            calendar_frozen_at_utc="2026-12-20T00:00:01Z",
            protocol_frozen_at_utc="2026-12-20T00:00:02Z",
        )
        self.assertTrue(result.ready_for_target_open_authority, result.blockers)
        self.assertIsNotNone(result.protocol)
        return plan, impl, result.protocol

    def test_v02_preflight_accepts_complete_plan_with_tentative_fomc(self):
        plan, impl, protocol = self._preflight()
        self.assertEqual(protocol["protocol_version"], "0.2")
        self.assertFalse(protocol["governance"]["target_observation_authorized"])
        self.assertTrue(protocol["calendar"]["event_activation_receipt_required"])
        self.assertEqual(protocol["freeze"]["ruleset_sha256"], EXPECTED_RULESET_HASH)

    def test_event_runtime_passes_only_with_bound_activation_receipt(self):
        plan, impl, protocol = self._preflight()
        auth = target_authority(protocol, plan, impl)
        result = validate_event_capture_open_v02(
            protocol=protocol,
            annual_plan=plan,
            implementation_manifest=impl,
            target_open_authority=auth,
            event_activation_receipt=activation(),
            ruleset=RULESET,
            now_utc="2027-01-20T12:00:00Z",
        )
        self.assertTrue(result.ready, result.blockers)

    def test_changed_fomc_date_fails_event_runtime(self):
        plan, impl, protocol = self._preflight()
        auth = target_authority(protocol, plan, impl)
        result = validate_event_capture_open_v02(
            protocol=protocol,
            annual_plan=plan,
            implementation_manifest=impl,
            target_open_authority=auth,
            event_activation_receipt=activation(t0="2027-01-28T19:00:00Z"),
            ruleset=RULESET,
            now_utc="2027-01-20T12:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn(
            "EVENT_ACTIVATION:T0_DATE_DIFFERS_FROM_ANNUAL_PLAN",
            result.blockers,
        )

    def test_mutated_activation_receipt_fails_runtime(self):
        plan, impl, protocol = self._preflight()
        auth = target_authority(protocol, plan, impl)
        receipt = activation()
        receipt["scheduled_time_utc"] = "2027-01-27T19:01:00Z"
        result = validate_event_capture_open_v02(
            protocol=protocol,
            annual_plan=plan,
            implementation_manifest=impl,
            target_open_authority=auth,
            event_activation_receipt=receipt,
            ruleset=RULESET,
            now_utc="2027-01-20T12:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn(
            "EVENT_ACTIVATION:ACTIVATION_RECEIPT_SHA256_MISMATCH",
            result.blockers,
        )

    def test_wrong_annual_plan_authority_binding_fails_runtime(self):
        plan, impl, protocol = self._preflight()
        auth = target_authority(protocol, plan, impl)
        auth["bindings"]["calendar_source_manifest_sha256"] = "9" * 64
        auth["receipt_sha256"] = receipt_fingerprint(auth)
        result = validate_event_capture_open_v02(
            protocol=protocol,
            annual_plan=plan,
            implementation_manifest=impl,
            target_open_authority=auth,
            event_activation_receipt=activation(),
            ruleset=RULESET,
            now_utc="2027-01-20T12:00:00Z",
        )
        self.assertFalse(result.ready)
        self.assertIn(
            "TARGET_AUTHORITY_ANNUAL_PLAN_BINDING_MISMATCH",
            result.blockers,
        )


if __name__ == "__main__":
    unittest.main()
