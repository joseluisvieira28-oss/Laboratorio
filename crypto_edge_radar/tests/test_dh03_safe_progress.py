from __future__ import annotations

import unittest

from radar.dh03_safe_progress import (
    DH03SafeProgressError,
    SCHEMA_VERSION,
    STRATEGY_ID,
    sanitize_receipt,
    validate_safe_payload,
)


class DH03SafeProgressTests(unittest.TestCase):
    def _receipt(self):
        return {
            "strategy_id": STRATEGY_ID,
            "status": "OK",
            "checked_at_utc": "2026-09-26T04:03:51Z",
            "latest_archive_day": "2026-09-25",
            "used_as_forward_evidence": True,
            "evaluation": {
                "totals": {
                    "signals": 4,
                    "price_exits": 2,
                    "final_resolutions": 1,
                    "funding_pending": 1,
                    "unresolved_price_paths": 2,
                    "overlap_skipped": 3,
                },
                "symbols": {
                    "BTCUSDT": {
                        "rows": [
                            {
                                "signal": {"entry": 123.4},
                                "final_resolution": {"base_net_r": 2.0},
                            }
                        ]
                    }
                },
            },
        }

    def test_sanitizer_keeps_counts_and_drops_all_outcome_rows(self):
        payload = sanitize_receipt(self._receipt(), run_id=36216704993)
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertEqual(payload["source_workflow_run_id"], 36216704993)
        self.assertEqual(payload["counts"]["signals"], 4)
        self.assertEqual(payload["counts"]["final_resolutions"], 1)
        encoded = str(payload)
        self.assertNotIn("BTCUSDT", encoded)
        self.assertNotIn("entry", encoded)
        self.assertNotIn("base_net_r", encoded)
        self.assertFalse(payload["outcomes_included"])
        self.assertFalse(payload["prices_included"])
        self.assertFalse(payload["returns_included"])
        self.assertFalse(payload["trade_rows_included"])

    def test_validator_requires_exact_workflow_run_binding(self):
        payload = sanitize_receipt(self._receipt(), run_id=100)
        with self.assertRaisesRegex(DH03SafeProgressError, "workflow run mismatch"):
            validate_safe_payload(payload, expected_run_id=101)

    def test_validator_rejects_extra_field_even_if_benign_looking(self):
        payload = sanitize_receipt(self._receipt(), run_id=100)
        payload["base_profit_factor"] = None
        with self.assertRaisesRegex(DH03SafeProgressError, "unexpected top-level"):
            validate_safe_payload(payload, expected_run_id=100)

    def test_validator_rejects_any_outcome_firewall_flip(self):
        payload = sanitize_receipt(self._receipt(), run_id=100)
        payload["returns_included"] = True
        with self.assertRaisesRegex(DH03SafeProgressError, "firewall field not false"):
            validate_safe_payload(payload, expected_run_id=100)

    def test_waiting_state_publishes_zero_counts_only(self):
        receipt = {
            "strategy_id": STRATEGY_ID,
            "status": "WAITING_ARCHIVE_PUBLICATION",
            "checked_at_utc": "2026-09-26T04:03:51Z",
            "latest_archive_day": "2026-09-25",
            "used_as_forward_evidence": False,
        }
        payload = sanitize_receipt(receipt, run_id=100)
        self.assertTrue(all(value == 0 for value in payload["counts"].values()))
        self.assertFalse(payload["used_as_forward_evidence"])

    def test_negative_count_fails_closed(self):
        receipt = self._receipt()
        receipt["evaluation"]["totals"]["signals"] = -1
        with self.assertRaisesRegex(DH03SafeProgressError, "negative count"):
            sanitize_receipt(receipt, run_id=100)


if __name__ == "__main__":
    unittest.main()
