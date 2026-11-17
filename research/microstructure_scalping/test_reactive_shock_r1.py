"""Unit tests use zero market data and no network."""
import unittest
from research.microstructure_scalping.reactive_shock_r1_runner import strict_gate,quality_manifest
class TestR1(unittest.TestCase):
    def test_empty_fail(self):
        g=strict_gate([])
        self.assertEqual(g['decision'],'REPLICATION_FAILS_STRICT_GATE')
    def test_winning_all_gates(self):
        rows=[{'type':'CPI' if i%2 else 'NFP','status':'RESOLVED','stress10_bps':15+i} for i in range(14)]
        self.assertEqual(strict_gate(rows)['decision'],'REPLICATION_SURVIVES')
    def test_7_is_insufficient(self):
        rows=[{'type':'CPI' if i%2 else 'NFP','status':'RESOLVED','stress10_bps':15} for i in range(7)]
        self.assertEqual(strict_gate(rows)['decision'],'REPLICATION_FAILS_STRICT_GATE')
    def test_no_signal_excluded(self):
        rows=[{'type':'CPI' if i%2 else 'NFP','status':'RESOLVED','stress10_bps':30} for i in range(14)]
        rows[0]['status']='NO_SIGNAL_OR_OUTCOME'
        self.assertEqual(strict_gate(rows)['decision'],'REPLICATION_SURVIVES')
    def test_negative_ci_fail(self):
        rows=[{'type':'CPI' if i%2 else 'NFP','status':'RESOLVED','stress10_bps':1 if i<13 else -100} for i in range(14)]
        self.assertEqual(strict_gate(rows)['decision'],'REPLICATION_FAILS_STRICT_GATE')
    def test_sample_overlap_rejected(self):
        raw={'event_count':14,'prior_mve_dates':['2023-02-03']*8,'events':[]}
        with self.assertRaises(AssertionError):quality_manifest(raw)
if __name__=='__main__':unittest.main()