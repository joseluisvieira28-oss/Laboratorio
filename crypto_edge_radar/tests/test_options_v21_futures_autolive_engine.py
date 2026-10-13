from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.options_v21_futures_autolive_engine import (
    OptionsV21FuturesAutoLiveEngine,
    _direction_meta,
    _exclusive_write,
    _floor_step,
)


class NoPositionRO:
    def open_positions(self, symbol=None): return []
    def open_orders(self, symbol=None): return []


class EngineSafetyV02Tests(unittest.TestCase):
    def test_direction_side_mapping(self):
        self.assertEqual(_direction_meta("LONG")["entry_side"], 1)
        self.assertEqual(_direction_meta("LONG")["exit_side"], 4)
        self.assertEqual(_direction_meta("SHORT")["entry_side"], 3)
        self.assertEqual(_direction_meta("SHORT")["exit_side"], 2)

    def test_floor_step_never_rounds_up(self):
        self.assertEqual(_floor_step(3.99, 1.0), 3.0)

    def test_order_intent_is_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "intent.json"
            self.assertTrue(_exclusive_write(p, {"a": 1}))
            self.assertFalse(_exclusive_write(p, {"a": 2}))

    def test_unarmed_fails_closed_without_spot_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            e = OptionsV21FuturesAutoLiveEngine(
                credentials=MEXCCredentials("K", "S"),
                db_path=str(root / "e.sqlite3"),
                receipt_root=str(root / "receipts"),
                armed_path=str(root / "ARMED.json"),
                kill_switch_path=str(root / "KILL_SWITCH"),
                status_path=str(root / "status.json"),
            )
            e.futures_ro = NoPositionRO()
            gate = e._global_gate(datetime(2026, 9, 26, 0, 0, tzinfo=timezone.utc))
            self.assertFalse(gate["pass"])
            self.assertIn("AUTO_MICROLIVE_FUTURES_NOT_ARMED", gate["blockers"])

    @staticmethod
    def _valid_arm():
        return {
            "authority": "TIER2-AUTO-MICROLIVE-POLICY-V2.0-FROZEN-2026-09-25",
            "execution_contract": "OPTIONS-SPOTPERP-001-V2.1-FUTURES-ONLY-AUTOLIVE-V0.2.1-SOURCE-HOTFIX",
            "strategy_id": "OPTIONS-SPOTPERP-001-V2.1",
            "execution_fork": "FUTURES_ONLY",
            "symbol": "BTC_USDT",
            "long_enabled": True,
            "short_enabled": True,
            "max_notional_usdt": 10,
            "leverage": 1,
            "margin_mode": "ISOLATED",
            "maximum_concurrent_positions": 1,
            "installed_by_windows_user": "test\\operator",
            "armed_at_utc": "2026-09-25T10:00:00Z",
        }

    def _engine(self, root):
        e = OptionsV21FuturesAutoLiveEngine(
            credentials=MEXCCredentials("K", "S"),
            db_path=str(root / "e.sqlite3"),
            receipt_root=str(root / "receipts"),
            armed_path=str(root / "ARMED.json"),
            kill_switch_path=str(root / "KILL_SWITCH"),
            status_path=str(root / "status.json"),
        )
        e.futures_ro = NoPositionRO()
        return e

    def test_empty_arm_receipt_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ARMED.json").write_text("{}")
            gate = self._engine(root)._global_gate(datetime(2026, 9, 26, tzinfo=timezone.utc))
            self.assertFalse(gate["pass"])
            self.assertIn("AUTO_MICROLIVE_ARM_RECEIPT_MISMATCH:authority", gate["blockers"])

    def test_wrong_contract_symbol_or_boolean_must_fail_closed(self):
        for key, bad in (
            ("execution_contract", "INVALID"),
            ("symbol", "ETH_USDT"),
            ("long_enabled", "true"),
            ("leverage", 10),
            ("max_notional_usdt", 100),
        ):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                row = self._valid_arm()
                row[key] = bad
                (root / "ARMED.json").write_text(json.dumps(row))
                gate = self._engine(root)._global_gate(datetime(2026, 9, 26, tzinfo=timezone.utc))
                self.assertFalse(gate["pass"])
                self.assertTrue(any("ARM_RECEIPT_MISMATCH" in x for x in gate["blockers"]))

    def test_valid_windows_utf8_bom_receipt_passes_schema_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ARMED.json").write_text(json.dumps(self._valid_arm()), encoding="utf-8-sig")
            gate = self._engine(root)._global_gate(datetime(2026, 9, 26, tzinfo=timezone.utc))
            self.assertTrue(gate["pass"], gate["blockers"])

    def test_kill_switch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ARMED.json").write_text("{}")
            (root / "KILL_SWITCH").write_text("{}")
            e = OptionsV21FuturesAutoLiveEngine(
                credentials=MEXCCredentials("K", "S"),
                db_path=str(root / "e.sqlite3"),
                receipt_root=str(root / "receipts"),
                armed_path=str(root / "ARMED.json"),
                kill_switch_path=str(root / "KILL_SWITCH"),
                status_path=str(root / "status.json"),
            )
            e.futures_ro = NoPositionRO()
            gate = e._global_gate(datetime(2026, 9, 26, 0, 0, tzinfo=timezone.utc))
            self.assertIn("KILL_SWITCH_PRESENT", gate["blockers"])


if __name__ == "__main__":
    unittest.main()
