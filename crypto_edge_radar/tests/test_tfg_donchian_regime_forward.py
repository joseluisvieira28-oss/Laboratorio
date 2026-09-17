from __future__ import annotations

from unittest import TestCase

from radar.strategies.tfg_donchian_regime_forward import (
    ATR_LENGTH,
    DAY_MS,
    FIFTEEN_MIN_MS,
    FORWARD_FREEZE_MS,
    FROZEN_UNIVERSE,
    LOOKBACK,
    TWELVE_HOUR_MS,
    Candle,
    MEXCSpotKlineFeed,
    PaperTrade,
    TFGSourceError,
    aggregate_15m_to_12h,
    atr_series,
    detect_signal,
    latest_due_signal_close_ms,
    materialize_entry,
    regime_state,
    resolve_paper_trade,
)


def candle(open_time: int, step: int, price: float, *, high: float | None = None, low: float | None = None, close: float | None = None) -> Candle:
    return Candle(
        open_time=open_time,
        open=price,
        high=high if high is not None else price + 1.0,
        low=low if low is not None else price - 1.0,
        close=close if close is not None else price + 0.1,
        volume=10.0,
        close_time=open_time + step - 1,
    )


class TFGForwardMechanicsTests(TestCase):
    def test_exact_48x15m_aggregation_and_missing_bar_fail_closed(self) -> None:
        start = 43_200_000 * 100
        rows = [candle(start + i * FIFTEEN_MIN_MS, FIFTEEN_MIN_MS, 100 + i * 0.01) for i in range(48)]
        bars, incomplete = aggregate_15m_to_12h(rows)
        self.assertEqual(incomplete, 0)
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0].open_time, start)
        self.assertEqual(bars[0].close_time, start + TWELVE_HOUR_MS - 1)

        bars, incomplete = aggregate_15m_to_12h(rows[:-1])
        self.assertEqual(bars, [])
        self.assertEqual(incomplete, 1)

    def test_atr_matches_canonical_seed_then_wilder_update(self) -> None:
        rows = []
        start = DAY_MS * 1000
        for i in range(ATR_LENGTH + 2):
            p = 100.0 + i
            rows.append(candle(start + i * DAY_MS, DAY_MS, p, high=p + 2.0, low=p - 1.0, close=p + 0.5))
        values = atr_series(rows, ATR_LENGTH)
        self.assertIsNone(values[ATR_LENGTH - 1])
        self.assertIsNotNone(values[ATR_LENGTH])

        trs = []
        for i in range(1, ATR_LENGTH + 1):
            c, p = rows[i], rows[i - 1]
            trs.append(max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)))
        seed = sum(trs) / ATR_LENGTH
        self.assertAlmostEqual(values[ATR_LENGTH], seed, places=12)
        c, p = rows[ATR_LENGTH + 1], rows[ATR_LENGTH]
        tr = max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close))
        expected = ((seed * (ATR_LENGTH - 1)) + tr) / ATR_LENGTH
        self.assertAlmostEqual(values[ATR_LENGTH + 1], expected, places=12)

    def test_regime_requires_all_three_frozen_conditions(self) -> None:
        start = DAY_MS * 1000
        daily = {}
        for n, symbol in enumerate(FROZEN_UNIVERSE):
            rows = []
            for i in range(220):
                p = 100.0 + i * 0.5 + n
                rows.append(candle(start + i * DAY_MS, DAY_MS, p, close=p + 0.2))
            daily[symbol] = rows
        signal_close = start + 221 * DAY_MS
        state = regime_state(daily, signal_close_ms=signal_close)
        self.assertEqual(state["state"], "ON")
        self.assertTrue(state["checks"]["btc_close_gt_sma200"])
        self.assertTrue(state["checks"]["btc_sma200_rising_20d"])
        self.assertGreaterEqual(state["breadth_count"], 4)

        broken = dict(daily)
        broken["DOGEUSDT"] = broken["DOGEUSDT"][:-1]
        missing = regime_state(broken, signal_close_ms=signal_close)
        self.assertEqual(missing["state"], "MISSING")

    def test_breakout_uses_previous_40_complete_bars_only(self) -> None:
        start = (FORWARD_FREEZE_MS // TWELVE_HOUR_MS + 10) * TWELVE_HOUR_MS
        rows = []
        for i in range(LOOKBACK + 5):
            p = 100.0 + i * 0.05
            rows.append(candle(start + i * TWELVE_HOUR_MS, TWELVE_HOUR_MS, p, high=p + 1.0, low=p - 1.0, close=p + 0.1))
        idx = LOOKBACK + 1
        prior = max(c.high for c in rows[idx - LOOKBACK : idx])
        old = rows[idx]
        rows[idx] = Candle(old.open_time, prior, prior + 10.0, prior - 1.0, prior + 0.5, old.volume, old.close_time)
        close_ms = rows[idx].open_time + TWELVE_HOUR_MS
        candidate = detect_signal("BTCUSDT", rows, signal_close_ms=close_ms)
        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertAlmostEqual(candidate.prior_40_high, prior)
        self.assertGreater(candidate.signal_close, candidate.prior_40_high)

    def test_entry_materialization_waits_for_fully_known_boundary_bar(self) -> None:
        start = (FORWARD_FREEZE_MS // TWELVE_HOUR_MS + 10) * TWELVE_HOUR_MS
        rows = []
        for i in range(LOOKBACK + 5):
            p = 100.0 + i * 0.05
            rows.append(candle(start + i * TWELVE_HOUR_MS, TWELVE_HOUR_MS, p))
        idx = LOOKBACK + 1
        prior = max(c.high for c in rows[idx - LOOKBACK : idx])
        old = rows[idx]
        rows[idx] = Candle(old.open_time, prior, prior + 2.0, prior - 0.5, prior + 0.5, old.volume, old.close_time)
        close_ms = rows[idx].open_time + TWELVE_HOUR_MS
        candidate = detect_signal("ETHUSDT", rows, signal_close_ms=close_ms)
        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertIsNone(materialize_entry(candidate, []))
        entry15 = candle(close_ms, FIFTEEN_MIN_MS, candidate.stop + 10.0)
        trade = materialize_entry(candidate, [entry15])
        self.assertIsNotNone(trade)
        assert trade is not None
        self.assertEqual(trade.entry_open_time, close_ms)
        self.assertGreater(trade.target, trade.entry)

    def test_same_bar_stop_target_is_stop_first_conservative(self) -> None:
        start = TWELVE_HOUR_MS * 1000
        trade = PaperTrade(
            symbol="BTCUSDT",
            signal_close_ms=start,
            entry_open_time=start,
            entry=100.0,
            stop=90.0,
            target=130.0,
            initial_risk_fraction=0.10,
        )
        bars = [
            candle(start, TWELVE_HOUR_MS, 100.0, high=140.0, low=80.0, close=100.0),
        ]
        outcome = resolve_paper_trade(trade, bars)
        self.assertEqual(outcome.exit_reason, "STOP_AMBIGUOUS_SAME_BAR")
        self.assertTrue(outcome.same_bar_stop_target_ambiguity)
        self.assertEqual(outcome.exit_price, 90.0)
        self.assertAlmostEqual(outcome.base_net_r, -1.0, places=12)
        self.assertAlmostEqual(outcome.stress_net_r, -1.0, places=12)

    def test_schedule_is_0010_and_1210_semantics(self) -> None:
        boundary = (FORWARD_FREEZE_MS // TWELVE_HOUR_MS + 10) * TWELVE_HOUR_MS
        self.assertEqual(latest_due_signal_close_ms(boundary + 9 * 60_000), boundary - TWELVE_HOUR_MS)
        self.assertEqual(latest_due_signal_close_ms(boundary + 10 * 60_000), boundary)

    def test_source_object_exposes_only_frozen_public_spot_surface(self) -> None:
        feed = MEXCSpotKlineFeed()
        self.assertEqual(feed.provider, "MEXC_SPOT_PUBLIC")
        self.assertEqual(feed.path, "/api/v3/klines")
        with self.assertRaises(TFGSourceError):
            feed.klines("NOTFROZENUSDT", "15m", start_ms=0, end_ms=FIFTEEN_MIN_MS, now_ms=FIFTEEN_MIN_MS * 2)
        with self.assertRaises(TFGSourceError):
            feed.klines("BTCUSDT", "5m", start_ms=0, end_ms=FIFTEEN_MIN_MS, now_ms=FIFTEEN_MIN_MS * 2)


if __name__ == "__main__":
    import unittest

    unittest.main()
