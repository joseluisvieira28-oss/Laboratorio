from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from radar.options_v21_spot_live_gate import validate_options_spot_long


NOW=datetime(2026,9,25,0,0,1,tzinfo=timezone.utc)


class OptionsSpotGateTests(unittest.TestCase):
    def _write(self,root,name,row):
        p=Path(root)/name
        p.write_text(json.dumps(row),encoding="utf-8")
        return str(p)

    def _authority(self,**x):
        row={
            "status":"ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY",
            "micro_live_policy_id":"TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24",
            "strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
            "exchange":"MEXC","market":"SPOT","symbol":"BTCUSDT","direction":"LONG",
            "leverage":1,"leverage_above_one":False,"order_type":"MARKET",
            "max_simultaneous_positions":1,
            "signal_identity":"sig-2026-09-24",
            "weight":0.8,
            "base_micro_live_notional_usdt":10.0,
            "quote_order_qty_usdt":8.0,
            "maximum_notional_usdt_equivalent":10.0,
            "maximum_total_account_exposure_usdt_equivalent":10.0,
            "daily_realized_loss_kill_usdt":2.0,
            "rolling_7d_realized_loss_kill_usdt":5.0,
            "entry_target_utc":"2026-09-25T00:00:00Z",
            "exit_target_utc":"2026-09-26T00:00:00Z",
            "max_late_seconds":2,
            "max_preflight_age_seconds":60,
            "max_risk_state_age_seconds":60,
            "max_order_test_age_seconds":60,
            "new_client_order_id":"optlong-test",
            "duplicate_protection_key":"dup-sig",
        }
        row.update(x); return row

    def _signal(self,**x):
        row={
            "immutable_signal_key":"sig-2026-09-24",
            "strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
            "signal_date":"2026-09-24",
            "signal_direction":"LONG","position":1,"weight":0.8,
            "canonical":True,"source_healthy":True,"radar_motor_healthy":True,
        }
        row.update(x); return row

    def _preflight(self,**x):
        row={
            "pass":True,"status":"PASS","checked_at_utc":"2026-09-25T00:00:00Z",
            "checks":{
                "orders":{"open_order_count":0},
                "symbol":{"pass":True},
                "account":{"usdt_free":50.0}
            }
        }
        row.update(x); return row

    def _risk(self,**x):
        row={
            "status":"PASS","as_of_utc":"2026-09-25T00:00:00Z",
            "daily_realized_loss_usdt":0.0,"weekly_realized_loss_usdt":0.0,
            "concurrent_planned_notional_usdt":0.0,"open_micro_live_positions":0,
        }
        row.update(x); return row

    def _ordertest(self,**x):
        row={
            "status":"PASS","checked_at_utc":"2026-09-25T00:00:00Z",
            "symbol":"BTCUSDT","side":"BUY","quote_order_qty_usdt":8.0,
            "client_order_id":"optlong-test","matching_engine_order_created":False,
        }
        row.update(x); return row

    def _run(self,td,a=None,s=None,p=None,r=None,t=None,now=NOW):
        return validate_options_spot_long(
            authority_path=self._write(td,"a.json",a or self._authority()),
            signal_path=self._write(td,"s.json",s or self._signal()),
            preflight_path=self._write(td,"p.json",p or self._preflight()),
            risk_state_path=self._write(td,"r.json",r or self._risk()),
            order_test_path=self._write(td,"t.json",t or self._ordertest()),
            kill_switch_path=str(Path(td)/"none"),
            now_utc=now,
        )

    def test_exact_long_lane_passes(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td)
            self.assertTrue(out["pass"],out)
            self.assertEqual(out["quote_order_qty_usdt"],8.0)

    def test_template_cannot_trade(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,a=self._authority(status="TEMPLATE_NOT_AUTHORITY"))
            self.assertFalse(out["pass"])
            self.assertIn("ACTIVE_CANDIDATE_SPECIFIC_AUTHORITY_ABSENT",out["blockers"])

    def test_weight_cannot_be_rounded_up(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,a=self._authority(quote_order_qty_usdt=8.1))
            self.assertFalse(out["pass"])
            self.assertIn("QUOTE_ORDER_QTY_NOT_EXACT_SCIENTIFIC_WEIGHT_X_10_USDT",out["blockers"])

    def test_short_signal_cannot_enter_spot_long_lane(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,s=self._signal(signal_direction="SHORT",position=-1))
            self.assertFalse(out["pass"])
            self.assertIn("SIGNAL_NOT_LONG",out["blockers"])

    def test_order_test_must_match_exact_qty(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,t=self._ordertest(quote_order_qty_usdt=7.9))
            self.assertFalse(out["pass"])
            self.assertIn("ORDER_TEST_QTY_MISMATCH",out["blockers"])

    def test_daily_loss_kill_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            out=self._run(td,r=self._risk(daily_realized_loss_usdt=2.0))
            self.assertFalse(out["pass"])
            self.assertIn("DAILY_HALT_ACTIVE",out["blockers"])

    def test_entry_after_two_seconds_is_no_chase(self):
        with tempfile.TemporaryDirectory() as td:
            late=datetime(2026,9,25,0,0,3,tzinfo=timezone.utc)
            out=self._run(td,now=late)
            self.assertFalse(out["pass"])
            self.assertIn("STALE_SIGNAL_NO_CHASE",out["blockers"])


if __name__=="__main__":
    unittest.main()
