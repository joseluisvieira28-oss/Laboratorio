"""Frozen common-window tests. Only source/time configuration differs from V5."""
import unittest
from research.convex_8alt_common_2023_25 import common_3yr as m
from research.convex_multialt_4tf_20261013 import multialt_matrix as old

class WindowTests(unittest.TestCase):
    def test_2022_11_warmup_covers_4h_sma200(self):
        self.assertEqual(m.MONTHS[0],"2022-11")
        self.assertEqual(m.MONTHS[-1],"2025-12")
        self.assertEqual(len(m.MONTHS),38)
        self.assertEqual(len(m.FUNDING_MONTHS),36)
        self.assertEqual((m.ECON_MS-m.PRE_MS)//3600000,61*24)
        self.assertGreaterEqual((m.ECON_MS-m.PRE_MS)//3600000,200*4)

    def test_full_three_year_economic_interval(self):
        self.assertEqual(m.START_UTC,"2023-01-01T00:00:00Z")
        self.assertEqual(m.END_UTC,"2026-01-01T00:00:00Z")
        self.assertEqual((m.END_MS-m.ECON_MS)//86400000,1096)

    def test_original_trading_parameters_and_all_64_arms(self):
        self.assertTrue(m.apply_locked_3year_window())
        self.assertEqual(old.base.PCT_NOTIONAL,.20)
        self.assertEqual(old.base.STOP,.04)
        self.assertEqual(old.base.TRAIL,.12)
        self.assertEqual(old.base.ACTIVATE,.05)
        self.assertEqual(old.base.FEE,.0008)
        self.assertEqual(len(old.ASSETS)*len(old.TIMEFRAMES)*len(old.SCENARIOS),64)
        self.assertEqual((old.START_PRICE,old.START,old.END),(m.PRE_MS,m.ECON_MS,m.END_MS))
        self.assertEqual((old.base.PRE,old.base.START,old.base.END),(m.PRE_MS,m.ECON_MS,m.END_MS))

if __name__=="__main__":
    unittest.main()
