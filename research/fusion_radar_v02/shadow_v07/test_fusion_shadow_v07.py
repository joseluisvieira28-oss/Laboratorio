import json
import math
import tempfile
import unittest
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
import fusion_shadow_observer_v07 as m

UTC=timezone.utc
DAY=date(2026,10,27)
NOW=datetime(2026,10,27,1,0,15,tzinfo=UTC)

def bars(day=DAY,prices=None):
    prices=prices or [100+i for i in range(21)]
    out=[]
    for i,price in enumerate(prices):
        d=day-timedelta(days=21-i);start=m.utc_midnight_ms(d)
        out.append([start,str(price),0,0,str(price),0,start+m.DAY_MS-1])
    return out

def depth(now=NOW):
    return {'success':True,'code':0,'data':{
        'timestamp':int(now.timestamp()*1000),
        'asks':[[8.955,22339,1],[8.956,50232,2]],
        'bids':[[8.954,5568,1],[8.953,17095,1]]}}

def contract():
    return {'success':True,'code':0,'data':{'symbol':'AVAX_USDT','contractSize':0.1}}

class ShadowTests(unittest.TestCase):
    def test_utc_entry(self):
        self.assertEqual(m.bounded_window(NOW),(DAY,'entry'))
    def test_utc_exit(self):
        self.assertEqual(m.bounded_window(NOW.replace(hour=2)),(DAY,'exit'))
    def test_expiry_no_backfill(self):
        for when in [datetime(2026,10,26,1,tzinfo=UTC),datetime(2026,11,10,1,tzinfo=UTC)]:
            with self.assertRaises(m.SourceBlocked):m.bounded_window(when)
    def test_gate_late(self):
        for minute in [4,25]:
            with self.assertRaises(m.SourceBlocked):m.bounded_window(NOW.replace(minute=minute))
    def test_source_signals(self):
        self.assertEqual(m.validate_klines(bars(),DAY)['state'],'UP')
        self.assertEqual(m.validate_klines(bars(prices=list(reversed([100+i for i in range(21)]))),DAY)['state'],'DOWN')
    def test_source_missing_bar(self):
        b=bars();b.pop(9)
        with self.assertRaises(m.SourceBlocked):m.validate_klines(b,DAY)
    def test_source_future_bar(self):
        b=bars();b[-1][0]+=m.DAY_MS;b[-1][6]+=m.DAY_MS
        with self.assertRaises(m.SourceBlocked):m.validate_klines(b,DAY)
    def test_source_nonfinite(self):
        b=bars();b[2][4]='NaN'
        with self.assertRaises(m.SourceBlocked):m.validate_klines(b,DAY)
    def test_source_exact_start_close(self):
        b=bars();b[-1][6]+=1
        with self.assertRaises(m.SourceBlocked):m.validate_klines(b,DAY)
    def test_contract_size(self):
        self.assertEqual(m.validate_contract(contract())['contract_size_avax'],0.1)
        c=contract();c['data']['contractSize']=1
        with self.assertRaises(m.SourceBlocked):m.validate_contract(c)
    def test_depth(self):
        d=m.validate_depth(depth(),NOW)
        self.assertAlmostEqual(d['spread_bps'],1.11676,places=4)
        self.assertAlmostEqual(d['bid_top_notional_usdt'],4985.5872,places=3)
    def test_depth_stale(self):
        d=depth();d['data']['timestamp']-=35_000
        with self.assertRaises(m.SourceBlocked):m.validate_depth(d,NOW)
    def test_depth_crossover(self):
        d=depth();d['data']['bids'][0][0]=8.955
        with self.assertRaises(m.SourceBlocked):m.validate_depth(d,NOW)
    def test_depth_reverse(self):
        d=depth();d['data']['asks'].reverse()
        with self.assertRaises(m.SourceBlocked):m.validate_depth(d,NOW)
    def test_context_two_sources_agree(self):
        with patch.object(m,'get_json',side_effect=[(bars(), '1'*64),(bars(), '2'*64)]):
            c=m.read_context(DAY)
            self.assertEqual(c['confluence'],'LONG_CONTEXT')
            self.assertEqual(c['avax_um_futures']['market'],'USD-M_PERPETUAL')
    def test_context_conflict_no_signal(self):
        down=list(reversed([100+i for i in range(21)]))
        with patch.object(m,'get_json',side_effect=[(bars(),'1'*64),(bars(prices=down),'2'*64)]):
            self.assertEqual(m.read_context(DAY)['confluence'],'NO_CONFLUENCE')
    def test_book_metadata_and_depth(self):
        with patch.object(m,'get_json',side_effect=[(contract(),'a'*64),(depth(),'b'*64)]):
            book=m.read_book(NOW)
            self.assertEqual(book['contract_size_avax'],0.1)
            self.assertEqual(book['depth_response_sha256'],'b'*64)
    def test_atomic_no_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(m,'read_context',return_value={'btc_spot':{'state':'UP'},'avax_um_futures':{'state':'UP'},'confluence':'LONG_CONTEXT'}),patch.object(m,'read_book',return_value={'best_bid':8.954,'best_ask':8.955,'spread_bps':1.116}):
                r=m.cycle(NOW,Path(d));self.assertEqual(r['status'],'OBSERVED')
                with self.assertRaises(m.SourceBlocked):m.cycle(NOW,Path(d))
                self.assertEqual(len(list(Path(d).glob('*entry.json'))),1)
    def test_blocked_fails_closed_and_reserved(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(m,'read_context',side_effect=m.SourceBlocked('TEST_SOURCE_DOWN')):
                r=m.cycle(NOW,Path(d));self.assertEqual(r['status'],'SOURCE_BLOCKED')
                self.assertEqual(r['error_code'],'TEST_SOURCE_DOWN')
                self.assertTrue((Path(d)/'2026-10-27_entry.json').exists())
    def test_no_telegram_default(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(m,'read_context',return_value={'a':1}),patch.object(m,'read_book',return_value={'best_bid':8.954,'best_ask':8.955,'spread_bps':1.116}),patch.object(m,'send_telegram_once') as send:
                r=m.cycle(NOW,Path(d))
                self.assertEqual(r['telegram_delivery'],'DISABLED_OR_EXIT')
                send.assert_not_called()
    def test_url_allowlist(self):
        with self.assertRaises(m.SourceBlocked):m.get_json('https://attacker.example/api')

if __name__=='__main__': unittest.main()
