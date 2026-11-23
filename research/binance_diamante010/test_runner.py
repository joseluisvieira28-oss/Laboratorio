#!/usr/bin/env python3
"""BINANCE010 source-free original rule and expanded timing tests, no prices/network."""
import unittest
from decimal import Decimal as D
from runner import (SECONDS,WINDOWS,DECISION_SECONDS,FRAME_CAP,JOURNAL_CAP,
                    blob_sha,guard,setup,OUT,PINS)

class OriginalFrozenScience(unittest.TestCase):
    def test_original_source_has_not_changed(self):
        self.assertEqual(len(PINS),6)
        result=guard()
        self.assertTrue(result["no_paid_api"])
        self.assertEqual(result["real_orders"],0)
    def test_git_blob_known_sha(self):
        self.assertEqual(blob_sha(b"test\n"),"9daeafb9864cf43055ae93beb0afd6c7d144bfa4")
    def test_one_thirty_minute_no_trading_window(self):
        self.assertEqual(SECONDS,1800)
        self.assertEqual(WINDOWS,60)
        self.assertEqual(DECISION_SECONDS,1680)
        self.assertEqual(SECONDS-DECISION_SECONDS,120)
        self.assertEqual(str(OUT),"binance010-evidence")
    def test_longer_caps_are_explicit(self):
        self.assertEqual(FRAME_CAP,250000)
        self.assertEqual(JOURNAL_CAP,220000000)
    def test_original_depth_rule_has_not_changed(self):
        _,study=setup()
        self.assertEqual(str(study.SELL_THRESHOLD), "0.65")
        self.assertEqual(str(study.DEPTH_PERSIST_MIN), "0.80")
        self.assertEqual(str(study.MID_FLOOR_BPS), "-3")
        self.assertEqual(str(study.MIN_QUOTE), "5000")
        self.assertEqual(str(study.FEE_BPS), "10")
        self.assertEqual(study.HORIZON_NS,60000000000)
        self.assertEqual(study.CAPTURE_NS,1800*10**9)
        self.assertEqual(study.LATEST_DECISION_NS,1680*10**9)
    def test_same_004_window_rules_extend_exactly_sixty(self):
        _,study=setup()
        m=study.ProspectiveStudy()
        for s,b in m.books.items():
            b.status="SYNCED"
            b.last_update_id=100
            b.bids={D("99.99"):D("100"),D("99.98"):D("100")}
            b.asks={D("100.01"):D("100"),D("100.02"):D("100")}
            m.last_depth_ns[s]=0
        m._start(0)
        m._advance(1800*10**9)
        self.assertEqual(m.idx,60)
        self.assertEqual(len(m.windows),180)
        self.assertEqual(sum(w["allowed_before_cutoff"] for w in m.windows),56*3)
        self.assertFalse(any(w["allowed_before_cutoff"] for w in m.windows if w["end_t0_seconds"]>1680))
        # There are NO market prints in synthetic data: zero real signals.
        self.assertEqual(len(m.events),0)
        m._advance(3600*10**9)
        self.assertEqual(m.idx,60)
        self.assertEqual(m.summary()["real_fills"],0)
    def test_quotewalks_remain_hypothetical(self):
        _,study=setup()
        self.assertEqual(study.NOTIONALS,(D("100"),D("1000")))
        self.assertEqual(study.SCENARIOS["BASE_2BPS"],D("2"))
        self.assertEqual(study.SCENARIOS["STRESS_5BPS"],D("5"))
        self.assertEqual(study.MIN_EVENTS_FOR_GO,200)
        self.assertEqual(study.MIN_DAYS_FOR_GO,20)

if __name__=="__main__":unittest.main()
