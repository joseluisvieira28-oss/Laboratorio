from __future__ import annotations

import unittest

from scripts import mexc_operator_futures_readiness_v01 as cli


class OperatorReadinessCliTests(unittest.TestCase):
    def test_symbol_allowlist_is_exact(self):
        self.assertEqual(cli.ALLOWED_SYMBOLS, ("BNB_USDT", "AVAX_USDT"))


if __name__ == "__main__":
    unittest.main()
