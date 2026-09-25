from __future__ import annotations

import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_spot_auth import MEXCSpotAuthError
from radar.mexc_spot_generic_auth_v01 import MEXCSpotPolicyBoundClient, SpotMutationPolicy


class GenericSpotPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.credentials = MEXCCredentials(api_key="key", api_secret="secret")

    def test_requires_explicit_policy(self) -> None:
        with self.assertRaises(MEXCSpotAuthError):
            MEXCSpotPolicyBoundClient(self.credentials, policies=[])

    def test_bnbbtc_can_be_allowlisted_without_becoming_live_authorized(self) -> None:
        client = MEXCSpotPolicyBoundClient(
            self.credentials,
            policies=[SpotMutationPolicy(symbol="BNBBTC", max_quote_order_qty=0.001)],
        )
        self.assertEqual(client._policy("BNBBTC").normalized_symbol(), "BNBBTC")
        with self.assertRaises(MEXCSpotAuthError):
            client._policy("BTCUSDT")

    def test_quote_cap_is_enforced_before_transport(self) -> None:
        client = MEXCSpotPolicyBoundClient(
            self.credentials,
            policies=[SpotMutationPolicy(symbol="BNBBTC", max_quote_order_qty=0.001)],
        )
        with self.assertRaises(MEXCSpotAuthError):
            client.test_market_buy(
                symbol="BNBBTC",
                quote_order_qty=0.0011,
                client_order_id="bnb-test-cap",
            )

    def test_duplicate_policies_fail_closed(self) -> None:
        policy = SpotMutationPolicy(symbol="BNBBTC", max_quote_order_qty=0.001)
        with self.assertRaises(MEXCSpotAuthError):
            MEXCSpotPolicyBoundClient(self.credentials, policies=[policy, policy])

    def test_invalid_symbol_fails_closed(self) -> None:
        with self.assertRaises(MEXCSpotAuthError):
            MEXCSpotPolicyBoundClient(
                self.credentials,
                policies=[SpotMutationPolicy(symbol="../BAD", max_quote_order_qty=1)],
            )


if __name__ == "__main__":
    unittest.main()
