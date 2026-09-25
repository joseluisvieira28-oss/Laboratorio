from __future__ import annotations

import json
import unittest
from urllib.parse import parse_qs, urlparse

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_spot_auth import MEXCSpotAuthenticatedClient, MEXCSpotAuthError


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
        if path == "/api/v3/account":
            return Resp({"canTrade": True, "balances": [{"asset": "USDT", "free": "25", "locked": "0"}]})
        if path == "/api/v3/openOrders":
            return Resp([])
        if path == "/api/v3/order" and request.get_method() == "GET":
            return Resp({"symbol": "BTCUSDT", "orderId": "1", "clientOrderId": "abc", "status": "FILLED"})
        if path == "/api/v3/myTrades":
            return Resp([])
        if path == "/api/v3/order" and request.get_method() == "POST":
            return Resp({"symbol": "BTCUSDT", "orderId": "1", "transactTime": 1})
        return Resp({})


class SpotAuthTests(unittest.TestCase):
    def _client(self, opener):
        return MEXCSpotAuthenticatedClient(MEXCCredentials("KEY", "SECRET"), clock_ms=lambda: 1700000000000, opener=opener)

    def test_account_and_open_orders_are_signed_and_read_only(self):
        op = Opener(); c = self._client(op)
        self.assertTrue(c.account()["canTrade"])
        self.assertEqual(c.open_orders(), [])
        self.assertEqual(op.requests[0].get_header("X-mexc-apikey"), "KEY")
        self.assertIn("signature=", op.requests[0].full_url)

    def test_market_buy_is_btcusdt_quote_capped_10(self):
        op = Opener(); c = self._client(op)
        c.submit_market_buy_quote(quote_usdt=10, client_order_id="opt-buy-1")
        req = op.requests[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(urlparse(req.full_url).path, "/api/v3/order")
        q = parse_qs(req.data.decode())
        self.assertEqual(q["symbol"], ["BTCUSDT"])
        self.assertEqual(q["side"], ["BUY"])
        self.assertEqual(q["type"], ["MARKET"])
        self.assertEqual(q["quoteOrderQty"], ["10"])
        with self.assertRaises(MEXCSpotAuthError):
            c.submit_market_buy_quote(quote_usdt=10.01, client_order_id="x")

    def test_market_sell_only_btcusdt_and_positive_qty(self):
        op = Opener(); c = self._client(op)
        c.submit_market_sell_quantity(quantity_btc=0.0001, client_order_id="opt-sell-1")
        q = parse_qs(op.requests[0].data.decode())
        self.assertEqual(q["side"], ["SELL"])
        self.assertEqual(q["quantity"], ["0.0001"])
        with self.assertRaises(MEXCSpotAuthError):
            c.submit_market_sell_quantity(quantity_btc=0, client_order_id="x")

    def test_no_transfer_or_withdraw_surface(self):
        c = self._client(Opener())
        with self.assertRaises(MEXCSpotAuthError):
            c._signed("POST", "/api/v3/capital/transfer", {})
        with self.assertRaises(MEXCSpotAuthError):
            c._signed("POST", "/api/v3/capital/withdraw", {})


if __name__ == "__main__":
    unittest.main()
