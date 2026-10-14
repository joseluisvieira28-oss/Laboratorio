import unittest
from pine_source_preflight import audit

class PineSourcePreflightTest(unittest.TestCase):
    def test_minimal_strategy_is_only_intake(self):
        x = audit(b"//@version=6\nstrategy('abc')\nstrategy.entry('L', strategy.long)\n")
        self.assertEqual(x["source_gate"], "RECEIVED_NOT_AUDITED")
        self.assertEqual(x["economic_outcome"], "UNTESTED")
        self.assertEqual(x["live_authority"], "NONE")
        self.assertTrue(x["flags_for_human_review"]["strategy_order"])
        self.assertEqual(len(x["source_sha256"]), 64)

    def test_higher_tf_lookahead_flag_does_not_promote(self):
        x = audit(b"//@version=5\nstrategy('abc')\nx=request.security(syminfo.tickerid, '60', close, lookahead=barmerge.lookahead_on)\n")
        self.assertTrue(x["flags_for_human_review"]["lookahead_on"])
        self.assertTrue(x["flags_for_human_review"]["higher_or_external_series"])
        self.assertEqual(x["source_gate"], "RECEIVED_NOT_AUDITED")

    def test_indicator_is_not_strategy(self):
        x = audit(b"//@version=6\nindicator('signals')\nplot(close)\n")
        self.assertEqual(x["kind"], "indicator")
        self.assertFalse(x["flags_for_human_review"]["strategy_order"])

    def test_empty_version_and_double_declaration_fail(self):
        for b in (b"", b"strategy('no version')", b"//@version=6\nstrategy('s')\nindicator('i')"):
            with self.subTest(raw=b), self.assertRaises(ValueError):
                audit(b)

    def test_refuse_large_source(self):
        with self.assertRaises(ValueError):
            audit(b"//@version=6\nstrategy('s')\n" + b"x" * (1024 * 1024))

if __name__ == "__main__":
    unittest.main()
