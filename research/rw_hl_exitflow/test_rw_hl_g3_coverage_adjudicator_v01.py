"""G3 synthetic source-only validator tests; NO live market requests or outcomes."""
import json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
import rw_hl_g3_coverage_adjudicator_v01 as c

START=datetime(2026,10,10,tzinfo=timezone.utc)
END=datetime(2026,10,24,tzinfo=timezone.utc)

def sample(utc="2026-10-10T00:15:00Z",markets=100):
    slot=utc[:13]+":00:00Z"
    return {
      "lab_id":"RW-HL-EXITFLOW-001","record_type":"PUBLIC_HL_HOURLY_SOURCE",
      "observed_at_utc":utc,"source_hour_utc":slot,
      "github_run_id":"4200000","source":"HYPERLIQUID_PUBLIC_META_AND_ASSET_CTXS",
      "no_backfill":True,"economic_outcomes_opened":False,"trading_authority":"NONE",
      "market_count":markets,
      "market_data":{"valid_public_markets":markets,"market_context":[
        {"coin":f"C{i:03d}","openInterest":"1","markPx":"25.35","funding":"-0.00003"}
        for i in range(markets)]}
    }

def write_days(root,n):
    for k in range(n):
        dt=START+timedelta(hours=k)
        file=Path(root)/dt.strftime("%Y-%m-%d")/(dt.strftime("%H")+".json")
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text("{}")

class G3CoverageTests(unittest.TestCase):
    def test_activation_frozen(self):
        d=c.frozen()
        self.assertEqual(d["expected_utc_hours"],336)
        self.assertFalse(d["economic_outcomes_authorized"])
    def test_one_valid_public_source(self):
        self.assertEqual(c.verify_record(sample(),Path("any"),START),100)
    def test_future_returns_sealed(self):
        x=sample();x["economic_outcomes_opened"]=True
        with self.assertRaises(c.SourceBlocked):c.verify_record(x,Path("a"),START)
    def test_wrong_coin_binding(self):
        x=sample();x["market_data"]["market_context"][1]["coin"]="C000"
        with self.assertRaises(c.SourceBlocked):c.verify_record(x,Path("a"),START)
    def test_invalid_funding(self):
        x=sample();x["market_data"]["market_context"][0]["funding"]="nan"
        with self.assertRaises(c.SourceBlocked):c.verify_record(x,Path("a"),START)
    def test_true_source_hour_mismatch(self):
        x=sample(utc="2026-10-10T01:00:01Z");x["source_hour_utc"]="2026-10-10T00:00:00Z"
        with self.assertRaises(c.SourceBlocked):c.verify_record(x,Path("a"),START)
    def test_bogus_run_id_rejected(self):
        x=sample();x["github_run_id"]="local"
        with self.assertRaises(c.SourceBlocked):c.verify_record(x,Path("a"),START)
    def test_start_before_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            z=c.source_gate(START-timedelta(hours=1),tmp)
            self.assertEqual(z["classification"],"G3_FORWARD_INSUFFICIENT_UNTIL_2026_10_24_UTC")
            self.assertEqual(z["hours_elapsed"],0)
    def test_early_320_is_not_economic_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp,320)
            with patch.object(c,"verify_record",return_value=100):
                z=c.source_gate(END-timedelta(hours=1),tmp)
            self.assertEqual(z["classification"],"G3_FORWARD_INSUFFICIENT_UNTIL_2026_10_24_UTC")
            self.assertFalse(z["economic_outcomes_unlocked"])
    def test_320_source_hours_14_dates_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp,320)
            with patch.object(c,"verify_record",return_value=100):
                z=c.source_gate(END,tmp)
            self.assertEqual(z["classification"],"G3_SOURCE_COVERAGE_PASS")
            self.assertEqual(z["distinct_utc_dates"],14)
    def test_319_source_hours_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp,319)
            with patch.object(c,"verify_record",return_value=100):
                z=c.source_gate(END,tmp)
            self.assertEqual(z["classification"],"G3_SOURCE_COVERAGE_BLOCKED_OR_INSUFFICIENT")
    def test_invalid_blob_records_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp,336)
            z=c.source_gate(END,tmp)
            self.assertTrue(z["receipt_failures"])
            self.assertEqual(z["classification"],"G3_SOURCE_COVERAGE_BLOCKED_OR_INSUFFICIENT")
    def test_other_date_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            x=root/"2026-10-09"/"23.json";x.parent.mkdir();x.write_text("{}")
            z=c.source_gate(END,root)
            self.assertEqual(z["valid_unique_hour_receipts"],0)
    def test_no_trades_or_future_marks_computed(self):
        import inspect
        txt=inspect.getsource(c)
        self.assertNotIn("create_order(",txt)
        self.assertNotIn("price_exit",txt)
        self.assertNotIn("trading_execution",txt)
if __name__=="__main__":unittest.main()
