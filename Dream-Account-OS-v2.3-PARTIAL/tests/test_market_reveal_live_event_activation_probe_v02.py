import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from authority_transition import receipt_fingerprint
from live_event_activation_probe_v02 import (
    _minutes_url,
    _preceding_regular_meeting_end,
    evaluate_event_activation_from_official_texts_v02,
)
from trigger_a_finalizer_v02 import run_trigger_a_finalizer_v02


RULESET = json.loads(
    (MODULE_DIR / "H02_SCIENTIFIC_RULESET_V01.json").read_text(encoding="utf-8")
)

BLS_POLICY = """
All seven PFEIs are scheduled for release at 8:30 a.m. Eastern Time on the dates shown on our public calendar.
The Employment Situation
Consumer Price Index
"""

CPI_TEXT = """
Reference Month
Release Date
Release Time
September 2027
Oct. 14, 2027
08:30 AM
"""

FOMC_ANNOUNCEMENT = """
Tuesday, October 26, and Wednesday, October 27
The Committee releases a policy statement at 2 p.m. Eastern Time on the second day of each regularly scheduled meeting
"""

PRECEDING_MINUTES = """
It was agreed that the next meeting of the Committee would be held on Tuesday-Wednesday, October 26-27, 2027.
"""

FED_CALENDAR = """
2026 FOMC Meetings
December
8-9
2027 FOMC Meetings
January
26-27
March
16-17*
April
27-28
June
8-9*
July
27-28
September
14-15*
October
26-27
December
7-8*
2028 FOMC Meetings
"""


def bls_events():
    names = [
        "Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.",
        "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.",
    ]
    return [
        {
            "reference_month": f"M{i:02d}-2026",
            "release_date": f"{name} {min(i+2,28)}, 2027",
            "release_time": "08:30 AM",
            "official_status": "CONFIRMED",
        }
        for i, name in enumerate(names, 1)
    ]


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
        "target_observation_authorized": False,
        "outcomes_authorized": False,
        "promotion_credit": "NONE",
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


class LiveEventActivationProbeV02Tests(unittest.TestCase):
    def test_bls_receipt_ready_but_target_remains_locked(self):
        plan = {
            "events": [{
                "event_id": "CPI-X",
                "event_family": "US_CPI",
                "scheduled_date": "2027-10-14",
            }]
        }
        status = evaluate_event_activation_from_official_texts_v02(
            annual_plan=plan,
            event_id="CPI-X",
            retrieved_at_utc="2027-10-01T12:00:00Z",
            bls_schedule_text=CPI_TEXT,
            bls_policy_text=BLS_POLICY,
        )
        self.assertEqual(
            status["status"],
            "ACTIVATION_RECEIPT_READY_TARGET_OBSERVATION_STILL_LOCKED",
        )
        self.assertFalse(status["event_capture_runtime_ready"])
        self.assertFalse(status["target_observation_authorized"])
        self.assertEqual(
            status["scheduled_time_utc"],
            "2027-10-14T12:30:00Z",
        )

    def test_fomc_receipt_ready_but_target_remains_locked(self):
        plan = {
            "events": [{
                "event_id": "FOMC-X",
                "event_family": "FOMC_STATEMENT",
                "scheduled_date": "2027-10-27",
                "meeting_start_date": "2027-10-26",
                "meeting_end_date": "2027-10-27",
            }]
        }
        status = evaluate_event_activation_from_official_texts_v02(
            annual_plan=plan,
            event_id="FOMC-X",
            retrieved_at_utc="2027-10-20T12:00:00Z",
            fomc_announcement_text=FOMC_ANNOUNCEMENT,
            preceding_minutes_text=PRECEDING_MINUTES,
            preceding_minutes_url=(
                "https://www.federalreserve.gov/monetarypolicy/"
                "fomcminutes20270915.htm"
            ),
        )
        self.assertEqual(
            status["status"],
            "ACTIVATION_RECEIPT_READY_TARGET_OBSERVATION_STILL_LOCKED",
        )
        self.assertEqual(
            status["scheduled_time_utc"],
            "2027-10-27T18:00:00Z",
        )

    def test_fomc_preceding_meeting_resolution_crosses_year(self):
        preceding = _preceding_regular_meeting_end(
            calendar_text=FED_CALENDAR,
            target_start=__import__("datetime").date(2027, 1, 26),
        )
        self.assertEqual(preceding.isoformat(), "2026-12-09")
        self.assertEqual(
            _minutes_url(preceding),
            "https://www.federalreserve.gov/monetarypolicy/fomcminutes20261209.htm",
        )

    def test_missing_fomc_confirmation_fails_closed(self):
        plan = {
            "events": [{
                "event_id": "FOMC-X",
                "event_family": "FOMC_STATEMENT",
                "scheduled_date": "2027-10-27",
                "meeting_start_date": "2027-10-26",
                "meeting_end_date": "2027-10-27",
            }]
        }
        with self.assertRaisesRegex(
            ValueError,
            "FOMC_NEXT_MEETING_NOT_CONFIRMED",
        ):
            evaluate_event_activation_from_official_texts_v02(
                annual_plan=plan,
                event_id="FOMC-X",
                retrieved_at_utc="2027-10-20T12:00:00Z",
                fomc_announcement_text=FOMC_ANNOUNCEMENT,
                preceding_minutes_text="Minutes published, no next-meeting line.",
                preceding_minutes_url=(
                    "https://www.federalreserve.gov/monetarypolicy/"
                    "fomcminutes20270915.htm"
                ),
            )

    def test_full_runtime_guard_can_reach_ready_without_starting_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            final = run_trigger_a_finalizer_v02(
                implementation_head_sha="d" * 40,
                output_dir=out,
                live_status=ready_status(),
                protocol_frozen_at_utc="2026-12-15T12:00:01Z",
                project_root=ROOT,
                enforce_git_head_match=False,
            )
            self.assertEqual(
                final["status"],
                "PASS_TARGET_LOCKED_PROTOCOL_FROZEN",
            )
            plan = json.loads(
                (out / "MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json").read_text(
                    encoding="utf-8"
                )
            )
            protocol = json.loads(
                (out / "MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json").read_text(
                    encoding="utf-8"
                )
            )
            impl = json.loads(
                (
                    out / "MRCR_IMPLEMENTATION_MANIFEST_TRIGGER_A_V02.json"
                ).read_text(encoding="utf-8")
            )
            auth = target_authority(protocol, plan, impl)

            status = evaluate_event_activation_from_official_texts_v02(
                annual_plan=plan,
                event_id="FOMC_STATEMENT-2027-07",
                retrieved_at_utc="2027-10-20T12:00:00Z",
                fomc_announcement_text=FOMC_ANNOUNCEMENT,
                preceding_minutes_text=PRECEDING_MINUTES,
                preceding_minutes_url=(
                    "https://www.federalreserve.gov/monetarypolicy/"
                    "fomcminutes20270915.htm"
                ),
                protocol=protocol,
                implementation_manifest=impl,
                target_open_authority=auth,
                ruleset=RULESET,
            )
            self.assertEqual(status["status"], "READY_FOR_EVENT_CAPTURE")
            self.assertTrue(status["event_capture_runtime_ready"])
            self.assertFalse(status["outcomes_authorized"])
            self.assertFalse(status["orders_enabled"])


if __name__ == "__main__":
    unittest.main()
