"""Synthetic f1c daily source 1440 gap proof, no historical economics."""
import unittest
from research.convex_sol_bnb_gates_v01 import repaired_mark_1m_proxy_replay as r

class DailyRepairSourceContracts(unittest.TestCase):
    def test_whole_day_exactly_one_source_and_three_settlements(self):
        original={r.DAY_START-60000:100}
        mark={t:123. for t in range(r.DAY_START,r.END,60000)}
        def monthly(symbol,month):
            return original,{"month":month}
        def daily(symbol,date):
            return mark,{"publisher_sha256":r.EXPECTED_DAILY_PUBLISHER_SHA[symbol],
                         "rows":1440,"url":"SYNTHETIC"}
        merged,rec=r.recovered_source("SOLUSDT","2023-02",monthly,daily)
        self.assertEqual(len(merged),1441)
        self.assertEqual(rec["supplement"]["full_daily_bars"],1440)
        self.assertEqual(rec["supplement"]["recovered_three_funding_times"],list(r.MISSING_SETTLEMENT_MINUTES))

    def test_never_merge_overlapping_or_partial_day(self):
        mark={t:123. for t in range(r.DAY_START,r.END,60000)}
        def d(symbol,date):return mark,{"publisher_sha256":r.EXPECTED_DAILY_PUBLISHER_SHA[symbol]}
        def overlap(symbol,month):return {r.DAY_START:44.},{"month":month}
        with self.assertRaisesRegex(ValueError,"OVERLAP"):
            r.recovered_source("BNBUSDT","2023-02",overlap,d)
        def partial(symbol,date):
            m=dict(mark);m.pop(r.DAY_START+60000)
            return m,{"publisher_sha256":r.EXPECTED_DAILY_PUBLISHER_SHA[symbol]}
        with self.assertRaisesRegex(ValueError,"1440_BAR_COVERAGE"):
            r.recovered_source("BNBUSDT","2023-02",lambda a,b:({},{}),partial)

    def test_wrong_sha_or_month_never_rescues(self):
        bad=lambda symbol,date: ({}, {"publisher_sha256":"fake"})
        with self.assertRaisesRegex(ValueError,"SHA_DIFFERS"):
            r.recovered_source("BNBUSDT","2023-02",lambda a,b:({},{}),bad)
        called=[]
        def monthly(symbol,month):called.append(month);return {1:2.},{"month":month}
        data,_=r.recovered_source("BNBUSDT","2024-01",monthly,bad)
        self.assertEqual(data,{1:2.})
        self.assertEqual(called,["2024-01"])

if __name__=="__main__":unittest.main()
