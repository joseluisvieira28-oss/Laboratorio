import unittest
from research.convex_okx_l2_stop_v02.monotonic_child_replay import verify_single_change,CONFIGS
class ChildInvariantTests(unittest.TestCase):
    def test_exact_single_line_stop_mutation(self):
        self.assertTrue(verify_single_change()["one_stop_assignment_replaced"])
    def test_exact_two_predeclared_symbols(self):
        self.assertEqual(set(CONFIGS),{"SOLUSDT","BNBUSDT"})
    def test_original_baseline_sample_predefined(self):
        self.assertEqual(CONFIGS["SOLUSDT"][2]["BASE"][1],84)
        self.assertEqual(CONFIGS["BNBUSDT"][2]["STRESS"][1],28)
if __name__=="__main__":unittest.main()
