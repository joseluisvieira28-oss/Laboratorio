from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from radar.mexc_tier2_live_gate import validate_tier2_options_short_execution

NOW=datetime(2026,9,25,0,0,0,tzinfo=timezone.utc)

class Tier2GateTests(unittest.TestCase):
    def _write(self,root,name,payload):
        p=Path(root)/name
        p.write_text(json.dumps(payload),encoding="utf-8")
        return str(p)

    def _authority(self,**overrides):
        row={
            "status":"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY",
            "policy_id":"TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24",
            "strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
            "exchange":"MEXC","contract":"BTC_USDT","direction":"SHORT",
            "execution_translation":"NEGATIVE_SIGNAL_TO_MEXC_USDT_PERPETUAL_SHORT_V0.1",
            "margin_mode":"ISOLATED","leverage":1,"auto_margin_add":"OFF_REQUIRED",
            "implementation_mapping_review_status":"ACCEPTED_PRE_ORDER",
            "order_type":"MARKET","position_mode":1,
            "api_place_order_path":"/api/v1/private/order/create",
            "max_simultaneous_positions":1,"late_chase_allowed":False,
            "max_notional_usdt":10.0,"daily_realized_loss_kill_usdt":2.0,
            "rolling_7d_realized_loss_kill_usdt":5.0,
            "signal_identity":"sig","max_preflight_age_seconds":60,
            "max_risk_state_age_seconds":60,
            "entry_target_utc":"2026-09-25T00:00:00Z",
            "exit_target_utc":"2026-09-26T00:00:00Z",
            "max_late_seconds":2,"duplicate_protection_key":"dup",
            "friction_budget_bps":20.0,"projected_round_trip_bps":18.0,
            "reference_entry_price":85000.0,"volume_contracts":1
        }
        row.update(overrides)
        return row

    def _preflight(self,min_notional=8.5,contract_size=0.0001,price=85000.0):
        return {
            "pass":True,"status":"PASS","checked_at_utc":"2026-09-25T00:00:00Z",
            "checks":{
                "positions":{"open_position_count":0},"orders":{"open_order_count":0},
                "clock":{"pass":True},
                "contract":{
                    "minimum_executable_notional_estimate_usdt":min_notional,
                    "contract_size_base":contract_size,"reference_price":price,
                    "min_contract_volume":1.0,"contract_volume_step":1.0
                },
                "account":{"equity_usdt":112.3763},
                "fees":{"effective_taker_fee_bps_for_execution_model":8.0}
            }
        }

    def _signal(self,direction="SHORT"):
        return {
            "immutable_signal_key":"sig","strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
            "signal_direction":direction,"canonical":True,"source_healthy":True,
            "radar_motor_healthy":True,"information_safe_time_passed":True
        }

    def _risk(self,day=0.0,week=0.0,open_positions=0):
        return {
            "status":"PASS","as_of_utc":"2026-09-25T00:00:00Z",
            "daily_realized_loss_usdt":day,"rolling_7d_realized_loss_usdt":week,
            "open_micro_live_positions":open_positions
        }

    def _run(self,td,a=None,p=None,s=None,r=None):
        ap=self._write(td,"a.json",a or self._authority())
        pp=self._write(td,"p.json",p or self._preflight())
        sp=self._write(td,"s.json",s or self._signal())
        rp=self._write(td,"r.json",r or self._risk())
        return validate_tier2_options_short_execution(
            authority_path=ap,preflight_path=pp,signal_path=sp,risk_state_path=rp,
            kill_switch_path=str(Path(td)/"none"),now_utc=NOW
        )

    def test_112_usdt_account_can_pass_venue_minimum_under_10_usdt_cap(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td)
            self.assertTrue(out["pass"],out)
            self.assertAlmostEqual(out["requested_notional_usdt"],8.5)
            self.assertEqual(out["maximum_authorized_notional_usdt"],10.0)

    def test_old_point_one_percent_budget_is_not_used(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td)
            self.assertNotIn("VENUE_MINIMUM_EXCEEDS_AUTHORITY_RISK_BUDGET",out["blockers"])
            self.assertTrue(out["pass"],out)

    def test_above_10_usdt_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            pf=self._preflight(min_notional=10.5,contract_size=0.0001,price=105000.0)
            out=self._run(td,p=pf,a=self._authority(reference_entry_price=105000.0))
            self.assertFalse(out["pass"])
            self.assertIn("VENUE_MINIMUM_EXCEEDS_10_USDT_CAP",out["blockers"])
            self.assertIn("REQUESTED_NOTIONAL_EXCEEDS_10_USDT_CAP",out["blockers"])

    def test_long_signal_does_not_get_converted_to_short(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,s=self._signal("LONG"))
            self.assertFalse(out["pass"])
            self.assertIn("SIGNAL_DIRECTION_NOT_SHORT",out["blockers"])

    def test_daily_2_usdt_kill_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,r=self._risk(day=2.0))
            self.assertFalse(out["pass"])
            self.assertIn("DAILY_HALT_ACTIVE",out["blockers"])

    def test_weekly_5_usdt_kill_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,r=self._risk(week=5.0))
            self.assertFalse(out["pass"])
            self.assertIn("WEEKLY_HALT_ACTIVE",out["blockers"])

    def test_open_position_blocks_second_trade(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,r=self._risk(open_positions=1))
            self.assertFalse(out["pass"])
            self.assertIn("MICRO_LIVE_POSITION_ALREADY_OPEN",out["blockers"])

    def test_exit_must_be_exactly_24h(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,a=self._authority(exit_target_utc="2026-09-27T00:00:00Z"))
            self.assertFalse(out["pass"])
            self.assertIn("EXIT_TARGET_NOT_EXACTLY_PLUS_24H",out["blockers"])

    def test_template_never_authorizes(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,a=self._authority(status="TEMPLATE_NOT_AUTHORITY"))
            self.assertFalse(out["pass"])
            self.assertIn("ACTIVE_CANDIDATE_SPECIFIC_AUTHORITY_ABSENT",out["blockers"])

if __name__=="__main__":
    unittest.main()
