import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from quote_audit import quote_buy,quote_sell,choose,settle

def point(t,index,buyer=True,wallet="w",real=6.):
    return dict(ts=1700000000+t,order=(1000+index,index,index),
        vs=30.,vt=1000000000.,rs=real,rt=700000000.,
        flow=.35,who=wallet,buy=buyer)

class TestProxy(unittest.TestCase):
    def test_roundtrip_same_reserves_is_negative(self):
        a=point(0,0)
        q=quote_buy(a,.05,.017)
        self.assertIsNotNone(q)
        self.assertLess(quote_sell(a,q,.017),.05)

    def test_cannot_sell_more_than_real_sol(self):
        a=point(0,0,real=.001)
        self.assertIsNone(quote_sell(a,1e9,.017))

    def test_wallet_filter_requires_diversity(self):
        p=[point(i*30,i,wallet="wallet"+str(i)) for i in range(8)]
        self.assertIsNotNone(choose(p,True))
        for x in p:x["who"]="same"
        self.assertIsNone(choose(p,True))

    def test_no_exit_is_censored(self):
        p=[point(i*30,i,wallet=str(i)) for i in range(8)]
        idx=choose(p,True)
        self.assertIsNotNone(idx)
        result=settle(p,idx)
        self.assertEqual(result["status"],"NO_OBSERVED_EXIT")

    def test_bounded_horizon_curve_quote(self):
        p=[point(i*30,i,wallet=str(i)) for i in range(8)]
        sig=choose(p,True)
        p.extend([point(300,30),point(450,31)])
        ret=settle(p,sig)
        self.assertEqual(ret["status"],"HYPOTHETICAL_CURVE_QUOTE")
        self.assertLess(ret["net_pct"],0)

    def test_exit_price_floor(self):
        a=point(0,0)
        a["vt"]=1.
        a["rt"]=0.001
        self.assertIsNone(quote_buy(a,.05,.017))

if __name__=="__main__": unittest.main()
