from __future__ import annotations

import unittest

from scripts.mexc_exit_guard import _exit_external_oid, _fee


class ExitGuardTests(unittest.TestCase):
    def test_exit_external_oid_is_deterministic_and_short(self):
        a=_exit_external_oid("sig-123",1)
        b=_exit_external_oid("sig-123",1)
        self.assertEqual(a,b)
        self.assertLessEqual(len(a),32)

    def test_fee_prefers_total_fee(self):
        self.assertEqual(_fee({"totalFee":0.12,"takerFee":0.5}),0.12)
        self.assertAlmostEqual(_fee({"takerFee":0.1,"makerFee":0.02}),0.12)


if __name__=="__main__":
    unittest.main()
