import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from decision_boundary import (
    assert_no_future,
    bounded_window,
    epoch_ms_to_ns,
    latest_at_or_before,
    raw_sha256,
    rfc3339_to_ns,
)


@dataclass(frozen=True)
class Row:
    ts: int
    value: str


class DecisionBoundaryTests(unittest.TestCase):
    def test_bounded_window_excludes_future_and_pre_anchor(self):
        rows = [Row(9, "old"), Row(10, "a"), Row(15, "b"), Row(21, "future")]
        out = bounded_window(
            rows,
            timestamp_ns=lambda row: row.ts,
            anchor_ns=10,
            decision_ns=20,
        )
        self.assertEqual([row.value for row in out], ["a", "b"])

    def test_latest_at_or_before_never_uses_future(self):
        rows = [Row(10, "a"), Row(20, "b"), Row(30, "future")]
        row = latest_at_or_before(
            rows,
            timestamp_ns=lambda item: item.ts,
            decision_ns=25,
        )
        self.assertEqual(row.value, "b")

    def test_assert_no_future_fails_closed(self):
        rows = [Row(10, "a"), Row(21, "future")]
        with self.assertRaises(ValueError):
            assert_no_future(
                rows,
                timestamp_ns=lambda item: item.ts,
                decision_ns=20,
            )

    def test_epoch_ms_to_ns(self):
        self.assertEqual(epoch_ms_to_ns(1234), 1_234_000_000)

    def test_rfc3339_requires_timezone(self):
        with self.assertRaises(ValueError):
            rfc3339_to_ns("2026-01-01T00:00:00")

    def test_rfc3339_z(self):
        self.assertEqual(
            rfc3339_to_ns("1970-01-01T00:00:01Z"),
            1_000_000_000,
        )

    def test_rfc3339_preserves_all_nine_fractional_digits(self):
        self.assertEqual(
            rfc3339_to_ns("1970-01-01T00:00:01.123456789Z"),
            1_123_456_789,
        )

    def test_rfc3339_offset_is_exact(self):
        self.assertEqual(
            rfc3339_to_ns("1970-01-01T01:00:01.000000001+01:00"),
            1_000_000_001,
        )
        self.assertEqual(
            rfc3339_to_ns("1969-12-31T19:00:01.000000001-05:00"),
            1_000_000_001,
        )

    def test_one_nanosecond_after_decision_is_future(self):
        decision = rfc3339_to_ns("2026-09-24T17:00:00.123456788Z")
        future = rfc3339_to_ns("2026-09-24T17:00:00.123456789Z")
        with self.assertRaises(ValueError):
            assert_no_future(
                [Row(future, "future")],
                timestamp_ns=lambda item: item.ts,
                decision_ns=decision,
            )

    def test_invalid_fraction_beyond_nanoseconds_rejected(self):
        with self.assertRaises(ValueError):
            rfc3339_to_ns("2026-01-01T00:00:00.1234567890Z")

    def test_hash_is_deterministic_and_tamper_evident(self):
        a = raw_sha256(b'{"x":1}')
        b = raw_sha256(b'{"x":1}')
        c = raw_sha256(b'{"x":2}')
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


if __name__ == "__main__":
    unittest.main()
