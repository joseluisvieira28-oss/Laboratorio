import unittest
from radar.mexc_spot import floor_market_quantity, market_quantity_rules, MEXCSpotPublicError

class SpotQuantityTests(unittest.TestCase):
    def _info(self):
        return {
            "baseAssetPrecision":8,
            "filters":[
                {"filterType":"LOT_SIZE","minQty":"0.00001000","maxQty":"1000","stepSize":"0.00001000"}
            ]
        }
    def test_quantity_floors_down_never_up(self):
        out=floor_market_quantity(0.00010999,self._info())
        self.assertAlmostEqual(out,0.00010)
        self.assertLessEqual(out,0.00010999)
    def test_below_minimum_fails_closed(self):
        with self.assertRaises(MEXCSpotPublicError):
            floor_market_quantity(0.00000999,self._info())
    def test_market_lot_size_takes_precedence(self):
        info=self._info()
        info["filters"].insert(0,{"filterType":"MARKET_LOT_SIZE","minQty":"0.00002000","maxQty":"100","stepSize":"0.00002000"})
        rules=market_quantity_rules(info)
        self.assertEqual(rules["source_filter"],"MARKET_LOT_SIZE")
        self.assertAlmostEqual(floor_market_quantity(0.000059,info),0.00004)

if __name__=="__main__": unittest.main()
