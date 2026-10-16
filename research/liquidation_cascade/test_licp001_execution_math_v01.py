import unittest
from research.liquidation_cascade.licp001_execution_math_v01 import executable_returns

class ExecutionMathTests(unittest.TestCase):
    def test_sell_short_continuation(self):
        r=executable_returns(100,101,98,99,"SELL")
        self.assertAlmostEqual(r["taker_gross_bps"],100.0)
        self.assertAlmostEqual(r["mexc_taker_net_bps"],84.0)
        self.assertAlmostEqual(r["maker_ceiling_gross_bps"],(101-98)/101*10000)

    def test_buy_long_continuation(self):
        r=executable_returns(100,101,102,103,"BUY")
        self.assertAlmostEqual(r["taker_gross_bps"],(102-101)/101*10000)
        self.assertAlmostEqual(r["maker_ceiling_gross_bps"],300.0)

    def test_flat_price_pays_spread(self):
        r=executable_returns(100,101,100,101,"BUY")
        self.assertLess(r["taker_gross_bps"],0)
        r2=executable_returns(100,101,100,101,"SELL")
        self.assertLess(r2["taker_gross_bps"],0)

    def test_crossed_book_fails(self):
        with self.assertRaisesRegex(ValueError,"CROSSED"):
            executable_returns(101,100,99,100,"SELL")

if __name__=="__main__":unittest.main()
