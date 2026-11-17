"""LP-NET-003 deterministic offline guard tests; no network calls or trading."""
import inspect,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import historical_price_markout as h
import frozen_pool_snapshot as s

class PriceGateTests(unittest.TestCase):
 def quote(self,ts,offset=0,conf=.99,price=1):
  raw={v:{"price":price if k!="ETH" else 2000,"timestamp":ts+offset,
           "confidence":conf} for k,v in h.COINS.items()}
  return {"coins":raw}
 def test_historical_three_valid(self):
  with patch.object(h,"fetch",return_value=(self.quote(1700000000,-60),"d")):
   r=h.get_prices(1700000000)
  self.assertEqual(r["status"],"PASS")
  self.assertEqual(set(r["prices"]),{"DAI","USDC","ETH"})
 def test_future_price_blocked(self):
  with patch.object(h,"fetch",return_value=(self.quote(1700000000,10),"d")):
   self.assertEqual(h.get_prices(1700000000)["status"],"PRICE_SOURCE_BLOCKED")
 def test_price_stale_blocked(self):
  with patch.object(h,"fetch",return_value=(self.quote(1700000000,-21601),"d")):
   self.assertEqual(h.get_prices(1700000000)["status"],"PRICE_SOURCE_BLOCKED")
 def test_weak_confidence_blocked(self):
  with patch.object(h,"fetch",return_value=(self.quote(1700000000,-30,.5),"d")):
   self.assertEqual(h.get_prices(1700000000)["status"],"PRICE_SOURCE_BLOCKED")
 def test_notional_hodl_vs_gas(self):
  e={"timestamp":1000000000};x={"timestamp":1000086400}
  ps={"status":"PASS","prices":{
   "DAI":{"price_usd":"1"},"USDC":{"price_usd":"1"},"ETH":{"price_usd":"2000"}}}
  px={"status":"PASS","prices":{
   "DAI":{"price_usd":"1"},"USDC":{"price_usd":"1"},"ETH":{"price_usd":"1000"}}}
  p={"initial_dai":"100","initial_usdc":"100","exit_dai":"110",
     "exit_usdc":"91","gas_entry_eth":"0.01","gas_exit_eth":"0.01"}
  r=h.compute(p,e,x,ps,px)
  self.assertEqual(r["incremental_gross_vs_hodl_usd"],"1")
  self.assertEqual(r["incremental_net_full_gas_vs_hodl_usd"],"-29.00")
  self.assertEqual(r["hold_absolute_pnl_usd"],"0")
 def test_missing_prices_not_filled_with_peg(self):
  e={"timestamp":1000000000};x={"timestamp":1000086400}
  p={"initial_dai":"100","initial_usdc":"100"}
  r=h.compute(p,e,x,{"status":"PRICE_SOURCE_BLOCKED","errors":["USDC:NO_PRICE"]},
              {"status":"PASS","prices":{}})
  self.assertEqual(r["state"],"PRICE_SOURCE_BLOCKED")
  self.assertIsNone(r["real_dollar_result"])
 def test_pool_universe_is_only_two_canonical_pools(self):
  self.assertEqual(len(s.POOLS),2)
  self.assertEqual(set(x["fee"] for x in s.POOLS.values()),{0.0001,0.0005})
 def test_snapshot_source_disagreement_fail_closed(self):
  addr=s.POOLS["DAI_USDC_500"]["address"]
  a={"data":{"attributes":{"address":addr,"volume_usd":{"h24":"1000000"},
                         "reserve_in_usd":"4000000"}}}
  b={"pairs":[{"pairAddress":addr,"chainId":"ethereum",
                "volume":{"h24":10000000},"liquidity":{"usd":4000000}}]}
  with patch.object(s,"call",side_effect=[(a,"sha1"),(b,"sha2")]):
   r=s.metrics("DAI_USDC_500",s.POOLS["DAI_USDC_500"])
  self.assertFalse(r["source_threshold_pass"])
  self.assertEqual(r["decision"],"WATCH_ONLY_NO_LIVE_GO")
 def test_no_transaction_broadcast_or_wallet(self):
  src=inspect.getsource(h)+inspect.getsource(s)
  for forbidden in ["eth_sendRawTransaction","eth_sendTransaction","PRIVATE_KEY","sign_transaction"]:
   self.assertNotIn(forbidden,src)

if __name__=="__main__":unittest.main()
