import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from triple_flow_three_venue_stream_source_v02 import make,classify_msg,judge
D=1800000000000
class ThreeVenue(unittest.TestCase):
 def test_real_bybit_pong_format_counted(self):
  s=make("BYBIT")
  classify_msg("BYBIT",'{"op":"ping","ret_msg":"pong"}',D,s)
  self.assertEqual(s["pongs_received"],1)
 def test_bybit_long_liquidation(self):
  s=make("BYBIT")
  classify_msg("BYBIT",'{"topic":"allLiquidation.BTCUSDT","data":[{"s":"BTCUSDT","S":"Buy","T":1799999999900,"p":"71000","v":"0.1"}]}',D,s)
  self.assertEqual((s["liquidation_children"],s["long_liquidated"]),(1,1))
 def test_okx_spot_side_signed(self):
  s=make("OKX")
  classify_msg("OKX",'{"arg":{"channel":"trades","instId":"BTC-USDT"},"data":[{"instId":"BTC-USDT","side":"sell","tradeId":"123","px":"71000","sz":"0.01","ts":"1799999999900"}]}',D,s)
  self.assertEqual(s["sell_trade_children"],1)
 def test_mexc_ws_deal_contract_units(self):
  s=make("MEXC")
  classify_msg("MEXC",'{"channel":"push.deal","symbol":"BTC_USDT","data":{"T":1,"p":71000,"v":5,"t":1799999999900}}',D,s)
  self.assertEqual(s["buy_trade_children"],1)
 def test_mexc_index_source_ts(self):
  s=make("MEXC")
  classify_msg("MEXC",'{"channel":"push.index.price","symbol":"BTC_USDT","ts":1799999999900,"data":{"price":71000,"symbol":"BTC_USDT"}}',D,s)
  self.assertEqual(s["index_messages"],1)
 def test_invalid_future_trade_rejected(self):
  s=make("MEXC")
  with self.assertRaises(ValueError):
   classify_msg("MEXC",'{"channel":"push.deal","symbol":"BTC_USDT","data":{"T":1,"p":71000,"v":5,"t":1800000000001}}',D,s)
 def test_missing_okx_index_blocks(self):
  states={x:make(x) for x in ("BYBIT","OKX","MEXC")}
  for s in states.values():
   s["connected"]=True;s["completed_window"]=True;s["trade_children"]=4
  states["BYBIT"]["subscription_ack"]=True;states["BYBIT"]["pongs_received"]=3
  states["OKX"]["subscription_ack"]=True
  self.assertEqual(judge(states),"SOURCE_BLOCKED")
 def test_joint_source_acceptance_no_liquidation_required(self):
  states={x:make(x) for x in ("BYBIT","OKX","MEXC")}
  for s in states.values():
   s["connected"]=True;s["completed_window"]=True;s["trade_children"]=4
  states["BYBIT"]["subscription_ack"]=True;states["BYBIT"]["pongs_received"]=3
  states["OKX"]["subscription_ack"]=True
  states["MEXC"]["index_messages"]=1
  self.assertEqual(judge(states),"THREE_PUBLIC_WS_SCHEMA_SOURCE_PASS")
if __name__=="__main__":unittest.main()
