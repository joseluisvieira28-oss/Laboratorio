"""Offline fixture tests of authenticated account interpretation. No network."""
import unittest
import time
from copy import deepcopy
from engine.three_convex_v06.test_market_gate import spec, ticker

from engine.three_convex_v06.status_app import (
    inspect, fee_summary, usdt_balance, strict_order_pages, ReadonlyGate,
)

FEE = dict(
    originalMakerFee=0,realMakerFee=0,originalTakerFee=0,
    realTakerFee=0, minLeverage=1, maxLeverage=50,
    feeRateMode="NORMAL", tieredFeeRates=[], leverageFeeRates=[]
)
ASSETS = [{"currency":"USDT","equity":101.25,"availableBalance":101.20},
          {"currency":"BTC","equity":1,"availableBalance":1}]


class FakeClient:
    def __init__(self):
        self.positions=[]
        self.orders={"resultList":[],"totalPage":1,"totalCount":0}
        self.stops=[]
        self.mode=1
        self.assets=deepcopy(ASSETS)
        self.fees=deepcopy(FEE)
        self.extra_pages={}
        self.read_paths=[]

    def open_positions(self): return self.positions
    def open_orders(self): return self.orders
    def open_stops(self): return self.stops
    def position_mode(self): return self.mode
    def account_assets(self): return self.assets
    def account_fees(self,symbol): return self.fees
    def contract_metadata(self,symbol):
        return spec(symbol, "0.1" if symbol=="SOL_USDT" else "0.01")
    def public_ticker(self,symbol):
        q=ticker(symbol, "100" if symbol=="SOL_USDT" else "740",
                 "99.99" if symbol=="SOL_USDT" else "739.99")
        if symbol=="BNB_USDT":
            q["fairPrice"]="741"
        return q
    def _exchange(self,method,path,params):
        self.read_paths.append((method,path,params))
        return self.extra_pages[params["page_num"]]


class TestAuthInterpretation(unittest.TestCase):
    def test_actual_fields_parsed_without_secrets(self):
        res=inspect(FakeClient())
        self.assertEqual(res["status"],"AUTHENTICATED_ACCOUNT_AND_PUBLIC_MARKET_READS_NO_LIVE_GO")
        self.assertEqual(res["usdt_equity"],"101.25")
        self.assertEqual(res["usdt_available"],"101.2")
        self.assertEqual(res["position_mode"],"HEDGE")
        self.assertTrue(res["broker_account_flat_observed_once"])
        self.assertEqual(res["fees_by_symbol"]["SOL_USDT"]["api_fee_model_taker_bps"],"8.0000")
        self.assertTrue(res["fees_by_symbol"]["BNB_USDT"]["ten_x_eligible_from_reported_api_fee_bounds"])
        self.assertFalse(res["broker_order_execution_path_armed"])
        self.assertTrue(res["both_public_one_lot_risk_budgets_pass"])
        self.assertTrue(res["exchange_contract_tick_lot_verified"])

    def test_real_fee_above_floor_kept(self):
        d=deepcopy(FEE)
        d["realTakerFee"]="0.0012"
        self.assertEqual(fee_summary(d)["api_fee_model_taker_bps"],"12.0000")

    def test_fee_floor_applied_under_promo(self):
        d=deepcopy(FEE)
        self.assertEqual(fee_summary(d)["api_fee_model_maker_bps"],"6.0000")
        self.assertEqual(fee_summary(d)["api_fee_model_taker_bps"],"8.0000")

    def test_fee_tiers_conservative_max(self):
        d=deepcopy(FEE)
        d["tieredFeeRates"]=[{"takerFeeRate":0.0015,"makerFeeRate":0.0008}]
        self.assertEqual(fee_summary(d)["api_fee_model_taker_bps"],"15.0000")

    def test_leverage_not_eligible_is_not_pass(self):
        d=deepcopy(FEE); d["maxLeverage"]=5
        self.assertFalse(fee_summary(d)["ten_x_eligible_from_reported_api_fee_bounds"])

    def test_leverage_missing_explicit_unknown(self):
        d=deepcopy(FEE); d.pop("maxLeverage")
        self.assertEqual(fee_summary(d)["ten_x_eligible_from_reported_api_fee_bounds"],
                         "UNKNOWN_API_LIMITS_MISSING")

    def test_missing_usdt_equity_fail_closed(self):
        c=FakeClient(); c.assets=[{"currency":"USDT","availableBalance":100}]
        self.assertEqual(inspect(c)["status"],"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED")

    def test_null_positions_never_zero(self):
        c=FakeClient(); c.positions=None
        self.assertEqual(inspect(c)["status"],"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED")

    def test_none_orders_never_zero(self):
        c=FakeClient(); c.orders=None
        self.assertEqual(inspect(c)["status"],"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED")

    def test_unknown_mode_never_hedge(self):
        c=FakeClient(); c.mode=3
        self.assertEqual(inspect(c)["status"],"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED")

    def test_oneway_mode_reported_and_not_hedge(self):
        c=FakeClient(); c.mode=2
        self.assertEqual(inspect(c)["position_mode"],"ONE_WAY")

    def test_paginated_orders_are_counted(self):
        c=FakeClient()
        c.orders={"resultList":[{"id":1}],"totalPage":2,"totalCount":2}
        c.extra_pages[2]={"resultList":[{"id":2}]}
        res=inspect(c)
        self.assertEqual(res["open_orders_count_all_pages"],2)
        self.assertEqual(res["open_order_pages_checked"],2)
        self.assertFalse(res["broker_account_flat_observed_once"])
        self.assertEqual(c.read_paths[0][0],"GET")

    def test_missing_pagination_on_full_page_is_blocked(self):
        c=FakeClient(); c.orders={"resultList":[{}]*100}
        self.assertEqual(inspect(c)["status"],"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED")

    def test_inconsistent_total_rejected(self):
        c=FakeClient(); c.orders={"resultList":[],"totalPage":1,"totalCount":5}
        self.assertEqual(inspect(c)["status"],"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED")

    def test_stop_presence_never_clean(self):
        c=FakeClient(); c.stops=[{"id":"x"}]
        self.assertFalse(inspect(c)["broker_account_flat_observed_once"])

    def test_fee_shape_invalid_closed(self):
        c=FakeClient(); c.fees={}
        self.assertEqual(inspect(c)["status"],"ACCOUNT_DATA_INSUFFICIENT_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
