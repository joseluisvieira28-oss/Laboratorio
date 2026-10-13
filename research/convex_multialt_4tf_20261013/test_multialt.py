"""Offline zero-market-outcome guards for the frozen multi-alt experiment."""
import unittest
from unittest.mock import patch
from research.convex_multialt_4tf_20261013 import multialt_matrix as m

class GuardTests(unittest.TestCase):
    def test_exactly_eight_preregistered_symbols_and_four_tf(self):
        self.assertEqual(m.ASSETS,("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
                                  "DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT"))
        self.assertEqual([x for x,_ in m.TIMEFRAMES],["15m","30m","1h","4h"])
        self.assertEqual(m.SCENARIOS,(("BASE",2),("STRESS",5)))
        self.assertEqual(m.MONTHS[0],"2020-11")
        self.assertEqual(m.MONTHS[-1],"2025-12")
        self.assertEqual(len(m.FUNDING_MONTHS),60)
        self.assertEqual(len(m.ASSETS)*len(m.TIMEFRAMES)*len(m.SCENARIOS),64)

    def test_reject_unfrozen_symbol_and_venue(self):
        with self.assertRaisesRegex(ValueError,"SYMBOL_NOT_FROZEN"):
            m.archive_path("BTCUSDT","5m","2024-01")
        with self.assertRaisesRegex(ValueError,"KIND_NOT_FROZEN"):
            m.archive_path("ETHUSDT","trades","2024-01")
        with self.assertRaisesRegex(ValueError,"MONTH_NOT_FROZEN"):
            m.archive_path("ETHUSDT","5m","2026-01")
        self.assertEqual(m.archive_path("SOLUSDT","5m","2021-02"),
                         "klines/SOLUSDT/5m/SOLUSDT-5m-2021-02.zip")
        self.assertEqual(m.archive_path("BNBUSDT","fundingRate","2021-04"),
                         "fundingRate/BNBUSDT/BNBUSDT-fundingRate-2021-04.zip")

    def test_no_synthetic_funding_month_substitution(self):
        with patch.object(m,"START_PRICE",0),patch.object(m,"START",0),\
             patch.object(m,"END",m.base.HOUR*2),\
             patch.object(m,"FUNDING_MONTHS",("2021-01",)):
            five={i*m.base.M5:{} for i in range(24)}
            one={i*m.base.HOUR:{} for i in range(2)}
            with self.assertRaisesRegex(ValueError,"FUNDING_MONTHS_MISSING"):
                m.validate_coverage(five,one,{}, {})
            with self.assertRaisesRegex(ValueError,"FUNDING_MONTH_WITH_NO_RECORDS"):
                m.validate_coverage(five,one,{}, {"2021-01":0})

    def test_contiguity_blocks_source_gap(self):
        with patch.object(m,"START_PRICE",0),patch.object(m,"START",0),\
             patch.object(m,"END",m.base.HOUR*2),\
             patch.object(m,"FUNDING_MONTHS",("2021-01",)):
            five={i*m.base.M5:{} for i in range(24)}
            one={i*m.base.HOUR:{} for i in range(2)}
            del five[5*m.base.M5]
            with self.assertRaisesRegex(ValueError,"PRICE_COVERAGE_INCOMPLETE"):
                m.validate_coverage(five,one,{m.base.HOUR:0.001},{"2021-01":1})

    def test_original_model_retained_no_parameter_replacement(self):
        self.assertEqual(m.base.STOP,.04)
        self.assertEqual(m.base.TRAIL,.12)
        self.assertEqual(m.base.ACTIVATE,.05)
        self.assertEqual(m.base.PCT_NOTIONAL,.20)
        self.assertEqual(m.base.FEE,.0008)
        self.assertEqual(m.base.TFS,m.TIMEFRAMES)

if __name__=="__main__":
    unittest.main()
