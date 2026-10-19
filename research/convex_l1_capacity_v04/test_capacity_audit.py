"""Synthetic-only immutable source frontier tests; not real market evidence."""
import unittest
from collections import Counter
from research.convex_l1_capacity_v04.capacity_audit import (
    EXPECTED, TIERS, analyze_receipt,
)

def sample(symbol="SOLUSDT", fresh_n=32, ask_qty="0.5"):
    total=EXPECTED[symbol]
    entries=[]
    for i in range(total):
        if i<fresh_n:
            status="BOOK_QUOTE_CAUSAL_CANDIDATE" if float(ask_qty)>=1 else "TOP_OF_BOOK_SIZE_INSUFFICIENT"
            entries.append({"symbol":symbol,"entry_utc":f"2023-11-{i+1:02d}T00:00:00Z",
                "status":status,"quote_age_ms":500,
                "best_ask":"100.1","best_bid":"100",
                "book_ask_qty":ask_qty,"modeled_trade_qty":"1",
                "ask_vs_modeled_entry_bps":"-1.5"})
        else:
            entries.append({"symbol":symbol,"entry_utc":f"2023-11-{i+1:02d}T00:00:00Z",
                "status":"SOURCE_NO_PRIOR_QUOTE"})
    return {"symbol":symbol,"full_population":total,"all_entry_checks":entries,
        "new_status_counts":dict(Counter(x["status"] for x in entries)),
        "source_original_run":38432883246,"source_v03b_run":39026521571,
        "trading_authority":"NONE","protected_2026_opened":False,
        "cross_venue_execution_proven":False,"broker_native_stop_proven":False,
        "original_ledger_sha256":"a"*64,"source_v03b_receipt_sha256":"b"*64,
        "fresh_quote_fraction":fresh_n/total}

class CapacityContracts(unittest.TestCase):
    def test_four_predeclared_only(self):
        self.assertEqual(TIERS,("0.25","0.50","0.75","1.00"))
    def test_full_33_observation_denominator(self):
        x=analyze_receipt(sample(),"SOLUSDT","c"*64)
        self.assertEqual(x["full_population"],33)
        self.assertEqual(x["fresh_causal_quote_count"],32)
    def test_static_halving_qualifies_not_full(self):
        x=analyze_receipt(sample(),"SOLUSDT","c"*64)
        self.assertEqual(x["largest_predeclared_tier_passing_source_only"],"0.50")
        self.assertFalse(x["frozen_size_tiers"][3]["conditional_L1_screen_pass_not_execution"])
    def test_bnb_frozen_6_and_no_one_level_sufficiency_for_full(self):
        x=analyze_receipt(sample(symbol="BNBUSDT",fresh_n=6,ask_qty="0.49"),
                          "BNBUSDT","c"*64)
        self.assertEqual(x["largest_predeclared_tier_passing_source_only"],"0.25")
    def test_source_incomplete_fails_all_tiers(self):
        x=analyze_receipt(sample(fresh_n=20,ask_qty="2"),"SOLUSDT","c"*64)
        self.assertIsNone(x["largest_predeclared_tier_passing_source_only"])
        self.assertFalse(x["frozen_size_tiers"][0]["source_coverage_gate_pass"])
    def test_duplicate_episode_rejected(self):
        d=sample()
        d["all_entry_checks"][1]["entry_utc"]=d["all_entry_checks"][0]["entry_utc"]
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            analyze_receipt(d,"SOLUSDT","c"*64)
    def test_future_quote_age_rejected(self):
        d=sample()
        d["all_entry_checks"][0]["quote_age_ms"]=2001
        with self.assertRaisesRegex(ValueError,"AGE"):
            analyze_receipt(d,"SOLUSDT","c"*64)
    def test_full_size_label_parity_rejected(self):
        d=sample()
        d["all_entry_checks"][0]["status"]="BOOK_QUOTE_CAUSAL_CANDIDATE"
        d["new_status_counts"]=dict(Counter(x["status"] for x in d["all_entry_checks"]))
        with self.assertRaisesRegex(ValueError,"CONTRADICTION"):
            analyze_receipt(d,"SOLUSDT","c"*64)
    def test_invalid_depth_rejected(self):
        d=sample()
        d["all_entry_checks"][0]["book_ask_qty"]="NaN"
        with self.assertRaises(ValueError):
            analyze_receipt(d,"SOLUSDT","c"*64)
    def test_false_live_authority_rejected(self):
        d=sample()
        d["trading_authority"]="GO"
        with self.assertRaisesRegex(ValueError,"AUTHORITY"):
            analyze_receipt(d,"SOLUSDT","c"*64)
    def test_never_promote_to_execution(self):
        d=sample(fresh_n=33,ask_qty="3")
        x=analyze_receipt(d,"SOLUSDT","c"*64)
        self.assertFalse(x["cross_venue_execution_proven"])
        self.assertFalse(x["independent_economic_OOS"])
        self.assertEqual(x["trading_authority"],"NONE")

if __name__=="__main__":unittest.main()
