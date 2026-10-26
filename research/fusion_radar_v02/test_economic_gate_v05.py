"""Synthetic regression checks for economic_gate_v05.py (requires operator CSV)."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from economic_gate_v05 import (
    load_rows, scenario, GateError, EXPECTED_CSV_SHA256, TOTAL_COST_GRID_BPS
)

DATA = Path("results/AVAX_BTC_DAILY_2022_2023.csv")


class EconomicGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows(DATA)

    def test_source_hash(self):
        self.assertEqual(hashlib.sha256(DATA.read_bytes()).hexdigest(), EXPECTED_CSV_SHA256)

    def test_730_days(self):
        self.assertEqual(len(self.rows), 730)
        self.assertEqual(self.rows[0]['day'].isoformat(), '2022-01-01')
        self.assertEqual(self.rows[-1]['day'].isoformat(), '2023-12-31')

    def test_masks(self):
        self.assertEqual(sum(r['masks']['baseline_trade'] for r in self.rows), 730)
        self.assertEqual(sum(r['masks']['fusion_trade'] for r in self.rows), 568)
        self.assertEqual(sum(r['masks']['opposite_context_trade'] for r in self.rows), 162)

    def test_base14_reconciles(self):
        got = scenario(self.rows, 14)['all']
        self.assertAlmostEqual(got['fusion_net_sum_bps_daily_unit_notional'], 1051.384634, places=5)
        self.assertAlmostEqual(got['baseline_net_sum_bps_daily_unit_notional'], -2270.573221, places=5)

    def test_stress20_reconciles(self):
        got = scenario(self.rows, 20)['all']
        self.assertAlmostEqual(got['fusion_net_sum_bps_daily_unit_notional'], -2356.615366, places=5)

    def test_break_even_whole(self):
        self.assertAlmostEqual(scenario(self.rows, 8)['all']['break_even_total_friction_bps'], 15.851029, places=5)

    def test_break_even_2023(self):
        self.assertAlmostEqual(scenario(self.rows, 8)['2023']['break_even_total_friction_bps'], 8.466395, places=5)

    def test_2023_eightbps_barely_positive(self):
        value = scenario(self.rows, 8)['2023']['fusion_net_mean_bps_per_trade']
        self.assertTrue(0 < value < 0.5)

    def test_2023_tenbps_negative(self):
        self.assertLess(scenario(self.rows, 10)['2023']['fusion_net_sum_bps_daily_unit_notional'], 0)

    def test_costs_apply_once(self):
        eight = scenario(self.rows, 8)['all']['fusion_net_sum_bps_daily_unit_notional']
        fourteen = scenario(self.rows, 14)['all']['fusion_net_sum_bps_daily_unit_notional']
        self.assertAlmostEqual(eight - fourteen, 568 * 6, places=5)

    def test_cost_grid_fixed(self):
        self.assertEqual(TOTAL_COST_GRID_BPS, (0, 4, 8, 10, 12, 14, 16, 20, 24))

    def test_mutated_source_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'modified.csv'
            target.write_bytes(DATA.read_bytes().replace(b'2022-01-01', b'2024-01-01', 1))
            with self.assertRaises(GateError):
                load_rows(target)

    def test_negative_cost_rejected(self):
        with self.assertRaises(GateError):
            scenario(self.rows, -1)

    def test_nan_cost_rejected(self):
        with self.assertRaises(GateError):
            scenario(self.rows, float('nan'))


if __name__ == '__main__':
    unittest.main()
