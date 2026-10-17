import json
import unittest
from research.convex_okx_l2_stop_v02.okx_source_gate import classify,inputs,epoch_ms
from research.convex_okx_l2_stop_v02.stop_receipt_gate import (
    StopHalt,initial,prepare,confirm_readback,uncertain_timeout,recover
)

class OKXTests(unittest.TestCase):
    def test_exact_six_frozen(self):
        self.assertEqual(len(list(inputs())),6)
    def test_http_200_empty_is_not_pass(self):
        x=classify("SOL-USDT","4","daily","2024-06-03",200,b'{"code":"0","data":[]}')
        self.assertEqual(x["status"],"SOURCE_BLOCKED")
    def test_nonzero_exchange_api_code_is_not_pass(self):
        x=classify("SOL-USDT","4","daily","2024-06-03",200,b'{"code":"50010","data":[{}]}')
        self.assertEqual(x["status"],"SOURCE_BLOCKED")
    def test_source_catalogue_nonempty_not_market_verified(self):
        x=classify("SOL-USDT","4","daily","2024-06-03",200,
            b'{"code":"0","data":[{"url":"https://data.example.com/f.zip?secret=redacted"}]}')
        self.assertEqual(x["status"],"CATALOGUE_NONEMPTY_NOT_DATA_VERIFIED")
        self.assertEqual(x["link_hostnames"],["data.example.com"])
        self.assertNotIn("secret",json.dumps(x))
    def test_only_registered_queries(self):
        with self.assertRaises(ValueError):
            classify("SOL-USDT","4","daily","2026-10-17",200,b"{}")
    def test_calendar_milliseconds(self):
        self.assertEqual(epoch_ms("2024-06-03"),1717372800000)

class BrokerProofTests(unittest.TestCase):
    def base(self,side="LONG"):
        old="98" if side=="LONG" else "102"
        return initial("p-1","stop-1",side,"5",old,"0.1",{
            "position_id":"p-1","stop_id":"stop-1","side":side,
            "contracts":"5","stop":old,"active":True,"verified":True})
    def readback(self,side="LONG",stop="99",intent="i-1",**kw):
        d={"position_id":"p-1","stop_id":"stop-1","side":side,
           "contracts":"5","stop":stop,"active":True,"verified":True,"intent_id":intent}
        d.update(kw);return d
    def test_long_prepare_is_not_ack(self):
        p=prepare(self.base(),"99","100",20,"i-1")
        self.assertEqual(p.state,"PENDING_UNACKNOWLEDGED")
        self.assertEqual(str(p.ack_stop),"98")
    def test_long_exact_readback(self):
        q=confirm_readback(prepare(self.base(),"99","100",20,"i-1"),self.readback())
        self.assertEqual(str(q.ack_stop),"99")
        self.assertEqual(q.state,"ACK_VERIFIED")
    def test_short_tightens_correctly(self):
        p=prepare(self.base("SHORT"),"101","100",20,"i-1")
        self.assertEqual(str(p.ack_stop),"102")
        q=confirm_readback(p,self.readback(side="SHORT",stop="101"))
        self.assertEqual(str(q.ack_stop),"101")
    def test_long_weaken_rejected(self):
        with self.assertRaises(StopHalt):
            prepare(self.base(),"97.9","100",20,"i-1")
    def test_short_weaken_rejected(self):
        with self.assertRaises(StopHalt):
            prepare(self.base("SHORT"),"102.1","100",20,"i-1")
    def test_bid_crossed_stop_rejected(self):
        with self.assertRaises(StopHalt):
            prepare(self.base(),"100.1","100",20,"i-1")
    def test_stale_quote_rejected(self):
        with self.assertRaises(StopHalt):
            prepare(self.base(),"99","100",2001,"i-1")
    def test_boolean_quote_age_rejected(self):
        with self.assertRaises(StopHalt):
            prepare(self.base(),"99","100",True,"i-1")
    def test_off_tick_rejected(self):
        with self.assertRaises(StopHalt):
            prepare(self.base(),"99.05","100",20,"i-1")
    def test_duplicate_pending_rejected(self):
        p=prepare(self.base(),"99","100",20,"i-1")
        with self.assertRaises(StopHalt):
            prepare(p,"99.5","101",20,"i-2")
    def test_missing_readback_no_promotion(self):
        p=prepare(self.base(),"99","100",20,"i-1")
        with self.assertRaises(StopHalt):
            confirm_readback(p,{})
        self.assertEqual(str(p.ack_stop),"98")
    def test_wrong_quantity_no_promotion(self):
        p=prepare(self.base(),"99","100",20,"i-1")
        with self.assertRaises(StopHalt):
            confirm_readback(p,self.readback(contracts="4"))
    def test_wrong_order_id_no_promotion(self):
        p=prepare(self.base(),"99","100",20,"i-1")
        with self.assertRaises(StopHalt):
            confirm_readback(p,self.readback(stop_id="another"))
    def test_timeout_blocks_new_commands(self):
        p=uncertain_timeout(prepare(self.base(),"99","100",20,"i-1"))
        self.assertEqual(p.state,"UNKNOWN_NEEDS_RECONCILIATION")
        with self.assertRaises(StopHalt):
            prepare(p,"99.5","101",20,"i-2")
    def test_recovery_requires_exact_readback(self):
        p=uncertain_timeout(prepare(self.base(),"99","100",20,"i-1"))
        with self.assertRaises(StopHalt):
            recover(p,self.readback(stop="98"))
        q=recover(p,self.readback(stop="99"))
        self.assertEqual(q.state,"ACK_VERIFIED")
        self.assertEqual(str(q.ack_stop),"99")
    def test_initial_missing_broker_ack_blocks(self):
        with self.assertRaises(StopHalt):
            initial("p-1","s","LONG","5","98","0.1",{})
    def test_initial_wrong_position_quantity_blocks(self):
        with self.assertRaises(StopHalt):
            initial("p-1","s","LONG","5","98","0.1",{
            "position_id":"p-1","stop_id":"s","side":"LONG",
            "contracts":"4","stop":"98","active":True,"verified":True})

if __name__=="__main__":
    unittest.main()
