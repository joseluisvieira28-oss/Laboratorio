"""Offline adversarial checks: no market requests, no economic observations."""
import contextlib
import copy
import datetime as dt
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import probe

UTC=dt.timezone.utc
EXP=dt.datetime(2026,11,4,8,tzinfo=UTC)
META={k:dict(instrument_name='BTC_USDC-4NOV26-76500-'+s,kind='option',
    base_currency='BTC',quote_currency='USDC',settlement_currency='USDC',
    price_index='btc_usdc',is_active=True,contract_size=1,min_trade_amount=.01,
    taker_commission=.0003,expiration_timestamp=int(EXP.timestamp()*1000),
    tick_size=5,strike=76500,option_type=side)
    for k,s,side in [('atm_call','C','call'),('atm_put','P','put')]}

def book(m, timestamp=100000):
    return dict(instrument_name=m['instrument_name'],state='open',timestamp=timestamp,
                bids=[[100,1]],asks=[[105,1]],index_price=76500)

class SyncTests(unittest.TestCase):
    def test_real_source_parallel_dispatch_hashes_and_name_binding(self):
        barrier=threading.Barrier(2)
        class Response:
            status=200
            def __init__(self,request): self.request=request
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,n):
                # Sequential dispatch cannot pass this rendezvous.
                barrier.wait(timeout=2)
                m=META['atm_call' if '-C' in self.request.full_url else 'atm_put']
                if m['option_type']=='call': time.sleep(.02) # reverse completion
                return json.dumps(dict(testnet=False,result=book(m))).encode()
        class Opener:
            def open(self,request,timeout): return Response(request)
        with tempfile.TemporaryDirectory() as tmp:
            source=probe.Source(Path(tmp)/'raw')
            with patch('probe.urllib.request.build_opener',return_value=Opener()), patch('probe.stamp',return_value='1970-01-01T00:01:40+00:00'):
                legs=probe.parallel_books(source,META,EXP,.05)
            self.assertEqual(set(legs),set(META))
            self.assertEqual(len(source.manifest),2)
            for row in source.manifest:
                raw=(source.root/(row['name']+'.json')).read_bytes()
                self.assertEqual(probe.digest(raw),row['sha256'])
                self.assertEqual(legs[row['name']]['symbol'],json.loads(raw)['result']['instrument_name'])

    def test_each_book_uses_own_receipt_time(self):
        class Source:
            def get(self,key,*a,**kw):return book(META[key],100000 if key=='atm_call' else 101000)
            def received(self,key):return '1970-01-01T00:01:40+00:00' if key=='atm_call' else '1970-01-01T00:01:51.001000+00:00'
        with self.assertRaisesRegex(AssertionError,'STALE_OR_FUTURE_BOOK'):
            probe.parallel_books(Source(),META,EXP,.05)

    def test_failure_keeps_other_raw_and_never_retries(self):
        barrier=threading.Barrier(2)
        class Opener:
            def open(self,request,timeout):
                barrier.wait(timeout=2)
                if '-C' in request.full_url:raise TimeoutError('fixture')
                class Response:
                    status=200
                    def __enter__(self):return self
                    def __exit__(self,*args):pass
                    def read(self,n):return b'{"testnet":false,"result":{}}'
                return Response()
        with tempfile.TemporaryDirectory() as tmp:
            source=probe.Source(Path(tmp)/'raw')
            with patch('probe.urllib.request.build_opener',return_value=Opener()):
                with self.assertRaises(TimeoutError):probe.parallel_books(source,META,EXP,.05)
            self.assertEqual(len(source.manifest),2)
            self.assertTrue((source.root/'atm_put.json').exists())
            self.assertIn('error',next(x for x in source.manifest if x['name']=='atm_call'))

    def test_request_budget_reserved_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=probe.Source(Path(tmp)/'raw')
            source.manifest=[dict(name=str(i)) for i in range(8)]
            with self.assertRaisesRegex(AssertionError,'REQUEST_BUDGET'):
                source.get('extra','get_order_book')
            self.assertEqual(len(source.manifest),8)

    def test_collect_keeps_1000ms_gate_and_diagnostics_never_forecast(self):
        now=dt.datetime(2026,11,3,8,6,tzinfo=UTC)
        class Clock(dt.datetime):
            @classmethod
            def now(cls,tz=None):return now
        def fake_get(source,name,method,**params):
            source.manifest.append(dict(name=name,received=now.isoformat()))
            return list(META.values()) if name=='instruments' else {'index_price':76500} if name=='index' else {}
        for skew,mode,expected in [(1000,'sync-check','SYNC_DIAGNOSTIC_PASS'),(1001,'sync-check','SOURCE_BLOCKED'),(1001,'entry','SOURCE_BLOCKED')]:
            legs={k:dict(timestamp=int(now.timestamp()*1000)+(skew if k=='atm_put' else 0)) for k in META}
            with tempfile.TemporaryDirectory() as tmp, patch('probe.dt.datetime',Clock), patch.object(probe.Source,'get',fake_get), patch('probe.parallel_books',return_value=legs), patch('probe.forecast',side_effect=AssertionError('must not run')),contextlib.redirect_stdout(io.StringIO()):
                r=probe.collect(Path(tmp)/'raw',mode)
            self.assertEqual(r['status'],expected)
            self.assertEqual(r['synchronization']['book_skew_limit_ms'],1000)
            self.assertNotIn('forecast',r)
            self.assertNotIn('control_selected',r)

    def test_diagnostic_cannot_be_settled(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry=Path(tmp)/'receipt.json'
            sha=probe.save(entry,dict(freeze=probe.FREEZE,mode='sync-check',status='SYNC_DIAGNOSTIC_PASS'))
            with self.assertRaises(AssertionError):probe.settlement(entry,Path(tmp)/'out',sha)

if __name__=='__main__':unittest.main()
