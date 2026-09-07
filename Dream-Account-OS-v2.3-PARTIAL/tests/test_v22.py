import json
import tempfile
import unittest
from unittest.mock import patch

from dream_account.candles import validate_candles
from dream_account.database import Journal
from dream_account.models import Candle
from dream_account.reliability import ReliableHTTP
from dream_account.state_machine import PaperTrade, SignalStateMachine


class FakeResponse:
    status = 200
    fp = None
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.payload).encode()


class V22Tests(unittest.TestCase):
    def test_candle_boundary_and_open_candle(self):
        width = 60_000
        rows = [Candle(0, 1, 2, .5, 1.5, 10, width - 1), Candle(width, 1.5, 2, 1, 1.7, 10, 2 * width - 1)]
        result = validate_candles(rows, "1m", 90_000)
        self.assertTrue(result.valid)
        self.assertEqual(result.open_candles, 1)
        self.assertTrue(rows[0].closed)
        self.assertFalse(rows[1].closed)

    def test_candle_gap_fails_integrity(self):
        rows = [Candle(0, 1, 2, .5, 1.5, 10, 59_999), Candle(120_000, 1.5, 2, 1, 1.7, 10, 179_999)]
        result = validate_candles(rows, "1m", 200_000)
        self.assertFalse(result.valid)
        self.assertEqual(len(result.gaps), 1)

    def test_state_machine_blocks_impossible_jump(self):
        machine = SignalStateMachine("sig-1")
        with self.assertRaises(ValueError):
            machine.transition("PAPER_OPEN", "illegal")

    def test_complete_paper_lifecycle_and_persistence(self):
        machine = SignalStateMachine("sig-2")
        for target in ["WATCHING", "ARMED", "ACTIVATED", "PAPER_OPEN"]:
            machine.transition(target, "test")
        trade = PaperTrade("sig-2", "2026-01-01T00:00:00Z", 100, 98, 104, 106, 0.56, 1.12, .05, 86, "A+", "RISK_ON_TREND")
        self.assertEqual(trade.update(104.5, 99, 104, "2026-01-01T01:00:00Z"), "TP1_HIT")
        machine.transition("TP1_HIT", "target one")
        self.assertEqual(trade.update(106.2, 103, 106, "2026-01-01T02:00:00Z"), "TP2_HIT")
        machine.transition("TP2_HIT", "target two")
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/db.sqlite3"
            journal = Journal(path)
            journal.record_signal("sig-2", trade.entry_timestamp, "TESTUSDT", "BREAKOUT_RETEST", "A+", {})
            for transition in machine.history: journal.record_transition("sig-2", transition)
            journal.save_paper_trade("paper-2", trade, machine.state)
            journal.close()
            reopened = Journal(path)
            row = reopened.connection.execute("SELECT state,realized_r,closed_at FROM paper_trades WHERE id='paper-2'").fetchone()
            self.assertEqual(row[0], "TP2_HIT")
            self.assertGreater(row[1], 0)
            self.assertIsNotNone(row[2])
            reopened.close()

    def test_reliability_metrics_and_cache(self):
        transport = ReliableHTTP(max_retries=0)
        with patch("urllib.request.urlopen", return_value=FakeResponse({"ok": True})) as call:
            first = transport.get_json(["https://api.example"], "/health", cache_ttl=60)
            second = transport.get_json(["https://api.example"], "/health", cache_ttl=60)
        self.assertEqual(first, second)
        self.assertEqual(call.call_count, 1)
        report = transport.report()["api.example"]
        self.assertEqual(report["success_rate"], 100.0)
        self.assertIsNotNone(report["last_successful_snapshot"])


if __name__ == "__main__":
    unittest.main()
