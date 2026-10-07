import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from radar import mexc_universe_runtime as rt
from radar import mexc_universe_trade_scanner as sc

def candidate():
    now = time.time()
    return dict(symbol='TEST_USDT', side='LONG', signal_family='BREAKOUT',
                signal_candle_open=(int(now)//900)*900-900,
                confirmation_candle_open=(int(now)//3600)*3600-3600,
                source_book_timestamp=now, expires_at_epoch=now+60,
                entry=100, stop=99, tp1=101.6, tp2=102.5, contracts=1,
                notional_usdt=100, leverage=3, margin_mode='ISOLATED',
                fee_roundtrip_bps=16, funding_rate=0.0001, funding_cycle_hours=8,
                entry_impact_bps=0, net_rr_tp1=1.3, net_rr_tp2=2.1,
                invalidation='closed 15m breach of stop')

def result(candidates=None):
    c = candidates or []
    return dict(source_health='OK', verdict='TRADE' if c else 'NO_TRADE',
                classification='TRADEABLE_CANDIDATE' if c else 'RADAR_EMPTY',
                candidates=c, universe_eligible_count=41, reject_counts={'NO_SIGNAL': 40})

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.env={'TELEGRAM_BOT_TOKEN':'fake-secret', 'TELEGRAM_CHAT_ID':'fake-chat'}
    def tearDown(self):
        self.temp.cleanup()
    def prepare(self, run='1', value=None, env=None):
        return rt.prepare(self.root, run, scanner=lambda: value or result(),
                          environ=self.env if env is None else env)
    def test_deterministic_identity(self):
        c=candidate(); d=copy.deepcopy(c);d['entry']=101
        self.assertEqual(rt.signal_id(c),rt.signal_id(d))
        for key,value in [('symbol','OTHER_USDT'),('side','SHORT'),('signal_family','TREND_RETEST'),('signal_candle_open',c['signal_candle_open']-900)]:
            d=copy.deepcopy(c);d[key]=value
            self.assertNotEqual(rt.signal_id(c),rt.signal_id(d))
    def test_no_trade_silent(self):
        self.prepare(); post=Mock()
        rt.notify(self.root,'1',environ=self.env,post=post)
        post.assert_not_called()
    def test_missing_secrets_disabled(self):
        for env in ({},{'TELEGRAM_BOT_TOKEN':'fake'},{'TELEGRAM_CHAT_ID':'fake'}):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                value=rt.prepare(root,'1',scanner=lambda:result([candidate()]),environ=env)
                self.assertEqual(value['notifier'],'DISABLED_MISSING_SECRETS')
                self.assertEqual(value['pending_signal_ids'],[])
                post=Mock();rt.notify(root,'1',environ=env,post=post);post.assert_not_called()
    def test_send_once_across_runs_and_restarts(self):
        c=candidate(); self.prepare(value=result([c]))
        post=Mock(return_value=Mock(status_code=200,json=lambda:{'ok':True}))
        rt.notify(self.root,'1',environ=self.env,post=post)
        rt.notify(self.root,'1',environ=self.env,post=post)
        v=self.prepare('2',result([c]));self.assertEqual(v['pending_signal_ids'],[])
        rt.notify(self.root,'2',environ=self.env,post=post)
        self.assertEqual(post.call_count,1)
        self.assertFalse(post.call_args.kwargs['allow_redirects'])
    def test_ambiguous_post_no_retry_or_secret_log(self):
        self.prepare(value=result([candidate()]))
        post=Mock(side_effect=RuntimeError('fake-secret fake-chat'))
        event=rt.notify(self.root,'1',environ=self.env,post=post)
        self.assertIn('UNKNOWN_NO_RETRY',event['results'].values())
        self.assertNotIn('fake-secret',json.dumps(event))
        rt.notify(self.root,'1',environ=self.env,post=post)
        self.assertEqual(post.call_count,1)
    def test_expired_at_send_silent(self):
        c=candidate();self.prepare(value=result([c]));post=Mock()
        with patch.object(rt.time,'time',return_value=c['expires_at_epoch']+1):
            event=rt.notify(self.root,'1',environ=self.env,post=post)
        self.assertIn('EXPIRED',event['results'].values());post.assert_not_called()
    def test_source_error_fail_closed(self):
        def broken(): raise RuntimeError('fake-secret')
        v=rt.prepare(self.root,'1',scanner=broken,environ=self.env)
        self.assertEqual(v['source_health'],'BLOCKED');self.assertEqual(v['verdict'],'NO_TRADE')
        self.assertEqual(v['pending_signal_ids'],[])
    def test_stale_and_future_candidates_fail_closed(self):
        for field,value in [('expires_at_epoch',time.time()-1),('signal_candle_open',0),('confirmation_candle_open',0),('source_book_timestamp',time.time()+100)]:
            with tempfile.TemporaryDirectory() as directory:
                c=candidate();c[field]=value
                v=rt.prepare(Path(directory),'1',scanner=lambda:result([c]),environ=self.env)
                self.assertEqual(v['source_health'],'BLOCKED');self.assertEqual(v['candidates'],[])
    def test_receipt_append_only(self):
        self.prepare()
        before=(self.root/'runs/1.json').read_bytes()
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(before,(self.root/'runs/1.json').read_bytes())
    def test_ledger_loss_fail_closed(self):
        self.prepare();(self.root/'notifications.json').unlink()
        with self.assertRaises(ValueError):self.prepare('2')
    def test_payload_format(self):
        c=rt.payload(candidate());text=rt.format_message(c)
        for item in ['TEST_USDT LONG','Entry:','Stop:','TP1:','TP2:','3x ISOLATED','Validation:','Fees assumption:','Funding:','Depth impact:','Net RR','Signal:','Expiry:','Invalidation:','signal_id:']:
            self.assertIn(item,text)
    def test_source_timestamp(self):
        with patch.object(sc.time,'time',return_value=1000):
            self.assertEqual(sc.fresh_timestamp(999000),999)
            for value in (None,0,900000,1100000,float('nan')):
                with self.assertRaises((RuntimeError,TypeError)):sc.fresh_timestamp(value)
    def test_candle_gap_duplicate_unequal_rejected(self):
        now=180000;secs=900;last=now//secs*secs-secs
        times=list(range(last-79*secs,last+1,secs))
        base={'time':times,'open':[100]*80,'close':[100]*80,'high':[101]*80,'low':[99]*80,'vol':[1]*80}
        with patch.object(sc.time,'time',return_value=now),patch.object(sc,'req',return_value=base):
            self.assertEqual(len(sc.candles('TEST','Min15',secs)),80)
        for variant in ('gap','duplicate','unequal','stale','nan'):
            d=copy.deepcopy(base)
            if variant=='gap':
                for arr in d.values():arr.pop(20)
            elif variant=='duplicate':d['time'][20]=d['time'][19]
            elif variant=='unequal':d['vol'].pop()
            elif variant=='stale':
                for arr in d.values():arr.pop()
            else:d['close'][20]=float('nan')
            with patch.object(sc.time,'time',return_value=now),patch.object(sc,'req',return_value=d):
                with self.assertRaises(RuntimeError):sc.candles('TEST','Min15',secs)

if __name__=='__main__':unittest.main()
