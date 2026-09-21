from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from radar.mexc_live_gate import validate_futures_short_execution


NOW=datetime(2026,9,23,0,0,0,tzinfo=timezone.utc)


class GateTests(unittest.TestCase):
    def _write(self,root,name,payload):
        p=Path(root)/name
        p.write_text(json.dumps(payload),encoding="utf-8")
        return str(p)

    def _authority(self,**overrides):
        row={
            "status":"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY",
            "strategy_id":"ETF-CME-INSTFLOW-001",
            "exchange":"MEXC",
            "contract":"BTC_USDT",
            "direction":"SHORT",
            "margin_mode":"ISOLATED",
            "leverage":1,
            "auto_margin_add":"OFF_REQUIRED",
            "auto_margin_enforcement_mode":"POST_FILL_IMMEDIATE_OFF__EMERGENCY_FLATTEN_IF_NOT_VERIFIED",
            "implementation_mapping_review_status":"ACCEPTED_PRE_ORDER",
            "order_type":"MARKET",
            "position_mode":1,
            "late_chase_allowed":False,
            "max_simultaneous_positions":1,
            "api_place_order_path":"/api/v1/private/order/create",
            "signal_identity":"sig",
            "max_initial_isolated_margin_fraction_of_equity":0.001,
            "max_concurrent_planned_risk_fraction_equity":0.003,
            "daily_stop_fraction_equity":0.003,
            "weekly_stop_fraction_equity":0.0075,
            "entry_target_utc":"2026-09-23T00:00:00Z",
            "exit_target_utc":"2026-09-30T00:00:00Z",
            "max_late_seconds":2,
            "max_preflight_age_seconds":60,
            "max_risk_state_age_seconds":60,
            "duplicate_protection_key":"dup",
            "friction_budget_bps":20.0,
            "projected_round_trip_bps":18.0,
            "reference_entry_price":100000.0,
            "volume_contracts":1,
        }
        row.update(overrides)
        return row

    def _preflight(self,*,equity=10000,min_notional=10,contract_size=0.0001,candidate_pass=True):
        return {
            "pass":True,"status":"PASS","checked_at_utc":"2026-09-23T00:00:00Z",
            "candidate_feasibility":{
                "ETF-CME-INSTFLOW-001":{
                    "pass":candidate_pass,
                    "status":"PASS" if candidate_pass else "BLOCKED",
                    "blockers":[] if candidate_pass else ["ETF_CME_VENUE_MIN_NOTIONAL_EXCEEDS_FROZEN_VALIDATION_BUDGET"]
                }
            },
            "checks":{
                "positions":{"open_position_count":0},
                "orders":{"open_order_count":0},
                "clock":{"pass":True},
                "contract":{
                    "minimum_executable_notional_estimate_usdt":min_notional,
                    "contract_size_base":contract_size,
                    "reference_price":100000.0,
                    "min_contract_volume":1.0,
                    "contract_volume_step":1.0
                },
                "account":{"equity_usdt":equity},
                "fees":{"effective_taker_fee_bps_for_execution_model":8.0}
            }
        }

    def _signal(self):
        return {
            "immutable_signal_key":"sig",
            "strategy_id":"ETF-CME-INSTFLOW-001",
            "signal_direction":"SHORT",
            "canonical":True,
            "source_healthy":True,
            "radar_motor_healthy":True,
            "information_safe_time_passed":True
        }

    def _risk(self):
        return {
            "status":"PASS",
            "as_of_utc":"2026-09-23T00:00:00Z",
            "daily_realized_loss_fraction_equity":0.0,
            "weekly_realized_loss_fraction_equity":0.0,
            "concurrent_planned_risk_fraction_equity":0.0,
            "open_micro_live_positions":0
        }

    def _run(self,td,authority,preflight=None,signal=None,risk=None):
        a=self._write(td,"a.json",authority)
        p=self._write(td,"p.json",preflight or self._preflight())
        s=self._write(td,"s.json",signal or self._signal())
        r=self._write(td,"r.json",risk or self._risk())
        return validate_futures_short_execution(
            authority_path=a,preflight_path=p,signal_path=s,risk_state_path=r,
            kill_switch_path=str(Path(td)/"none"),now_utc=NOW
        )

    def test_template_never_authorizes_order(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,self._authority(status="TEMPLATE_NOT_AUTHORITY"))
            self.assertFalse(out["pass"])
            self.assertIn("ACTIVE_CANDIDATE_SPECIFIC_AUTHORITY_ABSENT",out["blockers"])

    def test_venue_minimum_above_frozen_budget_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            pf=self._preflight(equity=112.3763,min_notional=8.6,candidate_pass=False)
            out=self._run(td,self._authority(),preflight=pf)
            self.assertFalse(out["pass"])
            self.assertIn("CANDIDATE_CAPITAL_FEASIBILITY_NOT_PASS",out["blockers"])
            self.assertIn("VENUE_MINIMUM_EXCEEDS_AUTHORITY_RISK_BUDGET",out["blockers"])

    def test_current_api_schema_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,self._authority(api_place_order_path="/api/v1/private/order/submit"))
            self.assertFalse(out["pass"])
            self.assertIn("AUTHORITY_API_SCHEMA_NOT_CURRENT",out["blockers"])

    def test_valid_frozen_short_gate_can_reach_trade_ready_without_order(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,self._authority())
            self.assertTrue(out["pass"],out)
            self.assertEqual(out["blockers"],[])
            self.assertEqual(out["api_place_order_path"],"/api/v1/private/order/create")
            self.assertEqual(out["requested_notional_usdt"],10.0)
            self.assertEqual(out["maximum_authorized_notional_usdt"],10.0)

    def test_daily_halt_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            risk=self._risk()
            risk["daily_realized_loss_fraction_equity"]=0.003
            out=self._run(td,self._authority(),risk=risk)
            self.assertFalse(out["pass"])
            self.assertIn("DAILY_HALT_ACTIVE",out["blockers"])

    def test_exit_target_must_be_exactly_plus_seven_days(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,self._authority(exit_target_utc="2026-09-29T23:59:59Z"))
            self.assertFalse(out["pass"])
            self.assertIn("EXIT_TARGET_NOT_EXACTLY_PLUS_7D",out["blockers"])


if __name__=="__main__":
    unittest.main()
