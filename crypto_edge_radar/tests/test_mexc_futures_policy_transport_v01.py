from __future__ import annotations

import json
import unittest
from urllib.parse import urlparse

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_futures_policy_transport_v01 import (
    FuturesMutationPolicy,
    MEXCFuturesPolicyBoundTransport,
    MEXCPolicyTransportError,
)


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
            return Resp({"success": True, "data": {"orderId": "123"}})
        return Resp({"success": True, "data": {}})


class PolicyTransportTests(unittest.TestCase):
    def client(self, symbol="AVAX_USDT", dirs=("LONG", "SHORT")):
        op = Opener()
        policy = FuturesMutationPolicy(
            policy_id="TEST",
            symbol=symbol,
            allowed_directions=dirs,
        )
        client = MEXCFuturesPolicyBoundTransport(
            MEXCCredentials("K", "S"),
            policy,
            clock_ms=lambda: 1700000000000,
            opener=op,
        )
        return client, op

    def test_symbol_and_direction_are_immutable_policy_boundaries(self):
        c, op = self.client(symbol="BNB_USDT", dirs=("LONG",))
        with self.assertRaises(MEXCPolicyTransportError):
            c.submit_market_order(
                symbol="AVAX_USDT",
                direction="LONG",
                phase="ENTRY",
                volume_contracts=1,
                external_oid="x",
            )
        with self.assertRaises(MEXCPolicyTransportError):
            c.submit_market_order(
                symbol="BNB_USDT",
                direction="SHORT",
                phase="ENTRY",
                volume_contracts=1,
                external_oid="x",
            )
        self.assertEqual(op.requests, [])

    def test_long_entry_and_exit_use_hedge_mode_sides_1_and_4(self):
        c, op = self.client(symbol="BNB_USDT", dirs=("LONG",))
        c.submit_market_order(
            symbol="BNB_USDT", direction="LONG", phase="ENTRY",
            volume_contracts=1, external_oid="bnb-entry"
        )
        c.submit_market_order(
            symbol="BNB_USDT", direction="LONG", phase="EXIT",
            volume_contracts=1, external_oid="bnb-exit", position_id=77
        )
        entry = json.loads(op.requests[0].data.decode())
        exit_ = json.loads(op.requests[1].data.decode())
        self.assertEqual(entry["side"], 1)
        self.assertEqual(exit_["side"], 4)
        self.assertEqual(entry["leverage"], 1)
        self.assertEqual(entry["openType"], 1)
        self.assertEqual(entry["positionMode"], 1)

    def test_short_entry_and_exit_use_hedge_mode_sides_3_and_2(self):
        c, op = self.client()
        c.submit_market_order(
            symbol="AVAX_USDT", direction="SHORT", phase="ENTRY",
            volume_contracts=2, external_oid="avax-entry"
        )
        c.submit_market_order(
            symbol="AVAX_USDT", direction="SHORT", phase="EXIT",
            volume_contracts=2, external_oid="avax-exit", position_id=88
        )
        entry = json.loads(op.requests[0].data.decode())
        exit_ = json.loads(op.requests[1].data.decode())
        self.assertEqual(entry["side"], 3)
        self.assertEqual(exit_["side"], 2)

    def test_exit_requires_position_id_and_entry_forbids_it(self):
        c, op = self.client()
        with self.assertRaises(MEXCPolicyTransportError):
            c.submit_market_order(
                symbol="AVAX_USDT", direction="LONG", phase="EXIT",
                volume_contracts=1, external_oid="exit"
            )
        with self.assertRaises(MEXCPolicyTransportError):
            c.submit_market_order(
                symbol="AVAX_USDT", direction="LONG", phase="ENTRY",
                volume_contracts=1, external_oid="entry", position_id=9
            )
        self.assertEqual(op.requests, [])

    def test_exactly_1x_and_auto_add_margin_off_only(self):
        c, op = self.client()
        c.configure_isolated_leverage(
            symbol="AVAX_USDT", direction="LONG", leverage=1
        )
        body = json.loads(op.requests[0].data.decode())
        self.assertEqual(body["openType"], 1)
        self.assertEqual(body["leverage"], 1)
        with self.assertRaises(MEXCPolicyTransportError):
            c.configure_isolated_leverage(
                symbol="AVAX_USDT", direction="LONG", leverage=2
            )
        c.set_auto_add_margin(position_id=42, enabled=False)
        with self.assertRaises(MEXCPolicyTransportError):
            c.set_auto_add_margin(position_id=42, enabled=True)

    def test_non_allowlisted_mutation_path_is_impossible_through_api(self):
        c, op = self.client()
        with self.assertRaises(MEXCPolicyTransportError):
            c._post_json("/api/v1/private/account/transfer", {})
        with self.assertRaises(MEXCPolicyTransportError):
            c._post_json("/api/v1/private/account/withdraw", {})
        self.assertEqual(op.requests, [])


if __name__ == "__main__":
    unittest.main()
