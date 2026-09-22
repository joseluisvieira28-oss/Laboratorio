from __future__ import annotations

import json
import unittest
from urllib.parse import urlparse

from radar.mexc_auth_readonly import (
    MEXCAuthenticatedReadError,
    MEXCCredentials,
    MEXCFuturesAuthenticatedReadOnlyClient,
    _encoded_query,
    _signature,
)


class _Response:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def read(self): return json.dumps(self._payload).encode("utf-8")


class _Opener:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []
    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        return _Response(self.payload)


class MEXCAuthReadOnlyTests(unittest.TestCase):
    def test_query_is_sorted_and_encoded(self):
        self.assertEqual(
            _encoded_query({"symbol": "BTC_USDT", "page_size": 100, "page_num": 1}),
            "page_num=1&page_size=100&symbol=BTC_USDT",
        )

    def test_signature_matches_independent_hmac_vector(self):
        sig = _signature(
            api_key="key", api_secret="secret",
            request_time_ms=123, query="a=1&b=2",
        )
        self.assertEqual(
            sig,
            "c882f568119d28d1d0f51e6fd1aeffe97f84cee07188f5e04a76d31533f034c4",
        )

    def test_private_read_is_get_only_and_headers_are_not_in_url(self):
        opener = _Opener({
            "success": True, "code": 0,
            "data": [{"currency": "USDT", "equity": 1, "availableBalance": 1}],
        })
        client = MEXCFuturesAuthenticatedReadOnlyClient(
            MEXCCredentials("KEY123", "SECRET456"),
            clock_ms=lambda: 1_700_000_000_000,
            opener=opener,
        )
        rows = client.assets()
        self.assertEqual(rows[0]["currency"], "USDT")
        request, _ = opener.requests[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(urlparse(request.full_url).netloc, "api.mexc.com")
        self.assertNotIn("KEY123", request.full_url)
        self.assertNotIn("SECRET456", request.full_url)
        self.assertEqual(request.get_header("Apikey"), "KEY123")
        self.assertTrue(request.get_header("Signature"))

    def test_current_open_orders_endpoint_is_exact_documented_path(self):
        opener=_Opener({"success":True,"code":0,"data":{"resultList":[]}})
        client=MEXCFuturesAuthenticatedReadOnlyClient(
            MEXCCredentials("K","S"),clock_ms=lambda:1700000000000,opener=opener
        )
        self.assertEqual(client.open_orders(),[])
        request,_=opener.requests[0]
        self.assertEqual(urlparse(request.full_url).path,"/api/v1/private/order/list/open_orders")

    def test_external_oid_lookup_is_read_only(self):
        opener=_Opener({"success":True,"code":0,"data":{"orderId":"123","state":3}})
        client=MEXCFuturesAuthenticatedReadOnlyClient(
            MEXCCredentials("K","S"),clock_ms=lambda:1700000000000,opener=opener
        )
        row=client.order_by_external(symbol="BTC_USDT",external_oid="abc-123")
        self.assertEqual(row["orderId"],"123")
        request,_=opener.requests[0]
        self.assertEqual(request.get_method(),"GET")
        self.assertEqual(
            urlparse(request.full_url).path,
            "/api/v1/private/order/external/BTC_USDT/abc-123"
        )

    def test_mutating_paths_are_blocked_before_network(self):
        opener = _Opener({"success": True, "data": {}})
        client = MEXCFuturesAuthenticatedReadOnlyClient(
            MEXCCredentials("k", "s"), opener=opener,
        )
        for path in (
            "/api/v1/private/order/create",
            "/api/v1/private/position/change_leverage",
            "/api/v1/private/position/change_auto_add_im",
        ):
            with self.assertRaises(MEXCAuthenticatedReadError):
                client._get_json(path)
        self.assertEqual(opener.requests, [])


if __name__ == "__main__":
    unittest.main()
