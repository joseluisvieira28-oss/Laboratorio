import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from engine.three_convex_v08.order_ledger import DurableLedger,SignalIntent
from engine.three_convex_v08.readiness import audit

def account():
    return {"status":"AUTHENTICATED_ACCOUNT_AND_PUBLIC_MARKET_READS_NO_LIVE_GO",
            "broker_account_flat_observed_once":True,"position_mode":"HEDGE",
            "usdt_equity":"111.04","usdt_available":"111.04",
            "open_positions_count":0,"open_orders_count_all_pages":0,
            "open_stops_count":0,
            "current_public_contract_and_one_lot_models":{
                "SOL_USDT":{"one_contract_model_risk_budget_pass":True},
                "BNB_USDT":{"one_contract_model_risk_budget_pass":True}}}

class Tests(unittest.TestCase):
    def setUp(self):self.t=TemporaryDirectory();self.d=DurableLedger(self.t.name)
    def tearDown(self):self.d.close();self.t.cleanup()
    def check(self,a):
        with patch("engine.three_convex_v08.readiness.inspect",return_value=a):
            return audit(account_client=None,ledger=self.d)
    def test_good_market_still_no_live(self):
        x=self.check(account())
        self.assertTrue(x["broker_authenticated_read_ok"])
        self.assertEqual(x["status"],"NO_LIVE_GO")
        self.assertEqual(x["order_posts_sent"],0)
    def test_open_position_blocks(self):
        a=account();a["broker_account_flat_observed_once"]=False
        self.assertIn("ACCOUNT_NOT_PROVEN_FLAT_AND_ORDER_FREE",self.check(a)["blockers"])
    def test_unknown_api_blocks(self):
        self.assertFalse(self.check({"status":"BROKER_UNAVAILABLE"})["broker_authenticated_read_ok"])
    def test_symbol_budget_blocks(self):
        a=account();a["current_public_contract_and_one_lot_models"]["SOL_USDT"]["one_contract_model_risk_budget_pass"]=False
        self.assertIn("CURRENT_SOL_BNB_ONE_CONTRACT_RISK_GATE_NOT_PROVEN",self.check(a)["blockers"])
    def test_wrong_mode_blocks(self):
        a=account();a["position_mode"]="ONE_WAY"
        self.assertIn("HEDGE_POSITION_MODE_NOT_PROVEN",self.check(a)["blockers"])
    def test_inflight_blocks_restart(self):
        s=SignalIntent("SOL_CONVEX_NATIVE_5M","SOL_CONVEX_NATIVE_5M:1000000",1000000,1005000)
        self.d.reserve(s)
        self.assertIn("PENDING_ORDER_INTENT_MUST_RECONCILE_BEFORE_RESTART",self.check(account())["blockers"])
