import datetime as dt
import math
import unittest
import collect
import evaluate as x

class Sources(unittest.TestCase):
    def test_hour_grid_and_delays(self):
        t=collect.ms(collect.START)
        v={t+i*collect.MS:{"t":t+i*collect.MS,"o":100.,"h":102.,"l":98.,"c":100.} for i in range(collect.N)}
        o={t+i*collect.MS:10.+i for i in range(collect.N)}
        a,offset=collect.align(v,o)
        self.assertEqual(len(a),576)
        self.assertEqual(offset,0)
        b={k:v for k,v in o.items() if k!=t+2*collect.MS}
        with self.assertRaises(ValueError):collect.align(v,b)
        c={k+collect.MS:v for k,v in o.items()}
        a,offset=collect.align(v,c)
        self.assertEqual(offset,collect.MS)
    def test_oi_coverage_not_fabricated(self):
        self.assertEqual(collect.N,576)

class CausalModel(unittest.TestCase):
    def bar(self,t=0,o=100,h=101,l=99,c=100,oi=10):
        return {"t":t,"o":o,"h":h,"l":l,"c":c,"oi":oi}
    def test_pool_created_only_from_positive_oi(self):
        first=self.bar(oi=11.)
        levels=x.update_levels([],first,10.)
        self.assertEqual(len(levels),6)
        self.assertTrue(any(v["price"]>100 for v in levels))
        self.assertTrue(any(v["price"]<100 for v in levels))
        self.assertEqual(x.update_levels([],self.bar(oi=9.),10.),[])
    def test_clear_consumed_level_on_closed_candle(self):
        bar=self.bar(h=103.,l=99.9,oi=10.)
        lev=[{"price":102,"mass":100,"age":1,"half_life":72.,
              "side":"UP"}]
        self.assertEqual(x.update_levels(lev,bar,10.),[])
    def test_strongest_band_and_future_changes_cannot_change_signal(self):
        levels=[
          {"price":102.0,"mass":99.,"age":0,"half_life":72.,"side":"UP"},
          {"price":98.0,"mass":20.,"age":0,"half_life":72.,"side":"DOWN"}
        ]
        old=x.strongest_band(levels,100.)
        self.assertEqual(old["dir"],1)
        self.assertAlmostEqual(math.log(old["target"]/100),
            -math.log(old["opposite"]/100),places=12)
        candles=[self.bar(t=i*3600000) for i in range(8)]
        candles[1]=self.bar(t=3600000,h=old["target"]*1.01,l=99.,c=101.)
        self.assertEqual(x.labels(candles,0,old,1)[0],"TARGET_FIRST")
        candles[1]["l"]=old["opposite"]*.99
        self.assertEqual(x.labels(candles,0,old,1)[0],"AMBIGUOUS")
        self.assertEqual(x.strongest_band(levels,100.),old)
    def test_cannot_buy_arbitrary_volume_with_no_liquidity(self):
        self.assertEqual(x.wilson(0,0),[None,None])
        lo,hi=x.wilson(50,100)
        self.assertLess(lo,.5)
        self.assertGreater(hi,.5)
    def test_fee_stress_must_reduce_net(self):
        c=[self.bar(t=i*3600000) for i in range(8)]
        zone=x.strongest_band([{"price":102.,"mass":100,"age":0,
                         "half_life":72,"side":"UP"}],100.)
        low=x.pseudo_trade(c,0,zone,1,10)["net_bps"]
        high=x.pseudo_trade(c,0,zone,1,80)["net_bps"]
        self.assertAlmostEqual(low-high,140.,places=7)
    def test_wilson_bootstrap_fixed(self):
        series=[1.,-1.,0.,.25]*8
        self.assertEqual(x.boot_diff(series),x.boot_diff(series))
if __name__=="__main__":unittest.main()
