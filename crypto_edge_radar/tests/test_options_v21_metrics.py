import os
import tempfile
import unittest

from radar.evidence import EvidenceStore
from radar.options_v21_metrics import evaluate_options_v21_forward


class OptionsV21MetricsGateTests(unittest.TestCase):
    def _store(self, tmp):
        return EvidenceStore(os.path.join(tmp, "evidence.sqlite3"))

    def _append(self, store, i, base, stress=None):
        if stress is None:
            stress=base-0.5
        key=f"OPTIONS-SPOTPERP-001:V2.1:2026-10-{i+1:02d}"
        signal={
            "event_key":key,
            "signal_date":f"2026-10-{i+1:02d}",
            "signal":{"valid":True,"position":1},
        }
        resolution={
            "event_key":key,
            "signal_date":f"2026-10-{i+1:02d}",
            "base_net_bps":float(base),
            "stress_net_bps":float(stress),
        }
        store.append("OPTIONS_V21_FORWARD_SIGNAL_DAY",signal)
        store.append("OPTIONS_V21_FORWARD_RESOLUTION",resolution)

    def test_under_ten_accumulates_and_never_authorizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._store(tmp)
            for i in range(5):
                self._append(store,i,1.0)
            r=evaluate_options_v21_forward(store)
            self.assertFalse(r["operational_shadow_readiness"]["sample_ready"])
            self.assertFalse(r["tier1_forward_gate"]["first_50_window_locked"])
            self.assertEqual(r["classification"],"FORWARD_EVIDENCE_ACCUMULATING_TIER1_GATE_FROZEN")
            self.assertFalse(r["micro_live_authorized"])

    def test_ten_is_operational_milestone_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._store(tmp)
            for i in range(10):
                self._append(store,i,1.0)
            r=evaluate_options_v21_forward(store)
            self.assertTrue(r["operational_shadow_readiness"]["sample_ready"])
            self.assertFalse(r["operational_shadow_readiness"]["automatic_micro_live_authorization"])
            self.assertFalse(r["tier1_forward_gate"]["statistical_gate_pass"])
            self.assertFalse(r["micro_live_authorized"])

    def test_first_fifty_positive_stable_low_concentration_pass_statistically(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._store(tmp)
            values=[]
            for _ in range(5):
                values.extend([1.0]*7+[-1.0]*3)
            for i,v in enumerate(values):
                self._append(store,i,v,stress=v-0.8)
            r=evaluate_options_v21_forward(store)
            self.assertTrue(r["tier1_forward_gate"]["first_50_window_locked"])
            self.assertTrue(r["tier1_forward_gate"]["statistical_gate_pass"])
            self.assertEqual(r["tier1_forward_gate"]["nonnegative_blocks"],5)
            self.assertLessEqual(
                r["tier1_forward_gate"]["largest_single_positive_base10_trade_share"],0.40
            )
            self.assertEqual(
                r["classification"],
                "TIER1_FORWARD_EVIDENCE_STATISTICALLY_PASS__OPERATIONAL_AND_EXECUTION_AUDIT_REQUIRED",
            )
            self.assertFalse(r["tier1_forward_gate"]["automatic_tier1_promotion"])
            self.assertFalse(r["micro_live_authorized"])

    def test_first_fifty_negative_fail_no_rescue(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._store(tmp)
            for i in range(50):
                self._append(store,i,-1.0,-1.5)
            r=evaluate_options_v21_forward(store)
            self.assertFalse(r["tier1_forward_gate"]["statistical_gate_pass"])
            self.assertEqual(
                r["classification"],
                "TIER1_FORWARD_EVIDENCE_FAIL__NO_RESCUE_UNDER_THIS_GATE",
            )

    def test_duplicate_key_fails_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=self._store(tmp)
            self._append(store,0,1.0)
            dup={
                "event_key":"OPTIONS-SPOTPERP-001:V2.1:2026-10-01",
                "signal_date":"2026-10-01",
                "signal":{"valid":True,"position":1},
            }
            store.append("OPTIONS_V21_FORWARD_SIGNAL_DAY",dup)
            r=evaluate_options_v21_forward(store)
            self.assertEqual(r["integrity"]["duplicate_signal_keys"],1)
            self.assertFalse(r["integrity"]["pass"])


if __name__=="__main__":
    unittest.main()
