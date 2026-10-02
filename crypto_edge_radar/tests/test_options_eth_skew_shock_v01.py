from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "eth_skew_shock" / "options_eth_skew_shock_source_shard_v01.py"

spec = importlib.util.spec_from_file_location("eth_skew_shock_source", SRC)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class EthSkewShockSourceTests(unittest.TestCase):
    def test_eth_instrument_parses(self):
        expiry, strike, side = mod.parse_instrument("ETH-29MAR24-3500-C")
        self.assertEqual(expiry.isoformat(), "2024-03-29")
        self.assertEqual(strike, 3500.0)
        self.assertEqual(side, "C")

    def test_non_eth_instrument_rejected(self):
        with self.assertRaises(ValueError):
            mod.parse_instrument("BTC-29MAR24-70000-C")

    def test_2024_is_blocked_for_new_candidate_source_runner(self):
        with self.assertRaises(RuntimeError):
            mod.month_bounds("2024-06")

    def test_2026_is_blocked(self):
        with self.assertRaises(RuntimeError):
            mod.month_bounds("2026-01")

    def test_stage_a_and_oos_years_are_allowed(self):
        for month in ("2021-01", "2022-07", "2023-12", "2025-06"):
            a, b = mod.month_bounds(month)
            self.assertLess(a, b)
            self.assertIn(a.year, {2021, 2022, 2023, 2025})


class FrozenShockSemanticsTests(unittest.TestCase):
    def test_calendar_day_delta_direction(self):
        prev = 1.25
        cur = 1.40
        shock = cur - prev
        position = 1 if shock > 0 else (-1 if shock < 0 else 0)
        self.assertEqual(position, 1)

        prev = 1.40
        cur = 1.25
        shock = cur - prev
        position = 1 if shock > 0 else (-1 if shock < 0 else 0)
        self.assertEqual(position, -1)


if __name__ == "__main__":
    unittest.main()
