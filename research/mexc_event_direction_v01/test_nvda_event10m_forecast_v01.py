import datetime as dt,sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from nvda_event10m_forecast_v01 import forecast,slot
H="a"*64
def example():
    decision=int(dt.datetime(2026,11,2,14,35,10,tzinfo=dt.timezone.utc).timestamp()*1000)
    boundary=decision//60000*60000
    def pkt(sym,old,new):
        return {"symbol":sym,"sha256":H,"received_ms":decision-1000,
          "bars":[{"start_ms":boundary-4*60000,"close":old,
                   "received_ms":boundary-3*60000+4000},
                  {"start_ms":boundary-60000,"close":new,
                   "received_ms":boundary+3000}]}
    cash=pkt("NVDA",100,100.15)
    idx=pkt("NVIDIA_USDT",100,100.05)
    product={"symbol":"NVIDIA_USDT","state":"ONLINE","horizon_min":10,
      "received_ms":decision-500,"sha256":H,"up_pay_rate":0.8,"down_pay_rate":0.8}
    tick={"symbol":"NVIDIA_USDT","received_ms":decision-200,
      "index_price":100,"sha256":H}
    return decision,cash,idx,product,tick
class TestShadow(unittest.TestCase):
    def test_up(self):
        self.assertEqual(forecast(*example())["candidate"],"UP")
    def test_down(self):
        d,c,i,p,t=example()
        c["bars"][1]["close"]=99.85;i["bars"][1]["close"]=99.95
        self.assertEqual(forecast(d,c,i,p,t)["candidate"],"DOWN")
    def test_abstain(self):
        d,c,i,p,t=example()
        c["bars"][1]["close"]=100.005
        self.assertEqual(forecast(d,c,i,p,t)["candidate"],"ABSTAIN")
    def test_future_bar_rejected(self):
        d,c,i,p,t=example()
        c["bars"][1]["received_ms"]=d+1
        with self.assertRaises(ValueError):forecast(d,c,i,p,t)
    def test_stale_payout_rejected(self):
        d,c,i,p,t=example();p["received_ms"]=d-11000
        with self.assertRaises(ValueError):forecast(d,c,i,p,t)
    def test_stale_ref_rejected(self):
        d,c,i,p,t=example();c["received_ms"]=d-91000
        with self.assertRaises(ValueError):forecast(d,c,i,p,t)
    def test_no_quote_rejected(self):
        d,c,i,p,t=example();t["received_ms"]=d-4000
        with self.assertRaises(ValueError):forecast(d,c,i,p,t)
    def test_wrong_time_rejected(self):
        d,c,i,p,t=example()
        with self.assertRaises(ValueError):forecast(d+60000,c,i,p,t)
    def test_holiday_rejected(self):
        d=int(dt.datetime(2026,11,26,14,35,10,tzinfo=dt.timezone.utc).timestamp()*1000)
        with self.assertRaises(ValueError):slot(d)
if __name__=="__main__":unittest.main()
