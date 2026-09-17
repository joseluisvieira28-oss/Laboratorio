from __future__ import annotations

import unittest

from radar.strategies.tfg_donchian_regime_forward import FIFTEEN_MIN_MS, MEXCSpotKlineFeed


class FiveHundredRowMEXC(MEXCSpotKlineFeed):
    """Synthetic current MEXC behavior: <=500 rows even when client requests 1000."""

    def __init__(self, total_rows: int = 1200) -> None:
        super().__init__(timeout=1)
        self.total_rows = total_rows
        self.origin = 1_800_000_000_000 - (1_800_000_000_000 % FIFTEEN_MIN_MS)
        self.calls = 0

    def _get_json(self, query):
        self.calls += 1
        start = int(query["startTime"])
        end = int(query["endTime"])
        rows = []
        for i in range(self.total_rows):
            open_ms = self.origin + i * FIFTEEN_MIN_MS
            if start <= open_ms <= end:
                rows.append([
                    open_ms,
                    "100.0",
                    "101.0",
                    "99.0",
                    "100.5",
                    "1.0",
                    open_ms + FIFTEEN_MIN_MS,
                    "100.5",
                ])
                if len(rows) == 500:
                    break
        return rows


class MEXCPaginationTests(unittest.TestCase):
    def test_client_continues_after_short_500_row_page(self) -> None:
        feed = FiveHundredRowMEXC(total_rows=1200)
        start = feed.origin
        end = start + 1200 * FIFTEEN_MIN_MS
        rows = feed.klines(
            "BTCUSDT",
            "15m",
            start_ms=start,
            end_ms=end,
            now_ms=end + FIFTEEN_MIN_MS,
        )
        self.assertEqual(len(rows), 1200)
        self.assertEqual(rows[0].open_time, start)
        self.assertEqual(rows[-1].open_time, end - FIFTEEN_MIN_MS)
        self.assertGreaterEqual(feed.calls, 3)


if __name__ == "__main__":
    unittest.main()
