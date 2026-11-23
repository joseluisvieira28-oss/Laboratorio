#!/usr/bin/env python3
"""BINANCE008 strict synthetic security and normalized L2 tests; NO NETWORK."""
import sys
import unittest
from datetime import datetime, timezone, timedelta

from probe_sources import (
    HF_URL,TARDIS_URLS,DATE,RedirectObserved,SourceBlocked,official_hostname,
    public_url,utc_parse_ms,parse_numeric,verify_l2,verify_trades,
    MAX_ONE,MAX_TOTAL
)

def at(seconds=0):
    return (datetime(2026,9,1,tzinfo=timezone.utc)
            +timedelta(seconds=seconds)).isoformat().replace("+00:00","Z")

def l2(s,side,price,qty=1.0,snapshot=True):
    return {"exchange":"binance","symbol":"SOLUSDT",
            "timestamp":at(s),"local_timestamp":at(s),
            "is_snapshot":str(snapshot).lower(),"side":side,
            "price":str(price),"amount":str(qty)}

class OfficialHost(unittest.TestCase):
    def test_exact_official_hf_cdn_hosts(self):
        for host in ("huggingface.co","cas-server.xethub.hf.co","transfer.xethub-eu.hf.co",
                     "us.aws.cdn.hf.co","cdn-lfs-us-1.hf.co"):
            self.assertTrue(official_hostname(host))
    def test_official_suffix_spoof_rejected(self):
        self.assertFalse(official_hostname("us.aws.cdn.hf.co.attacker.org"))
        self.assertFalse(official_hostname("hf.co.attacker.org"))
        self.assertFalse(official_hostname("cdn-lfs-new-unknown.hf.co"))
    def test_pinned_initial_hf_source(self):
        self.assertEqual(public_url(HF_URL,"hf").hostname,"huggingface.co")
    def test_no_other_private_or_nonpublic_sources(self):
        for url in ("https://evil.example/anything","http://datasets.tardis.dev/secret",
                    "https://datasets.tardis.dev/v1/binance/trades/2026/10/01/BTCUSDT.csv.gz"):
            with self.assertRaises(SourceBlocked):public_url(url,"tardis")
    def test_fixed_free_sample_utc_day(self):
        self.assertEqual(len(TARDIS_URLS),2)
        self.assertEqual(DATE,"2026-09-01")
        self.assertTrue(all("/2026/09/01/SOLUSDT.csv.gz" in x for x in TARDIS_URLS.values()))
    def test_bounded_compressed_budget(self):
        self.assertEqual(MAX_ONE,90_000_000)
        self.assertEqual(MAX_TOTAL,120_000_000)

class NormalizedL2(unittest.TestCase):
    def setUp(self):
        self.rows=[]
        for i in range(110):
            self.rows.append(l2(0,"bid",100.00-i*0.01))
            self.rows.append(l2(0,"ask",100.01+i*0.01))
        for i in range(520):
            self.rows.append(l2(0.1+i/1000.0, "bid", 100.00, 1+i/100, False))
    def test_receipt_parsing(self):
        self.assertEqual(utc_parse_ms(at(0)),int(datetime(2026,9,1,tzinfo=timezone.utc).timestamp()*1000))
    def test_can_replay_realistic_synthetic_group(self):
        r=verify_l2(self.rows,len(self.rows))
        self.assertEqual(r["replayed_price_level_diffs"],520)
        self.assertFalse(r["native_binance_U_u_ids_seen"])
        self.assertFalse(r["full_24h_continuity_verified"])
    def test_snapshot_missing_side_cannot_pass(self):
        r=[x for x in self.rows if x["side"]=="bid"]
        with self.assertRaises(SourceBlocked):verify_l2(r,len(r))
    def test_crossed_book_fails(self):
        self.rows[-1]["price"]="10000.01"
        with self.assertRaisesRegex(SourceBlocked,"CROSSED"):verify_l2(self.rows,len(self.rows))
    def test_same_second_receipt_regression_fail_closed(self):
        self.rows[-1]["local_timestamp"]=at(-100)
        with self.assertRaisesRegex(SourceBlocked,"REGRESSION|LOCAL_TIMESTAMP_BEFORE_SOURCE_TIME"):verify_l2(self.rows,len(self.rows))
    def test_nan_price_fails(self):
        self.rows[-1]["price"]="nan"
        with self.assertRaises(SourceBlocked):verify_l2(self.rows,len(self.rows))
    def test_one_aligned_trade_matches(self):
        b=verify_l2(self.rows,len(self.rows))
        r={"exchange":"binance","symbol":"SOLUSDT","timestamp":at(.3),
           "local_timestamp":at(.3),"id":"123","side":"buy","price":"100","amount":"1"}
        v=verify_trades([r],b)
        self.assertEqual(v["matching_trade_rows"],1)
    def test_no_trade_overlap_is_blocked(self):
        b=verify_l2(self.rows,len(self.rows))
        r={"exchange":"binance","symbol":"SOLUSDT","timestamp":at(100),
           "local_timestamp":at(100),"id":"123","side":"buy","price":"100","amount":"1"}
        with self.assertRaises(SourceBlocked):verify_trades([r],b)

if __name__=="__main__":unittest.main()
