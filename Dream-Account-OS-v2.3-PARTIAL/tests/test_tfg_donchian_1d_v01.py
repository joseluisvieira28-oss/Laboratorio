import unittest

from research import tfg_donchian_1d_discovery_runner_v01 as d


class Donchian1DTests(unittest.TestCase):
    def make_daily(self, n=80):
        base = d.common.parse_ms("2024-01-01T00:00:00.000Z")
        rows = []
        for i in range(n):
            t = base + i * d.DAY_MS
            p = 100.0 + i * 0.03
            rows.append(d.Candle(t, p, p + 1.0, p - 1.0, p + 0.1, 10.0, t + d.DAY_MS - 1))
        return rows

    def test_breakout_uses_prior_20_bars_excluding_signal(self):
        rows = self.make_daily()
        i = 30
        prior = max(c.high for c in rows[i - d.LOOKBACK : i])
        old = rows[i]
        rows[i] = d.Candle(old.open_time, prior - 0.2, prior + 0.8, prior - 0.6, prior + 0.4, old.volume, old.close_time)
        signals, raw, cancelled = d.derive_signals("BTCUSDT", rows)
        self.assertGreaterEqual(raw, 1)
        self.assertEqual(cancelled, 0)
        sig = next(x for x in signals if x.signal_open_time == rows[i].open_time)
        self.assertAlmostEqual(sig.prior_20_day_high, prior)
        self.assertGreater(sig.signal_close, prior)

    def test_equal_close_is_not_breakout(self):
        rows = self.make_daily()
        i = 30
        prior = max(c.high for c in rows[i - d.LOOKBACK : i])
        old = rows[i]
        rows[i] = d.Candle(old.open_time, prior - 0.2, prior + 0.8, prior - 0.6, prior, old.volume, old.close_time)
        signals, _, _ = d.derive_signals("BTCUSDT", rows)
        self.assertFalse(any(x.signal_open_time == rows[i].open_time for x in signals))

    def test_target_is_exactly_three_r_gross_geometry(self):
        rows = self.make_daily()
        i = 30
        prior = max(c.high for c in rows[i - d.LOOKBACK : i])
        old = rows[i]
        rows[i] = d.Candle(old.open_time, prior - 0.2, prior + 0.8, prior - 0.6, prior + 0.4, old.volume, old.close_time)
        signals, _, _ = d.derive_signals("BTCUSDT", rows)
        sig = next(x for x in signals if x.signal_open_time == rows[i].open_time)
        self.assertAlmostEqual(sig.target - sig.entry, 3.0 * (sig.entry - sig.stop), places=12)

    def test_same_bar_stop_target_ambiguity_stops_out(self):
        rows = self.make_daily()
        i = 30
        prior = max(c.high for c in rows[i - d.LOOKBACK : i])
        old = rows[i]
        rows[i] = d.Candle(old.open_time, prior - 0.2, prior + 0.8, prior - 0.6, prior + 0.4, old.volume, old.close_time)
        signals, _, _ = d.derive_signals("BTCUSDT", rows)
        sig = next(x for x in signals if x.signal_open_time == rows[i].open_time)
        eidx = next(j for j, c in enumerate(rows) if c.open_time == sig.entry_open_time)
        c = rows[eidx]
        rows[eidx] = d.Candle(c.open_time, sig.entry, sig.target * 1.01, sig.stop * 0.99, sig.entry, c.volume, c.close_time)
        out = d.simulate(sig, rows, d.BASE_COST_PCT)
        self.assertEqual(out.exit_reason, "STOP_AMBIGUOUS_SAME_BAR")
        self.assertTrue(out.same_bar_stop_target_ambiguity)


if __name__ == "__main__":
    unittest.main()
