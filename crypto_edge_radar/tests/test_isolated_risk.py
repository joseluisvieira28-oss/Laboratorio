import unittest

from radar.risk import isolated_margin_validation_size


class IsolatedMarginValidationSizingTests(unittest.TestCase):
    def test_floors_contracts_without_exceeding_budget(self):
        result = isolated_margin_validation_size(
            account_equity=10_000.0,
            price=80_000.0,
            contract_size=0.0001,
            min_vol=1,
            vol_unit=1,
        )
        self.assertTrue(result["eligible"])
        self.assertEqual(result["contracts"], 1)
        self.assertAlmostEqual(result["notional"], 8.0)
        self.assertAlmostEqual(result["initial_margin"], 8.0)
        self.assertLessEqual(result["initial_margin"], 10.0)
        self.assertFalse(result["orders_created"])
        self.assertFalse(result["capital_enabled"])

    def test_blocks_when_minimum_contract_exceeds_budget(self):
        result = isolated_margin_validation_size(
            account_equity=5_000.0,
            price=80_000.0,
            contract_size=0.0001,
            min_vol=1,
            vol_unit=1,
        )
        self.assertFalse(result["eligible"])
        self.assertEqual(
            result["status"],
            "BLOCKED_MINIMUM_CONTRACT_EXCEEDS_VALIDATION_MARGIN",
        )
        self.assertEqual(result["contracts"], 0)

    def test_never_rounds_up_to_next_contract(self):
        result = isolated_margin_validation_size(
            account_equity=19_999.0,
            price=80_000.0,
            contract_size=0.0001,
            min_vol=1,
            vol_unit=1,
        )
        self.assertTrue(result["eligible"])
        self.assertEqual(result["contracts"], 2)
        self.assertAlmostEqual(result["initial_margin"], 16.0)
        self.assertLessEqual(result["initial_margin"], result["max_initial_margin"])

    def test_invalid_contract_grid_fails_closed(self):
        with self.assertRaises(ValueError):
            isolated_margin_validation_size(
                account_equity=10_000.0,
                price=80_000.0,
                contract_size=0.0001,
                min_vol=3,
                vol_unit=2,
            )


if __name__ == "__main__":
    unittest.main()
