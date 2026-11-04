import unittest,json
from source import Observer,book
class Adversarial(unittest.TestCase):
 def row(self,o,t,v='mexc',k='frame',m=None):
  o.feed({'seq':1 if o.last is None else o.last['seq']+1,'utc_ms':100000+int(t*1000),'mono_ns':int(t*1e9),'elapsed':t,'venue':v,'kind':k,'raw':json.dumps(m or {})})
 def depth(self,n=1): return {'channel':'push.depth.full','symbol':'BTC_USDT','ts':100000,'data':{'version':n,'bids':[[100-i,1] for i in range(5)],'asks':[[101+i,1] for i in range(5)]}}
 def test_ack_success_not_book(self):
  o=Observer(); self.row(o,0,m={'channel':'rs.sub.depth.full','data':'success'}); self.assertTrue(o.state['mexc']['ack']); self.assertFalse(o.healthy(31))
 def test_rejected_ack(self):
  o=Observer(); self.row(o,0,m={'channel':'rs.sub.depth.full','data':'error'}); self.assertEqual(o.count['reset:INVALID'],1)
 def test_envelope_timestamp(self):
  o=Observer(); self.row(o,0,m=self.depth()); self.assertEqual(o.count['mexc:book'],1)
 def test_duplicate_and_regression(self):
  o=Observer(); d=self.depth(2); self.row(o,0,m=d); self.row(o,.1,m=d); self.assertEqual(o.count['mexc:duplicate_book'],1)
  self.row(o,.2,m=self.depth(1)); self.assertEqual(o.count['reset:INVALID'],1)
 def test_conflicting_duplicate(self):
  o=Observer(); d=self.depth(); self.row(o,0,m=d); d['data']['bids'][0][1]=2; self.row(o,.1,m=d); self.assertEqual(o.count['reset:INVALID'],1)
 def test_crossed_and_nonfinite(self):
  for value in (102,float('nan'),0):
   d=self.depth(); d['data']['bids'][0][0]=value
   with self.assertRaises(ValueError): book(d,'mexc')
 def test_delta_not_snapshot(self):
  with self.assertRaises(ValueError): book({'type':'delta','data':{'s':'BTCUSDT'}},'bybit')
 def test_reconnect_clears_version_and_both_books(self):
  o=Observer(); self.row(o,0,m=self.depth(7)); self.row(o,.1,k='connect'); self.assertIsNone(o.state['mexc']['version']); self.assertEqual(o.quarantine,30.1)
 def test_no_future_coverage(self):
  o=Observer(); self.row(o,60,k='end',v='system'); self.assertEqual(len(o.good),0); self.assertEqual(len(o.bad),60)
 def test_clock_reversal(self):
  o=Observer(); self.row(o,2,k='start'); self.row(o,1,k='start'); self.assertEqual(o.count['integrity'],1)
 def test_stale_restarts_warmup(self):
  o=Observer(); self.row(o,0,m=self.depth()); self.row(o,2,k='start'); self.assertGreaterEqual(o.quarantine,32)
 def test_pong_no_market_health(self):
  o=Observer(); self.row(o,0,m={'channel':'pong'}); self.assertFalse(o.healthy(31))
 def test_actual_liquidation_dedup(self):
  o=Observer(); m={'topic':'allLiquidation.BTCUSDT','data':[{'T':100000,'s':'BTCUSDT','S':'Buy','v':'1','p':'100000'}]}
  self.row(o,0,v='bybit',m=m); self.row(o,.1,v='bybit',m=m); self.assertEqual(o.count['liquidations'],1); self.assertEqual(o.count['duplicates'],1)
 def test_never_pnl(self):
  r=Observer().report('RETRY_EXHAUSTED'); self.assertEqual(r['source_verdict'],'SOURCE_BLOCKED'); self.assertEqual(r['pnl'],'NOT_COMPUTED_GATE_CLOSED')
if __name__=='__main__': unittest.main()
