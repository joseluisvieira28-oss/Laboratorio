from __future__ import annotations

import json
import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_operator_futures_transport_v02 import (
    MEXCOperatorFuturesTransportV02,
    MEXCOperatorTransportError,
    OperatorFuturesPolicy,
    direction_meta,
)


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Recorder:
    def __init__(self):
        self.requests = []

    def __call__(self, request, timeout=10):
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        self.requests.append((request.full_url, request.get_method(), body))
        return FakeResponse({"success": True, "data": {"orderId": "123"}})


class OperatorTransportV02Tests(unittest.TestCase):
    def build(self, *, symbol="BNB_USDT", directions=("LONG",)):
        rec = Recorder()
        policy = OperatorFuturesPolicy(
            policy_id="TEST",
            symbol=symbol,
            allowed_directions=directions,
            required_leverage=5,
        )
        client = MEXCOperatorFuturesTransportV02(
            MEXCCredentials("K", "S"),
            policy,
            clock_ms=lambda: 123456,
            opener=rec,
        )
        return client, rec

    def test_direction_mapping(self):
        self.assertEqual(direction_meta("LONG"), {"position_type": 1, "entry_side": 1, "exit_side": 4})
        self.assertEqual(direction_meta("SHORT"), {"position_type": 2, "entry_side": 3, "exit_side": 2})

    def test_policy_rejects_non_5x(self):
        with self.assertRaises(ValueError):
            OperatorFuturesPolicy("X", "BNB_USDT", ("LONG",), required_leverage=1)

    def test_configure_isolated_leverage_is_exactly_5x(self):
        client, rec = self.build()
        client.configure_isolated_leverage(symbol="BNB_USDT", direction="LONG")
        body = rec.requests[-1][2]
        self.assertEqual(body["openType"], 1)
        self.assertEqual(body["leverage"], 5)
        self.assertEqual(body["positionType"], 1)

    def test_entry_market_order_is_5x_and_isolated(self):
        client, rec = self.build()
        out = client.submit_market_order(
            symbol="BNB_USDT",
            direction="LONG",
            phase="ENTRY",
            volume_contracts=2,
            external_oid="abc",
        )
        self.assertEqual(out["orderId"], "123")
        body = rec.requests[-1][2]
        self.assertEqual(body["type"], 5)
        self.assertEqual(body["openType"], 1)
        self.assertEqual(body["leverage"], 5)
        self.assertEqual(body["side"], 1)
        self.assertEqual(body["positionMode"], 1)

    def test_exit_requires_position_id(self):
        client, _ = self.build()
        with self.assertRaises(MEXCOperatorTransportError):
            client.submit_market_order(
                symbol="BNB_USDT",
                direction="LONG",
                phase="EXIT",
                volume_contracts=1,
                external_oid="exit",
            )

    def test_wrong_symbol_and_direction_fail_closed(self):
        client, _ = self.build()
        with self.assertRaises(MEXCOperatorTransportError):
            client.configure_isolated_leverage(symbol="AVAX_USDT", direction="LONG")
        with self.assertRaises(MEXCOperatorTransportError):
            client.configure_isolated_leverage(symbol="BNB_USDT", direction="SHORT")

    def test_auto_add_can_only_be_disabled(self):
        client, _ = self.build()
        with self.assertRaises(MEXCOperatorTransportError):
            client.set_auto_add_margin(position_id=1, enabled=True)


    def test_position_tpsl_uses_documented_market_trigger_payload(self):
        client, rec = self.build(directions=("LONG", "SHORT"))
        client.place_position_tpsl(
            symbol="BNB_USDT",
            direction="LONG",
            position_id=77,
            volume_contracts=3,
            stop_loss_price=90.0,
            take_profit_price=130.0,
        )
        url, method, body = rec.requests[-1]
        self.assertTrue(url.endswith("/api/v1/private/stoporder/place"))
        self.assertEqual(method, "POST")
        self.assertEqual(body["positionId"], 77)
        self.assertEqual(body["vol"], 3)
        self.assertEqual(body["lossTrend"], 1)
        self.assertEqual(body["profitTrend"], 1)
        self.assertEqual(body["stopLossPrice"], 90.0)
        self.assertEqual(body["takeProfitPrice"], 130.0)
        self.assertEqual(body["takeProfitType"], 0)
        self.assertEqual(body["stopLossType"], 0)
        self.assertEqual(body["takeProfitReverse"], 2)
        self.assertEqual(body["stopLossReverse"], 2)

    def test_tpsl_geometry_fails_closed(self):
        client, _ = self.build(directions=("LONG", "SHORT"))
        with self.assertRaises(MEXCOperatorTransportError):
            client.place_position_tpsl(
                symbol="BNB_USDT",
                direction="LONG",
                position_id=1,
                volume_contracts=1,
                stop_loss_price=110.0,
                take_profit_price=100.0,
            )


if __name__ == "__main__":
    unittest.main()
