"""Synthetic-only audit contracts. Never considered market evidence."""
import unittest
from research.convex_historical_adversarial_v01.ledger_attack import intersect, overlap_report, CANDIDATES


class ForensicContracts(unittest.TestCase):
    def test_open_intervals_intersect(self):
        self.assertTrue(intersect({"open_t":10,"close_t":30},{"open_t":20,"close_t":50}))

    def test_adjacent_windows_not_intersect(self):
        self.assertFalse(intersect({"open_t":10,"close_t":30},{"open_t":30,"close_t":50}))

    def test_max_simultaneous_three(self):
        d = {
            "SOL_1H": [{"open_t":10,"close_t":30}],
            "BNB_4H": [{"open_t":20,"close_t":40}],
            "SOL_5M": [{"open_t":25,"close_t":35}],
        }
        r = overlap_report(d)
        self.assertEqual(r["max_simultaneously_open_on_separate_paper_ledgers"],3)
        self.assertEqual(sum(p["overlap_pairs"] for p in r["pairs"]),3)

    def test_no_overlap_when_sequential(self):
        d = {
            "SOL_1H": [{"open_t":10,"close_t":20}],
            "BNB_4H": [{"open_t":20,"close_t":30}],
            "SOL_5M": [{"open_t":30,"close_t":40}],
        }
        r = overlap_report(d)
        self.assertEqual(r["max_simultaneously_open_on_separate_paper_ledgers"],1)
        self.assertEqual(sum(p["overlap_pairs"] for p in r["pairs"]),0)

    def test_synthetic_three_lanes_expected_identity(self):
        self.assertEqual([x[0] for x in CANDIDATES],["SOL_1H","BNB_4H","SOL_5M"])

    def test_both_sol_lanes_correlated(self):
        d = {
            "SOL_1H":[{"open_t":10,"close_t":20}],
            "BNB_4H":[{"open_t":30,"close_t":40}],
            "SOL_5M":[{"open_t":12,"close_t":18}],
        }
        r = overlap_report(d)
        flagged=[p for p in r["pairs"] if p["same_underlying"]]
        self.assertEqual(len(flagged),1)
        self.assertEqual(flagged[0]["overlap_pairs"],1)


if __name__=="__main__":
    unittest.main()
