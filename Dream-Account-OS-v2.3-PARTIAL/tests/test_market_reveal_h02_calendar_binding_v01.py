import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from calendar_manifest import manifest_sha256
from h02_calendar_binding import (
    EXPECTED_COUNTS,
    EXPECTED_FAMILIES,
    validate_h02_calendar_manifest,
)

RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)


def complete_h02_calendar():
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
    source_by_family = {
        "US_CPI": 0,
        "US_EMPLOYMENT_SITUATION": 1,
        "FOMC_STATEMENT": 2,
    }
    events = []
    for family in EXPECTED_FAMILIES:
        for index in range(EXPECTED_COUNTS[family]):
            month = (index % 12) + 1
            day = 10 if family == "US_CPI" else 5 if family == "US_EMPLOYMENT_SITUATION" else 20
            events.append({
                "event_id": f"{family}-2027-{index+1:02d}",
                "event_family": family,
                "scheduled_time_utc": f"2027-{month:02d}-{day:02d}T13:30:00Z",
                "official_source_ref": source_by_family[family],
                "official_status": "CONFIRMED",
            })
    m = {
        "document_type": "MRCR_OFFICIAL_CALENDAR_MANIFEST_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "calendar_year": 2027,
        "complete_official_calendar": True,
        "event_families": list(EXPECTED_FAMILIES),
        "official_sources": sources,
        "events": events,
        "family_completeness": {
            family: {
                "status": "COMPLETE_OFFICIAL_CONFIRMED",
                "calendar_year": 2027,
                "expected_event_count": EXPECTED_COUNTS[family],
                "confirmed_event_count": EXPECTED_COUNTS[family],
                "authority": "FEDERAL_RESERVE" if family == "FOMC_STATEMENT" else "BLS",
                "source_url": (
                    "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
                    if family == "FOMC_STATEMENT"
                    else "https://www.bls.gov/schedule/news_release/cpi.htm"
                    if family == "US_CPI"
                    else "https://www.bls.gov/schedule/news_release/empsit.htm"
                ),
            }
            for family in EXPECTED_FAMILIES
        },
        "all_events_confirmed": True,
        "tentative_events_allowed": False,
        "manifest_sha256": None,
    }
    m["manifest_sha256"] = manifest_sha256(m)
    return m


class H02CalendarBindingTests(unittest.TestCase):
    def test_complete_exact_manifest_passes(self):
        m = complete_h02_calendar()
        ready, blockers = validate_h02_calendar_manifest(m, ruleset=RULESET)
        self.assertTrue(ready, blockers)

    def test_partial_bls_calendar_fails(self):
        m = complete_h02_calendar()
        m["events"] = [
            e for e in m["events"]
            if not (e["event_family"] == "US_CPI" and e["event_id"].endswith("-12"))
        ]
        m["family_completeness"]["US_CPI"]["confirmed_event_count"] = 11
        m["manifest_sha256"] = manifest_sha256(m)
        ready, blockers = validate_h02_calendar_manifest(m, ruleset=RULESET)
        self.assertFalse(ready)
        self.assertIn("US_CPI_EVENT_COUNT_11_EXPECTED_12", blockers)

    def test_tentative_fomc_event_fails(self):
        m = complete_h02_calendar()
        event = next(e for e in m["events"] if e["event_family"] == "FOMC_STATEMENT")
        event["official_status"] = "TENTATIVE"
        m["manifest_sha256"] = manifest_sha256(m)
        ready, blockers = validate_h02_calendar_manifest(m, ruleset=RULESET)
        self.assertFalse(ready)
        self.assertTrue(any(x.endswith("_NOT_CONFIRMED") for x in blockers))

    def test_wrong_official_domain_fails(self):
        m = complete_h02_calendar()
        m["official_sources"][0]["source_url"] = "https://example.com/cpi"
        m["manifest_sha256"] = manifest_sha256(m)
        ready, blockers = validate_h02_calendar_manifest(m, ruleset=RULESET)
        self.assertFalse(ready)
        self.assertTrue(any("OFFICIAL_DOMAIN_MISMATCH" in x for x in blockers))

    def test_event_outside_2027_fails(self):
        m = complete_h02_calendar()
        m["events"][0]["scheduled_time_utc"] = "2028-01-10T13:30:00Z"
        m["manifest_sha256"] = manifest_sha256(m)
        ready, blockers = validate_h02_calendar_manifest(m, ruleset=RULESET)
        self.assertFalse(ready)
        self.assertIn("EVENT_0_OUTSIDE_2027", blockers)

    def test_extra_family_fails_exact_scope(self):
        m = complete_h02_calendar()
        m["event_families"].append("OTHER")
        m["manifest_sha256"] = manifest_sha256(m)
        ready, blockers = validate_h02_calendar_manifest(m, ruleset=RULESET)
        self.assertFalse(ready)
        self.assertIn("H02_EVENT_FAMILIES_EXACT_SET_ORDER_REQUIRED", blockers)


if __name__ == "__main__":
    unittest.main()
