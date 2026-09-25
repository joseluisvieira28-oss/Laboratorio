import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from h02_analysis import (
    OutcomeRow,
    cluster_bootstrap_ci,
    evaluate_primary,
    sample_gate,
    signed_forward_return_bps,
)


class H02AnalysisTests(unittest.TestCase):
    def _rows(self):
        rows = []
        for i in range(20):
            state = "ACCEPTANCE" if i % 2 == 0 else "REJECTION"
            base = 6.0 if state == "ACCEPTANCE" else -2.0
            rows.append(OutcomeRow(
                event_id=f"E{i:02d}",
                asset="BTC",
                state=state,
                signed_forward_return_bps=base + (i % 3),
            ))
            rows.append(OutcomeRow(
                event_id=f"E{i:02d}",
                asset="ETH",
                state=state,
                signed_forward_return_bps=base + ((i + 1) % 3),
            ))
        return rows

    def test_signed_return_respects_direction(self):
        long = signed_forward_return_bps(
            decision_mid=100,
            outcome_mid=101,
            direction=1,
        )
        short = signed_forward_return_bps(
            decision_mid=100,
            outcome_mid=99,
            direction=-1,
        )
        self.assertGreater(long, 0)
        self.assertGreater(short, 0)

    def test_sample_gate_enforces_family_and_state_minima(self):
        rows = self._rows()
        gate = sample_gate(
            rows,
            eligible_event_family_counts={
                "US_CPI": 10,
                "US_EMPLOYMENT_SITUATION": 10,
                "FOMC_STATEMENT": 6,
            },
        )
        self.assertTrue(gate.ready, gate.blockers)

    def test_bootstrap_is_deterministic_for_seed(self):
        rows = self._rows()
        a = cluster_bootstrap_ci(rows, reps=200, seed=1729)
        b = cluster_bootstrap_ci(rows, reps=200, seed=1729)
        self.assertEqual(a, b)

    def test_positive_synthetic_contrast_is_supported(self):
        result = evaluate_primary(
            self._rows(),
            eligible_event_family_counts={
                "US_CPI": 10,
                "US_EMPLOYMENT_SITUATION": 10,
                "FOMC_STATEMENT": 6,
            },
            reps=500,
            seed=1729,
        )
        self.assertEqual(result.classification, "H02_SUPPORTED")
        self.assertGreater(result.ci_lower_bps, 0)

    def test_insufficient_sample_fails_before_inference(self):
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_SAMPLE"):
            evaluate_primary(
                self._rows()[:4],
                eligible_event_family_counts={
                    "US_CPI": 1,
                    "US_EMPLOYMENT_SITUATION": 1,
                    "FOMC_STATEMENT": 1,
                },
                reps=20,
            )


if __name__ == "__main__":
    unittest.main()
