import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from october_replay import signal,estimate

def r(t,i,who,curve=4,sol=.40,side="buy",vs=30,vt=1000000000):
    return dict(t=1700000000+t,seq=(i+100,i,i),vs=vs,vt=vt,
       curve=curve,sol=sol,side=side,who=who)

class Tests(unittest.TestCase):
    def test_no_future_leakage(self):
        x=[r(t,i,str(i)) for i,t in enumerate([130,140,150,160,170])]
        i=signal(x,1700000000,True)
        self.assertIsNotNone(i)
        self.assertEqual(signal(x[:i+1],1700000000,True),i)

    def test_one_wallet_rejected(self):
        x=[r(t,i,"same") for i,t in enumerate([130,140,150,160,170])]
        self.assertIsNone(signal(x,1700000000,True))

    def test_exit_quote_not_profit_at_same_state(self):
        x=[r(t,i,str(i)) for i,t in enumerate([130,140,150,160,170])]
        sig=signal(x,1700000000,True)
        x.extend([r(210,50,"later"),r(510,51,"later2")])
        out=estimate(x,sig,None,.02)
        self.assertEqual(out["status"],"INDICATIVE_QUOTE_NOT_FILL")
        self.assertLess(out["net_pct"],0)

    def test_missing_exit(self):
        x=[r(t,i,str(i)) for i,t in enumerate([130,140,150,160,170])]
        sig=signal(x,1700000000,True)
        x.extend([r(210,50,"later")])
        self.assertEqual(estimate(x,sig,None,.02)["status"],"NO_OBSERVED_EXIT")

    def test_migration_censors(self):
        x=[r(t,i,str(i)) for i,t in enumerate([130,140,150,160,170])]
        sig=signal(x,1700000000,True)
        x.extend([r(210,50,"later"),r(510,51,"later2")])
        self.assertEqual(estimate(x,sig,1700000000+250,.02)["status"],"MIGRATED_BEFORE_EXIT")

if __name__=="__main__":unittest.main()
