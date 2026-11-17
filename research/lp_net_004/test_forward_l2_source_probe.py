"""LP-NET-004 adversarial offline source and economics guards."""
import inspect,sys,unittest
from pathlib import Path
from decimal import Decimal
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import forward_l2_source_probe as p

BASE={"id":"A-USDC-USDT-001","network":"arbitrum","chain_id":42161,
"token_pair":"USDC/USDT","fee_bps":1,"addr":"0xbe3ad6a5669dc0b8b12febc03608860c31e2eef6"}
T0="0x0000000000000000000000000000000000000001"
T1="0x0000000000000000000000000000000000000002"
class SourceTests(unittest.TestCase):
 def model_chain(self,fee=100,nibbles=0):
  return {"status":"POOL_STATE_ONCHAIN_OBSERVED","token0":T0,"token1":T1,
   "fee_tier_raw":fee,"gas_price_wei":10000000,
   "lp_effective_swap_fee_by_direction":["0.0001","0.0001"],
   "slot0_fee_protocol_byte":nibbles,
   "active_liquidity_raw_L":"123456789","IMPORTANT_active_L_is_not_dollar_TVL":True}
 def model_market(self,vol="2000000",reserve="1000000",consistent=True):
  return {"status":"MARKET_RECEIVED",
   "gecko_token_ids":["arbitrum_"+T0,"arbitrum_"+T1],
   "dex_token_addresses":[T1,T0],"dex_pair_found":True,
   "gecko_price_usd":["0.9999","1.0001"],
   "gecko_vol24_usd":vol,"gecko_tvl_usd":reserve,
   "two_source_consistent":consistent}
 def test_scenario_is_not_position_apr(self):
  result=p.combine(BASE,self.model_market(),self.model_chain(),
                   {"status":"PASS","eth_usd":"2500"})
  self.assertEqual(result["source_screen"],"MARKET_AND_POOL_STATE_PASS_WATCH_ONLY")
  self.assertEqual(result["economic_verdict"],"NO_LIVE_GO_INDIVIDUAL_ACTIVE_RANGE_SHARE_UNBOUND")
  self.assertEqual(result["lp_pool_total_fee_dollars_day_direction_bounds"],["200.0000","200.0000"])
  self.assertEqual(result["l1_data_fee_usd"],"UNBOUND_NOT_INCLUDED")
  self.assertTrue(result["critical_note"].startswith("TOTAL"))
 def test_missing_chain_blocks(self):
  q=p.combine(BASE,self.model_market(),{"status":"ONCHAIN_SOURCE_BLOCKED"},{"status":"PASS","eth_usd":"2500"})
  self.assertEqual(q["source_screen"],"BLOCKED")
 def test_missing_market_blocks(self):
  q=p.combine(BASE,{"status":"MARKET_SOURCE_BLOCKED"},self.model_chain(),{"status":"PASS","eth_usd":"2500"})
  self.assertEqual(q["source_screen"],"BLOCKED")
 def test_under_reserve(self):
  q=p.combine(BASE,self.model_market(reserve="499999"),self.model_chain(),{"status":"PASS","eth_usd":"2500"})
  self.assertEqual(q["source_screen"],"FAIL_VOLUME_OR_RESERVE")
 def test_under_volume(self):
  q=p.combine(BASE,self.model_market(vol="99999"),self.model_chain(),{"status":"PASS","eth_usd":"2500"})
  self.assertEqual(q["source_screen"],"FAIL_VOLUME_OR_RESERVE")
 def test_provider_mismatch_fails(self):
  q=p.combine(BASE,self.model_market(consistent=False),self.model_chain(),{"status":"PASS","eth_usd":"2500"})
  self.assertEqual(q["source_screen"],"BLOCKED")
 def test_token_mismatch_fails(self):
  m=self.model_market();m["dex_token_addresses"]=[T0,"0xdeadbeef"]
  q=p.combine(BASE,m,self.model_chain(),{"status":"PASS","eth_usd":"2500"})
  self.assertEqual(q["source_screen"],"BLOCKED")
 def test_price_depeg_fails(self):
  m=self.model_market();m["gecko_price_usd"]=["0.90","1.00"]
  q=p.combine(BASE,m,self.model_chain(),{"status":"PASS","eth_usd":"2500"})
  self.assertEqual(q["source_screen"],"BLOCKED")
 def test_protocol_fee_nibble_logic_known(self):
  cuts=[Decimal(0) if x==0 else Decimal(1)/Decimal(x) for x in (0x44 & 0xf,0x44>>4&0xf)]
  self.assertEqual(cuts,[Decimal("0.25"),Decimal("0.25")])
 def test_abi_rejects_short(self):
  with self.assertRaises(ValueError):p.words("0x00",1)
 def test_no_transactions(self):
  src=inspect.getsource(p)
  for forbidden in ["eth_sendTransaction","eth_sendRawTransaction","private_key","signTransaction"]:
   self.assertNotIn(forbidden,src)
if __name__=="__main__":unittest.main()
