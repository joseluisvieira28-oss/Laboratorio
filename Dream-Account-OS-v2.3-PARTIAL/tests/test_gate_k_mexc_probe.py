from __future__ import annotations

import os
import unittest
from unittest import mock

from dream_account.execution_mexc_probe import (
    ACCESS_KEY_ENV,
    PROBE_ENABLE_ENV,
    SCOPE_ATTESTATION_ENV,
    SECRET_KEY_ENV,
    ReadOnlyProbeBlocked,
    load_guarded_client_from_env,
    minimal_account_probe,
)
from dream_account.execution_mexc_readonly import SpotAccount, SpotBalance


class FakeReadOnlyClient:
    def __init__(self, *, skew=0, account_type="SPOT", balances=None):
        self.skew = skew
        self._account = SpotAccount(
            account_type=account_type,
            can_trade=True,
            can_withdraw=True,
            can_deposit=True,
            permissions=("SPOT",),
            balances=tuple(
                balances
                or (
                    SpotBalance("USDT", "56", "0"),
                    SpotBalance("BTC", "0", "0"),
                )
            ),
        )
        self.calls = []

    def sync_clock(self):
        self.calls.append("time")
        return self.skew

    def account(self):
        self.calls.append("account")
        return self._account


class GateKMEXCProbeTests(unittest.TestCase):
    def test_minimal_probe_only_reads_time_then_account(self):
        client = FakeReadOnlyClient()
        report = minimal_account_probe(client)
        self.assertEqual(report.status, "PASS")
        self.assertEqual(client.calls, ["time", "account"])
        self.assertEqual(report.balance_rows, 2)
        self.assertEqual(report.nonzero_balance_rows, 1)

    def test_report_does_not_expose_asset_names_or_amounts(self):
        client = FakeReadOnlyClient(
            balances=(SpotBalance("SECRET-ASSET", "123456.78", "0"),)
        )
        report = minimal_account_probe(client)
        rendered = str(report.sanitized_dict())
        self.assertNotIn("SECRET-ASSET", rendered)
        self.assertNotIn("123456.78", rendered)
        self.assertEqual(len(report.fingerprint()), 64)

    def test_large_clock_skew_blocks_before_private_account_read(self):
        client = FakeReadOnlyClient(skew=5001)
        with self.assertRaises(ReadOnlyProbeBlocked):
            minimal_account_probe(client)
        self.assertEqual(client.calls, ["time"])

    def test_non_spot_account_blocks(self):
        client = FakeReadOnlyClient(account_type="FUTURES")
        with self.assertRaises(ReadOnlyProbeBlocked):
            minimal_account_probe(client)
        self.assertEqual(client.calls, ["time", "account"])

    def test_scope_attestation_is_required_before_credentials_are_loaded(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ReadOnlyProbeBlocked):
                load_guarded_client_from_env()

    def test_explicit_probe_enable_is_separate_from_scope_attestation(self):
        with mock.patch.dict(os.environ, {SCOPE_ATTESTATION_ENV: "1"}, clear=True):
            with self.assertRaises(ReadOnlyProbeBlocked):
                load_guarded_client_from_env()

    def test_credentials_required_only_after_both_safety_gates(self):
        with mock.patch.dict(
            os.environ,
            {SCOPE_ATTESTATION_ENV: "1", PROBE_ENABLE_ENV: "1"},
            clear=True,
        ):
            with self.assertRaises(ReadOnlyProbeBlocked):
                load_guarded_client_from_env()

    def test_guarded_loader_passes_credentials_without_logging_them(self):
        seen = {}

        def factory(access_key, secret_key):
            seen["access"] = access_key
            seen["secret"] = secret_key
            return FakeReadOnlyClient()

        env = {
            SCOPE_ATTESTATION_ENV: "1",
            PROBE_ENABLE_ENV: "1",
            ACCESS_KEY_ENV: "ACCESS-SENTINEL",
            SECRET_KEY_ENV: "SECRET-SENTINEL",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            client = load_guarded_client_from_env(client_factory=factory)
        self.assertIsInstance(client, FakeReadOnlyClient)
        self.assertEqual(seen, {"access": "ACCESS-SENTINEL", "secret": "SECRET-SENTINEL"})

    def test_non_numeric_balance_fails_closed(self):
        client = FakeReadOnlyClient(balances=(SpotBalance("USDT", "not-number", "0"),))
        with self.assertRaises(ReadOnlyProbeBlocked):
            minimal_account_probe(client)


if __name__ == "__main__":
    unittest.main()
