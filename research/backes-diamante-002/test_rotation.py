import unittest
from rotation_backtest import signals,simulate,bootstrap,drawdown

class Backes002Tests(unittest.TestCase):
    def test_no_lookahead(self):
        lo=[10,9,8,4,8,9,10,8,7,6,5,9,10,11]
        xs=[{'low':v,'close':v+1} for v in lo]
        old=signals(xs)
        new=signals(xs+[{'low':0.1,'close':500}] * 10)
        self.assertEqual(old,new[:len(old)])
    def test_returns(self):
        btc=[{'date':'2025-01-06','open':100.,'close':120.},{'date':'2025-01-13','open':120.,'close':120.}]
        eth=[{'date':'2025-01-06','open':10.,'close':9.},{'date':'2025-01-13','open':9.,'close':9.}]
        res,count,weekly=simulate(btc,eth,['BTC','BTC'],2025,2025,0)
        self.assertEqual(count,0)
        self.assertAlmostEqual(res['BTC']['total_return_pct'],20.)
        self.assertAlmostEqual(res['ETH']['total_return_pct'],-10.)
        self.assertAlmostEqual(res['ROT']['total_return_pct'],20.)
        costed,_,_=simulate(btc,eth,['BTC','BTC'],2025,2025,100)
        self.assertLess(costed['BTC']['total_return_pct'],res['BTC']['total_return_pct'])
    def test_bootstrap_seed(self):
        a=[.02,-.01,.03,.005]*10
        b=[.01,-.02,.01,0.]*10
        self.assertEqual(bootstrap(a,b),bootstrap(a,b))
    def test_drawdown(self):
        self.assertAlmostEqual(drawdown([1.,2.,1.]),-.5)

if __name__=='__main__':unittest.main()
