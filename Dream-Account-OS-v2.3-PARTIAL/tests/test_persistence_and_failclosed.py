import tempfile
import unittest

from dream_account.config import Settings
from dream_account.database import Journal
from dream_account.mexc_client import DataUnavailable
from dream_account.scanner import Scanner


class BrokenClient:
    def exchange_info(self):
        raise DataUnavailable("simulated outage")


class RateLimitedClient:
    def exchange_info(self):
        raise DataUnavailable("HTTP 429: simulated rate limit")


class MalformedClient:
    def exchange_info(self):
        raise DataUnavailable("Malformed exchangeInfo")


class PersistenceTests(unittest.TestCase):
    def test_journal_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/journal.sqlite3"
            one = Journal(path)
            one.record_scan("2026-01-01T00:00:00Z", "TEST", "PASS", "RANGE", {})
            one.close()
            two = Journal(path)
            self.assertEqual(two.counts()["market_scans"], 1)
            two.close()

    def test_api_outage_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/journal.sqlite3")
            result = Scanner(BrokenClient(), Settings(database_path=f"{directory}/journal.sqlite3"), journal).live_scan()
            self.assertEqual(result.status, "FAIL_CLOSED")
            self.assertEqual(result.candidates, [])
            journal.close()

    def test_rate_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/journal.sqlite3")
            result = Scanner(RateLimitedClient(), Settings(), journal).live_scan()
            self.assertEqual(result.status, "FAIL_CLOSED")
            self.assertIn("429", result.errors[0])
            journal.close()

    def test_malformed_data_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Journal(f"{directory}/journal.sqlite3")
            result = Scanner(MalformedClient(), Settings(), journal).live_scan()
            self.assertEqual(result.status, "FAIL_CLOSED")
            self.assertEqual(result.pairs_scanned, 0)
            journal.close()


if __name__ == "__main__":
    unittest.main()
