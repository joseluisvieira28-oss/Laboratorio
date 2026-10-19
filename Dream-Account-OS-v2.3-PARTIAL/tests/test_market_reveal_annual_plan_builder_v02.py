import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from annual_plan_builder_v02 import build_annual_plan_v02_from_live_status
from h02_calendar_binding_v02 import validate_annual_plan_manifest

RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)


def bls_events():
    names = [
        "Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.",
        "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.",
    ]
    out=[]
    for i,name in enumerate(names,1):
        out.append({
            "reference_month": f"M{i:02d}-2026",
            "release_date": f"{name} {min(i+2,28)}, 2027",
            "release_time": "08:30 AM",
            "official_status": "CONFIRMED",
        })
    return out


def ready_status():
    return {
        "document_type": "MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "checked_at_utc": "2026-12-15T12:00:00Z",
        "status": "READY_FOR_V02_ANNUAL_PLAN",
        "annual_plan_trigger_ready_v02": True,
        "strict_v01_all_confirmed_trigger_ready": False,
        "inferred_dates_used": False,
        "sources": {
            "US_CPI": {
                "source_url": "https://www.bls.gov/schedule/news_release/cpi.htm",
                "evidence_format": "HTML_EXTRACTED_TEXT_UTF8",
                "extracted_text_sha256": "a" * 64,
                "confirmed_2027_event_count": 12,
                "events_2027": bls_events(),
            },
            "US_EMPLOYMENT_SITUATION": {
                "source_url": "https://www.bls.gov/schedule/news_release/empsit.htm",
                "evidence_format": "HTML_EXTRACTED_TEXT_UTF8",
                "extracted_text_sha256": "b" * 64,
                "confirmed_2027_event_count": 12,
                "events_2027": bls_events(),
            },
            "FOMC_STATEMENT": {
                "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
                "evidence_format": "HTML_EXTRACTED_TEXT_UTF8",
                "extracted_text_sha256": "c" * 64,
                "observed_2027_meeting_count": 8,
                "annual_plan_bindable_v02": True,
                "official_tentative_note_present": True,
                "observed_2027_meetings": [
                    "January 26-27",
                    "March 16-17",
                    "April 27-28",
                    "June 8-9",
                    "July 27-28",
                    "September 14-15",
                    "October 26-27",
                    "December 7-8",
                ],
            },
        },
    }


class AnnualPlanBuilderV02Tests(unittest.TestCase):
    def test_ready_live_status_builds_hash_valid_32_event_plan(self):
        plan=build_annual_plan_v02_from_live_status(
            live_status=ready_status(),
            ruleset=RULESET,
        )
        self.assertEqual(len(plan["events"]),32)
        self.assertIsInstance(plan["annual_plan_sha256"],str)
        self.assertEqual(len(plan["annual_plan_sha256"]),64)
        ok, blockers=validate_annual_plan_manifest(plan,ruleset=RULESET)
        self.assertTrue(ok,blockers)

        fomc=[
            row for row in plan["events"]
            if row["event_family"]=="FOMC_STATEMENT"
        ]
        self.assertEqual(len(fomc),8)
        self.assertTrue(all(
            row["official_plan_status"]=="OFFICIAL_TENTATIVE"
            for row in fomc
        ))
        self.assertEqual(fomc[0]["scheduled_date"],"2027-01-27")
        self.assertEqual(fomc[-1]["scheduled_date"],"2027-12-08")

    def test_blocked_status_never_builds_plan(self):
        status=ready_status()
        status["status"]="BLOCKED"
        status["annual_plan_trigger_ready_v02"]=False
        with self.assertRaisesRegex(ValueError,"LIVE_STATUS_NOT_READY"):
            build_annual_plan_v02_from_live_status(
                live_status=status,
                ruleset=RULESET,
            )

    def test_partial_bls_never_builds_plan(self):
        status=ready_status()
        status["sources"]["US_CPI"]["confirmed_2027_event_count"]=11
        status["sources"]["US_CPI"]["events_2027"]=bls_events()[:-1]
        with self.assertRaisesRegex(ValueError,"CPI_2027_COUNT_NOT_12"):
            build_annual_plan_v02_from_live_status(
                live_status=status,
                ruleset=RULESET,
            )

    def test_inferred_dates_are_rejected(self):
        status=ready_status()
        status["inferred_dates_used"]=True
        with self.assertRaisesRegex(ValueError,"INFERRED_DATES"):
            build_annual_plan_v02_from_live_status(
                live_status=status,
                ruleset=RULESET,
            )


if __name__=="__main__":
    unittest.main()
