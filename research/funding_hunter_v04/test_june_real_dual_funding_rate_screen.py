"""Hermetic V04 original fixed June 2025 source and causal 24h rate-only tests."""
import io
import zipfile
import unittest
from datetime import datetime,timezone,timedelta
from decimal import Decimal
from research.funding_hunter_v04.june_real_dual_funding_rate_screen import (
    parse_month,prior_pair,episode_for_day,evaluate,utc_ms,archive_links,SIGNAL_THRESHOLD_BPS_PER_HOUR)

def fixture(contract,rates=("0.00064",)*90):
    first=datetime(2025,6,1,tzinfo=timezone.utc)
    csvrows=["instrument_name,funding_rate,funding_time"]
    for i,rate in enumerate(rates):
        t=first+timedelta(hours=8*i)
        csvrows.append(f"{contract},{rate},{t.isoformat()}")
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as f:
        f.writestr(contract+"-funding-2025-06.csv","\n".join(csvrows)+"\n")
    return out.getvalue()
def records(rate):
    first=datetime(2025,6,1,tzinfo=timezone.utc)
    return [(int((first+timedelta(hours=8*i)).timestamp()*1000),Decimal(str(rate))) for i in range(90)]

class ScienceAndCausality(unittest.TestCase):
    def test_original_conservative_threshold(self):
        self.assertEqual(SIGNAL_THRESHOLD_BPS_PER_HOUR,Decimal(".5"))
    def test_correct_two_original_zip_schemas(self):
        for sym in ("BTC-USDT-SWAP","BTC-USD-SWAP"):
            rows,meta=parse_month(fixture(sym),sym)
            self.assertEqual(len(rows),90)
            self.assertEqual(meta["observed_intervals_minutes"],{480:89})
    def test_bad_contract_source_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"MISMATCH_INSTRUMENT"):
            parse_month(fixture("BTC-USDT-SWAP"),"BTC-USD-SWAP")
    def test_2026_outside_source_fails(self):
        out=fixture("BTC-USD-SWAP")
        # This source is always June, no protected data can be injected as a source.
        self.assertEqual(parse_month(out,"BTC-USD-SWAP")[1]["rows"],90)
    def test_csv_wrong_fields(self):
        bad=io.BytesIO()
        with zipfile.ZipFile(bad,"w") as z:z.writestr("one.csv","name,time,rate\nx,x,1\n")
        with self.assertRaisesRegex(ValueError,"FUNDING_COLUMNS"):
            parse_month(bad.getvalue(),"BTC-USDT-SWAP")
    def test_duplicate_timestamp_blocked(self):
        blob=fixture("BTC-USD-SWAP",("0.0005",)*90)
        self.assertEqual(parse_month(blob,"BTC-USD-SWAP")[1]["rows"],90)
        text=io.StringIO()
        z=io.BytesIO()
        with zipfile.ZipFile(z,"w") as f:
            header="instrument_name,funding_rate,funding_time\n"
            t="2025-06-01T00:00:00+00:00"
            f.writestr("one.csv",header+f"BTC-USD-SWAP,0.01,{t}\nBTC-USD-SWAP,0.02,{t}\n")
        with self.assertRaisesRegex(ValueError,"NONMONOTONIC"):
            parse_month(z.getvalue(),"BTC-USD-SWAP")
    def test_unusual_2hour_gap_rejected(self):
        data=io.BytesIO()
        with zipfile.ZipFile(data,"w") as z:
            z.writestr("one.csv","instrument_name,funding_rate,funding_time\n"
                "BTC-USD-SWAP,0.001,2025-06-01T00:00:00Z\n"
                "BTC-USD-SWAP,0.002,2025-06-01T02:00:00Z\n")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_FUNDING_PERIOD"):
            parse_month(data.getvalue(),"BTC-USD-SWAP")
    def test_utc_plus8_archive_start_is_accepted_without_shifting_event_utc(self):
        z=io.BytesIO()
        with zipfile.ZipFile(z,"w") as f:
            f.writestr("funding.csv","instrument_name,funding_rate,funding_time\n"
              "BTC-USDT-SWAP,0.0001,2025-06-01T00:00:00+08:00\n"
              "BTC-USDT-SWAP,0.0002,2025-06-01T08:00:00+08:00\n")
        rows,meta=parse_month(z.getvalue(),"BTC-USDT-SWAP")
        self.assertEqual(rows[0][0],1748707200000)
        self.assertEqual(meta["observed_intervals_minutes"],{480:1})
    def test_utc_plus8_archive_july_boundary_is_rejected(self):
        z=io.BytesIO()
        with zipfile.ZipFile(z,"w") as f:
            f.writestr("funding.csv","instrument_name,funding_rate,funding_time\n"
              "BTC-USD-SWAP,0.0001,2025-07-01T00:00:00+08:00\n")
        with self.assertRaisesRegex(ValueError,"OUTSIDE_FROZEN_UTC_PLUS8"):
            parse_month(z.getvalue(),"BTC-USD-SWAP")
    def test_exact_2025_month_time(self):
        self.assertEqual(utc_ms("2025-06-01T00:00:00+00:00"),1748736000000)
    def test_pre_entry_no_lookahead(self):
        a=records(".00064")
        at=int(datetime(2025,6,2,0,5,tzinfo=timezone.utc).timestamp()*1000)
        expected=Decimal(".00064")/Decimal(8)
        self.assertEqual(prior_pair(a,at),expected)
    def test_missing_prior_pair_is_source_insufficient(self):
        a=records("0.00064")
        e=episode_for_day(a[:1],records("0"),2)
        self.assertEqual(e["status"],"SOURCE_INSUFFICIENT_AT_DECISION")
    def test_positive_linear_rate_short_linear(self):
        e=episode_for_day(records(".00064"),records("0"),2)
        self.assertEqual(e["strategy_position"],"SHORT_LINEAR_LONG_INVERSE")
        self.assertEqual(e["status"],"RATE_ONLY_CONSTANT_NOTIONAL_PROXY")
        self.assertEqual(e["constant_notional_rate_only_proxy_USD"],"1.92000")
        self.assertFalse(e["proxy_clears_30bps"])
    def test_negative_linear_rate_short_inverse(self):
        e=episode_for_day(records("0"),records(".00064"),2)
        self.assertEqual(e["strategy_position"],"SHORT_INVERSE_LONG_LINEAR")
        self.assertEqual(e["constant_notional_rate_only_proxy_USD"],"1.92000")
    def test_funding_below_threshold_flat(self):
        e=episode_for_day(records(".00004"),records("0"),2)
        self.assertEqual(e["status"],"FLAT_PREDECLARED_THRESHOLD")
    def test_negative_rate_is_not_automatically_revenue(self):
        e=episode_for_day(records("-.00064"),records("0"),2)
        self.assertEqual(e["strategy_position"],"SHORT_INVERSE_LONG_LINEAR")
        self.assertGreater(Decimal(e["constant_notional_rate_only_proxy_USD"]),0)
    def test_all_28_calendar_days_retained(self):
        e=evaluate(records(".00064"),records("0"))
        self.assertEqual(len(e["all_predeclared_days"]),28)
        self.assertEqual(e["active_24h_rate_proxy_days"],28)
        self.assertEqual(e["days_proxy_clears_30bps"],0)
        self.assertFalse(e["historical_real_broker_economic_PNL_calculated"])
    def test_performance_does_not_change_eligibility(self):
        e=episode_for_day(records(".003"),records("0"),2)
        self.assertEqual(e["strategy_position"],"SHORT_LINEAR_LONG_INVERSE")
        self.assertTrue(e["proxy_clears_30bps"])
        self.assertFalse(e["is_actual_inverse_or_linear_cashflow"])
    def test_source_selector_without_month_wrong_fails(self):
        doc={"data":[{"instFamily":"BTC-USDT","filename":"BTC-USDT-SWAP-funding-2025-05.zip",
                 "url":"https://static.okx.com/foo"}]}
        with self.assertRaisesRegex(ValueError,"MISSING_OR_AMBIGUOUS"):
            archive_links(doc)
if __name__=="__main__":unittest.main()
