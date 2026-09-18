import unittest
from datetime import date
from math import exp

from radar.options_v21_live import (
    DAY_MS,
    FREEZE_MS,
    DailyBar,
    DeribitBTCOptionTradeFeed,
    OptionTrade,
    OptionsV21SourceError,
    build_daily_skew,
    rv20_and_weight,
    source_schema_probe,
)


class SplitFeed(DeribitBTCOptionTradeFeed):
    def _one_window(self, start_ms, end_ms):
        if end_ms - start_ms > 10:
            return [], True
        mid=(start_ms+end_ms)//2
        rows=[
            OptionTrade(f"id-{start_ms}", start_ms, "BTC-30OCT26-100000-C", 50.0, 90000.0),
            OptionTrade(f"id-{end_ms}", end_ms, "BTC-30OCT26-100000-C", 51.0, 90000.0),
        ]
        return rows, False


class StubProbeFeed(DeribitBTCOptionTradeFeed):
    def trades(self, *, start_ms, end_ms):
        return [
            OptionTrade("a", start_ms, "BTC-30OCT26-100000-C", 50.0, 90000.0)
        ]


class OptionsV21LiveTests(unittest.TestCase):
    def test_exact_daily_skew_uses_median_per_instrument_then_side(self):
        day=date(2026,9,19)
        ts=1789776000000
        rows=[]
        # 5 call instruments in frozen 1.05..1.20 moneyness range.
        for i,iv in enumerate([50,52,54,56,58]):
            strike=95000+i*1000
            name=f"BTC-30OCT26-{strike}-C"
            rows.append(OptionTrade(f"c{i}a",ts+i,name,float(iv-1),90000.0))
            rows.append(OptionTrade(f"c{i}b",ts+i+100,name,float(iv+1),90000.0))
        # 5 puts in 0.80..0.95 range.
        for i,iv in enumerate([40,42,44,46,48]):
            strike=75000+i*1500
            name=f"BTC-30OCT26-{strike}-P"
            rows.append(OptionTrade(f"p{i}a",ts+1000+i,name,float(iv),90000.0))
        out=build_daily_skew(day,rows)
        self.assertTrue(out["valid"])
        self.assertEqual(out["distinct_eligible_calls"],5)
        self.assertEqual(out["distinct_eligible_puts"],5)
        self.assertAlmostEqual(out["skew"],10.0)
        self.assertEqual(out["position"],1)

    def test_less_than_five_each_side_is_invalid_flat(self):
        day=date(2026,9,19); ts=1789776000000
        rows=[]
        for i in range(4):
            rows.append(OptionTrade(f"c{i}",ts+i,f"BTC-30OCT26-{95000+i*1000}-C",50,90000))
            rows.append(OptionTrade(f"p{i}",ts+100+i,f"BTC-30OCT26-{75000+i*1000}-P",40,90000))
        out=build_daily_skew(day,rows)
        self.assertFalse(out["valid"])
        self.assertIsNone(out["skew"])
        self.assertEqual(out["position"],0)

    def test_saturated_time_window_splits_instead_of_truncating(self):
        rows=SplitFeed().trades(start_ms=100,end_ms=140)
        self.assertGreater(len(rows),2)
        ids=[x.trade_id for x in rows]
        self.assertEqual(len(ids),len(set(ids)))

    def test_pre_freeze_probe_is_forbidden(self):
        with self.assertRaises(OptionsV21SourceError):
            source_schema_probe(StubProbeFeed(),start_ms=FREEZE_MS-1,end_ms=FREEZE_MS+100)

    def test_post_freeze_probe_is_never_forward_evidence(self):
        out=source_schema_probe(StubProbeFeed(),start_ms=FREEZE_MS,end_ms=FREEZE_MS+100)
        self.assertEqual(out["status"],"PASS_SOURCE_SCHEMA")
        self.assertFalse(out["used_as_forward_evidence"])
        self.assertFalse(out["authenticated_api_used"])

    def test_rv20_weight_uses_full_expanding_history(self):
        start=1617235200000  # 2021-04-01 UTC
        bars=[]
        price=100.0
        # Vary deterministic daily returns so RV is finite and nonzero.
        for i in range(120):
            r=0.002 + ((i%7)-3)*0.0003
            op=price
            price=price*exp(r)
            bars.append(DailyBar(start+i*DAY_MS,op,price))
        signal_day=date(2021,7,29)  # final bar
        out=rv20_and_weight(bars,signal_day=signal_day)
        self.assertGreaterEqual(out["valid_rv20_history_count"],60)
        self.assertGreater(out["rv20"],0)
        self.assertGreater(out["expanding_median_rv20"],0)
        self.assertGreater(out["weight"],0)
        self.assertLessEqual(out["weight"],1)


if __name__ == "__main__":
    unittest.main()
