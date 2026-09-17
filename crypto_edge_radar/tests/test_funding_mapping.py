import csv
import tempfile
import unittest
from pathlib import Path

from radar.funding_mapping import build_2025_funding_mapping_report
from radar.market import MEXCFuturesPublicFeed


class StubFundingFeed(MEXCFuturesPublicFeed):
    def __init__(self, rows):
        super().__init__(timeout=1)
        self.rows = rows

    def funding_rate_history(self, symbol, *, page_num=1, page_size=1000):
        self._validate_contract_symbol(symbol)
        return list(self.rows) if page_num == 1 else []


class FundingMappingTests(unittest.TestCase):
    def _ledger(self, tmp: str) -> Path:
        path = Path(tmp) / "events.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["as_of", "entry", "exit", "position", "forward_return"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "as_of": "2025-01-01",
                    "entry": "2025-01-02",
                    "exit": "2025-01-09",
                    "position": 1,
                    "forward_return": 999.0,
                }
            )
        return path

    def test_boundary_settlements_create_range_not_false_precision(self):
        entry = 1735776000000  # 2025-01-02 00:00 UTC
        exit_ = 1736380800000  # 2025-01-09 00:00 UTC
        rows = [
            {"settleTime": entry, "fundingRate": 0.0001},
            {"settleTime": entry + 8 * 60 * 60 * 1000, "fundingRate": 0.0002},
            {"settleTime": exit_, "fundingRate": -0.0001},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            report = build_2025_funding_mapping_report(
                event_csv=self._ledger(tmp),
                feed=StubFundingFeed(rows),
            )
        event = report["events"][0]
        self.assertEqual(event["interior_settlement_count"], 1)
        self.assertEqual(event["boundary_settlement_count"], 2)
        self.assertAlmostEqual(event["funding_burden_min_bps"], 1.0)
        self.assertAlmostEqual(event["funding_burden_max_bps"], 3.0)
        self.assertFalse(report["market_outcome_columns_read"])
        self.assertFalse(report["orders_created"])

    def test_short_funding_sign_is_reversed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["as_of", "entry", "exit", "position"])
                writer.writeheader()
                writer.writerow({"as_of": "2025-01-01", "entry": "2025-01-02", "exit": "2025-01-09", "position": -1})
            entry = 1735776000000
            rows = [
                {"settleTime": entry - 1, "fundingRate": 0.0},
                {"settleTime": entry + 8 * 60 * 60 * 1000, "fundingRate": 0.0002},
                {"settleTime": 1736380800000 + 1, "fundingRate": 0.0},
            ]
            report = build_2025_funding_mapping_report(event_csv=path, feed=StubFundingFeed(rows))
        event = report["events"][0]
        self.assertAlmostEqual(event["funding_burden_min_bps"], -2.0)
        self.assertAlmostEqual(event["funding_burden_max_bps"], -2.0)


if __name__ == "__main__":
    unittest.main()
