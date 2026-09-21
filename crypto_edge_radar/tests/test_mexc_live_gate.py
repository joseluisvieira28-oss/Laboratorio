from __future__ import annotations
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from radar.mexc_live_gate import validate_futures_short_execution


class GateTests(unittest.TestCase):
    def _write(self,root,name,payload):
        p=Path(root)/name
        p.write_text(json.dumps(payload),encoding="utf-8")
        return str(p)

    def test_template_never_authorizes_order(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._write(td,"a.json",{
                "status":"TEMPLATE_NOT_AUTHORITY","strategy_id":"ETF-CME-INSTFLOW-001",
                "exchange":"MEXC","contract":"BTC_USDT","direction":"SHORT",
                "margin_mode":"ISOLATED","leverage":1,"auto_margin_add":"OFF_REQUIRED",
                "order_type":"MARKET","late_chase_allowed":False,"max_simultaneous_positions":1,
                "signal_identity":"sig","max_initial_isolated_margin_fraction_of_equity":0.001,
                "entry_target_utc":"2026-09-21T21:00:00Z","max_late_seconds":2,
                "duplicate_protection_key":"x"
            })
            p=self._write(td,"p.json",{"pass":True,"status":"PASS","checks":{
                "positions":{"open_position_count":0},"orders":{"open_order_count":0},
                "clock":{"pass":True},"contract":{"minimum_executable_notional_estimate_usdt":8.6},
                "account":{"equity_usdt":10000},
                "fees":{"effective_taker_fee_bps_for_execution_model":8.0}
            }})
            s=self._write(td,"s.json",{
                "immutable_signal_key":"sig","strategy_id":"ETF-CME-INSTFLOW-001",
                "signal_direction":"SHORT","canonical":True,"source_healthy":True,
                "radar_motor_healthy":True
            })
            out=validate_futures_short_execution(
                authority_path=a,preflight_path=p,signal_path=s,
                kill_switch_path=str(Path(td)/"none"),
                now_utc=datetime(2026,9,21,21,0,0,tzinfo=timezone.utc)
            )
            self.assertFalse(out["pass"])
            self.assertIn("ACTIVE_CANDIDATE_SPECIFIC_AUTHORITY_ABSENT",out["blockers"])

    def test_venue_minimum_above_frozen_budget_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._write(td,"a.json",{
                "status":"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY",
                "strategy_id":"ETF-CME-INSTFLOW-001","exchange":"MEXC","contract":"BTC_USDT",
                "direction":"SHORT","margin_mode":"ISOLATED","leverage":1,
                "auto_margin_add":"OFF_REQUIRED","order_type":"MARKET",
                "late_chase_allowed":False,"max_simultaneous_positions":1,
                "signal_identity":"sig","max_initial_isolated_margin_fraction_of_equity":0.001,
                "entry_target_utc":"2026-09-21T21:00:00Z","max_late_seconds":2,
                "duplicate_protection_key":"dup"
            })
            p=self._write(td,"p.json",{"pass":True,"status":"PASS","checks":{
                "positions":{"open_position_count":0},"orders":{"open_order_count":0},
                "clock":{"pass":True},"contract":{"minimum_executable_notional_estimate_usdt":8.6},
                "account":{"equity_usdt":112.3763},
                "fees":{"effective_taker_fee_bps_for_execution_model":8.0}
            }})
            s=self._write(td,"s.json",{
                "immutable_signal_key":"sig","strategy_id":"ETF-CME-INSTFLOW-001",
                "signal_direction":"SHORT","canonical":True,"source_healthy":True,
                "radar_motor_healthy":True
            })
            out=validate_futures_short_execution(
                authority_path=a,preflight_path=p,signal_path=s,
                kill_switch_path=str(Path(td)/"none"),
                now_utc=datetime(2026,9,21,21,0,0,tzinfo=timezone.utc)
            )
            self.assertFalse(out["pass"])
            self.assertIn("VENUE_MINIMUM_EXCEEDS_AUTHORITY_RISK_BUDGET",out["blockers"])


if __name__=="__main__":
    unittest.main()
