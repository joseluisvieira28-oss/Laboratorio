import unittest
from one_shot_source import pair,bbo,ROUNDTRIP_FEES_BPS,STRESS_FEES_BPS,EIGHT_HOURS
NOW=1800000000000
FUND=NOW+3600000

def fixture(rate="0.0001"):
    a="BTC"
    return {
      "spot_info":{"data":[{"instId":"BTC-USDT","state":"live","minSz":"0.00001","lotSz":"0.00001"}]},
      "swap_info":{"data":[{"instId":"BTC-USDT-SWAP","state":"live","ctType":"linear",
                            "ctValCcy":"BTC","settleCcy":"USDT","ctVal":"0.01",
                            "ctMult":"1","minSz":"1","lotSz":"1"}]},
      "spot_book":{"data":[{"ts":str(NOW-1000),"bids":[["100","2"]],"asks":[["100.01","2"]]}]},
      "swap_book":{"data":[{"ts":str(NOW-1000),"bids":[["100.03","2"]],"asks":[["100.04","2"]]}]},
      "swap_funding":{"data":[{"instId":"BTC-USDT-SWAP","fundingTime":str(FUND),
                               "prevFundingTime":str(FUND-EIGHT_HOURS),"fundingRate":rate}]}
    }

class FrozenTest(unittest.TestCase):
  def test_fee_assumptions(self):
    self.assertEqual(ROUNDTRIP_FEES_BPS,30)
    self.assertEqual(STRESS_FEES_BPS,60)
  def test_ordinary_rate_below_hurdle(self):
    r=pair("BTC",fixture(),NOW)
    self.assertEqual(r["verdict"],"8H_ESTIMATE_BELOW_FROZEN_HURDLE")
    self.assertEqual(r["one_funding_predicted_gross_bps"],"1.0000")
  def test_large_rate_still_not_edge(self):
    r=pair("BTC",fixture("0.01"),NOW)
    self.assertEqual(r["verdict"],"8H_ESTIMATE_COVERS_FROZEN_HURDLE_NOT_EDGE")
    self.assertIsNone(r["profit_usdt"])
  def test_negative_rate_not_profit(self):
    r=pair("BTC",fixture("-0.0001"),NOW)
    self.assertLess(float(r["8h_net_estimate_bps"]),-30)
  def test_funding_timestamp_causal(self):
    p=fixture();p["swap_funding"]["data"][0]["fundingTime"]=str(NOW-1)
    with self.assertRaisesRegex(ValueError,"INTERVAL"):
      pair("BTC",p,NOW)
  def test_interval_must_be_eight_hours(self):
    p=fixture();p["swap_funding"]["data"][0]["prevFundingTime"]=str(FUND-4*3600000)
    with self.assertRaisesRegex(ValueError,"INTERVAL"):
      pair("BTC",p,NOW)
  def test_stale_bbo_blocks(self):
    p=fixture();p["spot_book"]["data"][0]["ts"]=str(NOW-40000)
    with self.assertRaisesRegex(ValueError,"STALE"):
      pair("BTC",p,NOW)
  def test_future_bbo_blocks(self):
    p=fixture();p["swap_book"]["data"][0]["ts"]=str(NOW+1000)
    with self.assertRaisesRegex(ValueError,"FUTURE"):
      pair("BTC",p,NOW)
  def test_crossed_book_blocks(self):
    with self.assertRaisesRegex(ValueError,"CROSSED"):
      bbo({"ts":str(NOW),"bids":[["101","1"]],"asks":[["100","1"]]},NOW)
  def test_zero_qty_blocks(self):
    with self.assertRaisesRegex(ValueError,"CROSSED"):
      bbo({"ts":str(NOW),"bids":[["99","1"]],"asks":[["100","0"]]},NOW)
  def test_perp_contract_currency_mismatch(self):
    p=fixture();p["swap_info"]["data"][0]["ctValCcy"]="USDT"
    with self.assertRaisesRegex(ValueError,"INVALID_CONTRACT_UNITS"):
      pair("BTC",p,NOW)
  def test_identity_mismatch(self):
    p=fixture();p["spot_info"]["data"][0]["instId"]="ETH-USDT"
    with self.assertRaisesRegex(ValueError,"IDENTITY"):
      pair("BTC",p,NOW)
  def test_minimum_contract_floor(self):
    p=fixture();x=pair("BTC",p,NOW)
    self.assertEqual(x["min_hedge_base_lower_bound"],"0.01")
    self.assertEqual(x["min_spot_capital_USDT_floor"],"1.0001")
  def test_nonfinite_rate_blocks(self):
    with self.assertRaisesRegex(ValueError,"NONFINITE"):
      pair("BTC",fixture("NaN"),NOW)

if __name__=="__main__":unittest.main()
