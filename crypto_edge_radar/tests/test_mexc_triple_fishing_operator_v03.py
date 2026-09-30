from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from scripts.mexc_triple_fishing_operator_v03 import (
    BNB,
    DH03,
    OPTIONS,
    TripleFishingOperatorV03,
)


class FakeSlot:
    def __init__(self, occupied=False):
        self.occupied=occupied
    def current(self):
        return {"signal_identity":"x"} if self.occupied else None


class FakeEngine:
    def __init__(self, *, active=False):
        self.active=active
        self.entered=[]
        self.global_slot=FakeSlot(False)
    def manage_active(self):
        if self.active:
            return {"status":"ACTIVE_WAITING_EXIT","signal_identity":"existing"}
        return {"status":"IDLE_NO_OPERATOR_POSITION"}
    def enter_signal(self, signal):
        self.entered.append(signal)
        return {
            "status":"FILLED_EXIT_PENDING",
            "candidate_id":signal["candidate_id"],
            "signal_identity":signal["immutable_signal_key"],
        }


class FakeSource:
    def __init__(self, result):
        self.result=result
        self.marks=[]
        self.poll_count=0
    def poll(self, **kwargs):
        self.poll_count+=1
        return self.result
    def mark(self, key, status):
        self.marks.append((key,status))


def sig(candidate, key, target):
    return {
        "candidate_id":candidate,
        "strategy_id":candidate,
        "immutable_signal_key":key,
        "entry_target_utc":target.isoformat().replace("+00:00","Z"),
        "exit_target_utc":(target+timedelta(days=1)).isoformat().replace("+00:00","Z"),
        "max_late_seconds":5.0,
    }


class TripleFishingOperatorTests(unittest.TestCase):
    def build(self, td, *, active=False):
        now=datetime.now(timezone.utc)-timedelta(milliseconds=100)
        b=FakeSource({"status":"OK","signals":[sig(BNB,"b",now)]})
        o=FakeSource({"status":"SIGNAL_AVAILABLE","signal":sig(OPTIONS,"o",now)})
        d=FakeSource({"status":"COLLECTING","signals":[sig(DH03,"d",now)]})
        engine=FakeEngine(active=active)
        sup=TripleFishingOperatorV03(
            engine=engine,
            bnb_source=b,
            options_source=o,
            dh03_source=d,
            state_path=str(Path(td)/"state.json"),
        )
        return sup,engine,b,o,d

    def test_exactly_one_due_lane_wins_and_losers_are_terminal_no_chase(self):
        with tempfile.TemporaryDirectory() as td:
            sup,engine,b,o,d=self.build(td)
            out=sup.run_cycle()
            self.assertEqual(len(engine.entered),1)
            self.assertEqual(engine.entered[0]["candidate_id"],BNB)
            self.assertIn(("b","CONSUMED_ACTIVE_REAL_MONEY"),b.marks)
            self.assertIn(("d","MISSED_CONFLICT_NO_CHASE"),d.marks)
            self.assertIn(("o","MISSED_CONFLICT_NO_CHASE"),o.marks)
            self.assertEqual(out["status"],"FILLED_EXIT_PENDING")

    def test_existing_active_position_consumes_slot_but_sources_still_poll(self):
        with tempfile.TemporaryDirectory() as td:
            sup,engine,b,o,d=self.build(td,active=True)
            out=sup.run_cycle()
            self.assertEqual(engine.entered,[])
            self.assertEqual(b.poll_count,1)
            self.assertEqual(o.poll_count,1)
            self.assertEqual(d.poll_count,1)
            self.assertIn(("b","MISSED_CONFLICT_NO_CHASE"),b.marks)
            self.assertIn(("d","MISSED_CONFLICT_NO_CHASE"),d.marks)
            self.assertIn(("o","MISSED_CONFLICT_NO_CHASE"),o.marks)
            self.assertEqual(out["status"],"MANAGING_GLOBAL_SLOT_WITH_THREE_SOURCES_WATCHING")


if __name__=="__main__":
    unittest.main()
