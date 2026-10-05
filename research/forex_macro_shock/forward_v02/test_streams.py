import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector as c
from feeds import DepthBook, clock_quality
import ecb_watcher as e
import runtime
import supervisor
import calibration
from transport import PublicHTTP

NOW = 1791198000000
URL='https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp261029~abc123.en.html'
DOC=b'<html><head><meta property="article:published_time" content="2026-10-29"></head><body><h1>Monetary policy decisions</h1><p>The Governing Council decided to keep the interest rates unchanged.</p></body></html>'


class Books(unittest.TestCase):
    def setUp(self):
        self.b=DepthBook('binance'); self.b.snapshot({'lastUpdateId':100,'bids':[['1','10']],'asks':[['1.1','10']]})

    def delta(self, first=101, last=101, ts=NOW, bids=None):
        return {'e':'depthUpdate','s':'EURUSDT','U':first,'u':last,'E':ts,'b':bids or [['1','9']],'a':[]}

    def test_bootstrap_bridge_and_deletion(self):
        self.assertFalse(self.b.observation(NOW)['valid'])
        self.assertFalse(self.b.delta(self.delta(99,100),NOW))
        self.assertTrue(self.b.delta(self.delta(100,103),NOW))
        self.assertTrue(self.b.observation(NOW+50)['valid'])
        self.b.delta(self.delta(104,104,bids=[['1','0'],['.9','4']]),NOW)
        self.assertEqual(self.b.observation(NOW)['bid'],.9)

    def test_gap_clears_book(self):
        with self.assertRaises(ValueError): self.b.delta(self.delta(102,102),NOW)
        self.assertIsNone(self.b.last);self.assertFalse(self.b.ready)

    def test_duplicate_and_conflict(self):
        obj=self.delta();self.b.delta(obj,NOW)
        self.assertFalse(self.b.delta(obj,NOW+1))
        with self.assertRaises(ValueError):self.b.delta(self.delta(bids=[['1','8']]),NOW+2)
        self.assertFalse(self.b.ready)

    def test_timestamp_and_stale(self):
        self.b.delta(self.delta(),NOW)
        self.assertFalse(self.b.observation(NOW+1001)['valid'])
        with self.assertRaises(ValueError):self.b.delta(self.delta(102,102,ts=NOW-1),NOW)

    def test_reconnect_requires_new_bootstrap(self):
        self.b.delta(self.delta(),NOW);self.b.reset()
        with self.assertRaises(ValueError):self.b.delta(self.delta(102,102),NOW)

    def test_mexc_requires_matching_engine_clock(self):
        b=DepthBook('mexc');b.snapshot({'success':True,'data':{'version':1,'bids':[[1,10,1]],'asks':[[1.1,10,1]]}})
        msg={'channel':'push.depth','symbol':'EUR_USDT','ts':NOW,'data':{'version':2,'bids':[[1,9,1]],'asks':[]}}
        with self.assertRaises(ValueError):b.delta(msg,NOW)
        b.snapshot({'success':True,'data':{'version':1,'bids':[[1,10,1]],'asks':[[1.1,10,1]]}})
        msg['data']['cts']=NOW;self.assertTrue(b.delta(msg,NOW))

    def test_clock_uncertainty_gate(self):
        row={'started_ms':NOW,'received_ms':NOW+400,'rtt_ms':400}
        self.assertTrue(clock_quality(row,{'schema_valid':True,'exchange_ms':NOW+200}))
        self.assertFalse(clock_quality(row,{'schema_valid':True,'exchange_ms':NOW+300}))


class Watcher(unittest.TestCase):
    def test_exact_official_identity(self):
        self.assertTrue(e.allowed_release(URL,'2026-10-29'))
        for url in [URL.replace('www.ecb.europa.eu','evil.test'),URL.replace('/2026/','/2025/'),URL+'?redirect=1',URL.replace('261029','261217')]:
            self.assertFalse(e.allowed_release(url,'2026-10-29'))

    def test_discovery_dedup(self):
        raw=('<a href="'+URL+'">decision</a><a href="'+URL+'">copy</a>').encode()
        self.assertEqual(e.discover(raw,'2026-10-29'),[URL])

    def test_semantic_date_and_placeholder(self):
        self.assertTrue(e.publication(DOC,URL,'2026-10-29')['semantic_publication_detected'])
        for doc in [DOC.replace(b'2026-10-29',b'2026-10-28'),DOC.replace(b'interest rates',b'weather'),DOC.replace(b'unchanged',b'unchanged. Content coming soon')]:
            with self.assertRaises(ValueError):e.publication(doc,URL,'2026-10-29')

    def test_first_seen_restart_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=c.Store(Path(tmp)/'db');parsed=e.publication(DOC,URL,'2026-10-29')
            s.append('release1',{'source':'ecb_release','received_ms':NOW,'raw_sha256':c.digest(DOC),'validation':parsed},DOC)
            s.db.close();s=c.Store(Path(tmp)/'db')
            self.assertEqual(e.first_seen(s,parsed['event_id']),NOW)
            self.assertEqual(s.verify()['integrity'],'PASS');s.db.close()

    def test_publication_interval(self):
        self.assertTrue(e.timing_interval(NOW-1000,NOW,500))
        self.assertFalse(e.timing_interval(None,NOW,500))
        self.assertFalse(e.timing_interval(NOW-3000,NOW,500))
        self.assertFalse(e.timing_interval(NOW-1000,NOW,1500))

    def test_live_cutoff_and_url_allowlist(self):
        self.assertFalse(runtime.setup_allowed(c.SETUP_STOP))
        with self.assertRaises(PermissionError):runtime.fetch_allowed('https://api.mexc.com/api/v1/private/account/assets','bad')

    def test_persistent_runtime_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=runtime.Runtime(Path(tmp)/'db')
            try:
                with self.assertRaises(RuntimeError):runtime.Runtime(Path(tmp)/'db')
            finally:a.store.release(a.owner);a.store.db.close()

    def test_calibration_cannot_promote_short_or_invalid_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=c.Store(Path(tmp)/'db')
            raw=c.canonical({'grid_ms':1791198000000,'source_valid':False}).encode()
            s.append('grid',{'source':'paired_grid','raw_sha256':c.digest(raw),'freeze_sha256':runtime.FREEZE_HASH},raw)
            result=calibration.evaluate(s)
            self.assertEqual(result['verdict'],'OPERATIONALLY_BLOCKED')
            self.assertEqual(result['valid_paired_grids'],0)
            self.assertFalse(result['activation']);self.assertIsNone(result['calibration'])
            s.db.close()

    def test_pooled_http_rejects_private_and_redirects(self):
        class Response:
            status_code=302;headers={}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def iter_raw(self):yield b'redirect'
        class Client:
            def stream(self,*args):return Response()
        http=PublicHTTP(Client())
        with self.assertRaises(PermissionError):http.fetch('bad','https://api.mexc.com/api/v1/private/account/assets')
        row,raw=http.fetch('binance_clock')
        self.assertIn('REDIRECT_NOT_ALLOWED',row['error'])
        self.assertEqual(raw,b'redirect')

    def test_supervisor_uses_prospective_full_weekday(self):
        from datetime import datetime,timezone
        start,end=supervisor.next_window(datetime(2026,10,5,13,tzinfo=timezone.utc))
        self.assertEqual(start.isoformat(),'2026-10-06T09:58:00+00:00')
        self.assertEqual(end.isoformat(),'2026-10-06T16:00:00+00:00')
        start,_=supervisor.next_window(datetime(2026,10,9,13,tzinfo=timezone.utc))
        self.assertEqual(start.isoformat(),'2026-10-12T09:58:00+00:00')


if __name__=='__main__':unittest.main()
