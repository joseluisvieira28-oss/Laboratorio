"""Hermetic source-evidence checks, not trading/economic PASS tests."""
import unittest
from decimal import Decimal
from source_probe import allowed,walk,summarize
class EvidenceTests(unittest.TestCase):
 def test_no_private_or_history(self):
  for u in ['https://api.mexc.com/api/v1/private/account/assets','https://api.mexc.com/api/v1/contract/funding_rate/history','https://fapi.binance.com/fapi/v1/klines','https://evil.test/api/v1/contract/ping','http://api.mexc.com/api/v1/contract/ping']:
   self.assertFalse(allowed(u))
 def test_contracts_not_order_count(self):
  self.assertEqual(walk([[100,2,9999],[101,3,1]],3),100+1/3)
  self.assertIsNone(walk([[100,2,9999]],3))
 def test_round_down_min_and_units(self):
  m={'contractSize':'.1','minVol':1,'volUnit':1,'priceUnit':'.01'}
  r=summarize(m,{'asks':[[100,10000,1]],'bids':[[99,10000,1]],'timestamp':1})
  self.assertEqual(r['sizes'][1]['contracts'],'2')
  self.assertEqual(Decimal(r['sizes'][1]['initial_nominal_1R_USDT']),Decimal('.8'))
  self.assertEqual(r['sizes'][0]['actual_fill_proven'],False)
 def test_missing_depth_never_fill(self):
  self.assertIsNone(walk([[100,1,100000]],2))
 def test_corrupt_and_crossed_fail(self):
  m={'contractSize':'.1','minVol':1,'volUnit':1,'priceUnit':'.01'}
  with self.assertRaises(ValueError):summarize(m,{'asks':[[100,1,1]],'bids':[[101,1,1]]})
  with self.assertRaises(ValueError):summarize(m,{'asks':[[100,1,1],[99,1,1]],'bids':[[98,1,1]]})
  with self.assertRaises(ValueError):walk([[100,-1,1]],1)
if __name__=='__main__':unittest.main()
