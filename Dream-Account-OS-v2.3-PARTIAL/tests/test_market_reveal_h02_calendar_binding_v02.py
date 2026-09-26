import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from h02_calendar_binding_v02 import (
    annual_plan_sha256,
    validate_annual_plan_manifest,
    validate_event_activation_receipt,
)


RULESET = {
    "event_scope": {
        "event_families": [
            "US_CPI",
            "US_EMPLOYMENT_SITUATION",
            "FOMC_STATEMENT",
        ],
        "calendar_year": 2027,
        "complete_official_calendar_required": True,
    }
}


def _source(authority, url):
    return {
        "authority": authority,
        "source_url": url,
        "retrieved_at_utc": "2026-12-15T12:00:00Z",
    }


def annual_plan():
    sources = [
        _source("BLS", "https://www.bls.gov/schedule/news_release/cpi.htm"),
        _source("BLS", "https://www.bls.gov/schedule/news_release/empsit.htm"),
        _source("FEDERAL_RESERVE", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
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
    fomc_dates = [
        "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09",
        "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08",
    ]
    for i, day in enumerate(fomc_dates, 1):
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


class CalendarBindingV02Tests(unittest.TestCase):
    def test_complete_plan_accepts_official_tentative_fomc_dates(self):
        plan = annual_plan()
        ok, blockers = validate_annual_plan_manifest(plan, ruleset=RULESET)
        self.assertTrue(ok, blockers)

    def test_bls_tentative_date_is_rejected(self):
        plan = annual_plan()
        plan["events"][0]["official_plan_status"] = "OFFICIAL_TENTATIVE"
        plan["annual_plan_sha256"] = annual_plan_sha256(plan)
        ok, blockers = validate_annual_plan_manifest(plan, ruleset=RULESET)
        self.assertFalse(ok)
        self.assertTrue(any("BLS_PLAN_STATUS_NOT_CONFIRMED" in x for x in blockers))

    def test_missing_event_keeps_plan_blocked(self):
        plan = annual_plan()
        plan["events"].pop()
        plan["annual_plan_sha256"] = annual_plan_sha256(plan)
        ok, blockers = validate_annual_plan_manifest(plan, ruleset=RULESET)
        self.assertFalse(ok)
        self.assertIn("FOMC_STATEMENT_COUNT_7_EXPECTED_8", blockers)

    def test_tampered_plan_hash_is_rejected(self):
        plan = annual_plan()
        plan["events"][0]["scheduled_date"] = "2027-01-16"
        ok, blockers = validate_annual_plan_manifest(plan, ruleset=RULESET)
        self.assertFalse(ok)
        self.assertIn("ANNUAL_PLAN_SHA256_MISMATCH", blockers)

    def test_event_activation_requires_exact_official_t0_before_event(self):
        plan = annual_plan()
        receipt = {
            "document_type": "MRCR_H02_EVENT_ACTIVATION_RECEIPT_V02",
            "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
            "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
            "event_id": "FOMC-01",
            "event_family": "FOMC_STATEMENT",
            "scheduled_time_utc": "2027-01-27T19:00:00Z",
            "confirmed_at_utc": "2026-12-10T15:00:00Z",
            "official_authority": "FEDERAL_RESERVE",
            "official_source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "official_status": "OFFICIAL_CONFIRMED_FOR_CAPTURE",
            "target_observation_authorized": False,
            "outcomes_authorized": False,
        }
        ok, blockers = validate_event_activation_receipt(
            receipt,
            annual_plan=plan,
            now_utc="2027-01-20T12:00:00Z",
        )
        self.assertTrue(ok, blockers)

    def test_event_activation_date_change_fails_closed(self):
        plan = annual_plan()
        receipt = {
            "document_type": "MRCR_H02_EVENT_ACTIVATION_RECEIPT_V02",
            "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
            "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
            "event_id": "FOMC-01",
            "event_family": "FOMC_STATEMENT",
            "scheduled_time_utc": "2027-01-28T19:00:00Z",
            "confirmed_at_utc": "2026-12-10T15:00:00Z",
            "official_authority": "FEDERAL_RESERVE",
            "official_source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "official_status": "OFFICIAL_CONFIRMED_FOR_CAPTURE",
            "target_observation_authorized": False,
            "outcomes_authorized": False,
        }
        ok, blockers = validate_event_activation_receipt(
            receipt,
            annual_plan=plan,
            now_utc="2027-01-20T12:00:00Z",
        )
        self.assertFalse(ok)
        self.assertIn("T0_DATE_DIFFERS_FROM_ANNUAL_PLAN", blockers)

    def test_activation_after_t0_fails_closed(self):
        plan = annual_plan()
        receipt = {
            "document_type": "MRCR_H02_EVENT_ACTIVATION_RECEIPT_V02",
            "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
            "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
            "event_id": "CPI-01",
            "event_family": "US_CPI",
            "scheduled_time_utc": "2027-01-15T13:30:00Z",
            "confirmed_at_utc": "2027-01-15T13:31:00Z",
            "official_authority": "BLS",
            "official_source_url": "https://www.bls.gov/schedule/news_release/cpi.htm",
            "official_status": "OFFICIAL_CONFIRMED_FOR_CAPTURE",
            "target_observation_authorized": False,
            "outcomes_authorized": False,
        }
        ok, blockers = validate_event_activation_receipt(
            receipt,
            annual_plan=plan,
            now_utc="2027-01-15T13:32:00Z",
        )
        self.assertFalse(ok)
        self.assertIn("CONFIRMATION_NOT_BEFORE_T0", blockers)
        self.assertIn("ACTIVATION_CHECK_AT_OR_AFTER_T0", blockers)


if __name__ == "__main__":
    unittest.main()
