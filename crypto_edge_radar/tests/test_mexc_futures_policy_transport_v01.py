from __future__ import annotations

import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_auth_trade import MEXCTradeTransportError
from radar.mexc_futures_policy_transport_v01 import (
    FuturesMutationPolicy,
    MEXCFuturesPolicyBoundTransport,
)


class FuturesPolicyTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.credentials = MEXCCredentials(api_key="key", api_secret="secret")

    def test_requires_explicit_policy(self) -> None:
        with self.assertRaises(MEXCTradeTransportError):
            MEXCFuturesPolicyBoundTransport(self.credentials, policies=[])

    def test_only_policy_symbols_are_available(self) -> None:
        client = MEXCFuturesPolicyBoundTransport(
            self.credentials,
            policies=[FuturesMutationPolicy(symbol="AVAX_USDT", allowed_sides=(1, 4))],
        )
        self.assertEqual(client._policy("AVAX_USDT").validate(), "AVAX_USDT")
        with self.assertRaises(MEXCTradeTransportError):
            client._policy("BTC_USDT")

    def test_policy_rejects_leverage_above_one(self) -> None:
        with self.assertRaises(MEXCTradeTransportError):
            MEXCFuturesPolicyBoundTransport(
                self.credentials,
                policies=[
                    FuturesMutationPolicy(
                        symbol="AVAX_USDT",
                        allowed_sides=(1, 4),
                        leverage=2,
                    )
                ],
            )

    def test_policy_rejects_cross_margin(self) -> None:
        with self.assertRaises(MEXCTradeTransportError):
            MEXCFuturesPolicyBoundTransport(
                self.credentials,
                policies=[
                    FuturesMutationPolicy(
                        symbol="AVAX_USDT",
                        allowed_sides=(1, 4),
                        margin_mode="CROSS",
                    )
                ],
            )

    def test_side_not_allowlisted_is_rejected_before_transport(self) -> None:
        client = MEXCFuturesPolicyBoundTransport(
            self.credentials,
            policies=[FuturesMutationPolicy(symbol="AVAX_USDT", allowed_sides=(1, 4))],
        )
        with self.assertRaises(MEXCTradeTransportError):
            client.submit_market_order(
                symbol="AVAX_USDT",
                volume_contracts=1,
                side=3,
                external_oid="blocked-short",
            )


if __name__ == "__main__":
    unittest.main()
