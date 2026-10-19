"""Synthetic CI only, no authentic historical OKX book or live trading."""
import unittest,json
from decimal import Decimal
from research.convex_okx_l2_v05.catalogue_gate import CASES,classify,file_link_hosts
from research.convex_okx_l2_v05.l2_reconstructor import (
    Book,SourceRejected,reconstruct_at,sweep,update
)
T=1698797100000
SYMBOL="BNB-USDT-SWAP"
def snap(ts=T,asks=None,bids=None,**extra):
    r={"instId":SYMBOL,"action":"snapshot","ts":ts,
       "asks":asks or [["100.0","4"],["101","8"]],
       "bids":bids or [["99","3"],["98","8"]]}
    r.update(extra)
    return r
def change(ts=T+1,asks=None,bids=None,**extra):
    r={"instId":SYMBOL,"action":"update","ts":ts,
       "asks":asks or [],"bids":bids or []}
    r.update(extra)
    return r

class CatalogueGuards(unittest.TestCase):
    def test_exact_two_historical_signal_dates(self):
        self.assertEqual(len(CASES),2)
        self.assertEqual(CASES[0][2],"2023-05-29")
        self.assertEqual(CASES[1][2],"2023-11-01")
    def test_http403_must_block(self):
        self.assertEqual(classify(CASES[0],403,error="HTTP_403")["status"],"SOURCE_BLOCKED")
    def test_empty_200_must_block(self):
        self.assertEqual(classify(CASES[0],200,b'{"code":"0","data":[]}')["status"],"SOURCE_BLOCKED")
    def test_nonempty_catalog_is_not_l2(self):
        d=classify(CASES[0],200,b'{"code":"0","data":[{"groupDetails":[{"fileDate":"2023-05-29"}]}]}')
        self.assertEqual(d["status"],"CATALOGUE_SCHEMA_ONLY_NO_FILE_URL")
        self.assertFalse(d["prices_observed"])
    def test_deep_explicit_https_link_only(self):
        blob={"groupDetails":[{"file":{"downloadUrl":"https://files.okx.com/a.tar.gz?token=PRIVATE"}}]}
        a=file_link_hosts(blob)
        self.assertEqual(len(a),1)
        self.assertEqual(a[0]["host"],"files.okx.com")
        self.assertNotIn("PRIVATE",json.dumps(a))
    def test_non_https_link_not_recognized(self):
        a=file_link_hosts({"downloadUrl":"http://untrusted.example/a.tar.gz"})
        self.assertEqual(a,[])
    def test_nonzero_provider_code_failclosed(self):
        d=classify(CASES[0],200,b'{"code":"50010","data":[{"downloadUrl":"https://files.okx.com/a"}]}')
        self.assertEqual(d["status"],"SOURCE_BLOCKED")

class BookSafety(unittest.TestCase):
    def test_valid_ask_bids_and_multilevel_sweep(self):
        b,age=reconstruct_at([snap()],SYMBOL,T+500)
        self.assertEqual(age,500)
        o=sweep(b,"BUY_LONG_ENTRY","6","1","1",True)
        self.assertEqual(o["status"],"HYPOTHETICAL_L2_LEVEL_SWEEP_NOT_FILL")
        self.assertEqual(o["levels_used"],2)
        self.assertEqual(Decimal(o["hypothetical_vwap_px"]),Decimal(602)/6)
        self.assertGreater(Decimal(o["hypothetical_impact_bps"]),0)
    def test_full_best_ask_no_impact(self):
        b,_=reconstruct_at([snap()],SYMBOL,T+200)
        x=sweep(b,"BUY_LONG_ENTRY","2","1","1",True)
        self.assertEqual(x["levels_used"],1)
        self.assertEqual(Decimal(x["hypothetical_impact_bps"]),0)
    def test_not_enough_l2_depth_fail_as_partial(self):
        b,_=reconstruct_at([snap()],SYMBOL,T+500)
        o=sweep(b,"BUY_LONG_ENTRY","20","1","1",True)
        self.assertEqual(o["status"],"INSUFFICIENT_400_LEVEL_DEPTH")
        self.assertEqual(o["contracts_missing"],"8")
    def test_bid_side_exit_worse_than_best(self):
        b,_=reconstruct_at([snap()],SYMBOL,T+200)
        o=sweep(b,"SELL_LONG_EXIT","6","1","1",True)
        self.assertGreater(Decimal(o["hypothetical_impact_bps"]),0)
    def test_original_qty_not_automatically_okx_contract_qty(self):
        b,_=reconstruct_at([snap()],SYMBOL,T+200)
        x=sweep(b,"BUY_LONG_ENTRY","1.5","0.5","1",True)
        self.assertEqual(x["contracts_required"],"3")
    def test_missing_historical_contract_metadata_rejected(self):
        b,_=reconstruct_at([snap()],SYMBOL,T+200)
        with self.assertRaisesRegex(SourceRejected,"METADATA_UNVERIFIED"):
            sweep(b,"BUY_LONG_ENTRY","1","1","1",False)
    def test_off_lot_rejected(self):
        b,_=reconstruct_at([snap()],SYMBOL,T+200)
        with self.assertRaisesRegex(SourceRejected,"OFF_HISTORICAL_CONTRACT_LOT"):
            sweep(b,"BUY_LONG_ENTRY","1.1","1","1",True)
    def test_future_quote_does_not_get_used(self):
        with self.assertRaisesRegex(SourceRejected,"NO_CAUSAL_SNAPSHOT"):
            reconstruct_at([snap(ts=T+5000)],SYMBOL,T)
    def test_stale_quote_rejected(self):
        with self.assertRaisesRegex(SourceRejected,"STALE"):
            reconstruct_at([snap(ts=T)],SYMBOL,T+2001)
    def test_missing_first_snapshot_rejected(self):
        with self.assertRaisesRegex(SourceRejected,"MISSING_FULL_SNAPSHOT"):
            reconstruct_at([change(ts=T)],SYMBOL,T)
    def test_crossed_book_rejected(self):
        with self.assertRaisesRegex(SourceRejected,"CROSSED"):
            reconstruct_at([snap(bids=[["100","1"]])],SYMBOL,T)
    def test_zero_qty_update_deletes_level(self):
        b,_=reconstruct_at([snap(),change(asks=[["100","0"]])],SYMBOL,T+2)
        self.assertEqual(sorted(b.asks),[Decimal("101")])
    def test_broken_prev_seq_rejected(self):
        s=snap(seqId=10,prevSeqId=-1)
        n=change(seqId=11,prevSeqId=9)
        with self.assertRaisesRegex(SourceRejected,"BROKEN_SEQ"):
            reconstruct_at([s,n],SYMBOL,T+2)
    def test_wrong_instrument_rejected(self):
        with self.assertRaisesRegex(SourceRejected,"WRONG_OR_UNVERIFIED"):
            reconstruct_at([snap(instId="SOL-USDT-SWAP")],SYMBOL,T)
    def test_400_limit_rejected(self):
        asks=[[str(100+i), "1"] for i in range(401)]
        with self.assertRaisesRegex(SourceRejected,"400_LEVEL"):
            reconstruct_at([snap(asks=asks)],SYMBOL,T)
    def test_duplicate_level_rejected(self):
        with self.assertRaisesRegex(SourceRejected,"DUPLICATE"):
            reconstruct_at([snap(asks=[["100","1"],["100","2"]])],SYMBOL,T)
    def test_no_real_fill_or_alpha_claim(self):
        b,_=reconstruct_at([snap()],SYMBOL,T)
        d=sweep(b,"BUY_LONG_ENTRY","5","1","1",True)
        self.assertFalse(d["source_books_prove_broker_fill"])
        self.assertFalse(d["live_go"])

if __name__=="__main__":
    unittest.main()
