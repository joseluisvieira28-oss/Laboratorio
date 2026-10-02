from __future__ import annotations

import io
import json
import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_operator_futures_transport_v04 import (
    MEXCMultiSlotFuturesTransportV04,
    MEXCMultiSlotTransportError,
    MultiSlotFuturesPolicy,
)


class Resp:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class CaptureOpener:
    def __init__(self):
        self.requests = []
    def __call__(self, request, timeout=10):
        body = json.loads(request.data.decode("utf-8"))
        self.requests.append((request.full_url, body))
        path = request.full_url
        if path.endswith("/order/create"):
            return Resp({"success": True, "data": {"orderId": "1"}})
        return Resp({"success": True, "data": {"ok": True}})


class TransportV04Tests(unittest.TestCase):
    def test_policy_allows_only_1x_or_5x(self):
        MultiSlotFuturesPolicy("p1", "BTC_USDT", ("LONG",), 1)
        MultiSlotFuturesPolicy("p5", "BNB_USDT", ("LONG",), 5)
        with self.assertRaises(ValueError):
            MultiSlotFuturesPolicy("p3", "BTC_USDT", ("LONG",), 3)

    def test_options_one_x_is_sent_exactly(self):
        opener = CaptureOpener()
        t = MEXCMultiSlotFuturesTransportV04(
            MEXCCredentials("k", "s"),
            MultiSlotFuturesPolicy("options", "BTC_USDT", ("LONG", "SHORT"), 1),
            clock_ms=lambda: 123,
            opener=opener,
        )
        t.configure_isolated_leverage(symbol="BTC_USDT", direction="SHORT")
        t.submit_market_order(
            symbol="BTC_USDT",
            direction="SHORT",
            phase="ENTRY",
            volume_contracts=1,
            external_oid="abc",
        )
        lev = opener.requests[0][1]
        order = opener.requests[1][1]
        self.assertEqual(lev["leverage"], 1)
        self.assertEqual(order["leverage"], 1)
        self.assertEqual(order["side"], 3)
        self.assertEqual(order["openType"], 1)

    def test_bnb_five_x_and_long_side(self):
        opener = CaptureOpener()
        t = MEXCMultiSlotFuturesTransportV04(
            MEXCCredentials("k", "s"),
            MultiSlotFuturesPolicy("bnb", "BNB_USDT", ("LONG",), 5),
            clock_ms=lambda: 123,
            opener=opener,
        )
        t.submit_market_order(
            symbol="BNB_USDT",
            direction="LONG",
            phase="ENTRY",
            volume_contracts=1,
            external_oid="abc",
        )
        order = opener.requests[-1][1]
        self.assertEqual(order["leverage"], 5)
        self.assertEqual(order["side"], 1)

    def test_exit_requires_position_id(self):
        opener = CaptureOpener()
        t = MEXCMultiSlotFuturesTransportV04(
            MEXCCredentials("k", "s"),
            MultiSlotFuturesPolicy("bnb", "BNB_USDT", ("LONG",), 5),
            opener=opener,
        )
        with self.assertRaises(MEXCMultiSlotTransportError):
            t.submit_market_order(
                symbol="BNB_USDT",
                direction="LONG",
                phase="EXIT",
                volume_contracts=1,
                external_oid="abc",
            )

    def test_symbol_escape_is_blocked(self):
        opener = CaptureOpener()
        t = MEXCMultiSlotFuturesTransportV04(
            MEXCCredentials("k", "s"),
            MultiSlotFuturesPolicy("bnb", "BNB_USDT", ("LONG",), 5),
            opener=opener,
        )
        with self.assertRaises(MEXCMultiSlotTransportError):
            t.submit_market_order(
                symbol="BTC_USDT",
                direction="LONG",
                phase="ENTRY",
                volume_contracts=1,
                external_oid="abc",
            )

    def test_auto_margin_can_only_be_disabled(self):
        opener = CaptureOpener()
        t = MEXCMultiSlotFuturesTransportV04(
            MEXCCredentials("k", "s"),
            MultiSlotFuturesPolicy("bnb", "BNB_USDT", ("LONG",), 5),
            opener=opener,
        )
        with self.assertRaises(MEXCMultiSlotTransportError):
            t.set_auto_add_margin(position_id=1, enabled=True)


if __name__ == "__main__":
    unittest.main()
