from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from radar.bnb_diamond_v02 import (
    BLOCKED_EVENT,
    FINAL_SAMPLE,
    MEASUREMENT_EVENT,
    BNBDiamondV02Error,
    BNBDiamondV02Sidecar,
    MinuteBar,
    ONE_MIN_MS,
    measure_causal_event,
    strict_next_minute_open_ms,
    summarize_complete_measurements,
)
from radar.evidence import EvidenceStore


def ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


class DeterministicFeed:
    provider = "FAKE_PUBLIC_READ_ONLY"

    def __init__(self, *, fail: bool = False, missing_days: set[str] | None = None):
        self.fail = fail
        self.missing_days = missing_days or set()
        self.calls: list[tuple[str, int, int]] = []

    def exact_window(self, *, symbol: str, start_ms: int, minutes: int, now_ms: int):
        self.calls.append((symbol, start_ms, minutes))
        if self.fail:
            raise BNBDiamondV02Error("synthetic transport failure")
        day = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc).date().isoformat()
        if day in self.missing_days:
            from radar.bnb_diamond_v02 import BNBDiamondWindowUnavailable
            raise BNBDiamondWindowUnavailable("INCOMPLETE_EXACT_1M_WINDOW")
        base = {"BNBBTC": 0.01, "BNBUSDT": 100.0, "BTCUSDT": 50_000.0}[symbol]
        drift = {"BNBBTC": 0.0002, "BNBUSDT": 0.002, "BTCUSDT": 0.001}[symbol]
        bars = []
        for i in range(minutes):
            op = base * (1 + drift * i / max(1, minutes))
            cl = base * (1 + drift * (i + 1) / max(1, minutes))
            bars.append(
                MinuteBar(
                    open_time=start_ms + i * ONE_MIN_MS,
                    open=op,
                    close=cl,
                    quote_volume=1000.0 + i,
                    close_time=start_ms + (i + 1) * ONE_MIN_MS - 1,
                )
            )
        return bars


class BNBDiamondV02Tests(unittest.TestCase):
    def test_strict_next_minute_is_strict_even_on_boundary(self):
        t = ms("2026-09-24T12:00:00Z")
        self.assertEqual(strict_next_minute_open_ms(t), t + ONE_MIN_MS)
        self.assertEqual(strict_next_minute_open_ms(t + 1), t + ONE_MIN_MS)

    def test_measurement_freezes_three_symbols_and_prior20_baseline(self):
        signal = ms("2026-09-24T12:00:12Z")
        feed = DeterministicFeed()
        result = measure_causal_event(
            feed,
            signal_timestamp_ms=signal,
            now_ms=ms("2026-09-24T13:02:00Z"),
        )
        self.assertEqual(result["status"], "CAUSAL_MEASUREMENT_COMPLETE")
        self.assertEqual(len(result["baseline_dates_utc"]), 20)
        self.assertGreater(result["bnbbtc_return_60m"], 0)
        self.assertGreater(result["bnbusdt_volume_shock_ratio"], 0)
        self.assertIn("bnbusdt_minus_btcusdt_return_60m", result)
        symbols = {x[0] for x in feed.calls}
        self.assertEqual(symbols, {"BNBBTC", "BNBUSDT", "BTCUSDT"})

    def test_baseline_can_skip_missing_days_but_requires_twenty_within_forty(self):
        signal = ms("2026-09-24T12:00:12Z")
        missing = {"2026-09-23", "2026-09-22", "2026-09-21"}
        feed = DeterministicFeed(missing_days=missing)
        result = measure_causal_event(
            feed,
            signal_timestamp_ms=signal,
            now_ms=ms("2026-09-24T13:02:00Z"),
        )
        self.assertEqual(len(result["baseline_dates_utc"]), 20)
        self.assertTrue(missing.isdisjoint(set(result["baseline_dates_utc"])))

    def test_sidecar_is_idempotent_and_uses_parent_selection_only(self):
        signal_utc = "2026-09-24T12:00:12Z"
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(str(Path(td) / "e.sqlite3"))
            key = "BNB-LAUNCHPOOL-DEMAND-001:test:1"
            store.append_once(
                "BNB_FORWARD_PAPER_SELECTION",
                key,
                {
                    "event_key": key,
                    "signal_timestamp_utc": signal_utc,
                    "binding": {"status": "ENTRY_BOUND_EXIT_PENDING"},
                },
            )
            sidecar = BNBDiamondV02Sidecar(store=store, feed=DeterministicFeed())
            first = sidecar.run_once(now_ms=ms("2026-09-24T13:02:00Z"))
            second = sidecar.run_once(now_ms=ms("2026-09-24T13:03:00Z"))
            self.assertEqual(first["inserted_measurements_this_run"], 1)
            self.assertEqual(second["inserted_measurements_this_run"], 0)
            self.assertEqual(first["complete_causal_measurements"], 1)
            self.assertEqual(len(store.read_payloads(MEASUREMENT_EVENT)), 1)
            self.assertEqual(len(store.read_payloads("BNB_FORWARD_PAPER_SELECTION")), 1)
            ok, detail = store.verify_chain()
            self.assertTrue(ok, detail)

    def test_transient_sidecar_failure_never_mutates_parent_or_creates_false_measurement(self):
        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(str(Path(td) / "e.sqlite3"))
            key = "BNB-LAUNCHPOOL-DEMAND-001:test:2"
            parent = {
                "event_key": key,
                "signal_timestamp_utc": "2026-09-24T12:00:12Z",
            }
            store.append_once("BNB_FORWARD_PAPER_SELECTION", key, parent)
            sidecar = BNBDiamondV02Sidecar(
                store=store,
                feed=DeterministicFeed(fail=True),
            )
            state = sidecar.run_once(now_ms=ms("2026-09-24T13:02:00Z"))
            self.assertEqual(state["transient_source_failures_this_run"], 1)
            self.assertEqual(state["complete_causal_measurements"], 0)
            self.assertEqual(len(store.read_payloads(MEASUREMENT_EVENT)), 0)
            self.assertEqual(len(store.read_payloads(BLOCKED_EVENT)), 0)
            self.assertEqual(store.read_payloads("BNB_FORWARD_PAPER_SELECTION")[0], parent)

    def test_no_final_causal_verdict_before_exact_twenty_five(self):
        rows = [
            {
                "bnbbtc_return_60m": 0.01,
                "bnbusdt_volume_shock_ratio": 1.2,
            }
            for _ in range(FINAL_SAMPLE - 1)
        ]
        early = summarize_complete_measurements(rows)
        self.assertEqual(early["status"], "COLLECTING")
        self.assertFalse(early["verdict_allowed_now"])

        rows.append(
            {"bnbbtc_return_60m": 0.01, "bnbusdt_volume_shock_ratio": 1.2}
        )
        final = summarize_complete_measurements(rows)
        self.assertTrue(final["verdict_allowed_now"])
        self.assertTrue(final["causal_gate_pass"])
        self.assertEqual(final["positive_bnbbtc_60m_events"], 25)

    def test_summary_does_not_hide_a_failed_preregistered_gate(self):
        rows = []
        for i in range(25):
            rows.append(
                {
                    "bnbbtc_return_60m": 0.01 if i < 16 else -0.01,
                    "bnbusdt_volume_shock_ratio": 1.2,
                }
            )
        final = summarize_complete_measurements(rows)
        self.assertEqual(final["positive_bnbbtc_60m_events"], 16)
        self.assertFalse(final["causal_gate_pass"])


if __name__ == "__main__":
    unittest.main()
