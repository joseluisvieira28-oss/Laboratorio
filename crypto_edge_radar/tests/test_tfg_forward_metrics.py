import os
import tempfile
import unittest

from radar.strategies.tfg_donchian_regime_forward import MAX_HOLD_BARS, TWELVE_HOUR_MS

from radar.evidence import EvidenceStore
from radar.tfg_forward_metrics import evaluate_tfg_forward_evidence


class TFGForwardMetricsTests(unittest.TestCase):
    def _store(self, tmp):
        return EvidenceStore(os.path.join(tmp, "evidence.sqlite3"))

    def _append_trade(self, store, idx, base_r, stress_r, resolve=True):
        key = f"TFG-DONCHIAN-REGIME-V1:BTCUSDT:{idx}"
        store.append_once("TFG_FORWARD_SIGNAL", key, {"event_key": key})
        if resolve:
            store.append_once(
                "TFG_FORWARD_RESOLUTION",
                key,
                {
                    "event_key": key,
                    "outcome": {
                        "base_net_r": base_r,
                        "stress_net_r": stress_r,
                    },
                },
            )

    def test_accumulates_until_ten_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            for i in range(3):
                self._append_trade(store, i, 1.0, 0.9)
            result = evaluate_tfg_forward_evidence(store)
            self.assertEqual(result["progress"], "3/10")
            self.assertEqual(result["classification"], "FORWARD_EVIDENCE_ACCUMULATING")
            self.assertFalse(result["readiness_gate_pass"])

    def test_exact_frozen_gate_passes_at_ten_with_positive_base_and_stress(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            base = [1, 1, 1, 1, 1, 1, 1, -1, -1, -1]
            stress = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, -1, -1, -1]
            for i, (b, s) in enumerate(zip(base, stress)):
                self._append_trade(store, i, b, s)
            result = evaluate_tfg_forward_evidence(store)
            self.assertEqual(result["resolved_forward_trades"], 10)
            self.assertGreater(result["base_expectancy_r"], 0)
            self.assertGreater(result["base_profit_factor"], 1)
            self.assertGreater(result["stress_expectancy_r"], 0)
            self.assertGreater(result["stress_profit_factor"], 1)
            self.assertEqual(result["unresolved_execution_paths"], 0)
            self.assertEqual(result["classification"], "MICRO_LIVE_RISK_REVIEW_ELIGIBLE")
            self.assertTrue(result["readiness_gate_pass"])
            self.assertFalse(result["live_trading_automatically_authorized"])

    def test_unresolved_signal_blocks_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            for i in range(10):
                self._append_trade(store, i, 1.0, 0.9, resolve=(i != 9))
            result = evaluate_tfg_forward_evidence(store)
            self.assertEqual(result["unresolved_execution_paths"], 1)
            self.assertFalse(result["gate_checks"]["unresolved_execution_paths_eq_0"])
            self.assertFalse(result["readiness_gate_pass"])

    def test_unresolved_visibility_separates_maturing_from_overdue_without_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            key1 = "TFG-DONCHIAN-REGIME-V1:BTCUSDT:100"
            key2 = "TFG-DONCHIAN-REGIME-V1:ETHUSDT:200"
            store.append_once("TFG_FORWARD_SIGNAL", key1, {
                "event_key": key1,
                "paper_trade": {"entry_open_time": 1_000_000},
            })
            store.append_once("TFG_FORWARD_SIGNAL", key2, {
                "event_key": key2,
                "paper_trade": {"entry_open_time": 2_000_000},
            })
            due1 = 1_000_000 + MAX_HOLD_BARS * TWELVE_HOUR_MS
            now = due1
            result = evaluate_tfg_forward_evidence(store, now_ms=now)
            self.assertEqual(result["resolved_forward_trades"], 0)
            self.assertEqual(result["unresolved_execution_paths"], 2)
            self.assertEqual(
                result["unresolved_state_breakdown"]["overdue_reconciliation_review"], 1
            )
            self.assertEqual(
                result["unresolved_state_breakdown"]["maturing_within_frozen_max_hold"], 1
            )
            self.assertFalse(result["readiness_gate_pass"])

    def test_ten_bad_trades_fail_without_rescue(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            for i in range(10):
                self._append_trade(store, i, -1.0, -1.1)
            result = evaluate_tfg_forward_evidence(store)
            self.assertEqual(result["classification"], "FORWARD_READINESS_GATE_FAIL")
            self.assertLess(result["base_expectancy_r"], 0)
            self.assertFalse(result["readiness_gate_pass"])

    def test_rule_deviation_event_blocks_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            for i in range(10):
                self._append_trade(store, i, 1.0 if i < 8 else -1.0, 0.9 if i < 8 else -1.0)
            store.append("TFG_FORWARD_RULE_DEVIATION", {"reason": "synthetic-test"})
            result = evaluate_tfg_forward_evidence(store)
            self.assertEqual(result["rule_deviations"], 1)
            self.assertFalse(result["readiness_gate_pass"])


if __name__ == "__main__":
    unittest.main()
