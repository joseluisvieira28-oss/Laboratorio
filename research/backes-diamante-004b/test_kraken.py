import datetime as dt
import unittest
import kraken_recovery as r
class ReadOnlyKrakenTests(unittest.TestCase):
    def make(self):
        w=[];e=[]
        for i,(b,x) in enumerate(((100.,10.),(110.,12.),(121.,12.))):
            date=str(dt.date(2025,1,6)+dt.timedelta(weeks=i))
            w.append({"date":date,"open":b,"close":b,"high":b,"low":b})
            e.append({"date":date,"open":x,"close":x,"high":x,"low":x})
        return {"BTC":w,"ETH":e}
    def test_fee_drag(self):
        d=self.make();states=["BTC"]*464
        a=r.evaluate_weekly(d,states,10)
        b=r.evaluate_weekly(d,states,80)
        self.assertGreater(a["ROT"]["total_return_pct"],b["ROT"]["total_return_pct"])
    def test_no_lookahead_and_switch(self):
        d=self.make();states=["BTC"]*464
        # At week 2025-01-13 (i=1), decide using previous closed week at 2025-01-06.
        start_index=(dt.date(2025,1,6)-r.b.START).days//7
        states[start_index]="ETH"
        a=r.evaluate_weekly(d,states,10)
        self.assertEqual(a["switches"],2)
        self.assertNotEqual(a["ROT"]["total_return_pct"],a["BTC"]["total_return_pct"])
if __name__=="__main__":unittest.main()
