"""Offline controls for frozen T0 LP capital share math."""
import json,unittest,inspect,sys
from pathlib import Path
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parent))
import arbitrum_static_fee_share_scenario as m
F=Path(__file__).resolve().parent/"FROZEN_ARBITRUM_T0_LP_CAPITAL_SHARE.json"
class CapitalShareTest(unittest.TestCase):
 def fixed(self):return json.loads(F.read_text())
 def test_frozen_nine_cases(self):
  d=m.fee_scenarios(self.fixed())
  self.assertEqual(len(d),9)
  self.assertEqual(set(x["notional_usd"] for x in d),{"1000","5000","20000"})
 def test_nontrivial_5000_capital_share(self):
  rows=m.fee_scenarios(self.fixed())
  x=next(x for x in rows if x["notional_usd"]=="5000" and
         x["half_width_frac"]=="0.0025")
  self.assertAlmostEqual(float(x["30d_static_gross_fee_USD"]),4.602,delta=.01)
  self.assertLess(Decimal(x["hypothetical_share_at_t0"]),Decimal(".001"))
  self.assertIsNone(x["actual_position_fees_received"])
 def test_best_frozen_static_fee_scenario_fails_4pct_hurdle(self):
  cases=m.fee_scenarios(self.fixed())
  self.assertTrue(all(x["simple_annual_fee_below_4pct_hurdle"] for x in cases))
 def test_wrong_protocol_fee_is_hard_failure(self):
  f=self.fixed();f["slot0_fee_protocol"]=0
  with self.assertRaises(ValueError):m.fee_scenarios(f)
 def test_wrong_raw_sqrt_is_hard_failure(self):
  f=self.fixed();f["sqrtPriceX96"]="79228162514264337593543950336"
  with self.assertRaises(ValueError):m.fee_scenarios(f)
 def test_position_liquidity_cannot_be_inferred_from_TVL(self):
  f=self.fixed();f["pool_reserve_usd"]="1"
  a=m.fee_scenarios(f);self.assertEqual(len(a),9)
  self.assertTrue(all("hypothetical_added_raw_liquidity_L" in x for x in a))
 def test_no_trading_or_credentials(self):
  source=inspect.getsource(m)
  for token in ("eth_sendTransaction","eth_sendRawTransaction","PRIVATE_KEY","signTransaction"):
   self.assertNotIn(token,source)
if __name__=="__main__":unittest.main()
