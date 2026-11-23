#!/usr/bin/env python3
"""Offline tests only: no network, no L2 economic predictions, no account access."""
import math
import unittest
from book_replay import StrictBook,decimal_positive,timestamp
from source_probe import PARTS,MAX_FILE_BYTES,MAX_ALL_BYTES,license_check,lfs_sha,is_allowed_redirect,entries_from_tree,SourceStop

SNAP_MS=1785501000000

def snap(asset="BTCUSDT",bid=60000,ask=60001,size=120):
    rows=[]
    for side in ("bid","ask"):
        for i in range(size):
            px=(bid-i if side=="bid" else ask+i)
            rows.append({"timestamp_ms":SNAP_MS,"exchange":"binance","asset":asset,
                         "side":side,"price":px,"quantity":1.0,"last_update_id":1000})
    return rows

def diff(U=1001,u=1001,ts=SNAP_MS+100,side="bid",price=60000,qty=2):
    return {"timestamp_ms":ts,"exchange":"binance","asset":"BTCUSDT",
            "side":side,"price":price,"quantity":qty,
            "first_update_id":U,"last_update_id":u}

class Validity(unittest.TestCase):
    def test_snapshot_bridge_one_event(self):
        book=StrictBook()
        book.seed(snap())
        self.assertEqual(book.last_id,1000)
        self.assertEqual(book.report()["best_bid"],"60000")
        self.assertEqual(book.report()["best_ask"],"60001")
        self.assertTrue(book.apply_event([diff()]))
        self.assertEqual(book.last_id,1001)
        self.assertEqual(book.events_applied,1)
    def test_first_depth_gap_fail_closed(self):
        b=StrictBook();b.seed(snap())
        with self.assertRaisesRegex(ValueError,"SEQUENCE_GAP"):
            b.apply_event([diff(1003,1003)])
        self.assertEqual(b.last_id,1000)
        self.assertEqual(len(b.gaps),1)
    def test_stale_depth_skips(self):
        b=StrictBook();b.seed(snap())
        self.assertFalse(b.apply_event([diff(998,1000)]))
        self.assertEqual(b.stale_events,1)
    def test_covering_bridging_range_allowed(self):
        b=StrictBook();b.seed(snap())
        self.assertTrue(b.apply_event([diff(999,1002)]))
        self.assertEqual(b.last_id,1002)
    def test_both_sides_in_one_ws_event(self):
        b=StrictBook();b.seed(snap())
        b.apply_event([diff(),diff(side="ask",price=60001,qty=3)])
        self.assertEqual(b.events_applied,1)
        self.assertEqual(b.changed_price_levels,2)
    def test_delete_only_price_level_not_order(self):
        b=StrictBook();b.seed(snap())
        b.apply_event([diff(price=60000,qty=0)])
        self.assertEqual(b.report()["best_bid"],"59999")
        self.assertFalse(b.report()["individual_order_cancellations_proven"])
    def test_cross_book_guard(self):
        b=StrictBook();b.seed(snap())
        with self.assertRaisesRegex(ValueError,"CROSSED"):
            b.apply_event([diff(price=60005)])
    def test_time_regression_guard(self):
        b=StrictBook();b.seed(snap())
        b.apply_event([diff()])
        with self.assertRaisesRegex(ValueError,"REGRESSION"):
            b.apply_event([diff(1002,1002,ts=SNAP_MS+50)])
    def test_repeat_level_row_group_guard(self):
        b=StrictBook();b.seed(snap())
        with self.assertRaisesRegex(ValueError,"MIXED"):
            b.apply_event([diff(),diff(1002,1002)])
    def test_snapshot_wrong_asset(self):
        b=StrictBook()
        with self.assertRaisesRegex(ValueError,"WRONG_EXCHANGE_OR_ASSET"):
            b.seed(snap(asset="ETHUSDT"))
    def test_snapshot_must_have_both_sides(self):
        b=StrictBook()
        with self.assertRaisesRegex(ValueError,"NOT_FULL_ENOUGH"):
            b.seed([r for r in snap() if r["side"]=="bid"])
    def test_nan_level_rejected(self):
        with self.assertRaises(ValueError):decimal_positive(float("nan"))
    def test_snapshot_qty_zero_rejected(self):
        r=snap();r[0]["quantity"]=0
        with self.assertRaises(ValueError):StrictBook().seed(r)
    def test_bounded_ghost_level_pruning(self):
        b=StrictBook();b.seed(snap(size=1000))
        b.apply_event([diff(price=60000.5,qty=1)])
        self.assertEqual(len(b.bids),1000)
        self.assertEqual(b.pruned_levels,1)
    def test_declared_free_scope_fixed(self):
        self.assertEqual(len(PARTS),3)
        self.assertEqual(MAX_FILE_BYTES,80000000)
        self.assertEqual(MAX_ALL_BYTES,160000000)
        self.assertTrue(all("BTCUSDT" in p and "2026-08" in p for p in PARTS.values()))
    def test_hf_license_must_be_explicit(self):
        data={"private":False,"gated":False,"cardData":{"license":"mit"},"sha":"a"*40}
        self.assertEqual(license_check(data)[0],"a"*40)
        data["cardData"]["license"]="unknown"
        with self.assertRaisesRegex(SourceStop,"LICENSE"):license_check(data)
    def test_reject_login_gated(self):
        with self.assertRaisesRegex(SourceStop,"ACCOUNT"):
            license_check({"private":False,"gated":"auto","cardData":{"license":"mit"},"sha":"a"*40})
    def test_unsafe_redirect_is_blocked(self):
        self.assertFalse(is_allowed_redirect("http://huggingface.co/x"))
        self.assertFalse(is_allowed_redirect("https://huggingface.co.bad.site/x"))
        self.assertTrue(is_allowed_redirect("https://huggingface.co/x"))
    def test_provenance_lfs_sha(self):
        e={"lfs":{"oid":"sha256:"+"b"*64}}
        self.assertEqual(lfs_sha(e),"b"*64)
    def test_tree_parsing_immutable_files(self):
        tree=[{"type":"file","path":"depth/binance/BTCUSDT/2026-08.parquet","size":5},
              {"type":"directory","path":"snapshots/binance/BTCUSDT"}]
        self.assertEqual(len(entries_from_tree(tree)),1)
if __name__=="__main__":unittest.main()
