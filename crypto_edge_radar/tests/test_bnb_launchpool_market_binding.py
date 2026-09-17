from __future__ import annotations

from unittest import TestCase

from radar.strategies.bnb_launchpool_demand import (
    FIFTEEN_MIN_MS,
    FORWARD_BOUNDARY_MS,
    HOLD_MS,
    BNBLaunchpoolSourceError,
    _parse_binance_spot_kline,
    exact_exit_open_ms,
    first_eligible_entry_open_ms,
)


class BNBLaunchpoolMarketBindingTests(TestCase):
    def test_entry_is_strictly_after_signal_even_on_exact_boundary(self) -> None:
        boundary = 1_800_000_000_000
        boundary -= boundary % FIFTEEN_MIN_MS
        self.assertEqual(first_eligible_entry_open_ms(boundary), boundary + FIFTEEN_MIN_MS)
        self.assertEqual(first_eligible_entry_open_ms(boundary + 1), boundary + FIFTEEN_MIN_MS)
        self.assertEqual(
            first_eligible_entry_open_ms(boundary + FIFTEEN_MIN_MS - 1),
            boundary + FIFTEEN_MIN_MS,
        )

    def test_exit_is_exactly_24h_after_entry(self) -> None:
        entry = 1_800_000_000_000
        entry -= entry % FIFTEEN_MIN_MS
        self.assertEqual(exact_exit_open_ms(entry), entry + HOLD_MS)
        self.assertEqual((exact_exit_open_ms(entry) - entry) // FIFTEEN_MIN_MS, 96)

    def test_binance_native_close_time_is_required(self) -> None:
        open_ms = 1_800_000_000_000
        open_ms -= open_ms % FIFTEEN_MIN_MS
        row = [
            open_ms,
            "0.0100",
            "0.0102",
            "0.0099",
            "0.0101",
            "100.0",
            open_ms + FIFTEEN_MIN_MS - 1,
            "1.01",
        ]
        bar = _parse_binance_spot_kline(row)
        self.assertEqual(bar.open_time, open_ms)
        self.assertEqual(bar.close_time, open_ms + FIFTEEN_MIN_MS - 1)

        bad = list(row)
        bad[6] = open_ms + FIFTEEN_MIN_MS
        with self.assertRaises(BNBLaunchpoolSourceError):
            _parse_binance_spot_kline(bad)

    def test_forward_boundary_is_hard_and_known(self) -> None:
        self.assertEqual(FORWARD_BOUNDARY_MS, 1_789_591_883_000)
