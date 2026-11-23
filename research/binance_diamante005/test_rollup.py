#!/usr/bin/env python3
"""Synthetic multi-day audit regressions; future return data is NEVER in tests."""
import datetime as dt
import unittest
from rollup import analyze, event_net_bps, cluster_lower_bound

def event(kind,net):
    return {"kind":kind,"status":"MATURED_HYPOTHETICAL_NOT_FILLED",
            "returns":{"1000":{"STRESS_5BPS_net_bps":str(net)}}}

def record(day,run_id=1,valid=True,n_primary=10):
    events=([event("PRIMARY",5) for _ in range(n_primary)]
            +[event("FLOW_ONLY_CONTROL",-3),event("UNCONDITIONAL_BASELINE",-4)])
    return {"day":str(day),"run_id":run_id,"status":"SOURCE_AND_FROZEN_LEDGER_PASS" if valid else "BLOCKED",
            "events":events if valid else []}

class AuditTests(unittest.TestCase):
    def test_not_matured_is_not_win(self):
        e=event("PRIMARY",1000);e["status"]="CENSORED_LATE_ENTRY"
        self.assertIsNone(event_net_bps(e))
    def test_no_sessions_inconclusive_not_go(self):
        r=analyze([],dt.date(2026,12,24))
        self.assertEqual(r["status"],"INCONCLUSIVE_INSUFFICIENT_PRIMARY")
        self.assertFalse(r["economic_go_scientific_limited"])
    def test_insufficient_8min_days_not_go(self):
        r=analyze([record(dt.date(2026,11,24),1,n_primary=0)],dt.date(2026,12,24))
        self.assertEqual(r["economic_groups"]["PRIMARY"]["matured"],0)
        self.assertFalse(r["economic_go_scientific_limited"])
    def test_first_of_day_failure_cannot_be_rescued(self):
        rows=[record(dt.date(2026,11,24),1,valid=False),
              record(dt.date(2026,11,24),2,valid=True)]
        r=analyze(rows,dt.date(2026,12,24))
        self.assertEqual(r["reported_distinct_days"],1)
        self.assertEqual(r["source_valid_days"],0)
        self.assertEqual(len(r["duplicates_excluded"]),1)
    def test_20_days_200_events_pass_only_synthetic(self):
        rows=[record(dt.date(2026,11,24)+dt.timedelta(days=i),i+1)
              for i in range(20)]
        r=analyze(rows,dt.date(2026,12,24))
        self.assertEqual(r["economic_groups"]["PRIMARY"]["matured"],200)
        self.assertEqual(r["primary_days_with_matured_signals"],20)
        self.assertEqual(r["status"],"SCIENTIFIC_LIMITED_GO_NO_LIVE_GO")
        self.assertFalse(r["live_trading_authorized"])
        self.assertEqual(r["real_fills"],0)
    def test_one_day_200_events_does_not_pass(self):
        rows=[record(dt.date(2026,11,24),1,n_primary=200)]
        r=analyze(rows,dt.date(2026,12,24))
        self.assertEqual(r["status"],"INCONCLUSIVE_INSUFFICIENT_PRIMARY")
        self.assertFalse(r["economic_go_scientific_limited"])
    def test_20_day_negative_does_not_pass(self):
        rows=[record(dt.date(2026,11,24)+dt.timedelta(days=i),i+1)
              for i in range(20)]
        for d in rows:
            for e in d["events"]:
                if e["kind"]=="PRIMARY":
                    e["returns"]["1000"]["STRESS_5BPS_net_bps"]="-5"
        r=analyze(rows,dt.date(2026,12,24))
        self.assertEqual(r["status"],"ECONOMIC_GATE_NOT_PASSED")
    def test_bootstrap_requires_20_days(self):
        self.assertIsNone(cluster_lower_bound({"2026-11-24":[100.0]}))
if __name__=="__main__":unittest.main()
