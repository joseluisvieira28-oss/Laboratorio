"""Public MEXC futures contract/quote validation — all mocked, no orders."""
from copy import deepcopy
from decimal import Decimal
from unittest import TestCase
import time
from engine.three_convex_v06.market_gate import risk_one_contract, MarketGateHalt

def spec(symbol="SOL_USDT",size="0.1"):
    return {
        "symbol":symbol,"apiAllowed":True,"settleCoin":"USDT",
        "quoteCoin":"USDT","positionOpenType":3,"minLeverage":1,
        "maxLeverage":125,"countryConfigContractMaxLeverage":0,
        "minVol":1,"maxVol":1000,"volUnit":1,
        "priceUnit":"0.01","contractSize":size
    }

def ticker(symbol="SOL_USDT",ask="100.01",bid="100.00",at=None):
    return {
        "symbol":symbol,"bid1":bid,"ask1":ask,"fairPrice":"100.02",
        "timestamp":int(time.time_ns()//1_000_000) if at is None else at
    }

class MarketGateTests(TestCase):
    def test_clean_one_contract_quote_model(self):
        p=risk_one_contract(spec(),ticker(),"SOL_USDT",
                            int(time.time_ns()//1_000_000))
        self.assertTrue(p["api_trading_contract_allowed"])
        self.assertTrue(p["one_contract_model_risk_budget_pass"])
        self.assertEqual(p["contract_size_base"],"0.1")
        self.assertEqual(p["actual_order_execution_authority"],"NONE")
        self.assertFalse(p["real_liquidation_mark_buffer_verified"])

    def test_bnb_one_contract(self):
        a=spec("BNB_USDT","0.01")
        b=ticker("BNB_USDT","740","739.9")
        b["fairPrice"]="741"
        p=risk_one_contract(a,b,"BNB_USDT",int(time.time_ns()//1_000_000))
        self.assertTrue(p["one_contract_model_risk_budget_pass"])

    def test_stop_tick_rounddown_can_exceed_risk_budget(self):
        a=spec(size="0.1")
        a["priceUnit"]="1"
        q=ticker(ask="125.41",bid="125.2")
        q["fairPrice"]="125.42"
        p=risk_one_contract(a,q,"SOL_USDT",
                            int(time.time_ns()//1_000_000))
        self.assertFalse(p["one_contract_model_risk_budget_pass"])

    def test_api_allowed_required(self):
        a=spec();a.pop("apiAllowed")
        with self.assertRaisesRegex(MarketGateHalt,"API_TRADING_NOT"):
            risk_one_contract(a,ticker(),"SOL_USDT",int(time.time_ns()//1_000_000))

    def test_isolated_required(self):
        a=spec();a["positionOpenType"]=2
        with self.assertRaisesRegex(MarketGateHalt,"ISOLATED_MARGIN"):
            risk_one_contract(a,ticker(),"SOL_USDT",int(time.time_ns()//1_000_000))

    def test_country_ten_x_cap(self):
        a=spec();a["countryConfigContractMaxLeverage"]=5
        with self.assertRaisesRegex(MarketGateHalt,"TEN_X"):
            risk_one_contract(a,ticker(),"SOL_USDT",int(time.time_ns()//1_000_000))

    def test_requires_one_contract_allowed(self):
        a=spec();a["minVol"]=2
        with self.assertRaisesRegex(MarketGateHalt,"ONE_CONTRACT"):
            risk_one_contract(a,ticker(),"SOL_USDT",int(time.time_ns()//1_000_000))

    def test_missing_actual_contract_size_fails(self):
        a=spec();a.pop("contractSize")
        with self.assertRaisesRegex(MarketGateHalt,"MISSING_CONTRACTSIZE"):
            risk_one_contract(a,ticker(),"SOL_USDT",int(time.time_ns()//1_000_000))

    def test_stale_or_future_market_fails(self):
        t=int(time.time_ns()//1_000_000)
        with self.assertRaisesRegex(MarketGateHalt,"PUBLIC_TICKER_STALE"):
            risk_one_contract(spec(),ticker(at=t-30_000),"SOL_USDT",t)
        with self.assertRaisesRegex(MarketGateHalt,"PUBLIC_TICKER_STALE"):
            risk_one_contract(spec(),ticker(at=t+1_000),"SOL_USDT",t)

    def test_bad_bbo_crossed(self):
        t=ticker(ask="99",bid="100")
        with self.assertRaisesRegex(MarketGateHalt,"CROSSED"):
            risk_one_contract(spec(),t,"SOL_USDT",int(time.time_ns()//1_000_000))

    def test_invalid_mark_trigger_geometry(self):
        t=ticker(ask="100",bid="99")
        t["fairPrice"]="90"
        with self.assertRaisesRegex(MarketGateHalt,"MARK_TRIGGER"):
            risk_one_contract(spec(),t,"SOL_USDT",int(time.time_ns()//1_000_000))

    def test_invalid_symbol_mismatch(self):
        with self.assertRaisesRegex(MarketGateHalt,"SYMBOL_MISMATCH"):
            risk_one_contract(spec(),ticker("BNB_USDT"),"SOL_USDT",
                              int(time.time_ns()//1_000_000))
