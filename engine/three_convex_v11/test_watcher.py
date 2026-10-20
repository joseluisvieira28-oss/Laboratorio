import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from engine.three_convex_v05.signals import Bar,MS5
from engine.three_convex_v07.feed import FeedHalt
from engine.three_convex_v11.watcher import Outbox,cycle
from engine.three_convex_v11.public_feed import fetch_experimental

class WatcherTests(unittest.TestCase):
    def test_outbox_duplicate_and_survive_restart(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            s={"lane":"ETH_CONVEX_1H_EXPERIMENTAL","symbol":"ETH_USDT",
               "signal_close_ms":3600000,
               "signal_id":"ETH_CONVEX_1H_EXPERIMENTAL:3600000"}
            q.queue(s);q.queue(s)
            self.assertEqual(q.pending(),1)
            q.db.close()
            q=Outbox(d)
            sent=[]
            self.assertEqual(q.flush(sent.append,4000000),1)
            self.assertEqual(q.flush(sent.append,4000000),0)
            self.assertEqual(len(sent),1)
            q.db.close()
    def test_healthy_source_notifications_survive_later_source_failure(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            sent=[]
            with patch("engine.three_convex_v11.watcher.experimental_signals",side_effect=lambda symbol,*a: [
                {"lane":"SOL_CONVEX_4H_EXPERIMENTAL","symbol":"SOL_USDT",
                "signal_close_ms":300000,
                "signal_id":"SOL_CONVEX_4H_EXPERIMENTAL:300000"}
            ] if symbol=="SOL_USDT" else []):
                def fail_on_bnb(symbol,now,path):
                    if symbol=="BNB_USDT": raise FeedHalt("FAILED_SECOND_SOURCE")
                    return []
                report=cycle(q,sent.append,now_ms=302000,server_ms=302000,fetch=fail_on_bnb)
            self.assertFalse(report["sources_ok"])
            self.assertTrue(report["source_status"]["SOL_USDT"])
            self.assertEqual(q.pending(),0)
            self.assertEqual(len(sent),1)
            q.db.close()
    def test_failed_telegram_preserves_queue(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            s={"lane":"ETH_CONVEX_1H_EXPERIMENTAL","symbol":"ETH_USDT",
               "signal_close_ms":3600000,"signal_id":"ETH_CONVEX_1H_EXPERIMENTAL:3600000"}
            q.queue(s)
            with self.assertRaises(RuntimeError):
                q.flush(lambda m: (_ for _ in ()).throw(RuntimeError("offline")),4000000)
            self.assertEqual(q.pending(),1)
            q.db.close()
    def test_symbols_are_public_only(self):
        self.assertEqual(set(fetch_experimental.__globals__["SYMBOLS"]),
                         {"SOL_USDT","BNB_USDT","ETH_USDT"})
if __name__=="__main__":unittest.main()
