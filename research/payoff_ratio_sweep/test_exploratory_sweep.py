"""Offline invariants for exploratory payoff ratios; never download outcomes."""
import unittest
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import exploratory_sweep as sweep


class FrozenSweepRules(unittest.TestCase):
    def test_four_exact_levels(self):
        self.assertEqual(list(sweep.TARGETS), ["2R","3R","4R","5R"])
        self.assertEqual(tuple(sweep.TARGETS.values()),(.20,.30,.40,.50))

    def test_same_stop_for_every_ratio(self):
        stops=[sweep.fixed_bounds(100,p)[1] for p in sweep.TARGETS.values()]
        self.assertTrue(all(x==stops[0] for x in stops))

    def test_monotonically_greater_target(self):
        targets=[sweep.fixed_bounds(100,p)[0] for p in sweep.TARGETS.values()]
        self.assertEqual(targets,sorted(targets))
        self.assertEqual(len(set(targets)),4)

    def test_four_r_matches_original_barriers(self):
        entry=123.45
        self.assertEqual(sweep.fixed_bounds(entry,.40),sweep.core.nominal_bounds(entry))

    def test_original_nominal_loss(self):
        entry=100.;target,stop=sweep.fixed_bounds(entry,.40)
        self.assertAlmostEqual(sweep.core.LEV*((1-sweep.core.NOMINAL_FEE)*
                                (stop/entry)-(1+sweep.core.NOMINAL_FEE)),-.10,places=12)

    def test_each_nominal_target_net_margin(self):
        for expected in sweep.TARGETS.values():
            entry=100.;target,_=sweep.fixed_bounds(entry,expected)
            observed=sweep.core.LEV*((1-sweep.core.NOMINAL_FEE)*
                            (target/entry)-(1+sweep.core.NOMINAL_FEE))
            self.assertAlmostEqual(observed,expected,places=12)

    def test_reject_other_payoff(self):
        with self.assertRaises(ValueError):
            sweep.fixed_bounds(100,.60)
        with self.assertRaises(ValueError):
            sweep.fixed_bounds(0,.40)

    def test_reject_unknown_source(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_NOT_VERIFIED"):
            sweep.run({"status":"MISSING"})

    def test_publication_regression_values(self):
        self.assertAlmostEqual(sweep.LEGACY_4R_RETURNS["BASE"],0.283296092471792)
        self.assertAlmostEqual(sweep.LEGACY_4R_RETURNS["STRESS"],0.26323957585754676)

    def test_core_original_untouched(self):
        f=sweep.core.nominal_bounds
        with self.assertRaises(ValueError):
            sweep.replay_ratio([],{}, {}, .0008,.0002,"6R")
        self.assertIs(f,sweep.core.nominal_bounds)


if __name__=="__main__":
    unittest.main()
