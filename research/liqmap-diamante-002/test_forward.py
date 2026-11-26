import datetime as dt
import math
import unittest

import point
import settle
import rollup

UTC=dt.timezone.utc
H=3600000

class ProtocolTests(unittest.TestCase):
    def test_no_past_or_future_backfill(self):
        valid=dt.datetime(2026,11,27,7,0,tzinfo=UTC)
        self.assertEqual(point.validate_time("future","2026-11-27",valid),"FUTURE_PENDING_OUTCOME")
        for when,date in [
             (dt.datetime(2026,11,26,8,tzinfo=UTC),"2026-11-27"),
             (dt.datetime(2026,11,27,15,tzinfo=UTC),"2026-11-27"),
             (dt.datetime(2026,12,1,8,tzinfo=UTC),"2026-11-27"),
             (dt.datetime(2027,1,27,8,tzinfo=UTC),"2027-01-27")]:
            with self.assertRaises(ValueError):point.validate_time("future",date,when)
    def test_symmetric_liquidation_price(self):
        snap={"coin":"BTC","markPx":60000,"coverage":{"share":.48},
              "ageMin":{"ntlP50":3.1},
              "longs":[{"px":58500-i*50,"ntlUsd":100000,"n":1} for i in range(35)],
              "shorts":[{"px":61500+i*50,"ntlUsd":10000,"n":1} for i in range(35)]}
        z=point.band_from_map(snap)
        self.assertEqual(z["signal"],"DOWN")
        self.assertAlmostEqual(math.log(z["target"]/z["mark"]),
                               -math.log(z["mirror"]/z["mark"]),places=10)
        snap["coverage"]["share"]=.1
        with self.assertRaises(ValueError):point.band_from_map(snap)
    def test_public_candles_must_be_complete_and_closed(self):
        t=1795672800000//H*H
        bars=[{"t":t+i*H,"T":t+(i+1)*H-1,"o":100,"h":110,"l":90,"c":105} for i in range(24)]
        self.assertEqual(len(point.clean_candles(bars,t,24,now_ms=t+24*H)),24)
        with self.assertRaises(ValueError):point.clean_candles(bars[:-1],t,24,now_ms=t+24*H)
        with self.assertRaises(ValueError):point.clean_candles(bars,t,24,now_ms=t+20*H)
    def test_first_touch_ambiguous_not_a_profit(self):
        mark=100;target=102;mirror=10000/102
        bar=lambda hi,lo:{"t":0,"o":100,"h":hi,"l":lo,"c":100}
        both=settle.touch([bar(103,97)],mark,target,mirror)
        self.assertEqual(both["kind"],"AMBIGUOUS")
        self.assertEqual(settle.classify(both,"UP"),"AMBIGUOUS")
        x=settle.pnl([bar(103,97)],both,"UP",mark,target,mirror,80)
        self.assertLess(x["net_bps"],0)
        up=settle.touch([bar(103,99),bar(101,97)],mark,target,mirror)
        self.assertEqual(settle.classify(up,"UP"),"TARGET_FIRST")
        self.assertEqual(settle.classify(up,"DOWN"),"MIRROR_FIRST")
    def test_fee_drag(self):
        mark=100;target=102;mirror=10000/102
        bars=[{"t":0,"o":100,"h":103,"l":99,"c":102}]
        first=settle.touch(bars,mark,target,mirror)
        low=settle.pnl(bars,first,"UP",mark,target,mirror,35)["net_bps"]
        high=settle.pnl(bars,first,"UP",mark,target,mirror,80)["net_bps"]
        self.assertAlmostEqual(low-high,90,places=5)
    def test_wilson_and_bootstrap(self):
        ci=rollup.wilson(5,10)
        self.assertLess(ci["low"],.5);self.assertGreater(ci["high"],.5)
        points=[(f"2026-12-{i+1:02d}",(-1)**i*10) for i in range(20)]
        self.assertEqual(rollup.bootstrap_by_week(points),rollup.bootstrap_by_week(points))
    def test_rolling_status_cannot_go_live(self):
        out=rollup.evaluate(dt.date(2026,11,26))
        self.assertEqual(out["live_trading_verdict"],"NO_GO")
        self.assertEqual(out["scientific_status"],"FORWARD_PENDING_OR_CENSORED")
if __name__=="__main__":unittest.main()
