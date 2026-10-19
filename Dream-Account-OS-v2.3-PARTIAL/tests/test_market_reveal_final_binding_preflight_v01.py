import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from authority_transition import receipt_fingerprint
from calendar_manifest import manifest_sha256
from final_binding_preflight import run_final_binding_preflight
from freeze_manifest import manifest_sha256 as implementation_manifest_sha256
from h02_calendar_binding import EXPECTED_COUNTS, EXPECTED_FAMILIES
from h02_ruleset import EXPECTED_RULESET_HASH
from target_open_runtime_guard import validate_target_capture_open

RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)
H02_AUTHORITY = json.loads(
    (MODULE_DIR / "H02_DESIGN_FREEZE_AUTHORITY_V01.json").read_text(encoding="utf-8")
)


def synthetic_complete_calendar():
    sources = [
        {
            "authority": "BLS",
            "source_url": "https://www.bls.gov/schedule/news_release/cpi.htm",
            "retrieved_at_utc": "2026-12-20T00:00:00Z",
            "publication_status": "OFFICIAL_COMPLETE",
        },
        {
            "authority": "BLS",
            "source_url": "https://www.bls.gov/schedule/news_release/empsit.htm",
            "retrieved_at_utc": "2026-12-20T00:00:00Z",
            "publication_status": "OFFICIAL_COMPLETE",
        },
        {
            "authority": "FEDERAL_RESERVE",
            "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "retrieved_at_utc": "2026-12-20T00:00:00Z",
            "publication_status": "OFFICIAL_COMPLETE",
        },
    ]
    ref = {"US_CPI": 0, "US_EMPLOYMENT_SITUATION": 1, "FOMC_STATEMENT": 2}
    events = []
    for family in EXPECTED_FAMILIES:
        for i in range(EXPECTED_COUNTS[family]):
            month = i + 1
            day = 10 if family == "US_CPI" else 5 if family == "US_EMPLOYMENT_SITUATION" else 20
            events.append({
                "event_id": f"{family}-2027-{i+1:02d}",
                "event_family": family,
                "scheduled_time_utc": f"2027-{month:02d}-{day:02d}T13:30:00Z",
                "official_source_ref": ref[family],
                "official_status": "CONFIRMED",
            })
    out = {
        "document_type": "MRCR_OFFICIAL_CALENDAR_MANIFEST_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "calendar_year": 2027,
        "complete_official_calendar": True,
        "event_families": list(EXPECTED_FAMILIES),
        "official_sources": sources,
        "events": events,
        "family_completeness": {},
        "all_events_confirmed": True,
        "tentative_events_allowed": False,
        "manifest_sha256": None,
    }
    for family in EXPECTED_FAMILIES:
        authority = "FEDERAL_RESERVE" if family == "FOMC_STATEMENT" else "BLS"
        url = (
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
            if family == "FOMC_STATEMENT"
            else "https://www.bls.gov/schedule/news_release/cpi.htm"
            if family == "US_CPI"
            else "https://www.bls.gov/schedule/news_release/empsit.htm"
        )
        out["family_completeness"][family] = {
            "status": "COMPLETE_OFFICIAL_CONFIRMED",
            "calendar_year": 2027,
            "expected_event_count": EXPECTED_COUNTS[family],
            "confirmed_event_count": EXPECTED_COUNTS[family],
            "authority": authority,
            "source_url": url,
        }
    out["manifest_sha256"] = manifest_sha256(out)
    return out


def synthetic_implementation():
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


class FinalBindingPreflightTests(unittest.TestCase):
    def test_end_to_end_synthetic_binding_rehearsal(self):
        calendar = synthetic_complete_calendar()
        implementation = synthetic_implementation()
        result = run_final_binding_preflight(
            ruleset=RULESET,
            calendar_manifest=calendar,
            implementation_manifest=implementation,
            h02_authority_receipt=H02_AUTHORITY,
            calendar_frozen_at_utc="2026-12-20T00:00:01Z",
            protocol_frozen_at_utc="2026-12-20T00:00:02Z",
        )
        self.assertTrue(result.ready_for_target_open_authority, result.blockers)
        protocol = result.protocol
        self.assertIsNotNone(protocol)
        self.assertFalse(protocol["governance"]["target_observation_authorized"])
        self.assertEqual(protocol["freeze"]["ruleset_sha256"], EXPECTED_RULESET_HASH)

        target = {
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
                "calendar_source_manifest_sha256": calendar["manifest_sha256"],
                "implementation_manifest_sha256": implementation["manifest_sha256"],
                "earliest_target_utc": "2027-01-01T00:00:00Z",
            },
            "chronology": {
                "requires_freeze_before_target_open": True,
                "authority_may_not_inherit_promotion_credit": True,
                "contaminated_history_may_not_select_parameters": True,
            },
            "receipt_sha256": None,
        }
        target["receipt_sha256"] = receipt_fingerprint(target)

        runtime = validate_target_capture_open(
            protocol=protocol,
            calendar_manifest=calendar,
            implementation_manifest=implementation,
            authority_receipt=target,
            now_utc="2027-01-01T00:00:00Z",
        )
        self.assertTrue(runtime.ready, runtime.blockers)

    def test_partial_calendar_never_builds_protocol(self):
        calendar = synthetic_complete_calendar()
        calendar["events"] = calendar["events"][:-1]
        calendar["manifest_sha256"] = manifest_sha256(calendar)
        result = run_final_binding_preflight(
            ruleset=RULESET,
            calendar_manifest=calendar,
            implementation_manifest=synthetic_implementation(),
            h02_authority_receipt=H02_AUTHORITY,
            calendar_frozen_at_utc="2026-12-20T00:00:01Z",
            protocol_frozen_at_utc="2026-12-20T00:00:02Z",
        )
        self.assertFalse(result.ready_for_target_open_authority)
        self.assertIsNone(result.protocol)

    def test_implementation_manifest_mutation_never_builds_protocol(self):
        implementation = synthetic_implementation()
        implementation["files"][0]["bytes"] = 11
        result = run_final_binding_preflight(
            ruleset=RULESET,
            calendar_manifest=synthetic_complete_calendar(),
            implementation_manifest=implementation,
            h02_authority_receipt=H02_AUTHORITY,
            calendar_frozen_at_utc="2026-12-20T00:00:01Z",
            protocol_frozen_at_utc="2026-12-20T00:00:02Z",
        )
        self.assertFalse(result.ready_for_target_open_authority)
        self.assertIn("IMPLEMENTATION:MANIFEST_SHA256_MISMATCH", result.blockers)


if __name__ == "__main__":
    unittest.main()
