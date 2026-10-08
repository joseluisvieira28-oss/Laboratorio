"""Hermetic forensic regressions; no credentials, exchange, DB or network."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from audits.tfg_forward_integrity_audit import audit_rows

HOUR = 3600_000
START = 1_790_000_000_000


def row(symbol, idx, entry, exit_ms, lag_minutes):
    stamp = datetime.fromtimestamp((entry + int(lag_minutes * 60_000)) / 1000, tz=timezone.utc)
    return {
        "event_key": f"TFG-DONCHIAN-REGIME-V1:{symbol}:{idx}",
        "symbol": symbol,
        "entry_ms": entry,
        "exit_ms": exit_ms,
        "receipt_ts_utc": stamp.isoformat(),
    }


class TFGIntegrityAuditTest(unittest.TestCase):
    def test_detects_same_symbol_reentry_before_prior_exit(self):
        rows = [
            row("BTCUSDT", 1, START, START + 5 * HOUR, 15.5),
            row("BTCUSDT", 2, START + HOUR, START + 3 * HOUR, 15.5),
            row("ETHUSDT", 3, START + HOUR, None, 15.5),
        ]
        result = audit_rows(rows)
        self.assertEqual(result["classification"], "EXECUTION_INTEGRITY_FAIL")
        self.assertEqual(result["overlap_violation_count"], 1)
        self.assertEqual(result["nonoverlap_resolved_descriptive_only"], 1)
        self.assertEqual(result["nonoverlap_unresolved_descriptive_only"], 1)
        self.assertEqual(result["retroactive_entry_receipt_count"], 3)
        self.assertFalse(result["economic_promotion_authorized"])

    def test_exit_before_later_entry_is_not_overlap(self):
        rows = [
            row("BNBUSDT", 1, START, START + HOUR, 0),
            row("BNBUSDT", 2, START + 2 * HOUR, START + 3 * HOUR, 0),
        ]
        result = audit_rows(rows)
        self.assertEqual(result["overlap_violation_count"], 0)
        self.assertEqual(result["retroactive_entry_receipt_count"], 0)
        self.assertEqual(result["classification"], "REQUIRES_SEPARATE_ECONOMIC_ADJUDICATION")
        self.assertFalse(result["economic_promotion_authorized"])

    def test_unresolved_parent_blocks_all_later_entries(self):
        rows = [
            row("SOLUSDT", 1, START, None, 0),
            row("SOLUSDT", 2, START + HOUR, START + 3 * HOUR, 0),
            row("SOLUSDT", 3, START + 4 * HOUR, START + 5 * HOUR, 0),
        ]
        result = audit_rows(rows)
        self.assertEqual(result["overlap_violation_count"], 2)
        self.assertEqual(result["nonoverlap_unresolved_descriptive_only"], 1)

    def test_fails_closed_for_missing_timestamp(self):
        broken = row("XRPUSDT", 1, START, None, 0)
        broken["receipt_ts_utc"] = None
        with self.assertRaises(ValueError):
            audit_rows([broken])

    def test_fails_closed_for_duplicate_key(self):
        a = row("ETHUSDT", 1, START, START + HOUR, 0)
        with self.assertRaises(ValueError):
            audit_rows([a, dict(a)])

    def test_exact_one_position_rule_is_symbol_scoped(self):
        rows = [
            row("BTCUSDT", 1, START, None, 0),
            row("ETHUSDT", 2, START, None, 0),
        ]
        result = audit_rows(rows)
        self.assertEqual(result["overlap_violation_count"], 0)
        self.assertEqual(result["nonoverlap_unresolved_descriptive_only"], 2)


if __name__ == "__main__":
    unittest.main()
