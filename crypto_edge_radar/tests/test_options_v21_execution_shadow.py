from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
import unittest

from radar.evidence import EvidenceStore
from radar.market import MEXCFuturesPublicFeed
from radar.mexc_spot import MEXCSpotPublicFeed
from radar.models import MarketSnapshot
from radar.options_v21_execution_shadow import (
    AUTHORITY_ID,
    FIRST_ELIGIBLE_ENTRY_DAY,
    MISSED_EVENT,
    OBSERVATION_EVENT,
    OPERATIONAL_SAMPLE_MIN,
    OptionsV21PublicExecutionShadow,
    evaluate_options_v21_execution_shadow,
)


def ms(y, m, d, hh=0, mm=0, ss=0):
    return int(datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc).timestamp() * 1000)


class StubSpot(MEXCSpotPublicFeed):
    def default_symbols(self):
        return {"BTCUSDT"}

    def book_ticker(self, symbol):
        return {"symbol": symbol, "bidPrice": "99.9", "askPrice": "100.1"}

    def depth(self, symbol, limit=20):
        return {
            "bids": [["99.9", "5"]],
            "asks": [["100.1", "5"]],
        }


class StubFutures(MEXCFuturesPublicFeed):
    def server_time_ms(self):
        return 1_800_000_000_000

    def all_market_snapshots(self):
        return {
            "BTCUSDT": MarketSnapshot(
                symbol="BTCUSDT",
                observed_at="2026-09-26T00:00:01Z",
                last_price=100.0,
                bid_price=99.9,
                ask_price=100.1,
                quote_volume_24h=1_000_000.0,
            )
        }

    def contract_row(self, symbol):
        return {
            "symbol": "BTC_USDT",
            "apiAllowed": True,
            "futureType": 1,
            "state": 0,
            "contractSize": 0.001,
            "minVol": 1,
            "volUnit": 1,
        }

    def order_book_depth(self, symbol, limit=20):
        return {
            "bids": [[99.9, 2000, 1]],
            "asks": [[100.1, 2000, 1]],
        }

    def funding_rate(self, symbol):
        return {
            "fundingRate": 0.0001,
            "collectCycle": 8,
            "nextSettleTime": 1_800_000_100_000,
            "idxPrice": 100.0,
            "fairPrice": 100.05,
        }


class OptionsExecutionShadowTests(unittest.TestCase):
    def _store(self):
        td = tempfile.TemporaryDirectory()
        return td, EvidenceStore(os.path.join(td.name, "e.sqlite3"))

    def _entry(self, store, key, entry_date, position):
        store.append_once(
            "OPTIONS_V21_FORWARD_ENTRY",
            key,
            {
                "event_key": key,
                "signal_date": "2026-09-25",
                "entry_date": entry_date,
                "position": position,
                "weight": 1.0,
            },
        )

    def test_boundary_is_prospective(self):
        self.assertEqual(FIRST_ELIGIBLE_ENTRY_DAY.isoformat(), "2026-09-26")
        self.assertEqual(
            AUTHORITY_ID,
            "OPTIONS-SPOTPERP-001-V2.1-PUBLIC-EXECUTION-SHADOW-V0.1",
        )

    def test_long_receipt_is_public_read_only_and_does_not_change_science(self):
        td, store = self._store()
        try:
            self._entry(store, "long-1", "2026-09-26", 1)
            sidecar = OptionsV21PublicExecutionShadow(
                store=store,
                spot=StubSpot(),
                futures=StubFutures(),
            )
            result = sidecar.run_once(now_ms=ms(2026, 9, 26, 0, 0, 30))
            self.assertEqual(result["inserted_execution_observations"], 1)
            rows = store.read_payloads(OBSERVATION_EVENT)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["public_execution"]["route"], "MEXC_SPOT_LONG")
            self.assertTrue(row["public_execution"]["capacity_covers_100usdt"])
            self.assertAlmostEqual(
                row["public_execution"]["public_taker_round_trip_bps_reference"],
                10.0,
            )
            self.assertFalse(row["used_to_modify_parent_science"])
            self.assertFalse(row["authenticated_exchange_api_used"])
            self.assertFalse(row["orders_created"])
            self.assertFalse(row["exchange_mutation_performed"])
            self.assertFalse(row["live_capital_enabled"])
            self.assertEqual(row["scientific_costs_bps"]["base"], 10.0)
            self.assertFalse(row["scientific_costs_bps"]["changed_by_observation"])
        finally:
            td.cleanup()

    def test_short_receipt_keeps_funding_as_scenario_only(self):
        td, store = self._store()
        try:
            self._entry(store, "short-1", "2026-09-26", -1)
            sidecar = OptionsV21PublicExecutionShadow(
                store=store,
                spot=StubSpot(),
                futures=StubFutures(),
            )
            sidecar.run_once(now_ms=ms(2026, 9, 26, 0, 0, 30))
            row = store.read_payloads(OBSERVATION_EVENT)[0]
            execution = row["public_execution"]
            self.assertEqual(execution["route"], "MEXC_USDT_PERP_SHORT")
            self.assertAlmostEqual(
                execution["public_taker_round_trip_bps_reference"],
                16.0,
            )
            self.assertTrue(execution["funding_applies"])
            self.assertTrue(execution["funding_scenario_is_not_forecast"])
            self.assertAlmostEqual(
                execution["constant_current_rate_24h_short_burden_bps_scenario"],
                -3.0,
            )
            self.assertTrue(execution["capacity_covers_100usdt"])
        finally:
            td.cleanup()

    def test_pre_boundary_entry_is_ignored_not_reconstructed(self):
        td, store = self._store()
        try:
            self._entry(store, "old-1", "2026-09-25", 1)
            sidecar = OptionsV21PublicExecutionShadow(
                store=store,
                spot=StubSpot(),
                futures=StubFutures(),
            )
            result = sidecar.run_once(now_ms=ms(2026, 9, 26, 0, 1))
            self.assertEqual(result["inserted_execution_observations"], 0)
            self.assertEqual(len(store.read_payloads(OBSERVATION_EVENT)), 0)
            self.assertEqual(len(store.read_payloads(MISSED_EVENT)), 0)
        finally:
            td.cleanup()

    def test_late_post_boundary_entry_becomes_missed_and_is_not_backfilled(self):
        td, store = self._store()
        try:
            self._entry(store, "miss-1", "2026-09-26", 1)
            sidecar = OptionsV21PublicExecutionShadow(
                store=store,
                spot=StubSpot(),
                futures=StubFutures(),
            )
            result = sidecar.run_once(now_ms=ms(2026, 9, 27, 0, 1))
            self.assertEqual(result["inserted_execution_observations"], 0)
            self.assertEqual(result["inserted_missed_observations"], 1)
            self.assertEqual(len(store.read_payloads(OBSERVATION_EVENT)), 0)
            self.assertEqual(len(store.read_payloads(MISSED_EVENT)), 1)
        finally:
            td.cleanup()

    def test_ten_receipts_is_readiness_milestone_not_authority(self):
        td, store = self._store()
        try:
            for i in range(OPERATIONAL_SAMPLE_MIN):
                store.append_once(
                    OBSERVATION_EVENT,
                    f"k{i}",
                    {
                        "event_key": f"k{i}",
                        "entry_date": f"2026-10-{i+1:02d}",
                        "position": 1 if i % 2 == 0 else -1,
                        "public_execution": {
                            "observable_nonfunding_round_trip_proxy_bps": 12.0,
                            "capacity_covers_100usdt": True,
                        },
                    },
                )
            metrics = evaluate_options_v21_execution_shadow(store)
            self.assertEqual(
                metrics["status"],
                "PUBLIC_EXECUTION_SAMPLE_READY_FOR_AUDIT",
            )
            self.assertEqual(metrics["complete_execution_observations"], 10)
            self.assertFalse(metrics["automatic_tier1_promotion"])
            self.assertFalse(metrics["automatic_micro_live_authorization"])
            self.assertFalse(metrics["live_capital_enabled"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
