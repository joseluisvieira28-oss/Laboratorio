from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from radar.mexc_local_state import read_mexc_local_state


NOW = datetime(2026, 9, 22, 8, 0, tzinfo=timezone.utc)


class MexcLocalStateTests(unittest.TestCase):
    def _write(self, root: Path, name: str, value: dict) -> Path:
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def _preflight(self) -> dict:
        checks = {name: {"pass": True} for name in (
            "account", "clock", "contract", "fees", "funding", "orders",
            "positions", "rate_limits", "risk_limit",
        )}
        checks["etf_cme_existing_validation_budget"] = {
            "pass": False,
            "maximum_validation_allocation_usdt": 0.1123763,
            "estimated_venue_minimum_notional_usdt": 8.66,
        }
        return {
            "preflight_id": "MEXC_FUTURES_AUTHENTICATED_READ_ONLY_PREFLIGHT_V0.1",
            "checked_at_utc": "2026-09-22T07:59:00Z",
            "pass": False,
            "status": "FAIL_CLOSED",
            "blockers": ["ETF_CME_VENUE_MIN_NOTIONAL_EXCEEDS_FROZEN_VALIDATION_BUDGET"],
            "checks": checks,
            "security": {
                "api_key_returned_in_receipt": False,
                "api_secret_returned_in_receipt": False,
                "exchange_mutation_performed": False,
                "withdrawal_endpoint_implemented": False,
            },
        }

    def _risk(self) -> dict:
        return {
            "status": "PASS", "as_of_utc": "2026-09-22T07:59:30Z",
            "daily_realized_loss_fraction_equity": 0.0,
            "weekly_realized_loss_fraction_equity": 0.0,
            "concurrent_planned_risk_fraction_equity": 0.0,
        }

    def _standing(self) -> dict:
        return {
            "authority_id": "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1",
            "status": "ACTIVE_STANDING_OPERATOR_AUTHORIZATION",
            "scope": {
                "exchange": "MEXC", "product": "USDT_PERPETUAL_FUTURES",
                "micro_live_only": True, "per_trade_reconfirmation_required": False,
            },
            "standing_authorized_routes": [{
                "strategy_id": "ETF-CME-INSTFLOW-001", "direction": "SHORT",
                "symbol": "BTC_USDT", "scientific_tier": 2,
            }],
        }

    def test_exchange_pass_does_not_override_candidate_capital_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write(root, "mexc_authenticated_preflight_receipt.json", self._preflight())
            self._write(root, "mexc_account_risk_state.json", self._risk())
            authority = self._write(root, "standing.json", self._standing())
            state = read_mexc_local_state(data_dir=root, standing_authority_path=authority, now_utc=NOW)
            self.assertEqual(state["exchange_authenticated_preflight"]["status"], "PASS")
            self.assertEqual(state["account_risk_firewall"]["status"], "PASS")
            self.assertEqual(state["candidate_capital_feasibility"]["ETF-CME-INSTFLOW-001"]["status"], "BLOCKED")
            self.assertTrue(state["standing_operator_authority"]["routes"]["ETF-CME-INSTFLOW-001"]["operator_authorized"])
            self.assertFalse(state["secrets_loaded"])

    def test_stale_and_partial_receipts_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            preflight = self._preflight()
            preflight["checked_at_utc"] = "2026-09-21T00:00:00Z"
            self._write(root, "mexc_authenticated_preflight_receipt.json", preflight)
            authority = self._write(root, "standing.json", self._standing())
            (root / "mexc_account_risk_state.json").write_text('{"status":', encoding="utf-8")
            state = read_mexc_local_state(data_dir=root, standing_authority_path=authority, now_utc=NOW)
            self.assertEqual(state["exchange_authenticated_preflight"]["status"], "FAIL_CLOSED")
            self.assertEqual(state["exchange_authenticated_preflight"]["reason"], "AUTHENTICATED_PREFLIGHT_STALE")
            self.assertEqual(state["account_risk_firewall"]["status"], "FAIL_CLOSED")

    def test_secret_bearing_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            preflight = self._preflight()
            preflight["api_secret"] = "must-never-be-here"
            self._write(root, "mexc_authenticated_preflight_receipt.json", preflight)
            authority = self._write(root, "standing.json", self._standing())
            state = read_mexc_local_state(data_dir=root, standing_authority_path=authority, now_utc=NOW)
            self.assertEqual(state["exchange_authenticated_preflight"]["status"], "FAIL_CLOSED")
            self.assertFalse(state["exchange_authenticated_preflight"]["sanitized"])


if __name__ == "__main__":
    unittest.main()
