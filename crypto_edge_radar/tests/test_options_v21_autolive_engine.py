from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.options_v21_autolive_engine import (
    OptionsV21AutoLiveEngine,
    _exclusive_write,
    _floor_step,
)


class NoPositionRO:
    def open_positions(self, symbol=None): return []
    def open_orders(self, symbol=None): return []


class NoSpotOrders:
    def open_orders(self, symbol="BTCUSDT"): return []


class EngineSafetyTests(unittest.TestCase):
    def test_floor_step_never_rounds_up(self):
        self.assertEqual(_floor_step(3.99, 1.0), 3.0)
        self.assertAlmostEqual(_floor_step(0.000199, 0.0001), 0.0001)

    def test_order_intent_is_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "intent.json"
            self.assertTrue(_exclusive_write(p, {"a": 1}))
            self.assertFalse(_exclusive_write(p, {"a": 2}))
            self.assertIn('"a": 1', p.read_text())

    def test_unarmed_global_gate_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            e = OptionsV21AutoLiveEngine(
                credentials=MEXCCredentials("K", "S"),
                db_path=str(root / "e.sqlite3"),
                receipt_root=str(root / "receipts"),
                armed_path=str(root / "ARMED.json"),
                kill_switch_path=str(root / "KILL_SWITCH"),
                status_path=str(root / "status.json"),
            )
            e.futures_ro = NoPositionRO()
            e.spot_auth = NoSpotOrders()
            gate = e._global_gate(datetime(2026, 9, 26, 0, 0, tzinfo=timezone.utc))
            self.assertFalse(gate["pass"])
            self.assertIn("AUTO_MICROLIVE_NOT_ARMED", gate["blockers"])

    def test_kill_switch_blocks_new_entry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ARMED.json").write_text("{}")
            (root / "KILL_SWITCH").write_text("{}")
            e = OptionsV21AutoLiveEngine(
                credentials=MEXCCredentials("K", "S"),
                db_path=str(root / "e.sqlite3"),
                receipt_root=str(root / "receipts"),
                armed_path=str(root / "ARMED.json"),
                kill_switch_path=str(root / "KILL_SWITCH"),
                status_path=str(root / "status.json"),
            )
            e.futures_ro = NoPositionRO()
            e.spot_auth = NoSpotOrders()
            gate = e._global_gate(datetime(2026, 9, 26, 0, 0, tzinfo=timezone.utc))
            self.assertFalse(gate["pass"])
            self.assertIn("KILL_SWITCH_PRESENT", gate["blockers"])


if __name__ == "__main__":
    unittest.main()
