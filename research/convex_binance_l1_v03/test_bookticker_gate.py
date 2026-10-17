"""Synthetic no-network tests for the frozen Binance historical top-of-book witness."""
import csv
import io
import unittest
import zipfile
from decimal import Decimal

from research.convex_binance_l1_v03.bookticker_gate import (
    LOWER_MS, UPPER_MS, source_url, last_causal_quotes,
    verdict_for_entry, day_ms,
)

DAY="2023-11-01"
BASE_MS=day_ms(DAY)
FIELDS=["update_id","best_bid_price","best_bid_qty","best_ask_price",
        "best_ask_qty","transaction_time","event_time"]

def fixture(events):
    stream=io.StringIO()
    w=csv.DictWriter(stream,fieldnames=FIELDS)
    w.writeheader()
    for i,(stamp,bid,ask,askqty) in enumerate(events):
        w.writerow({
            "update_id":i,"best_bid_price":bid,"best_bid_qty":"5",
            "best_ask_price":ask,"best_ask_qty":askqty,
            "transaction_time":stamp,"event_time":stamp})
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("test.csv",stream.getvalue())
    return out.getvalue()

def entry(ts,qty="1",price="101"):
    return {"symbol":"SOLUSDT","tf":"1h","day":DAY,
            "entry_utc":"2023-11-01T00:00:02Z",
            "entry_ms":ts,"modeled_entry":price,"modeled_qty":qty}

class BookTickerFrozenContracts(unittest.TestCase):
    def test_url_exact_official_daily(self):
        self.assertTrue(source_url("SOLUSDT",DAY).endswith("/SOLUSDT/SOLUSDT-bookTicker-2023-11-01.zip"))
    def test_reject_out_of_time_range(self):
        with self.assertRaises(ValueError):source_url("SOLUSDT","2026-01-01")
    def test_only_prior_quote_never_future(self):
        t=BASE_MS+2000
        rows=[(BASE_MS+1000,"100","101","4"),(BASE_MS+3000,"200","201","4")]
        quotes,n=last_causal_quotes(fixture(rows),DAY,[t])
        self.assertEqual(str(quotes[t]["ask"]), "101")
    def test_missing_before_quote_is_not_fabricated(self):
        t=BASE_MS+500
        quotes,n=last_causal_quotes(fixture([(BASE_MS+1000,"100","101","5")]),DAY,[t])
        self.assertIsNone(quotes[t])
        self.assertEqual(verdict_for_entry(entry(t),quotes[t])["status"],"SOURCE_NO_PRIOR_QUOTE")
    def test_2sec_causal_eligible_and_capacity(self):
        t=BASE_MS+2000
        quotes,n=last_causal_quotes(fixture([(BASE_MS+1500,"100","101","5")]),DAY,[t])
        val=verdict_for_entry(entry(t),quotes[t])
        self.assertEqual(val["status"],"BOOK_QUOTE_CAUSAL_CANDIDATE")
        self.assertTrue(val["ask_qty_meets_original_modeled_qty"])
    def test_insufficient_top_quote_size(self):
        t=BASE_MS+2000
        quotes,n=last_causal_quotes(fixture([(BASE_MS+1500,"100","101","0.1")]),DAY,[t])
        self.assertEqual(verdict_for_entry(entry(t),quotes[t])["status"],"TOP_OF_BOOK_SIZE_INSUFFICIENT")
    def test_2_to_10_sensitivity_not_pass(self):
        t=BASE_MS+8000
        quotes,n=last_causal_quotes(fixture([(BASE_MS+1000,"100","101","5")]),DAY,[t])
        self.assertEqual(verdict_for_entry(entry(t),quotes[t])["status"],"QUOTE_2S_TO_10S_SENSITIVITY_ONLY")
    def test_over_10_seconds_stale(self):
        t=BASE_MS+13000
        quotes,n=last_causal_quotes(fixture([(BASE_MS+1000,"100","101","5")]),DAY,[t])
        self.assertEqual(verdict_for_entry(entry(t),quotes[t])["status"],"SOURCE_STALE_OVER_10S")
    def test_crossed_order_book_failclosed(self):
        with self.assertRaisesRegex(ValueError,"CROSSED_BOOK"):
            last_causal_quotes(fixture([(BASE_MS+1000,"105","104","5")]),DAY,[BASE_MS+2000])
    def test_decreasing_time_failclosed(self):
        with self.assertRaisesRegex(ValueError,"BAD_BOOKTICKER_EVENT_SEQUENCE_OR_DATE"):
            last_causal_quotes(fixture([
                (BASE_MS+2000,"100","101","5"),
                (BASE_MS+1000,"100","101","5")]),DAY,[BASE_MS+3000])
    def test_no_future_date_allowed(self):
        self.assertTrue(LOWER_MS<UPPER_MS)
    def test_price_comparison_is_bps_not_pnl(self):
        t=BASE_MS+2000
        quotes,n=last_causal_quotes(fixture([(BASE_MS+1500,"100","101","5")]),DAY,[t])
        x=verdict_for_entry(entry(t,price="100"),quotes[t])
        self.assertEqual(Decimal(x["ask_vs_modeled_entry_bps"]),Decimal("100"))
        self.assertTrue(x["does_not_prove_fill"])

if __name__=="__main__":unittest.main()
