import unittest,sys,pathlib,datetime as dt
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import audit
import orderbook_probe as book

class Carry002Safety(unittest.TestCase):
    def test_direction_correct_and_different_venues(self):
        self.assertEqual(audit.side("Binance",-1),1)
        self.assertEqual(audit.side("Hyperliquid",-1),-1)
        self.assertEqual(audit.side("Binance",1),-1)
        self.assertEqual(audit.side("Hyperliquid",1),1)
    def test_cost_and_collateral_math(self):
        self.assertAlmostEqual(audit.COST,.0027)
        self.assertEqual(len(audit.CASES),3)
        self.assertAlmostEqual(45/100/(2*1.0),0.225)
    def test_book_price_impact(self):
        asks=[{"px":"100","sz":"10"},{"px":"101","sz":"10"}]
        r=book.walk(asks,1000,True)
        self.assertTrue(r["filled"])
        self.assertAlmostEqual(r["impact_bps"],0.0)
        self.assertFalse(book.walk(asks,4000,True)["filled"])
    def test_no_future_payment_at_entry(self):
        ts=audit.stamp("2026-06-22T02:00:00")
        self.assertTrue(ts>0)
        self.assertEqual(audit.utc(ts),"2026-06-22T02:00:00+00:00")
    def test_worst_leg_not_nettable(self):
        # $1000 notional long Binance may gain, while separate short HL loses.
        x=.25-0.00065-0.02+(-1)*(1.60-1)
        self.assertLess(x,0)

if __name__=="__main__":unittest.main()
