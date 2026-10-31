import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from triple_flow_public_joint_source_v01 import validate_bybit_trade,validate_liquidation,validate_rest,classify
D=1800000000000
class Source(unittest.TestCase):
 def test_bybit_trade_buy(self):
  d=validate_bybit_trade({"s":"BTCUSDT","S":"Buy","T":D-300,
      "p":"71000","v":"0.2","i":"trade-x"},D)
  self.assertEqual((d["side"],d["notional_proxy"]),("Buy",14200))
 def test_bybit_liquidated_long_semantics(self):
  d=validate_liquidation({"s":"BTCUSDT","S":"Buy","T":D-100,
      "p":"71000","v":"0.1"},D)
  self.assertEqual(d["liquidated_position"],"LONG")
 def test_bybit_liquidated_short_semantics(self):
  d=validate_liquidation({"s":"BTCUSDT","S":"Sell","T":D-100,
      "p":"71000","v":"0.1"},D)
  self.assertEqual(d["liquidated_position"],"SHORT")
 def test_future_dated_event_fails(self):
  with self.assertRaises(ValueError):
   validate_bybit_trade({"s":"BTCUSDT","S":"Buy","T":D+1,
       "p":"71000","v":"1","i":"x"},D)
 def test_mexc_deal_side_and_volume_is_contracts(self):
  d=validate_rest("mexc_perp_deals",{"success":True,"data":[{
      "p":71000,"v":14,"T":1,"t":D-500}]},D)
  self.assertEqual(d["volume_unit"],"CONTRACTS_UNVERIFIED_MULTIPLIER")
 def test_wrong_mexc_deal_side_fails(self):
  with self.assertRaises(ValueError):
   validate_rest("mexc_perp_deals",{"success":True,"data":[{
       "p":71000,"v":14,"T":3,"t":D-100}]},D)
 def test_okx_aggressor_side(self):
  d=validate_rest("okx_spot_trades",{"code":"0","data":[{
      "instId":"BTC-USDT","tradeId":"abc","side":"sell",
      "px":"71000","sz":"0.1","ts":str(D-200)}]},D)
  self.assertEqual(d["side"],"sell")
 def test_old_index_fails(self):
  with self.assertRaises(ValueError):
   validate_rest("mexc_perp_index",{"success":True,"data":{
      "symbol":"BTC_USDT","timestamp":D-15000,"indexPrice":71000}},D)
 def test_empty_liquidations_not_zero_and_source_remains_schema_pass(self):
  b={"connected":True,"ack":True,"trade_children":10,
     "pings":2,"pongs":2,"schema_errors":[],"transport_errors":[],
     "liquidation_children":0}
  rr={n:{"success":1,"fail":0} for n in ("okx_spot_trades","mexc_perp_deals",
      "mexc_perp_index","mexc_perp_depth")}
  self.assertEqual(classify(b,rr,20),("JOINT_SCHEMA_SOURCE_PASS","NO_LIQUIDATION_EVENT_OBSERVED"))
 def test_missing_feed_blocks(self):
  b={"connected":True,"ack":True,"trade_children":10,
     "pings":2,"pongs":2,"schema_errors":[],"transport_errors":[],
     "liquidation_children":2}
  rr={n:{"success":1,"fail":0} for n in ("okx_spot_trades","mexc_perp_deals",
      "mexc_perp_index","mexc_perp_depth")}
  rr["okx_spot_trades"]["fail"]=1
  self.assertEqual(classify(b,rr,20)[0],"SOURCE_BLOCKED")
if __name__=="__main__":unittest.main()
