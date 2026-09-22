from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.mexc_risk_state import build_state


class RiskStateTests(unittest.TestCase):
    def _write(self,p,payload):
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(payload),encoding="utf-8")

    def test_first_trade_state_is_zeroed_and_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            pf=root/"pf.json"
            self._write(pf,{"pass":True,"checks":{"account":{"equity_usdt":1000},"positions":{"open_position_count":0}}})
            state=build_state(
                preflight_path=pf,receipt_root=root/"live",
                now=datetime(2026,9,21,21,0,tzinfo=timezone.utc)
            )
            self.assertEqual(state["status"],"PASS")
            self.assertEqual(state["daily_realized_loss_fraction_equity"],0)
            self.assertEqual(state["concurrent_planned_risk_fraction_equity"],0)

    def test_closed_loss_and_active_risk_are_counted(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            pf=root/"pf.json"
            self._write(pf,{"pass":True,"checks":{"account":{"equity_usdt":1000},"positions":{"open_position_count":0}}})
            self._write(root/"live"/"a"/"POST_TRADE_RECONCILIATION.json",{
                "closed_at_utc":"2026-09-21T10:00:00Z",
                "realized_net_pnl_usdt":-2.0
            })
            self._write(root/"live"/"b"/"ACTIVE_TRADE_STATE.json",{
                "state":"EXIT_PENDING","planned_risk_fraction_equity":0.001
            })
            state=build_state(
                preflight_path=pf,receipt_root=root/"live",
                now=datetime(2026,9,21,21,0,tzinfo=timezone.utc)
            )
            self.assertAlmostEqual(state["daily_realized_loss_fraction_equity"],0.002)
            self.assertAlmostEqual(state["concurrent_planned_risk_fraction_equity"],0.001)
            self.assertEqual(state["open_micro_live_positions"],1)


if __name__=="__main__":
    unittest.main()
