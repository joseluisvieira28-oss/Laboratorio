from __future__ import annotations

import hashlib
import hmac
import unittest
from urllib.parse import parse_qsl, urlsplit

from dream_account.execution_mexc_readonly import (
    MEXCSpotReadOnlyClient,
    ReadOnlyMEXCError,
    ReadOnlyPolicyViolation,
)


class FakeTransport:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get_json(self, url, headers, timeout):
        split = urlsplit(url)
        query = dict(parse_qsl(split.query, keep_blank_values=True))
        self.calls.append((split.path, query, dict(headers), timeout))
        route = self.routes.get(split.path)
        if callable(route):
            return route(query)
        if route is None:
            raise AssertionError(f"unexpected route {split.path}")
        return route


class StepClock:
    def __init__(self, values):
        self.values = list(values)
        self.last = self.values[-1]

    def __call__(self):
        if self.values:
            self.last = self.values.pop(0)
        return self.last


ACCOUNT = {
    "canTrade": False,
    "canWithdraw": False,
    "canDeposit": True,
    "accountType": "SPOT",
    "permissions": ["SPOT"],
    "balances": [
        {"asset": "USDT", "free": "56.00", "locked": "0"},
        {"asset": "BTC", "free": "0.001", "locked": "0.0001"},
    ],
}

OPEN_ORDER = {
    "symbol": "BTCUSDT",
    "orderId": "123",
    "clientOrderId": "client-123",
    "price": "60000",
    "origQty": "0.001",
    "executedQty": "0.0002",
    "cummulativeQuoteQty": "12",
    "status": "PARTIALLY_FILLED",
    "type": "LIMIT",
    "side": "BUY",
    "time": 1000,
    "updateTime": 2000,
}

TRADE = {
    "symbol": "BTCUSDT",
    "id": "deal-1",
    "orderId": "123",
    "clientOrderId": "client-123",
    "price": "60000",
    "qty": "0.0002",
    "quoteQty": "12",
    "commission": "0.0012",
    "commissionAsset": "USDT",
    "time": 1500,
    "isBuyer": True,
    "isMaker": False,
}


class GateKMEXCReadOnlyTests(unittest.TestCase):
    def client(self, routes=None, clock=None):
        transport = FakeTransport(routes or {"/api/v3/time": {"serverTime": 1_000_000}})
        client = MEXCSpotReadOnlyClient(
            "ACCESS",
            "SECRET",
            transport=transport,
            clock_ms=clock or (lambda: 1_000_000),
        )
        return client, transport

    def test_credentials_are_redacted_from_repr(self):
        client, _ = self.client()
        rendered = repr(client)
        self.assertNotIn("ACCESS", rendered)
        self.assertNotIn("SECRET", rendered)
        self.assertIn("<redacted>", rendered)

    def test_base_url_is_pinned_to_official_https_origin(self):
        with self.assertRaises(ReadOnlyPolicyViolation):
            MEXCSpotReadOnlyClient("a", "b", base_url="http://example.com")
        with self.assertRaises(ReadOnlyPolicyViolation):
            MEXCSpotReadOnlyClient("a", "b", base_url="https://api.mexc.com.evil.example")

    def test_recv_window_cannot_exceed_5000(self):
        with self.assertRaises(ValueError):
            MEXCSpotReadOnlyClient("a", "b", recv_window_ms=5001)

    def test_signed_get_uses_hmac_sha256_and_api_key_header(self):
        client, transport = self.client({
            "/api/v3/time": {"serverTime": 1_000_000},
            "/api/v3/account": ACCOUNT,
        })
        client.sync_clock()
        client.account()
        path, query, headers, timeout = transport.calls[-1]
        self.assertEqual(path, "/api/v3/account")
        signature = query.pop("signature")
        canonical = "&".join(f"{k}={query[k]}" for k in sorted(query))
        expected = hmac.new(b"SECRET", canonical.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(signature, expected)
        self.assertEqual(headers["X-MEXC-APIKEY"], "ACCESS")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(query["recvWindow"], "5000")
        self.assertEqual(query["timestamp"], "1000000")
        self.assertEqual(timeout, 10.0)

    def test_clock_sync_uses_request_midpoint(self):
        clock = StepClock([1_000, 1_020])
        client, _ = self.client({"/api/v3/time": {"serverTime": 1_015}}, clock=clock)
        self.assertEqual(client.sync_clock(), 5)

    def test_account_parses_balances_without_mutating_exchange(self):
        client, transport = self.client({
            "/api/v3/time": {"serverTime": 1_000_000},
            "/api/v3/account": ACCOUNT,
        })
        account = client.account()
        self.assertEqual(account.account_type, "SPOT")
        self.assertFalse(account.can_trade)
        self.assertEqual(account.balances[0].asset, "USDT")
        self.assertEqual(account.balances[0].free, "56.00")
        self.assertEqual([call[0] for call in transport.calls], ["/api/v3/time", "/api/v3/account"])

    def test_open_orders_is_symbol_scoped(self):
        client, transport = self.client({
            "/api/v3/time": {"serverTime": 1_000_000},
            "/api/v3/openOrders": [OPEN_ORDER],
        })
        rows = client.open_orders("BTCUSDT")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].order_id, "123")
        self.assertEqual(transport.calls[-1][1]["symbol"], "BTCUSDT")
        with self.assertRaises(ValueError):
            client.open_orders("")

    def test_query_order_requires_exactly_one_exchange_identifier(self):
        client, _ = self.client()
        with self.assertRaises(ValueError):
            client.query_order("BTCUSDT")
        with self.assertRaises(ValueError):
            client.query_order("BTCUSDT", order_id="1", client_order_id="2")

    def test_query_order_by_client_order_id_is_read_only(self):
        client, transport = self.client({
            "/api/v3/time": {"serverTime": 1_000_000},
            "/api/v3/order": OPEN_ORDER,
        })
        row = client.query_order("BTCUSDT", client_order_id="client-123")
        self.assertEqual(row.client_order_id, "client-123")
        self.assertEqual(transport.calls[-1][1]["origClientOrderId"], "client-123")

    def test_recent_trades_limit_is_bounded_by_documented_max(self):
        client, _ = self.client()
        with self.assertRaises(ValueError):
            client.recent_trades("BTCUSDT", limit=101)
        with self.assertRaises(ValueError):
            client.recent_trades("BTCUSDT", limit=0)

    def test_recent_trades_parses_fill_identity(self):
        client, _ = self.client({
            "/api/v3/time": {"serverTime": 1_000_000},
            "/api/v3/myTrades": [TRADE],
        })
        rows = client.recent_trades("BTCUSDT", order_id="123")
        self.assertEqual(rows[0].trade_id, "deal-1")
        self.assertEqual(rows[0].order_id, "123")
        self.assertEqual(rows[0].commission_asset, "USDT")

    def test_full_reconciliation_snapshot_is_deterministic_and_secret_free(self):
        routes = {
            "/api/v3/time": {"serverTime": 1_000_000},
            "/api/v3/account": ACCOUNT,
            "/api/v3/openOrders": [OPEN_ORDER],
            "/api/v3/order": OPEN_ORDER,
            "/api/v3/myTrades": [TRADE],
        }
        client, transport = self.client(routes)
        snapshot = client.reconciliation_snapshot("BTCUSDT", order_id="123")
        self.assertEqual(snapshot.symbol, "BTCUSDT")
        self.assertEqual(snapshot.queried_order.order_id, "123")
        self.assertEqual(len(snapshot.recent_trades), 1)
        self.assertEqual(len(snapshot.fingerprint()), 64)
        serialized = str(snapshot)
        self.assertNotIn("ACCESS", serialized)
        self.assertNotIn("SECRET", serialized)
        paths = [call[0] for call in transport.calls]
        self.assertEqual(
            paths,
            ["/api/v3/time", "/api/v3/account", "/api/v3/openOrders", "/api/v3/order", "/api/v3/myTrades"],
        )

    def test_malformed_account_fails_closed(self):
        client, _ = self.client({
            "/api/v3/time": {"serverTime": 1_000_000},
            "/api/v3/account": {"balances": "bad"},
        })
        with self.assertRaises(ReadOnlyMEXCError):
            client.account()

    def test_private_path_allowlist_rejects_write_and_wallet_routes(self):
        client, _ = self.client()
        for path in (
            "/api/v3/order/test",
            "/api/v3/batchOrders",
            "/api/v3/capital/withdraw",
            "/api/v3/capital/transfer",
        ):
            with self.assertRaises(ReadOnlyPolicyViolation):
                client._signed_get(path)

    def test_only_expected_read_paths_are_allowlisted(self):
        from dream_account.execution_mexc_readonly import READ_ONLY_SIGNED_PATHS

        self.assertEqual(
            READ_ONLY_SIGNED_PATHS,
            {
                "/api/v3/account",
                "/api/v3/openOrders",
                "/api/v3/order",
                "/api/v3/myTrades",
            },
        )


if __name__ == "__main__":
    unittest.main()
