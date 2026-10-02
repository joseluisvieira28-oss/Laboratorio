from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parents[1]
SRC = HERE / "scripts" / "options_multiasset_source_gate_v01.py"

spec = importlib.util.spec_from_file_location("multiasset_source_gate", SRC)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class MultiAssetSourceGateTests(unittest.TestCase):
    def test_linear_option_names_parse(self):
        for asset, name in (
            ("SOL", "SOL_USDC-29MAR24-150-C"),
            ("XRP", "XRP_USDC-29MAR24-0.55-P"),
        ):
            expiry, strike, side = mod.parse_instrument(asset, name)
            self.assertEqual(expiry.tzinfo, dt.timezone.utc)
            self.assertGreater(strike, 0)
            self.assertIn(side, {"C", "P"})

    def test_eth_inverse_name_parses(self):
        expiry, strike, side = mod.parse_instrument("ETH", "ETH-29MAR24-3500-C")
        self.assertEqual(expiry.date().isoformat(), "2024-03-29")
        self.assertEqual(strike, 3500)
        self.assertEqual(side, "C")

    def test_2025_request_is_blocked(self):
        with self.assertRaises(RuntimeError):
            mod.build_url(
                "ETH",
                int(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000),
                int(dt.datetime(2025, 1, 2, tzinfo=dt.timezone.utc).timestamp() * 1000) - 1,
            )

    def test_only_three_new_assets_are_supported(self):
        self.assertEqual(set(mod.WINDOWS), {"ETH", "SOL", "XRP"})


if __name__ == "__main__":
    unittest.main()
