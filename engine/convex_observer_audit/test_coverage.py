"""Coverage receipts and source independence; offline deterministic fault injection."""
import tempfile
import unittest
from unittest.mock import patch
from engine.three_convex_v05.signals import Bar,MS5
from engine.three_convex_v07.coverage import Coverage
from engine.three_convex_v07.watch import DurableQueue,cycle as cycle07
from engine.three_convex_v07.feed import FeedHalt
from engine.three_convex_v07.telegram import TelegramHalt
from engine.three_convex_v07.test_telegram_watch import flat,NoNetworkBot,fake_signal
from engine.three_convex_v11.watcher import Outbox,cycle as cycle11

class CoverageTests(unittest.TestCase):
    def test_gap_ranges_persist_and_no_signal_is_not_inferred(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);c=Coverage(q.db)
            c.record('SOL5',1,[],MS5*1000+2000,MS5*999,[],error=FeedHalt('offline'))
            c.record('SOL5',1,[],MS5*1005+2000,MS5*999,[],error=FeedHalt('offline'))
            self.assertEqual(c.summary()['unvisited_closes'],5) # 999 plus 1001..1004
            self.assertEqual(c.summary()['lanes']['SOL5']['state'],'SOURCE_FAILED')
            q.db.close();q=Outbox(d)
            try:self.assertEqual(Coverage(q.db).summary()['unvisited_closes'],5)
            finally:q.db.close()

    def test_no_signal_receipt_requires_complete_history_and_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);c=Coverage(q.db);close=MS5*1000
            bars=[Bar(i*MS5,100,101,99,100,10) for i in range(700,1000)]
            c.record('SOL5',1,bars,close+2000,close,[])
            c.record('SOL5',1,[],close+100000,close,[],error=FeedHalt('later failure'))
            try:
                self.assertEqual(q.db.execute('SELECT state FROM observer_coverage').fetchone()[0],'NO_SIGNAL')
                self.assertEqual(c.summary()['lanes']['SOL5']['state'],'SOURCE_FAILED')
            finally:q.db.close()

    def test_expired_close_is_not_classified_as_no_signal(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);c=Coverage(q.db);close=MS5*1000
            bars=[Bar(i*MS5,100,101,99,100,10) for i in range(700,1000)]
            c.record('SOL5',1,bars,close+180001,close,[])
            try:self.assertEqual(c.summary()['lanes']['SOL5']['state'],'EXPIRED_CLOSE')
            finally:q.db.close()

    def test_v07_healthy_sol_survives_bnb_failure(self):
        with tempfile.TemporaryDirectory() as d:
            q=DurableQueue(d);bot=NoNetworkBot()
            def source(symbol,*a):
                if symbol=='BNB_USDT':raise FeedHalt('bnb offline')
                return []
            try:
                with patch('engine.three_convex_v07.watch.account_inspect',return_value=flat()),patch('engine.three_convex_v07.watch.fresh_signals',return_value=[fake_signal()]):
                    report=cycle07(q,bot,account_client=None,public_clock=lambda:1000000,feed=source,now_ms=1000000)
                self.assertFalse(report['v5_public_source_ok'])
                self.assertEqual(sum('SINAL DETETADO' in m for m in bot.messages),1)
                self.assertEqual(report['source_status'],{'SOL_USDT':True,'BNB_USDT':False})
            finally:q.close()

    def test_v11_telegram_failure_does_not_abort_collection(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);calls=[]
            def source(symbol,*a):calls.append(symbol);return []
            def offline(message):raise TelegramHalt('offline')
            q.queue({'lane':'ETH_CONVEX_1H_EXPERIMENTAL','symbol':'ETH_USDT','signal_id':'ETH_CONVEX_1H_EXPERIMENTAL:3600000','signal_close_ms':3600000})
            try:
                with patch('engine.three_convex_v11.watcher.experimental_signals',return_value=[]):
                    report=cycle11(q,offline,now_ms=3602000,server_ms=3602000,fetch=source)
                self.assertEqual(len(calls),3);self.assertEqual(q.pending(),1)
                self.assertEqual(report['status'],'V11_DEGRADED_READONLY')
            finally:q.db.close()

    def test_slow_fetch_rechecks_freshness_before_signal(self):
        from engine.three_convex_v11.experimental import experimental_signals
        n=6;close=260*n*MS5;bars=[]
        for i in range(260):
            price=100+i*.2 if i<230 else (160 if i<259 else 150)
            volume=1000 if i==259 else 10
            bars.extend(Bar((i*n+j)*MS5,price,price+1,price-1,price,volume) for j in range(n))
        self.assertTrue(experimental_signals('BNB_USDT',bars,close+2000,0))
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);q.activation(0);sent=[]
            try:
                report=cycle11(q,sent.append,now_ms=close+2000,server_ms=close+2000,fetch=lambda *a:bars,completion_clock=lambda:close+180001)
                self.assertEqual(sent,[]);self.assertEqual(report['signal_events'],0)
                self.assertEqual(report['collection_elapsed_ms']['BNB_USDT'],178001)
            finally:q.db.close()
