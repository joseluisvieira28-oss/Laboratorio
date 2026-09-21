from __future__ import annotations

import json
import unittest
from urllib.parse import urlparse

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
        path=urlparse(request.full_url).path
        if path=="/api/v1/private/order/create":
            return Resp({"success":True,"code":0,"data":{"orderId":"12345","ts":1700000000123}})
        if path=="/api/v1/private/order/cancel_with_external":
            return Resp({"success":True,"code":0,"data":[{"orderId":"12345","errorCode":0}]})
        return Resp({"success":True,"code":0,"data":None})


class TradeTransportTests(unittest.TestCase):
    def test_only_1x_isolated_leverage_configuration_allowed(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(
            MEXCCredentials("KEY","SECRET"),
            clock_ms=lambda:1700000000000,
            opener=op,
        )
        c.configure_isolated_leverage(symbol="BTC_USDT",position_type=2,leverage=1)
        req=op.requests[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(urlparse(req.full_url).path,"/api/v1/private/position/change_leverage")
        body=json.loads(req.data.decode())
        self.assertEqual(body["openType"],1)
        self.assertEqual(body["leverage"],1)
        with self.assertRaises(MEXCTradeTransportError):
            c.configure_isolated_leverage(symbol="BTC_USDT",position_type=2,leverage=2)

    def test_auto_margin_can_only_be_disabled(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(MEXCCredentials("K","S"),opener=op)
        c.set_auto_add_margin(position_id=42,enabled=False)
        req=op.requests[0]
        self.assertEqual(urlparse(req.full_url).path,"/api/v1/private/position/change_auto_add_im")
        body=json.loads(req.data.decode())
        self.assertEqual(body,{"positionId":42,"isEnabled":False})
        with self.assertRaises(MEXCTradeTransportError):
            c.set_auto_add_margin(position_id=42,enabled=True)

    def test_non_allowlisted_contract_and_mutation_path_blocked(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(MEXCCredentials("K","S"),opener=op)
        with self.assertRaises(MEXCTradeTransportError):
            c.submit_market_order(
                symbol="ETH_USDT",volume_contracts=1,side=3,
                external_oid="x",position_mode=1
            )
        with self.assertRaises(MEXCTradeTransportError):
            c._post_json("/api/v1/private/account/transfer",{})
        self.assertEqual(op.requests,[])

    def test_market_order_uses_current_order_create_and_isolated_1x(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(
            MEXCCredentials("KEY","SECRET"),
            clock_ms=lambda:1700000000000,
            opener=op,
        )
        ack=c.submit_market_order(
            symbol="BTC_USDT",volume_contracts=1,side=3,
            external_oid="lab-test-id",position_mode=1
        )
        self.assertEqual(ack["orderId"],"12345")
        req=op.requests[0]
        self.assertEqual(urlparse(req.full_url).path,"/api/v1/private/order/create")
        body=json.loads(req.data.decode())
        self.assertEqual(body["type"],5)
        self.assertEqual(body["openType"],1)
        self.assertEqual(body["positionMode"],1)
        self.assertEqual(body["leverage"],1)
        self.assertEqual(body["side"],3)
        self.assertNotIn("positionId",body)

    def test_close_short_requires_position_id(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(MEXCCredentials("K","S"),opener=op)
        with self.assertRaises(MEXCTradeTransportError):
            c.submit_market_order(
                symbol="BTC_USDT",volume_contracts=1,side=2,
                external_oid="close-test",position_mode=1
            )
        c.submit_market_order(
            symbol="BTC_USDT",volume_contracts=1,side=2,
            external_oid="close-test",position_mode=1,position_id=99
        )
        body=json.loads(op.requests[0].data.decode())
        self.assertEqual(body["side"],2)
        self.assertEqual(body["positionId"],99)

    def test_cancel_by_external_is_narrowly_allowlisted(self):
        op=Opener()
        c=MEXCFuturesMutationTransport(MEXCCredentials("K","S"),opener=op)
        rows=c.cancel_by_external(symbol="BTC_USDT",external_oid="abc-123")
        self.assertEqual(rows[0]["errorCode"],0)
        req=op.requests[0]
        self.assertEqual(urlparse(req.full_url).path,"/api/v1/private/order/cancel_with_external")
        body=json.loads(req.data.decode())
        self.assertEqual(body,[{"symbol":"BTC_USDT","externalOid":"abc-123"}])


if __name__=="__main__":
    unittest.main()
