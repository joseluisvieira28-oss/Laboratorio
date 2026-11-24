import unittest
import depth

class BookDepthTests(unittest.TestCase):
    def test_depth_buy_slippage_increases_over_size(self):
        bids,asks,mid=depth.validate_book({"bids":[["99","100"],["98","100"]],
           "asks":[["101","1"],["102","100"]]})
        small=depth.vwap_quote_size(asks,bids,mid,50)
        bigger=depth.vwap_quote_size(asks,bids,mid,500)
        self.assertEqual(small["buy"]["status"],"MODEL_ONLY")
        self.assertGreater(bigger["buy"]["impact_vs_mid_bps"],
                           small["buy"]["impact_vs_mid_bps"])
        self.assertLessEqual(small["buy"]["slippage_over_best_ask_bps"],1e-8)
    def test_insufficient_depth_never_fabricates_fill(self):
        bids,asks,mid=depth.validate_book({"bids":[["99","0.1"]],
           "asks":[["101","0.1"]]})
        z=depth.vwap_quote_size(asks,bids,mid,10000)
        self.assertEqual(z["buy"]["status"],"DEPTH_INSUFFICIENT")
        self.assertEqual(z["sell"]["status"],"DEPTH_INSUFFICIENT")
    def test_cannot_trust_crossed_book(self):
        with self.assertRaises(ValueError):
            depth.validate_book({"bids":[["200","1"]],"asks":[["100","1"]]})
        with self.assertRaises(ValueError):
            depth.validate_book({"bids":[],"asks":[["100","1"]]})
if __name__=="__main__":unittest.main()
