import unittest
from copy import deepcopy
from source_first_sample_gate_v01 import evaluate,GateInvalid

def clean(primary=41,control=131):
    return {
      "lab_id":"SYNTHETIC-RLE-COUNT-001",
      "stage":"SOURCE_ONLY_PREOUTCOME_CENSUS",
      "source_receipt_sha256":"a"*64,
      "freeze_sha256":"b"*64,
      "source_observations_only":True,
      "future_prices_opened":False,
      "group_raw_candidate_counts":{"PRIMARY":primary,"CONTROL":control},
      "frozen_minimum_executed_count":{"PRIMARY":100,"CONTROL":100}
    }

class SourceFirstGateTests(unittest.TestCase):
    def test_insufficient_signal_upper_bound_blocks(self):
        z=evaluate(clean())
        self.assertEqual(z["classification"],"SOURCE_SAMPLE_IMPOSSIBLE_DO_NOT_OPEN_OUTCOMES")
        self.assertEqual(z["impossible_groups"]["PRIMARY"]["raw_candidate_upper_bound"],41)
        self.assertFalse(z["economic_outcome_access_authorized"])
    def test_enough_raw_signals_not_permission(self):
        z=evaluate(clean(primary=151,control=220))
        self.assertEqual(z["classification"],"RAW_SIGNAL_UPPER_BOUND_PASSES_NEXT_GATE_REQUIRED")
        self.assertFalse(z["economic_outcome_access_authorized"])
    def test_exact_floor_still_next_gate(self):
        z=evaluate(clean(primary=100,control=100))
        self.assertFalse(z["economic_outcome_access_authorized"])
    def test_forbidden_pnl_field(self):
        x=clean();x["net_return_bps"]=999
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_forbidden_results_nested(self):
        x=clean();x["group_raw_candidate_counts"]["PRIMARY"]={"pnl":100}
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_outcomes_opened_blocks(self):
        x=clean();x["future_prices_opened"]=True
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_bool_signal_count_is_invalid(self):
        x=clean();x["group_raw_candidate_counts"]["PRIMARY"]=True
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_negative_signal_count_is_invalid(self):
        x=clean();x["group_raw_candidate_counts"]["PRIMARY"]=-1
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_missing_source_hash_blocks(self):
        x=clean();x["source_receipt_sha256"]=""
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_missing_freeze_hash_blocks(self):
        x=clean();x["freeze_sha256"]="3"
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_missing_group_blocks(self):
        x=clean();del x["frozen_minimum_executed_count"]["CONTROL"]
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_wrong_stage_blocks(self):
        x=clean();x["stage"]="AFTER_PRICES"
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_unknown_key_blocks(self):
        x=clean();x["benchmark_2025_pnl"]=1
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_fractional_count_blocks(self):
        x=clean();x["group_raw_candidate_counts"]["PRIMARY"]=99.99
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_minimum_zero_blocks(self):
        x=clean();x["frozen_minimum_executed_count"]["PRIMARY"]=0
        with self.assertRaises(GateInvalid):evaluate(x)
    def test_source_not_observation_only_blocks(self):
        x=clean();x["source_observations_only"]=False
        with self.assertRaises(GateInvalid):evaluate(x)

if __name__=="__main__":unittest.main()
