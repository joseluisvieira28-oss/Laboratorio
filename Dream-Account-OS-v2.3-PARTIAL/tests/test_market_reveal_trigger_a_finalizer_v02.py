import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from trigger_a_finalizer_v02 import run_trigger_a_finalizer_v02


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
                "confirmed_2027_event_count": 12,
                "events_2027": bls_events(),
            },
            "US_EMPLOYMENT_SITUATION": {
                "source_url": "https://www.bls.gov/schedule/news_release/empsit.htm",
                "confirmed_2027_event_count": 12,
                "events_2027": bls_events(),
            },
            "FOMC_STATEMENT": {
                "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
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


class TriggerAFinalizerV02Tests(unittest.TestCase):
    def test_ready_status_freezes_target_locked_protocol_and_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            receipt = run_trigger_a_finalizer_v02(
                implementation_head_sha="a" * 40,
                output_dir=out,
                live_status=ready_status(),
                protocol_frozen_at_utc="2026-12-15T12:00:01Z",
                project_root=ROOT,
            )
            self.assertEqual(
                receipt["status"],
                "PASS_TARGET_LOCKED_PROTOCOL_FROZEN",
            )
            self.assertTrue(receipt["ready_for_separate_target_open_authority"])
            self.assertFalse(receipt["target_observation_authorized"])
            self.assertFalse(receipt["outcomes_authorized"])
            self.assertFalse(receipt["orders_enabled"])

            expected = {
                "MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01.json",
                "MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json",
                "MRCR_IMPLEMENTATION_MANIFEST_TRIGGER_A_V02.json",
                "MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json",
                "MRCR_TRIGGER_A_FINALIZER_RECEIPT_V02.json",
            }
            self.assertEqual({p.name for p in out.iterdir()}, expected)

            protocol = json.loads(
                (out / "MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                protocol["status"],
                "FROZEN_PRETARGET_PROTOCOL__TARGET_LOCKED",
            )
            self.assertEqual(protocol["protocol_version"], "0.2")
            self.assertFalse(
                protocol["governance"]["target_observation_authorized"]
            )
            self.assertTrue(
                protocol["calendar"]["event_activation_receipt_required"]
            )

    def test_blocked_status_writes_only_status_and_blocked_receipt(self):
        status = ready_status()
        status["status"] = "BLOCKED"
        status["annual_plan_trigger_ready_v02"] = False
        status["sources"]["US_CPI"]["confirmed_2027_event_count"] = 0
        status["sources"]["US_CPI"]["events_2027"] = []

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            receipt = run_trigger_a_finalizer_v02(
                implementation_head_sha="b" * 40,
                output_dir=out,
                live_status=status,
                protocol_frozen_at_utc="2026-12-15T12:00:01Z",
                project_root=ROOT,
            )
            self.assertEqual(
                receipt["status"],
                "BLOCKED_OFFICIAL_ANNUAL_PLAN_NOT_READY",
            )
            self.assertFalse(receipt["target_observation_authorized"])
            self.assertEqual(
                {p.name for p in out.iterdir()},
                {
                    "MRCR_OFFICIAL_2027_CALENDAR_LIVE_STATUS_V01.json",
                    "MRCR_TRIGGER_A_FINALIZER_RECEIPT_V02.json",
                },
            )
            self.assertFalse(
                (out / "MRCR_H02_ANNUAL_PLAN_MANIFEST_V02.json").exists()
            )
            self.assertFalse(
                (out / "MRCR_PRETARGET_PROTOCOL_V02_FROZEN.json").exists()
            )

    def test_protocol_freeze_cannot_predate_official_calendar_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                ValueError,
                "protocol freeze cannot predate",
            ):
                run_trigger_a_finalizer_v02(
                    implementation_head_sha="c" * 40,
                    output_dir=Path(tmp),
                    live_status=ready_status(),
                    protocol_frozen_at_utc="2026-12-15T11:59:59Z",
                    project_root=ROOT,
                )


if __name__ == "__main__":
    unittest.main()
