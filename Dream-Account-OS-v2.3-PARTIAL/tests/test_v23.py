import tempfile
import unittest

from dream_account.collector import cross_check_prices
from dream_account.config import Settings
from dream_account.data_contract import CollectionBatch, DataQuality, NormalizedSnapshot
from dream_account.database import Journal
from dream_account.live_engine import DreamAccountEngine


def snap(symbol, quality=DataQuality.VERIFIED):
    return NormalizedSnapshot("2026-01-01T00:00:00+00:00", "MEXC", symbol, "SPOT", 100, 99.9, 100.1,
                              .2, 10_000_000, data_quality=quality)


class V23Tests(unittest.TestCase):
    def test_coverage_gate_at_95_percent(self):
        batch = CollectionBatch("now", 20, [snap(f"S{i}") for i in range(19)])
        self.assertEqual(batch.coverage_pct, 95.0)
        self.assertTrue(batch.gate_passed)

    def test_stale_is_excluded_from_signals(self):
        rows = [snap(f"S{i}") for i in range(19)] + [snap("STALE", DataQuality.STALE)]
        batch = CollectionBatch("now", 20, rows)
        self.assertTrue(batch.gate_passed)
        result = DreamAccountEngine(Settings()).evaluate(batch, "RISK_ON")
        self.assertNotIn("STALE", [x.symbol for x in result])

    def test_partial_never_reaches_engine(self):
        rows = [snap(f"S{i}") for i in range(20)] + [snap("BAD", DataQuality.PARTIAL)]
        result = DreamAccountEngine(Settings()).evaluate(CollectionBatch("now", 20, rows), "RISK_ON")
        self.assertNotIn("BAD", [x.symbol for x in result])

    def test_cross_check_flags_divergence(self):
        mexc = {"BTCUSDT": 100, "ETHUSDT": 100, "SOLUSDT": 100}
        other = {"BTCUSDT": 100.2, "ETHUSDT": 105, "SOLUSDT": 100}
        flags = cross_check_prices(mexc, other)
        self.assertEqual(flags["BTCUSDT"], "PASS")
        self.assertTrue(flags["ETHUSDT"].startswith("DATA_ANOMALY"))

    def test_normalized_snapshot_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/db.sqlite3"
            journal = Journal(path); journal.record_snapshot(snap("BTCUSDT")); journal.close()
            journal = Journal(path)
            row = journal.connection.execute("SELECT symbol,data_quality FROM normalized_snapshots").fetchone()
            self.assertEqual(row, ("BTCUSDT", "VERIFIED")); journal.close()


if __name__ == "__main__":
    unittest.main()
