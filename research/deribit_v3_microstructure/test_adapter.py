import copy
import hashlib
import json
import unittest
from unittest.mock import patch
import adapter

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.symbol = 'BTC_USDC-6NOV26-80000-C'
        self.book = dict(testnet=False, result=dict(instrument_name=self.symbol, state='open',
            timestamp=100000, index_price=80000, bids=[[100, .05],[95,.1]], asks=[[105,.05],[110,.1]]))

    def decode(self, obj=None):
        raw = json.dumps(obj or self.book).encode()
        return adapter.decode(raw, self.symbol, 100500)

    def test_exact_hash_depth_age(self):
        result = self.decode()
        self.assertEqual(result['sha256'], hashlib.sha256(json.dumps(self.book).encode()).hexdigest())
        self.assertEqual(result['quote_age_ms'],500)
        self.assertEqual(len(result['depth']['bids']),2)
        self.assertIsNone(result['net_pnl'])
        self.assertFalse(result['prospective_v3'])

    def test_bad_books(self):
        for key, value in [('bids',[]),('asks',[[105,.049]]),('asks',[[99,.05]]),
                           ('bids',[[100,.05],[100,.05]]),('timestamp',80000),
                           ('timestamp',104000),('index_price',float('nan')),('state','closed')]:
            with self.subTest(key=key,value=value):
                obj=copy.deepcopy(self.book); obj['result'][key]=value
                with self.assertRaises(ValueError): self.decode(obj)

    def test_public_product_allowlist(self):
        for symbol in ['BTC-6NOV26-80000-C','../private/buy','BTC_USDC-x?x=1']:
            with self.assertRaises(ValueError): adapter.request_url(symbol)
        self.assertTrue(adapter.request_url(self.symbol).startswith(adapter.BASE))

    def test_source_error(self):
        for obj in [dict(self.book,testnet=True),dict(self.book,error={})]:
            with self.assertRaises(ValueError): self.decode(obj)

    def test_each_book_sync(self):
        call=self.decode(); put=dict(call,symbol=self.symbol[:-1]+'P',timestamp=100979)
        self.assertEqual(adapter.synchronize(call,put,100500)['book_skew_ms'],979)
        with self.assertRaises(ValueError): adapter.synchronize(call,put,110500)
        with self.assertRaises(ValueError): adapter.synchronize(call,dict(put,timestamp=101001),100500)

    def test_no_redirect(self):
        with self.assertRaises(ValueError): adapter.NoRedirect().redirect_request(None)

    def test_pinned_historical_books(self):
        import audit_deribit
        import datetime as dt
        import zipfile
        for day,(filename,digest) in audit_deribit.PINNED.items():
            path=audit_deribit.ROOT/'evidence'/day/filename
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
            with zipfile.ZipFile(path) as archive:
                prefix='raw/' if 'raw/receipt.json' in archive.namelist() else ''
                receipt=json.loads(archive.read(prefix+'receipt.json'))
                sources={m['name']:m for m in receipt['manifest']}
                legs=[]
                for name in ('atm_call','atm_put'):
                    raw=archive.read(prefix+name+'.json')
                    ms=dt.datetime.fromisoformat(sources[name]['received']).timestamp()*1000
                    leg=adapter.decode(raw,receipt['chosen'][name],ms,'historical')
                    self.assertEqual(leg['sha256'],sources[name]['sha256'])
                    self.assertFalse(leg['prospective_v3']); legs.append(leg)
                index_ms=dt.datetime.fromisoformat(sources['index']['received']).timestamp()*1000
                if day=='2026-11-03':
                    with self.assertRaises(ValueError): adapter.synchronize(*legs,index_ms)
                else: adapter.synchronize(*legs,index_ms)

    def test_fetch_uses_bounded_get(self):
        from unittest.mock import MagicMock
        response=MagicMock(); response.status=200; response.read.return_value=json.dumps(self.book).encode()
        opener=MagicMock(); opener.open.return_value.__enter__.return_value=response
        with patch.object(adapter.urllib.request,'build_opener',return_value=opener), patch.object(adapter.dt,'datetime') as clock:
            clock.now.return_value.timestamp.return_value=100.5
            raw, receipt=adapter.fetch(self.symbol)
        req=opener.open.call_args.args[0]
        self.assertEqual(req.get_method(),'GET')
        self.assertEqual(opener.open.call_args.kwargs['timeout'],15)
        response.read.assert_called_once_with(12000001)
        self.assertEqual(receipt['provenance'],'controlled_observation')
