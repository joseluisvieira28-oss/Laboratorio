from __future__ import annotations

import unittest

from radar.mexc_authenticated_preflight import run_authenticated_preflight


class _Snapshot:
    last_price = 100_000.0


class _PublicFeed:
    def __init__(self, contract_size):
        self.contract_size = contract_size

    def server_time_ms(self):
        return 1_700_000_000_050

    def contract_row(self, symbol):
        return {
            "symbol": symbol,
            "apiAllowed": True,
            "state": 0,
            "futureType": 1,
            "positionOpenType": 3,
            "minLeverage": 1,
            "maxLeverage": 500,
            "minVol": 1,
            "volUnit": 1,
            "contractSize": self.contract_size,
            "priceUnit": 0.1,
        }

    def all_market_snapshots(self):
        return {"BTCUSDT": _Snapshot()}

    def funding_rate(self, symbol):
        return {
            "fundingRate": 0.0001,
            "nextSettleTime": 1_700_003_600_000,
            "collectCycle": 8,
            "fairPrice": 100_001.0,
            "idxPrice": 100_000.0,
        }


class _PrivateClient:
    def assets(self):
        return [{
            "currency": "USDT",
            "equity": 112.3763,
            "availableBalance": 112.3763,
            "cashBalance": 112.3763,
            "frozenBalance": 0,
            "positionMargin": 0,
            "unrealized": 0,
        }]

    def open_positions(self):
        return []

    def open_orders(self, symbol):
        return []

    def tiered_fee_rate(self, symbol):
        return {
            "level": 0,
            "makerFee": 0.0006,
            "takerFee": 0.0008,
        }

    def leverage(self, symbol):
        return [
            {"positionType": 1, "leverage": 1, "level": 1, "imr": 1, "mmr": 0.004},
            {"positionType": 2, "leverage": 1, "level": 1, "imr": 1, "mmr": 0.004},
        ]

    def position_mode(self):
        return 2

    def risk_limit(self, symbol):
        return {symbol: [{"level": 1, "maxLeverage": 500}]}


class MEXCAuthenticatedPreflightTests(unittest.TestCase):
    def test_pass_when_exchange_minimum_fits_existing_frozen_budget(self):
        # 1 * 0.000001 BTC * 100k = 0.10 USDT <= 0.1123763 USDT.
        times = iter([1_700_000_000_000, 1_700_000_000_100])
        result = run_authenticated_preflight(
            private_client=_PrivateClient(),
            public_feed=_PublicFeed(contract_size=0.000001),
            clock_ms=lambda: next(times),
            expected_equity_usdt=112.3763,
        )
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["security"]["exchange_mutation_performed"])
        self.assertFalse(result["security"]["order_endpoint_implemented"])

    def test_fail_closed_when_exchange_minimum_exceeds_existing_budget(self):
        # 1 * 0.0001 BTC * 100k = 10 USDT > 0.1123763 USDT.
        times = iter([1_700_000_000_000, 1_700_000_000_100])
        result = run_authenticated_preflight(
            private_client=_PrivateClient(),
            public_feed=_PublicFeed(contract_size=0.0001),
            clock_ms=lambda: next(times),
            expected_equity_usdt=112.3763,
        )
        self.assertFalse(result["pass"])
        self.assertIn(
            "ETF_CME_VENUE_MIN_NOTIONAL_EXCEEDS_FROZEN_VALIDATION_BUDGET",
            result["blockers"],
        )

    def test_fail_closed_when_account_identity_reference_missing(self):
        times = iter([1_700_000_000_000, 1_700_000_000_100])
        result = run_authenticated_preflight(
            private_client=_PrivateClient(),
            public_feed=_PublicFeed(contract_size=0.000001),
            clock_ms=lambda: next(times),
        )
        self.assertFalse(result["pass"])
        self.assertIn(
            "ACCOUNT_IDENTITY_EXPECTED_EQUITY_NOT_PROVIDED",
            result["blockers"],
        )

    def test_fail_closed_on_existing_position(self):
        class WithPosition(_PrivateClient):
            def open_positions(self):
                return [{
                    "symbol": "ETH_USDT",
                    "positionType": 1,
                    "openType": 2,
                    "holdVol": 1,
                    "leverage": 500,
                    "autoAddIm": True,
                }]

        times = iter([1_700_000_000_000, 1_700_000_000_100])
        result = run_authenticated_preflight(
            private_client=WithPosition(),
            public_feed=_PublicFeed(contract_size=0.000001),
            clock_ms=lambda: next(times),
            expected_equity_usdt=112.3763,
        )
        self.assertFalse(result["pass"])
        self.assertIn("OPEN_FUTURES_POSITION_PRESENT", result["blockers"])


if __name__ == "__main__":
    unittest.main()
