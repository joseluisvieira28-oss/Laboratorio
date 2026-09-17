from __future__ import annotations

from unittest import TestCase

from radar.strategies.tfg_donchian_regime_forward import (
    FIFTEEN_MIN_MS,
    TFGSourceError,
    _parse_kline,
)


class MEXCNativeTimestampTests(TestCase):
    def test_provider_boundary_close_time_is_normalized_internally(self) -> None:
        open_ms = 1_800_000_000_000
        open_ms -= open_ms % FIFTEEN_MIN_MS
        row = [
            open_ms,
            "100.0",
            "102.0",
            "99.0",
            "101.0",
            "12.5",
            open_ms + FIFTEEN_MIN_MS,
            "1260.0",
        ]
        candle = _parse_kline(row, "15m")
        self.assertEqual(candle.open_time, open_ms)
        self.assertEqual(candle.close_time, open_ms + FIFTEEN_MIN_MS - 1)

    def test_binance_style_minus_one_source_timestamp_is_not_silently_accepted(self) -> None:
        open_ms = 1_800_000_000_000
        open_ms -= open_ms % FIFTEEN_MIN_MS
        row = [
            open_ms,
            "100.0",
            "102.0",
            "99.0",
            "101.0",
            "12.5",
            open_ms + FIFTEEN_MIN_MS - 1,
            "1260.0",
        ]
        with self.assertRaises(TFGSourceError):
            _parse_kline(row, "15m")
