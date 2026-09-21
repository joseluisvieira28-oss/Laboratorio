from __future__ import annotations
import json
import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_auth_trade import MEXCFuturesMutationTransport, MEXCTradeTransportError


class Resp:
    status=200
    def __init__(self,payload): self.payload=payload
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def read(self): return json.dumps(self.payload).encode()


class Opener:
    def __init__(self): self.requests=[]
    def __call__(self,request,timeout):
        self.requests.append(request)
        return Resp({"success":True,"code":0,"data":12345})


class TradeTransportTests(unittest.TestCase):
    def test_only_1x_isolated_leverage_configuration_allowed(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(
            MEXCCredentials("KEY","SECRET"),
            clock_ms=lambda:1700000000000,
            opener=op,
        )
        ack=c.configure_isolated_leverage(symbol="BTC_USDT",position_type=2,leverage=1)
        self.assertEqual(ack,12345)
        req=op.requests[0]
        self.assertEqual(req.get_method(),"POST")
        body=json.loads(req.data.decode())
        self.assertEqual(body["openType"],1)
        self.assertEqual(body["leverage"],1)
        with self.assertRaises(MEXCTradeTransportError):
            c.configure_isolated_leverage(symbol="BTC_USDT",position_type=2,leverage=2)

    def test_non_allowlisted_contract_and_mutation_path_blocked(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(MEXCCredentials("K","S"),opener=op)
        with self.assertRaises(MEXCTradeTransportError):
            c.submit_market_order(symbol="ETH_USDT",volume_contracts=1,side=3,external_oid="x")
        with self.assertRaises(MEXCTradeTransportError):
            c._post_json("/api/v1/private/account/transfer",{})
        self.assertEqual(op.requests,[])

    def test_market_order_payload_is_isolated_1x(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(
            MEXCCredentials("KEY","SECRET"),
            clock_ms=lambda:1700000000000,
            opener=op,
        )
        c.submit_market_order(
            symbol="BTC_USDT",volume_contracts=1,side=3,
            external_oid="lab-test-id",position_mode=1
        )
        body=json.loads(op.requests[0].data.decode())
        self.assertEqual(body["type"],5)
        self.assertEqual(body["openType"],1)
        self.assertEqual(body["leverage"],1)
        self.assertEqual(body["side"],3)


if __name__=="__main__":
    unittest.main()
