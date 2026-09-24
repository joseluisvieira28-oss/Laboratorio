import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from availability_boundary import (
    assert_available_by_decision,
    effective_available_ns,
)


@dataclass(frozen=True)
class Row:
    source_ns: int
    arrival_ns: int | None


class AvailabilityBoundaryTests(unittest.TestCase):
    def test_effective_availability_is_later_of_source_and_arrival(self):
        self.assertEqual(
            effective_available_ns(
                source_time_ns=100,
                collector_arrival_ns=120,
            ),
            120,
        )
        self.assertEqual(
            effective_available_ns(
                source_time_ns=120,
                collector_arrival_ns=100,
            ),
            120,
        )

    def test_old_source_arriving_one_ns_after_decision_is_rejected(self):
        row = Row(source_ns=100, arrival_ns=201)
        with self.assertRaises(ValueError):
            assert_available_by_decision(
                [row],
                source_time_ns=lambda item: item.source_ns,
                collector_arrival_ns=lambda item: item.arrival_ns,
                decision_ns=200,
            )

    def test_future_source_is_rejected_even_if_arrival_is_not_future(self):
        row = Row(source_ns=201, arrival_ns=200)
        with self.assertRaises(ValueError):
            assert_available_by_decision(
                [row],
                source_time_ns=lambda item: item.source_ns,
                collector_arrival_ns=lambda item: item.arrival_ns,
                decision_ns=200,
            )

    def test_missing_arrival_fails_closed_in_strict_mode(self):
        row = Row(source_ns=100, arrival_ns=None)
        with self.assertRaises(ValueError):
            assert_available_by_decision(
                [row],
                source_time_ns=lambda item: item.source_ns,
                collector_arrival_ns=lambda item: item.arrival_ns,
                decision_ns=200,
                require_arrival_provenance=True,
            )

    def test_non_target_synthetic_mode_can_fallback_to_source_time(self):
        row = Row(source_ns=100, arrival_ns=None)
        checks = assert_available_by_decision(
            [row],
            source_time_ns=lambda item: item.source_ns,
            collector_arrival_ns=lambda item: item.arrival_ns,
            decision_ns=200,
            require_arrival_provenance=False,
        )
        self.assertEqual(checks[0].collector_arrival_ns, 100)
        self.assertEqual(checks[0].effective_available_ns, 100)

    def test_both_source_and_arrival_at_decision_are_valid(self):
        row = Row(source_ns=200, arrival_ns=200)
        checks = assert_available_by_decision(
            [row],
            source_time_ns=lambda item: item.source_ns,
            collector_arrival_ns=lambda item: item.arrival_ns,
            decision_ns=200,
        )
        self.assertEqual(checks[0].effective_available_ns, 200)


if __name__ == "__main__":
    unittest.main()
