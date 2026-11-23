import unittest
import attribution as x

class TestBackes003(unittest.TestCase):
    def test_log_attribution_reproduces_002(self):
        b=[dict(date=d,open=a,close=c) for d,a,c in [("2025-01-06",100,110),("2025-01-13",110,100),("2025-01-20",100,95)]]
        e=[dict(date=d,open=a,close=c) for d,a,c in [("2025-01-06",10,11),("2025-01-13",11,14),("2025-01-20",14,14)]]
        rows,ref,n=x.attribution(b,e,["ETH","BTC","BTC"],2025,2025,10)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]["held"],"BTC")
        self.assertEqual(rows[1]["held"],"ETH")
        self.assertEqual(n,2)
        self.assertAlmostEqual(sum(t["excess_log_pct"] for t in rows),
            100*__import__("math").log(rows[-1]["rot_nav"]/rows[-1]["btc_nav"]))
    def test_episodes(self):
        rows=[dict(held=h,start=str(i),end=str(i),excess_log_pct=k)
          for i,(h,k) in enumerate([("BTC",0),("BTC",0),("ETH",2),("ETH",-1),("BTC",0)])]
        ep=x.episodes(rows)
        self.assertEqual([p["weeks"] for p in ep],[2,2,1])
        self.assertAlmostEqual(ep[1]["excess_log_pct"],1.)
    def test_future_change_does_not_revise_past(self):
        xs=[dict(low=float(v),close=float(v)+1) for v in [10,9,8,3,7,8,11,6,5,4,9,11,13]]
        old=x.base.signals(xs)
        self.assertEqual(old,x.base.signals(xs+[dict(low=0.1,close=1000) for _ in range(10)])[:len(old)])
if __name__=="__main__":unittest.main()
