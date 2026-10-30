import sys,pathlib,datetime as dt,unittest,copy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from event10m_spot_depth_divergence_v03 import decide
SHA="a"*64
def setup(spot=.35,perp=-.4):
    d=int(dt.datetime(2026,11,2,12,0,30,tzinfo=dt.timezone.utc).timestamp()*1000)
    pairs=[]
    for delta in (13000,8000,1500):
        t=d-delta
        pairs.append({"asset":"BTC_USDT","received_ms":t,
          "okx_spot":{"venue":"OKX_SPOT","sha256":SHA,"imbalance":spot,
            "spread_bps":.5,"received_ms":t-200,
            "server_ms":t-500},
          "mexc_futures":{"venue":"MEXC_PERPETUAL","sha256":SHA,
            "imbalance":perp,"spread_bps":.3,"received_ms":t-100}})
    prod={"symbol":"BTC_USDT","duration_min":10,"state":"ONLINE",
      "received_ms":d-900,"sha256":SHA,"up_pay_rate":.8,"down_pay_rate":.8}
    idx={"symbol":"BTC_USDT","index_price":66000.0,
       "received_ms":d-500,"server_ms":d-700,"sha256":SHA}
    return ["BTC_USDT",d,pairs,prod,idx]
class Guards(unittest.TestCase):
 def test_up(self):
    x=decide(*setup())
    self.assertEqual((x["side"],round(x["conditional_breakeven_probability"],6)),("UP",.555556))
 def test_down(self):self.assertEqual(decide(*setup(-.35,.4))["side"],"DOWN")
 def test_agree_abstain(self):self.assertEqual(decide(*setup(.35,.4))["side"],"ABSTAIN")
 def test_small_imbalance_abstain(self):self.assertEqual(decide(*setup(.24,-.9))["side"],"ABSTAIN")
 def test_future_market_outside_window(self):
    a=setup();a[1]-=40*86400000
    with self.assertRaises(ValueError):decide(*a)
 def test_lookahead_pair_rejected(self):
    a=setup();a[2][-1]["received_ms"]=a[1]+1
    with self.assertRaises(ValueError):decide(*a)
 def test_stale_payout_rejected(self):
    a=setup();a[3]["received_ms"]=a[1]-12000
    with self.assertRaises(ValueError):decide(*a)
 def test_wrong_index_source_rejected(self):
    a=setup();a[4]["symbol"]="ETH_USDT"
    with self.assertRaises(ValueError):decide(*a)
 def test_wrong_source_product_rejected(self):
    a=setup();a[3]["state"]="PAUSE"
    with self.assertRaises(ValueError):decide(*a)
 def test_wrong_venues_rejected(self):
    a=setup();a[2][0]["okx_spot"]["venue"]="MEXC_FUTURES"
    with self.assertRaises(ValueError):decide(*a)
if __name__=="__main__":unittest.main()
