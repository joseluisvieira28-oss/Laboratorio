import copy
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal as D
import probe
import audit

class EconomicsTests(unittest.TestCase):
    def setUp(self):
        self.legs=[dict(ask=a,bid=a-20,index=77908.37,tick=20,strike=78000,side=s,
                        expiry='2026-11-06T08:00:00+00:00') for a,s in [(1260,'call'),(1300,'put')]]

    def test_original_witness_and_closed_form_roots(self):
        e=probe.economics(self.legs,77908.37)
        self.assertAlmostEqual(e['roundtrip_loss'],1.33490044)
        d=[{k:audit.num(v) if k in ['ask','bid','index','tick','strike'] else v for k,v in x.items()} for x in self.legs]
        for a,b in zip(probe.roots(self.legs),audit.analytical_roots(d)):
            self.assertAlmostEqual(a,float(b),8)
        self.assertAlmostEqual(probe.net(self.legs,78000),-26.06745022)
        self.assertAlmostEqual(probe.payout(self.legs,81000)[1],.1215)

    def test_fee_cap_and_daily_exemption(self):
        self.assertEqual(probe.fee(1,100000),.00125)
        self.assertEqual(audit.fees(D(1),D(100000)),D('.00125'))
        self.legs[0]['expiry']=self.legs[1]['expiry']='2026-11-05T08:00:00+00:00'
        self.assertEqual(probe.payout(self.legs,81000)[1],0)

    def test_tick_threshold_crossing_uses_valid_grid(self):
        leg=dict(ask=995,tick=5,tick_steps=[dict(above_price=1000,tick_size=20)])
        self.assertEqual(probe.adverse_price(leg,1),1000)
        self.assertEqual(probe.adverse_price(leg,2),1020)
        leg['ask']=1000
        self.assertEqual(probe.adverse_price(leg,1),1020)

    def test_hash_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'x';f.write_text('{}')
            with self.assertRaises(AssertionError):audit.read(f,'0'*64)

    def test_stale_depth_and_wrong_contract(self):
        m=dict(instrument_name='BTC_USDC-6NOV26-78000-C',tick_size=5,tick_size_steps=[])
        b=dict(instrument_name=m['instrument_name'],timestamp=100000,state='open',bids=[[10,1]],asks=[[20,1]],index_price=78000)
        with self.assertRaises(AssertionError):probe.bookcheck(b,m,'1970-01-01T00:02:00+00:00')
        b['asks'][0][1]=.001
        with self.assertRaises(AssertionError):probe.bookcheck(b,m,'1970-01-01T00:01:40+00:00')
        b['instrument_name']='ETH_OTHER'
        with self.assertRaises(AssertionError):probe.bookcheck(b,m,'1970-01-01T00:01:40+00:00')

    def test_forecast_missing_dates_and_future_data_exclusion(self):
        day=dt.datetime(2026,11,3,8,5,tzinfo=dt.timezone.utc)
        rows=[dict(date=(day.date()-dt.timedelta(days=i)).isoformat(),delivery_price=78000+i*10) for i in range(61)]
        result=probe.forecast({'data':rows},day,78000,86100,self.legs)
        polluted=rows+[dict(date='2026-11-04',delivery_price=1e10)]
        self.assertEqual(result,probe.forecast({'data':polluted},day,78000,86100,self.legs))
        with self.assertRaises(AssertionError):probe.forecast({'data':rows[:-1]},day,78000,86100,self.legs)

    def test_missing_delivery_never_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'entry.json'
            receipt=dict(freeze=probe.FREEZE,mode='entry',status='SIMULATED_ENTRY_SELECTED',
                         expiry='2026-01-01T08:00:00+00:00')
            sha=probe.save(f,receipt)
            from unittest.mock import patch
            with patch.object(probe.Source,'get',return_value={'data':[]}):
                result=probe.settlement(f,Path(tmp)/'out',sha)
            self.assertEqual(result['status'],'UNSETTLED')
            self.assertNotIn('primary_net',result)

if __name__=='__main__':unittest.main()
