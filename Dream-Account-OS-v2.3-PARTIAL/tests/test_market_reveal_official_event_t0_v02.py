import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from event_activation_receipt_builder_v02 import (
    build_event_activation_receipt_v02,
)
from h02_calendar_binding_v02 import (
    annual_plan_sha256,
    validate_event_activation_receipt,
)
from official_event_t0_extractor_v02 import (
    extract_bls_t0,
    extract_fomc_t0,
)


BLS_POLICY = """
All seven PFEIs are scheduled for release at 8:30 a.m. Eastern Time on the dates shown on our public calendar.
The Employment Situation
Consumer Price Index
"""

CPI_SCHEDULE = """
Reference Month Release Date Release Time
August 2026
Sep. 11, 2026
08:30 AM
September 2026
Oct. 14, 2026
08:30 AM
"""

EMPSIT_SCHEDULE = """
Reference Month Release Date Release Time
August 2026
Sep. 4, 2026
08:30 AM
September 2026
Oct. 2, 2026
08:30 AM
"""

FOMC_2027_ANNOUNCEMENT = """
Tuesday, January 26, and Wednesday, January 27
Tuesday, October 26, and Wednesday, October 27
The Committee releases a policy statement at 2 p.m. Eastern Time on the second day of each regularly scheduled meeting
"""

PRECEDING_MINUTES = """
It was agreed that the next meeting of the Committee would be held on Tuesday-Wednesday, October 26-27, 2027.
"""


def minimal_plan(event_id, family, day):
    source = (
        {
            "authority": "FEDERAL_RESERVE",
            "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "retrieved_at_utc": "2027-09-30T12:00:00Z",
        }
        if family == "FOMC_STATEMENT"
        else {
            "authority": "BLS",
            "source_url": "https://www.bls.gov/schedule/news_release/cpi.htm",
            "retrieved_at_utc": "2026-12-15T12:00:00Z",
        }
    )
    # Activation validator only needs a uniquely bound event row here.
    return {
        "events": [{
            "event_id": event_id,
            "event_family": family,
            "scheduled_date": day,
            "official_source_ref": 0,
        }],
        "official_sources": [source],
    }


class OfficialEventT0V02Tests(unittest.TestCase):
    def test_cpi_t0_uses_official_0830_eastern_and_dst(self):
        evidence = extract_bls_t0(
            event_family="US_CPI",
            plan_date="2026-10-14",
            schedule_text=CPI_SCHEDULE,
            dissemination_policy_text=BLS_POLICY,
        )
        self.assertEqual(evidence.scheduled_time_utc, "2026-10-14T12:30:00Z")
        self.assertEqual(
            evidence.confirmation_mode,
            "BLS_OFFICIAL_SCHEDULE_PLUS_PFEI_TIME_POLICY",
        )

    def test_employment_t0_uses_official_0830_eastern(self):
        evidence = extract_bls_t0(
            event_family="US_EMPLOYMENT_SITUATION",
            plan_date="2026-10-02",
            schedule_text=EMPSIT_SCHEDULE,
            dissemination_policy_text=BLS_POLICY,
        )
        self.assertEqual(evidence.scheduled_time_utc, "2026-10-02T12:30:00Z")

    def test_bls_missing_plan_date_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "BLS_PLAN_DATE_NOT_UNIQUELY_PRESENT"):
            extract_bls_t0(
                event_family="US_CPI",
                plan_date="2026-10-15",
                schedule_text=CPI_SCHEDULE,
                dissemination_policy_text=BLS_POLICY,
            )

    def test_bls_timezone_policy_missing_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "BLS_PFEI_EASTERN_TIME_POLICY_NOT_PROVEN",
        ):
            extract_bls_t0(
                event_family="US_CPI",
                plan_date="2026-10-14",
                schedule_text=CPI_SCHEDULE,
                dissemination_policy_text="Consumer Price Index",
            )

    def test_fomc_t0_requires_annual_time_rule_and_preceding_minutes_confirmation(self):
        evidence = extract_fomc_t0(
            plan_start_date="2027-10-26",
            plan_end_date="2027-10-27",
            annual_schedule_announcement_text=FOMC_2027_ANNOUNCEMENT,
            preceding_meeting_minutes_text=PRECEDING_MINUTES,
        )
        self.assertEqual(evidence.scheduled_date, "2027-10-27")
        self.assertEqual(evidence.scheduled_time_utc, "2027-10-27T18:00:00Z")
        self.assertEqual(
            evidence.confirmation_mode,
            "FOMC_ANNUAL_SCHEDULE_TIME_RULE_PLUS_PRECEDING_MINUTES_CONFIRMATION",
        )

    def test_fomc_without_preceding_minutes_confirmation_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "FOMC_NEXT_MEETING_NOT_CONFIRMED_BY_PRECEDING_MINUTES",
        ):
            extract_fomc_t0(
                plan_start_date="2027-10-26",
                plan_end_date="2027-10-27",
                annual_schedule_announcement_text=FOMC_2027_ANNOUNCEMENT,
                preceding_meeting_minutes_text="No next meeting confirmation.",
            )

    def test_builder_produces_hash_valid_activation_receipt(self):
        evidence = extract_fomc_t0(
            plan_start_date="2027-10-26",
            plan_end_date="2027-10-27",
            annual_schedule_announcement_text=FOMC_2027_ANNOUNCEMENT,
            preceding_meeting_minutes_text=PRECEDING_MINUTES,
        )
        receipt = build_event_activation_receipt_v02(
            event_id="FOMC-07",
            evidence=evidence,
            confirmed_at_utc="2027-10-10T12:00:00Z",
            primary_official_source_url=(
                "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
            ),
            supporting_official_sources=[
                {
                    "role": "FOMC_ANNUAL_SCHEDULE_ANNOUNCEMENT",
                    "url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20250905a.htm",
                    "retrieved_at_utc": "2027-10-10T12:00:00Z",
                    "extracted_text_sha256": "6" * 64,
                },
                {
                    "role": "FOMC_PRECEDING_MEETING_MINUTES_CONFIRMATION",
                    "url": "https://www.federalreserve.gov/monetarypolicy/example-minutes.htm",
                    "retrieved_at_utc": "2027-10-10T12:00:00Z",
                    "extracted_text_sha256": "7" * 64,
                },
            ],
        )
        plan = minimal_plan("FOMC-07", "FOMC_STATEMENT", "2027-10-27")
        ok, blockers = validate_event_activation_receipt(
            receipt,
            annual_plan=plan,
            now_utc="2027-10-20T12:00:00Z",
        )
        self.assertTrue(ok, blockers)

    def test_receipt_mutation_after_build_fails_hash(self):
        evidence = extract_bls_t0(
            event_family="US_CPI",
            plan_date="2026-10-14",
            schedule_text=CPI_SCHEDULE,
            dissemination_policy_text=BLS_POLICY,
        )
        receipt = build_event_activation_receipt_v02(
            event_id="CPI-X",
            evidence=evidence,
            confirmed_at_utc="2026-09-27T12:00:00Z",
            primary_official_source_url=(
                "https://www.bls.gov/schedule/news_release/cpi.htm"
            ),
            supporting_official_sources=[
                {
                    "role": "BLS_RELEASE_SCHEDULE",
                    "url": "https://www.bls.gov/schedule/news_release/cpi.htm",
                    "retrieved_at_utc": "2026-09-27T12:00:00Z",
                    "extracted_text_sha256": "8" * 64,
                },
                {
                    "role": "BLS_DISSEMINATION_POLICY",
                    "url": "https://www.bls.gov/about-bls/dissemination.htm",
                    "retrieved_at_utc": "2026-09-27T12:00:00Z",
                    "extracted_text_sha256": "9" * 64,
                }
            ],
        )
        receipt["scheduled_time_utc"] = "2026-10-14T12:31:00Z"
        plan = minimal_plan("CPI-X", "US_CPI", "2026-10-14")
        ok, blockers = validate_event_activation_receipt(
            receipt,
            annual_plan=plan,
            now_utc="2026-10-01T12:00:00Z",
        )
        self.assertFalse(ok)
        self.assertIn("ACTIVATION_RECEIPT_SHA256_MISMATCH", blockers)


if __name__ == "__main__":
    unittest.main()
