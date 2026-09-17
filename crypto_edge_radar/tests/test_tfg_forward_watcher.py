from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from radar.evidence import EvidenceStore
from radar.tfg_forward_watcher import (
    TFGForwardShadowWatcher,
    latest_certifiable_signal_close_ms,
)
from radar.strategies.tfg_donchian_regime_forward import (
    FIFTEEN_MIN_MS,
    FORWARD_FREEZE_MS,
    FROZEN_UNIVERSE,
    TWELVE_HOUR_MS,
    Candle,
    PaperOutcome,
    PaperTrade,
    SignalCandidate,
)


class FakeFeed:
    provider = "MEXC_SPOT_PUBLIC"

    def klines(self, *args, **kwargs):
        return []


class TFGForwardWatcherTests(TestCase):
    def test_boundary_is_certifiable_only_after_exact_entry_15m_bar_closes(self) -> None:
        boundary = ((FORWARD_FREEZE_MS // TWELVE_HOUR_MS) + 10) * TWELVE_HOUR_MS
        self.assertEqual(
            latest_certifiable_signal_close_ms(boundary + FIFTEEN_MIN_MS - 1),
            boundary - TWELVE_HOUR_MS,
        )
        self.assertEqual(
            latest_certifiable_signal_close_ms(boundary + FIFTEEN_MIN_MS),
            boundary,
        )

    def test_replay_does_not_duplicate_signal_or_resolution(self) -> None:
        boundary = ((FORWARD_FREEZE_MS // TWELVE_HOUR_MS) + 10) * TWELVE_HOUR_MS
        signal_open = boundary - TWELVE_HOUR_MS
        h12 = [
            Candle(
                open_time=signal_open,
                open=100.0,
                high=110.0,
                low=95.0,
                close=109.0,
                volume=1.0,
                close_time=boundary - 1,
            )
        ]

        def candidate(symbol: str, bars, *, signal_close_ms: int):
            return SignalCandidate(
                symbol=symbol,
                signal_close_ms=signal_close_ms,
                signal_open_ms=signal_open,
                prior_40_high=100.0,
                atr28=4.0,
                signal_low=95.0,
                signal_close=109.0,
                stop=94.0,
            )

        def trade(c, source):
            return PaperTrade(
                symbol=c.symbol,
                signal_close_ms=c.signal_close_ms,
                entry_open_time=c.signal_close_ms,
                entry=110.0,
                stop=94.0,
                target=158.0,
                initial_risk_fraction=(110.0 - 94.0) / 110.0,
            )

        resolved = PaperOutcome(
            exit_reason="TARGET",
            exit_open_time=boundary + TWELVE_HOUR_MS,
            exit_price=158.0,
            bars_held=2,
            gross_return_pct=(158.0 / 110.0 - 1.0) * 100.0,
            base_net_r=2.9,
            stress_net_r=2.8,
            same_bar_stop_target_ambiguity=False,
        )

        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(str(Path(td) / "evidence.sqlite3"))
            watcher = TFGForwardShadowWatcher(store=store, feed=FakeFeed())
            with (
                patch("radar.tfg_forward_watcher.latest_certifiable_signal_close_ms", return_value=boundary),
                patch("radar.tfg_forward_watcher._boundaries_through", return_value=[boundary]),
                patch("radar.tfg_forward_watcher.aggregate_15m_to_12h", return_value=(h12, 0)),
                patch("radar.tfg_forward_watcher.regime_state", return_value={"state": "ON"}),
                patch("radar.tfg_forward_watcher.detect_signal", side_effect=candidate),
                patch("radar.tfg_forward_watcher.materialize_entry", side_effect=trade),
                patch("radar.tfg_forward_watcher.resolve_paper_trade", return_value=resolved),
            ):
                first = watcher.run_once(now_ms=boundary + FIFTEEN_MIN_MS)
                second = watcher.run_once(now_ms=boundary + FIFTEEN_MIN_MS)

            self.assertEqual(first["inserted_signals"], len(FROZEN_UNIVERSE))
            self.assertEqual(first["inserted_resolutions"], len(FROZEN_UNIVERSE))
            self.assertEqual(second["inserted_signals"], 0)
            self.assertEqual(second["inserted_resolutions"], 0)
            self.assertEqual(second["duplicate_signals"], len(FROZEN_UNIVERSE))
            self.assertEqual(second["duplicate_resolutions"], len(FROZEN_UNIVERSE))
            ok, detail = store.verify_chain()
            self.assertTrue(ok, detail)


if __name__ == "__main__":
    import unittest

    unittest.main()
