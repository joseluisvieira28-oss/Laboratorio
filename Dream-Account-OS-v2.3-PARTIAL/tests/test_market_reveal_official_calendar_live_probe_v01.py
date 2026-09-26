import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from official_2027_calendar_live_probe import evaluate_official_calendar_status


def bls_text(year=2027, count=12):
    months = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]
    abbr = ["Jan.","Feb.","Mar.","Apr.","May","Jun.","Jul.","Aug.","Sep.","Oct.","Nov.","Dec."]
    rows=[]
    for i in range(count):
        rows.extend([
            f"{months[i]} {year}",
            f"{abbr[i]} {min(i+1,28):02d}, {year}",
            "08:30 AM",
        ])
    return "\n".join(rows)


def fomc_text(tentative=True):
    body = """2027 FOMC Meetings
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
2028
"""
    if tentative:
        body += "\nEach meeting date is tentative until confirmed at the meeting immediately preceding it."
    return body


class OfficialCalendarLiveProbeTests(unittest.TestCase):
    def test_v02_annual_plan_can_be_ready_while_v01_all_confirmed_is_not(self):
        receipt = evaluate_official_calendar_status(
            cpi_text=bls_text(),
            empsit_text=bls_text(),
            fomc_text=fomc_text(tentative=True),
            checked_at_utc="2026-12-20T12:00:00Z",
        )
        self.assertEqual(receipt["status"], "READY_FOR_V02_ANNUAL_PLAN")
        self.assertTrue(receipt["annual_plan_trigger_ready_v02"])
        self.assertFalse(receipt["strict_v01_all_confirmed_trigger_ready"])
        self.assertTrue(
            receipt["sources"]["FOMC_STATEMENT"]["annual_plan_bindable_v02"]
        )
        self.assertFalse(
            receipt["sources"]["FOMC_STATEMENT"]["all_events_confirmed_v01"]
        )

    def test_incomplete_bls_keeps_v02_blocked(self):
        receipt = evaluate_official_calendar_status(
            cpi_text=bls_text(count=11),
            empsit_text=bls_text(),
            fomc_text=fomc_text(tentative=True),
            checked_at_utc="2026-12-20T12:00:00Z",
        )
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertFalse(receipt["annual_plan_trigger_ready_v02"])

    def test_fomc_missing_meeting_keeps_v02_blocked(self):
        text = fomc_text(tentative=True).replace("December\n7-8*\n", "")
        receipt = evaluate_official_calendar_status(
            cpi_text=bls_text(),
            empsit_text=bls_text(),
            fomc_text=text,
            checked_at_utc="2026-12-20T12:00:00Z",
        )
        self.assertFalse(receipt["annual_plan_trigger_ready_v02"])


if __name__ == "__main__":
    unittest.main()
