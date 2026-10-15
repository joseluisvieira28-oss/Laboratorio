"""Offline fixture proof for both 20:55 receipts and two cache reconstructions."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from tools.convex_signal_forensics import forensic_2055 as f

class ForensicFixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.local = Path(self.tmp.name)
        self.rows = []
        first = f.CLOSE_MS - 6 * f.MS5
        for i in range(6):
            t = first + i * f.MS5
            self.rows.append([t, 100.0, 101.0, 99.0, 100.5, 10.0])
        self.build_fixture()

    def cache(self, version, symbol, rows, backup=False):
        base = self.local / "CryptoLab"
        if backup:
            d = base / "CONVEX10_BACKUPS" / version / "test-backup"
            d.mkdir(parents=True, exist_ok=True)
            (d / "UPGRADE_RECEIPT.json").write_text('{"test":true}')
        else:
            d = base / f.ROOTS[version]
        dest = d / "data" / "market_cache" / (symbol + f.SUFFIXES[version])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps({"symbol": symbol, "source": "BINANCE_USDM_5M_PUBLIC", "bars": rows}))
        return dest

    def build_fixture(self):
        for version in ("V07", "V12"):
            for symbol in ("SOL_USDT", "BNB_USDT"):
                self.cache(version, symbol, self.rows[:4], backup=True)
                self.cache(version, symbol, self.rows[2:])
        v07db = self.local / "CryptoLab" / "ThreeConvexV07" / "data" / "v07_events.sqlite3"
        with sqlite3.connect(v07db) as db:
            db.execute("CREATE TABLE outbox (id TEXT PRIMARY KEY, sent_at_ms INTEGER, telegram_message_id INTEGER, added_ms INTEGER, message TEXT)")
            ev = f.EVENTS["V07_SOL_5M"]
            db.execute("INSERT INTO outbox VALUES(?,?,?,?,?)",
                (ev["row_id"], f.CLOSE_MS + 3000, 12345, f.CLOSE_MS + 2000,
                 "SOL_USDT SOL_CONVEX_NATIVE_5M:1792097700000"))
        v12db = self.local / "CryptoLab" / "ThreeConvexV12" / "data" / "V12_ONLY.sqlite3"
        with sqlite3.connect(v12db) as db:
            db.execute("CREATE TABLE notices (id TEXT PRIMARY KEY, sent_ms INTEGER, close_ms INTEGER, expired_ms INTEGER, message TEXT)")
            ev = f.EVENTS["V12_BNB_5M"]
            db.execute("INSERT INTO notices VALUES(?,?,?,?,?)",
                (ev["row_id"], f.CLOSE_MS + 3000, f.CLOSE_MS, None,
                 "BNB_USDT BNB_CONVEX_NATIVE_5M_EXPERIMENTAL:1792097700000"))

    @staticmethod
    def fn(_):
        return ([False] * (len(_) - 1) + [True], [{"score": 1}] * len(_))

    def audit(self):
        with patch.object(f, "LOOKBACK", 6), patch.object(f, "parent_signal_function", return_value=self.fn):
            return f.assess(self.local)

    def test_both_events_pass_offline_fixture(self):
        result = self.audit()
        a = result["event_results"]
        self.assertEqual(a["V07_SOL_5M"]["verdict"], "LOCAL_CAUSAL_REPLAY_PASS_NOT_EXTERNAL_MARKET_PARITY")
        self.assertEqual(a["V12_BNB_5M"]["verdict"], "LOCAL_CAUSAL_REPLAY_PASS_NOT_EXTERNAL_MARKET_PARITY")
        self.assertEqual(a["V07_SOL_5M"]["sqlite"]["telegram_message_id"], 12345)
        self.assertTrue(a["V12_BNB_5M"]["sqlite"]["telegram_message_id_not_persisted_by_v12"])
        self.assertTrue(all(e["independent_other_observer"]["full_source_parity_at_exact_close"]
                            for e in a.values()))

    def test_conflicting_backup_blocks_replay(self):
        altered = [list(x) for x in self.rows[:4]]
        altered[2][4] = 100.25
        self.cache("V07", "SOL_USDT", altered, backup=True)
        event = self.audit()["event_results"]["V07_SOL_5M"]
        self.assertIsNone(event["pinned_v5_replay_five_minute_signal"])
        self.assertGreater(event["source_window"]["overlap_conflicts"], 0)
        self.assertNotEqual(event["verdict"], "LOCAL_CAUSAL_REPLAY_PASS_NOT_EXTERNAL_MARKET_PARITY")

    def test_missing_old_cache_not_proved(self):
        old = self.local / "CryptoLab" / "CONVEX10_BACKUPS" / "V07" / "test-backup" / "data" / "market_cache" / "SOL_USDT_binance_5m.json"
        old.unlink()
        event = self.audit()["event_results"]["V07_SOL_5M"]
        self.assertLess(event["source_window"]["rows_available_in_target_window"], 6)
        self.assertNotEqual(event["verdict"], "LOCAL_CAUSAL_REPLAY_PASS_NOT_EXTERNAL_MARKET_PARITY")

    def test_outbox_missing_not_proved(self):
        path = self.local / "CryptoLab" / "ThreeConvexV07" / "data" / "v07_events.sqlite3"
        with sqlite3.connect(path) as db:
            db.execute("DELETE FROM outbox")
        result = self.audit()["event_results"]["V07_SOL_5M"]
        self.assertFalse(result["sqlite"]["found"])
        self.assertNotEqual(result["verdict"], "LOCAL_CAUSAL_REPLAY_PASS_NOT_EXTERNAL_MARKET_PARITY")

    def test_bad_cache_identity_rejected(self):
        target = self.cache("V12", "BNB_USDT", self.rows[2:])
        target.write_text(json.dumps({"symbol": "ETH_USDT", "source": "BINANCE_USDM_5M_PUBLIC",
                                     "bars": self.rows[2:]}))
        result = self.audit()["event_results"]["V12_BNB_5M"]
        self.assertFalse(result["source_window"]["exact_window_reconstructed"])

if __name__ == "__main__":
    unittest.main()
