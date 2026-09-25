from __future__ import annotations

import hashlib
import hmac
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs

from radar.mexc_spot_auth_v3 import (
    MEXCSpotCredentials,
    MEXCSpotMutationTransport,
    MEXCSpotV3Error,
)


class _Response:
    status=200
    def __init__(self,payload):
        self.payload=payload
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return json.dumps(self.payload).encode()


class SpotAuthTests(unittest.TestCase):
    def test_signed_market_buy_uses_only_allowlisted_spot_order(self):
        captured={}
        def fake(req,timeout=0):
            captured["url"]=req.full_url
            captured["data"]=req.data.decode()
            captured["headers"]=dict(req.header_items())
            return _Response({"orderId":"1"})
        creds=MEXCSpotCredentials("key","secret")
        with patch("radar.mexc_spot_auth_v3.urlopen",fake), patch("radar.mexc_spot_auth_v3.time.time",lambda:1000.0):
            row=MEXCSpotMutationTransport(creds).market_buy(
                quote_order_qty="8",
                client_order_id="cid",
            )
        self.assertEqual(row["orderId"],"1")
        self.assertTrue(captured["url"].endswith("/api/v3/order"))
        qs=parse_qs(captured["data"])
        self.assertEqual(qs["symbol"],["BTCUSDT"])
        self.assertEqual(qs["side"],["BUY"])
        self.assertEqual(qs["type"],["MARKET"])
        self.assertEqual(qs["quoteOrderQty"],["8"])
        self.assertIn("signature",qs)
        self.assertNotIn("withdraw",captured["url"])
        self.assertNotIn("transfer",captured["url"])

    def test_non_btcusdt_mutation_is_rejected_before_network(self):
        creds=MEXCSpotCredentials("key","secret")
        with self.assertRaises(MEXCSpotV3Error):
            MEXCSpotMutationTransport(creds).market_buy(
                quote_order_qty="8",
                client_order_id="cid",
                symbol="ETHUSDT",
            )


if __name__=="__main__":
    unittest.main()
