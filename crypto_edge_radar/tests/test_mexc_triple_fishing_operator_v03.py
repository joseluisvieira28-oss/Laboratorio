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
    def build(self, td, *, active=False, signal_time=None):
        now=signal_time or (datetime.now(timezone.utc)-timedelta(milliseconds=100))
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


    def test_meta_observer_on_off_preserves_operational_decision(self):
        class Observer:
            def __init__(self):
                self.seen=[]
            def observe(self, **kwargs):
                self.seen.append(kwargs)
                return {"status":"RECORDED"}

        with tempfile.TemporaryDirectory() as td_off, tempfile.TemporaryDirectory() as td_on:
            frozen_time=datetime.now(timezone.utc)-timedelta(milliseconds=100)
            off,engine_off,b_off,o_off,d_off=self.build(td_off,signal_time=frozen_time)
            on,engine_on,b_on,o_on,d_on=self.build(td_on,signal_time=frozen_time)
            observer=Observer()
            on.meta_observer=observer

            out_off=off.run_cycle()
            out_on=on.run_cycle()

            self.assertEqual(engine_off.entered,engine_on.entered)
            self.assertEqual(b_off.marks,b_on.marks)
            self.assertEqual(o_off.marks,o_on.marks)
            self.assertEqual(d_off.marks,d_on.marks)
            self.assertEqual(out_off["status"],out_on["status"])
            self.assertEqual(out_off.get("arbitration"),out_on.get("arbitration"))
            self.assertEqual(out_off.get("entry_result"),out_on.get("entry_result"))
            self.assertEqual(len(observer.seen),3)

    def test_meta_observer_failure_cannot_block_or_change_parent(self):
        class BrokenObserver:
            def observe(self, **kwargs):
                raise RuntimeError("synthetic recorder failure")

        with tempfile.TemporaryDirectory() as td:
            sup,engine,b,o,d=self.build(td)
            sup.meta_observer=BrokenObserver()
            out=sup.run_cycle()

            self.assertEqual(len(engine.entered),1)
            self.assertEqual(engine.entered[0]["candidate_id"],BNB)
            self.assertEqual(out["status"],"FILLED_EXIT_PENDING")
            self.assertEqual(len(sup.meta_state),3)
            self.assertTrue(all(
                row["status"]=="RECORDER_FAIL_CLOSED_PARENT_UNCHANGED"
                for row in sup.meta_state.values()
            ))


if __name__=="__main__":
    unittest.main()
