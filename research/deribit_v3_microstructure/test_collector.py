import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import collector as c

T=dt.datetime(2026,11,6,8,6,tzinfo=c.UTC)
E=T.replace(day=7,hour=8,minute=0)
def meta(side,strike=80000):
    return dict(instrument_name=f"BTC_USDC-7NOV26-{strike}-{'C' if side=='call' else 'P'}",
        kind='option',base_currency='BTC',quote_currency='USDC',settlement_currency='USDC',price_index='btc_usdc',
        contract_size=1,min_trade_amount=.01,taker_commission=.0003,is_active=True,tick_size=5,
        expiration_timestamp=int(E.timestamp()*1000),strike=strike,option_type=side)
def payload(url):
    from urllib.parse import urlparse,parse_qs
    q=parse_qs(urlparse(url).query)
    if 'get_instruments' in url: result=[meta('call'),meta('put')]
    elif 'get_index_price' in url: result=dict(index_price=80000)
    else: result=dict(instrument_name=q['instrument_name'][0],state='open',timestamp=int(T.timestamp()*1000),
                      index_price=80000,bids=[[100,.05]],asks=[[105,.05]])
    return json.dumps(dict(testnet=False,result=result)).encode()

class CollectorTests(unittest.TestCase):
    def transport(self,url):
        response=MagicMock(); response.status=200; response.read.return_value=payload(url.full_url)
        obj=MagicMock(); obj.__enter__.return_value=response
        return obj
    def run_attempt(self,root,mode='prospective',clock=lambda:T):
        opener=MagicMock(); opener.open.side_effect=lambda req,timeout:self.transport(req)
        with patch.object(c.urllib.request,'build_opener',return_value=opener):
            return c.collect(root,mode,clock)
    def test_complete_session_and_immutable_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            path,r=self.run_attempt(tmp)
            self.assertTrue(r['valid_technical']); self.assertTrue(r['prospective_v3'])
            manifest=json.loads((path/'manifest.json').read_bytes())
            self.assertEqual(len(manifest),4)
            for m in manifest:
                raw=(path/(m['name']+'.json')).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),m['sha256'])
            original=(path/'receipt.json').read_bytes()
            with self.assertRaises(FileExistsError): self.run_attempt(tmp)
            self.assertEqual(original,(path/'receipt.json').read_bytes())
            with self.assertRaises(FileExistsError): c.write(path/'receipt.json',b'bad')
    def test_diagnostic_outside_window_never_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,r=self.run_attempt(tmp,'controlled_observation',lambda:T.replace(hour=12))
            self.assertFalse(r['prospective_v3'])
            self.assertIsNone(r['net_pnl'])
    def test_outside_window_retains_failure_without_http(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(c.PublicSource,'get',side_effect=AssertionError('HTTP')):
            path,r=c.collect(tmp,'prospective',lambda:T.replace(minute=10))
            self.assertFalse(r['valid_technical']); self.assertIn('WINDOW',r['reject_reason'])
            self.assertTrue((path/'manifest.json').exists())
    def test_boundaries(self):
        c.window(T.replace(minute=5),T.date())
        for t in [T.replace(minute=4),T.replace(minute=10),T.replace(tzinfo=None)]:
            with self.assertRaises(ValueError): c.window(t,T.date())
    def test_selection_tie_and_bad_metadata(self):
        metas=[meta(side,strike) for strike in (79500,80500) for side in ('call','put')]
        self.assertEqual(c.select(metas,80000,E)['call']['strike'],79500)
        for field,value in [('contract_size',10),('taker_commission',0),('quote_currency','BTC'),('is_active',False),('instrument_name','BTC-7NOV26-80000-C')]:
            bad=meta('call'); bad[field]=value
            with self.assertRaises(ValueError): c.select([bad,meta('put')],80000,E)
        with self.assertRaises(ValueError): c.select([meta('call'),meta('put')],90000,E)
        with self.assertRaises(ValueError): c.select([meta('call'),meta('put')],80000,E+dt.timedelta(days=1))
    def test_failed_decode_keeps_both_raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            def transport(req,timeout):
                obj=self.transport(req)
                if 'get_order_book' in req.full_url:
                    obj.__enter__.return_value.read.return_value=b'not json'
                return obj
            opener=MagicMock(); opener.open.side_effect=transport
            with patch.object(c.urllib.request,'build_opener',return_value=opener):
                path,r=c.collect(tmp,'prospective',lambda:T)
            self.assertFalse(r['valid_technical'])
            self.assertEqual((path/'call.json').read_bytes(),b'not json')
            self.assertEqual((path/'put.json').read_bytes(),b'not json')
    def test_endpoint_rejected_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=c.PublicSource(Path(tmp))
            for name,method,params in [('x','buy',{}),('index','get_index_price',dict(index_name='eth_usdc'))]:
                with self.assertRaises(ValueError): source.get(name,method,**params)
    def test_decision_late_invalid_and_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[0]
            def clock():
                calls[0]+=1
                return T if calls[0]<11 else T.replace(minute=10)
            path,r=self.run_attempt(tmp,clock=clock)
            self.assertFalse(r['valid_technical']); self.assertTrue((path/'receipt.json').exists())

    def test_saved_controlled_observation_and_tamper(self):
        import audit_controlled
        from shutil import copytree
        source=Path(__file__).parent/'controlled-observation-2026-11-06.zip'
        self.assertEqual(audit_controlled.audit(source)['raw_hashes'],4)
        with tempfile.TemporaryDirectory() as tmp:
            import zipfile
            target=Path(tmp)/'copy'
            with zipfile.ZipFile(source) as archive: archive.extractall(target)
            (target/'call.json').write_bytes(b'altered')
            with self.assertRaises(ValueError): audit_controlled.audit(target)

    def test_stops_at_twenty(self):
        with tempfile.TemporaryDirectory() as tmp:
            namespace=Path(tmp)/'prospective'; namespace.mkdir()
            for i in range(20):
                p=namespace/str(i); p.mkdir(); (p/'receipt.json').write_text('{"prospective_v3":true}')
            with self.assertRaisesRegex(ValueError,'COHORT_COMPLETE'): self.run_attempt(tmp)

    def test_http_error_body_retained(self):
        import io
        import urllib.error
        with tempfile.TemporaryDirectory() as tmp:
            opener=MagicMock()
            opener.open.side_effect=urllib.error.HTTPError('https://www.deribit.com',429,'limit',{},io.BytesIO(b'{"error":"rate limit"}'))
            with patch.object(c.urllib.request,'build_opener',return_value=opener):
                path,r=c.collect(tmp,'controlled_observation',lambda:T)
            self.assertFalse(r['valid_technical'])
            self.assertEqual((path/'instruments.json').read_bytes(),b'{"error":"rate limit"}')
            self.assertEqual(json.loads((path/'manifest.json').read_bytes())[0]['http_status'],429)

if __name__=='__main__': unittest.main()
