"""Synthetic-only test: recent CONVEX signals reader never mutates SQLite databases."""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from tools.convex_signal_forensics import recent_signals as target

class Tests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.local = Path(self.t.name)
        self.before = {}
        self.add_data()

    def add_data(self):
        def make(version, sql, row):
            folder, name = target.DBS[version]
            path = self.local / "CryptoLab" / folder / "data" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(path)) as db, db:
                db.execute(sql)
                db.execute(row[0], row[1])
            self.before[str(path)] = path.read_bytes()
        make("V07",
             "CREATE TABLE outbox (id TEXT PRIMARY KEY, sent_at_ms INTEGER, telegram_message_id INTEGER, added_ms INTEGER)",
             ("INSERT INTO outbox VALUES(?,?,?,?)",
              ("SIGNAL:SOL_CONVEX_NATIVE_5M:1792097700000",1792097710000,222,1792097705000)))
        make("V11",
             "CREATE TABLE notices (id TEXT PRIMARY KEY, sent_ms INTEGER, telegram_message_id INTEGER)",
             ("INSERT INTO notices VALUES(?,?,?)",
              ("ETH_CONVEX_1H_EXPERIMENTAL:1792098000000",None,None)))
        make("V12",
             "CREATE TABLE notices (id TEXT PRIMARY KEY, sent_ms INTEGER, close_ms INTEGER, expired_ms INTEGER)",
             ("INSERT INTO notices VALUES(?,?,?,?)",
              ("BNB_CONVEX_NATIVE_5M_EXPERIMENTAL:1792097700000",1792097711000,1792097700000,None)))

    def test_full_three_version_report(self):
        report = target.assess(self.local, 30)
        self.assertEqual(len(report["events"]), 3)
        self.assertTrue(all(x["status"] == "READONLY_QUERY_OK" for x in report["monitors"].values()))
        self.assertTrue(report["local_only"])
        v07 = next(x for x in report["events"] if x["version"] == "V07")
        v11 = next(x for x in report["events"] if x["version"] == "V11")
        v12 = next(x for x in report["events"] if x["version"] == "V12")
        self.assertEqual(v07["telegram_message_id"], 222)
        self.assertTrue(v07["api_message_id_persisted"])
        self.assertFalse(v11["outbox_marked_sent"])
        self.assertFalse(v12["api_message_id_persisted"])
        self.assertEqual(v12["signal_close_utc"], "2026-10-15T20:55:00Z")

    def test_missing_db_fails_explicitly(self):
        folder, name = target.DBS["V11"]
        (self.local / "CryptoLab" / folder / "data" / name).unlink()
        self.assertEqual(target.read_one(self.local, "V11", 10)["status"], "SQLITE_NOT_FOUND")

    def test_input_invalid_id_ignored(self):
        folder, name = target.DBS["V12"]
        path = self.local / "CryptoLab" / folder / "data" / name
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("INSERT INTO notices VALUES(?,?,?,?)",
                       ("UNRECOGNIZED:1792098000000",None,1792098000000,None))
        self.assertEqual(target.read_one(self.local, "V12", 10)["unrecognized_rows_ignored"], 1)
        self.before[str(path)] = path.read_bytes()

    def test_repeated_reads_do_not_change_db_bytes(self):
        target.assess(self.local, 30)
        target.assess(self.local, 30)
        for p, raw in self.before.items():
            self.assertEqual(Path(p).read_bytes(), raw)

    def test_same_asset_same_close_is_flagged_not_a_trade(self):
        folder, name = target.DBS["V12"]
        path = self.local / "CryptoLab" / folder / "data" / name
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("INSERT INTO notices VALUES(?,?,?,?)",
                       ("SOL_CONVEX_30M_EXPERIMENTAL:1792097700000",None,1792097700000,None))
        report = target.assess(self.local, 30)
        self.assertEqual(len(report["potential_same_symbol_same_close_overlaps"]),1)
        self.assertEqual(report["potential_same_symbol_same_close_overlaps"][0]["symbol"],"SOL_USDT")

if __name__ == "__main__":
    unittest.main()
