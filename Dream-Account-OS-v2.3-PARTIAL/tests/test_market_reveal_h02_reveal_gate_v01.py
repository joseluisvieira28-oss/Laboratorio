import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from h02_reveal_gate import DecisionStateLabel, evaluate_reveal_gate


def labels():
    out = []
    for i in range(20):
        state = "ACCEPTANCE" if i % 2 == 0 else "REJECTION"
        out.append(DecisionStateLabel(
            event_id=f"E{i:02d}",
            event_family="US_CPI",
            asset="BTC",
            state=state,
        ))
        out.append(DecisionStateLabel(
            event_id=f"E{i:02d}",
            event_family="US_CPI",
            asset="ETH",
            state=state,
        ))
    return out


COUNTS = {
    "US_CPI": 10,
    "US_EMPLOYMENT_SITUATION": 10,
    "FOMC_STATEMENT": 6,
}


class RevealGateTests(unittest.TestCase):
    def test_ready_gate_uses_labels_only(self):
        result = evaluate_reveal_gate(
            labels(),
            eligible_event_family_counts=COUNTS,
            official_2027_calendar_exhausted=False,
        )
        self.assertEqual(result.action, "READY_FOR_SINGLE_OUTCOME_REVEAL")

    def test_insufficient_midyear_keeps_outcomes_locked(self):
        result = evaluate_reveal_gate(
            labels()[:4],
            eligible_event_family_counts={
                "US_CPI": 2,
                "US_EMPLOYMENT_SITUATION": 2,
                "FOMC_STATEMENT": 1,
            },
            official_2027_calendar_exhausted=False,
        )
        self.assertEqual(
            result.action,
            "HOLD_OUTCOMES_LOCKED_CONTINUE_BLIND_COLLECTION",
        )

    def test_insufficient_at_year_end_closes_without_reveal(self):
        result = evaluate_reveal_gate(
            labels()[:4],
            eligible_event_family_counts=COUNTS,
            official_2027_calendar_exhausted=True,
        )
        self.assertEqual(
            result.action,
            "CLOSE_INSUFFICIENT_SAMPLE_WITHOUT_OUTCOME_REVEAL",
        )


if __name__ == "__main__":
    unittest.main()
