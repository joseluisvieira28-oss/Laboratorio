from __future__ import annotations

import json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from radar.mexc_tier2_spot_gate import validate_options_long_spot_execution

NOW=datetime(2026,9,25,0,0,0,tzinfo=timezone.utc)

class SpotGateTests(unittest.TestCase):
    def _write(self,root,name,row):
        p=Path(root)/name; p.write_text(json.dumps(row),encoding="utf-8"); return str(p)
    def _authority(self,**x):
        row={
            "status":"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY","policy_id":"TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24",
            "strategy_id":"OPTIONS-SPOTPERP-001-V2.1","exchange":"MEXC_SPOT","symbol":"BTCUSDT","direction":"LONG",
            "execution_translation":"POSITIVE_SIGNAL_TO_MEXC_SPOT_BTCUSDT_LONG_V0.1","leverage":1,"margin_mode":"SPOT_UNLEVERED",
            "max_simultaneous_positions":1,"late_chase_allowed":False,"max_late_seconds":30,
            "max_quote_order_qty_usdt":10.0,"quote_order_qty_usdt":10.0,"daily_realized_loss_kill_usdt":2.0,
            "rolling_7d_realized_loss_kill_usdt":5.0,"signal_identity":"sig","max_preflight_age_seconds":60,
            "max_risk_state_age_seconds":60,"entry_target_utc":"2026-09-25T00:00:00Z","exit_target_utc":"2026-09-26T00:00:00Z",
            "duplicate_protection_key":"dup","client_order_id":"cid"
        }; row.update(x); return row
    def _pf(self,usdt=20.0,candidate=True):
        return {"pass":True,"status":"PASS","checked_at_utc":"2026-09-25T00:00:00Z",
                "candidate_feasibility":{"OPTIONS-SPOTPERP-001-V2.1-LONG":{"pass":candidate}},
                "checks":{"orders":{"open_order_count":0},"account":{"usdt_free":usdt}}}
    def _sig(self,d="LONG"):
        return {"immutable_signal_key":"sig","strategy_id":"OPTIONS-SPOTPERP-001-V2.1","signal_direction":d,"canonical":True,"source_healthy":True,"radar_motor_healthy":True,"information_safe_time_passed":True}
    def _risk(self):
        return {"status":"PASS","as_of_utc":"2026-09-25T00:00:00Z","daily_realized_loss_usdt":0.0,"rolling_7d_realized_loss_usdt":0.0,"open_micro_live_positions":0}
    def _run(self,td,a=None,p=None,s=None,r=None):
        return validate_options_long_spot_execution(
            authority_path=self._write(td,"a.json",a or self._authority()),
            preflight_path=self._write(td,"p.json",p or self._pf()),
            signal_path=self._write(td,"s.json",s or self._sig()),
            risk_state_path=self._write(td,"r.json",r or self._risk()),
            kill_switch_path=str(Path(td)/"none"),now_utc=NOW)
    def test_long_spot_passes_at_10_usdt(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td); self.assertTrue(out["pass"],out); self.assertEqual(out["quote_order_qty_usdt"],10.0)
    def test_short_is_never_converted_to_long(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,s=self._sig("SHORT")); self.assertFalse(out["pass"]); self.assertIn("SIGNAL_DIRECTION_NOT_LONG",out["blockers"])
    def test_quote_above_10_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,a=self._authority(quote_order_qty_usdt=10.01)); self.assertFalse(out["pass"]); self.assertIn("QUOTE_ORDER_QTY_OUTSIDE_10_USDT_CAP",out["blockers"])
    def test_spot_usdt_insufficient_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,p=self._pf(usdt=5.0,candidate=False)); self.assertFalse(out["pass"]); self.assertIn("SPOT_CAPITAL_OR_PERMISSION_FEASIBILITY_NOT_PASS",out["blockers"])
    def test_24h_hold_required(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,a=self._authority(exit_target_utc="2026-09-27T00:00:00Z")); self.assertFalse(out["pass"]); self.assertIn("EXIT_TARGET_NOT_EXACTLY_PLUS_24H",out["blockers"])

if __name__=="__main__": unittest.main()
