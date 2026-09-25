from __future__ import annotations

import json
import unittest
from urllib.parse import urlparse

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_auth_trade import MEXCFuturesMutationTransport, MEXCTradeTransportError


class Resp:
    status = 200
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.payload).encode()


class Opener:
    def __init__(self): self.requests = []
    def __call__(self, request, timeout):
        self.requests.append(request)
        path = urlparse(request.full_url).path
        if path == "/api/v1/private/order/create":
            return Resp({"success": True, "code": 0, "data": {"orderId": "12345"}})
        return Resp({"success": True, "code": 0, "data": None})


class OptionsFuturesTransportV02Tests(unittest.TestCase):
    def _client(self):
        op = Opener()
        c = MEXCFuturesMutationTransport(
            MEXCCredentials("KEY", "SECRET"),
            clock_ms=lambda: 1700000000000,
            opener=op,
        )
        return c, op

    def test_open_long_side_1(self):
        c, op = self._client()
        c.submit_market_order(
            symbol="BTC_USDT", volume_contracts=1, side=1,
            external_oid="open-long-1", position_mode=1
        )
        body = json.loads(op.requests[0].data.decode())
        self.assertEqual(body["side"], 1)
        self.assertEqual(body["leverage"], 1)
        self.assertEqual(body["openType"], 1)
        self.assertNotIn("positionId", body)

    def test_close_long_side_4_requires_position_id(self):
        c, op = self._client()
        with self.assertRaises(MEXCTradeTransportError):
            c.submit_market_order(
                symbol="BTC_USDT", volume_contracts=1, side=4,
                external_oid="close-long-1", position_mode=1
            )
        c.submit_market_order(
            symbol="BTC_USDT", volume_contracts=1, side=4,
            external_oid="close-long-1", position_mode=1, position_id=77
        )
        body = json.loads(op.requests[0].data.decode())
        self.assertEqual(body["side"], 4)
        self.assertEqual(body["positionId"], 77)

    def test_open_short_and_close_short_still_allowed(self):
        c, op = self._client()
        c.submit_market_order(
            symbol="BTC_USDT", volume_contracts=1, side=3,
            external_oid="open-short-1", position_mode=1
        )
        c.submit_market_order(
            symbol="BTC_USDT", volume_contracts=1, side=2,
            external_oid="close-short-1", position_mode=1, position_id=88
        )
        self.assertEqual(json.loads(op.requests[0].data.decode())["side"], 3)
        self.assertEqual(json.loads(op.requests[1].data.decode())["side"], 2)

    def test_still_btc_only_and_no_wallet_mutation(self):
        c, op = self._client()
        with self.assertRaises(MEXCTradeTransportError):
            c.submit_market_order(
                symbol="ETH_USDT", volume_contracts=1, side=1,
                external_oid="x", position_mode=1
            )
        with self.assertRaises(MEXCTradeTransportError):
            c._post_json("/api/v1/private/account/transfer", {})
        self.assertEqual(op.requests, [])


if __name__ == "__main__":
    unittest.main()
