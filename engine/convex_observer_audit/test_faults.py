"""Offline fault injection. No credentials, exchange requests or Telegram sends."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from engine.three_convex_v07.feed import _save_json_atomic, FeedHalt, fetch_complete, MS5, fresh_signals
from engine.three_convex_v07.watch import DurableQueue, cycle as cycle07
from engine.three_convex_v07.test_telegram_watch import flat, fake_signal, NoNetworkBot
from engine.three_convex_v07.test_feed import fixture
from engine.three_convex_v11.watcher import Outbox, cycle as cycle11

SIG={'lane':'ETH_CONVEX_1H_EXPERIMENTAL','symbol':'ETH_USDT',
     'signal_close_ms':3600000,'signal_id':'ETH_CONVEX_1H_EXPERIMENTAL:3600000'}

class Faults(unittest.TestCase):
    def test_v07_both_sol_observations_survive_collision(self):
        with tempfile.TemporaryDirectory() as d:
            q=DurableQueue(d); bot=NoNetworkBot()
            try:
                with patch('engine.three_convex_v07.watch.account_inspect',return_value=flat()), patch('engine.three_convex_v07.watch.fresh_signals',side_effect=[[fake_signal(),fake_signal('SOL_CONVEX_1H')],[]]):
                    cycle07(q,bot,account_client=None,public_clock=lambda:1000000,feed=lambda *a:[],now_ms=1000000)
                self.assertEqual(sum('SINAL DETETADO' in m for m in bot.messages),2)
            finally:q.close()

    def test_cache_orphan_tmp_does_not_permanently_block_writer(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cache.json'; p.with_suffix('.tmp').write_text('interrupted')
            _save_json_atomic(p,{'complete':True})
            self.assertEqual(json.loads(p.read_text()),{'complete':True})

    def test_v11_pending_drains_even_if_public_source_fails(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);q.queue(SIG);q.db.close();q=Outbox(d); sent=[]
            try:
                try:cycle11(q,sent.append,now_ms=3602000,server_ms=3602000,fetch=lambda *a:(_ for _ in ()).throw(FeedHalt('offline')))
                except FeedHalt:pass
                self.assertEqual(len(sent),1)
                self.assertEqual(q.pending(),0)
            finally:q.db.close()

    def test_v11_old_pending_is_marked_late(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);q.queue(SIG);sent=[]
            try:
                q.flush(sent.append,7200000)
                self.assertIn('ATRASADO',sent[0])
            finally:q.db.close()

    def test_v11_two_connections_cannot_send_same_notice_concurrently(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d);q.queue(SIG);q.db.close()
            entered=threading.Event();second_done=threading.Event();sent=[]; errors=[]
            def worker(first):
                box=Outbox(d)
                def send(msg):
                    sent.append(msg)
                    if first:
                        entered.set();second_done.wait(1)
                try:box.flush(send,3602000)
                except Exception as e:errors.append(type(e).__name__)
                finally:
                    box.db.close()
                    if not first:second_done.set()
            a=threading.Thread(target=worker,args=(True,));a.start();self.assertTrue(entered.wait(3))
            b=threading.Thread(target=worker,args=(False,));b.start();a.join(8);b.join(8)
            self.assertFalse(a.is_alive() or b.is_alive());self.assertEqual(errors,[])
            self.assertEqual(len(sent),1)

    def test_network_failure_does_not_save_partial_cache_and_recovers(self):
        now=2000000000000
        with tempfile.TemporaryDirectory() as d:
            public,calls=fixture('SOL_USDT',now)
            def interrupted(*a):
                if len(calls)==1:raise FeedHalt('internet interrupted')
                return public(*a)
            with self.assertRaises(FeedHalt):fetch_complete('SOL_USDT',now,d,public=interrupted)
            self.assertFalse((Path(d)/'SOL_USDT_binance_5m.json').exists())
            self.assertTrue(fetch_complete('SOL_USDT',now,d,public=public))

    def test_signal_after_eligibility_window_not_replayed(self):
        with patch('engine.three_convex_v07.feed.closed_signal_decisions',return_value=[fake_signal(close=300000)]):
            self.assertEqual(fresh_signals('SOL_USDT',[],480001,0),[])

    def test_v11_clock_drift_does_not_collect(self):
        with tempfile.TemporaryDirectory() as d:
            q=Outbox(d)
            try:
                with self.assertRaisesRegex(FeedHalt,'CLOCK'):
                    cycle11(q,lambda m:None,now_ms=3602000,server_ms=3702000,fetch=lambda *a:self.fail('clock must block collection'))
            finally:q.db.close()

if __name__=='__main__':unittest.main()

class BoundaryTests(unittest.TestCase):
    def test_os_lock_blocks_second_instance_and_releases(self):
        from engine.three_convex_v07.observer_io import instance_lock
        with tempfile.TemporaryDirectory() as d:
            with instance_lock(d):
                with self.assertRaises(OSError):
                    with instance_lock(d):self.fail('second instance accepted')
            with instance_lock(d):pass

    def test_exchange_write_rejected_before_network(self):
        from engine.three_convex_v07.watch import ObserverTransport, WatchHalt, PrivateKey
        client=ObserverTransport(PrivateKey('synthetic','synthetic'),opener=lambda *a,**k:self.fail('network forbidden'))
        with self.assertRaisesRegex(WatchHalt,'WRITE_FORBIDDEN'):
            client._exchange('POST','/api/v1/private/order/create',{})

    def test_telegram_ack_id_is_durable(self):
        with tempfile.TemporaryDirectory() as d:
            box=Outbox(d);box.queue(SIG)
            box.flush(lambda m:123456,3602000);box.db.close()
            box=Outbox(d)
            try:self.assertEqual(box.db.execute('SELECT telegram_message_id FROM notices').fetchone()[0],123456)
            finally:box.db.close()

    def test_incomplete_cache_is_reacquired(self):
        now=2000000000000
        with tempfile.TemporaryDirectory() as d:
            public,_=fixture('SOL_USDT',now)
            original=fetch_complete('SOL_USDT',now,d,public=public)
            p=Path(d)/'SOL_USDT_binance_5m.json'; saved=json.loads(p.read_text());saved['bars']=saved['bars'][10:];p.write_text(json.dumps(saved))
            restored=fetch_complete('SOL_USDT',now,d,public=public)
            self.assertEqual(original,restored)

    def test_all_timeframes_match_independent_ohlcv_groups(self):
        from engine.three_convex_v05.signals import Bar,aggregate_complete
        bars=[Bar(i*MS5,100+i*.01,102+i*.01,98+i*.01,101+i*.01,10+i) for i in range(48*260+17)]
        for n in (1,6,12,48):
            actual=aggregate_complete(bars,n)
            expected=[]
            for start in range(0,len(bars)-n+1,n):
                group=bars[start:start+n]
                expected.append(dict(t=start*MS5,open=group[0].open,high=max(x.high for x in group),low=min(x.low for x in group),close=group[-1].close,volume=sum(x.volume for x in group)))
            self.assertEqual(actual,expected)
