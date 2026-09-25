from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from scripts.mexc_tier2_risk_state import build_state

class Tier2RiskStateTests(unittest.TestCase):
    def _write(self,p,payload):
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(payload),encoding="utf-8")

    def _preflight(self,root):
        pf=root/"pf.json"
        self._write(pf,{"pass":True,"checks":{"account":{"equity_usdt":112.3763},"positions":{"open_position_count":0}}})
        return pf

    def test_clean_state_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            state=build_state(preflight_path=self._preflight(root),receipt_root=root/"live",now=datetime(2026,9,25,6,0,tzinfo=timezone.utc))
            self.assertEqual(state["status"],"PASS")
            self.assertEqual(state["policy"]["max_notional_usdt"],10.0)
            self.assertEqual(state["daily_realized_loss_usdt"],0)

    def test_daily_absolute_kill(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); pf=self._preflight(root)
            self._write(root/"live"/"a"/"POST_TRADE_RECONCILIATION.json",{"closed_at_utc":"2026-09-25T05:00:00Z","realized_net_pnl_usdt":-2.0})
            state=build_state(preflight_path=pf,receipt_root=root/"live",now=datetime(2026,9,25,6,0,tzinfo=timezone.utc))
            self.assertEqual(state["status"],"FAIL_CLOSED")
            self.assertIn("DAILY_2_USDT_KILL_ACTIVE",state["blockers"])

    def test_rolling_7d_absolute_kill(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); pf=self._preflight(root)
            self._write(root/"live"/"a"/"POST_TRADE_RECONCILIATION.json",{"closed_at_utc":"2026-09-20T05:00:00Z","realized_net_pnl_usdt":-5.0})
            state=build_state(preflight_path=pf,receipt_root=root/"live",now=datetime(2026,9,25,6,0,tzinfo=timezone.utc))
            self.assertEqual(state["status"],"FAIL_CLOSED")
            self.assertIn("ROLLING_7D_5_USDT_KILL_ACTIVE",state["blockers"])

    def test_active_receipt_counts_as_open_position(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); pf=self._preflight(root)
            self._write(root/"live"/"a"/"ACTIVE_TRADE_STATE.json",{"state":"EXIT_PENDING"})
            state=build_state(preflight_path=pf,receipt_root=root/"live",now=datetime(2026,9,25,6,0,tzinfo=timezone.utc))
            self.assertEqual(state["open_micro_live_positions"],1)
            self.assertEqual(state["status"],"PASS")

if __name__=="__main__":
    unittest.main()
