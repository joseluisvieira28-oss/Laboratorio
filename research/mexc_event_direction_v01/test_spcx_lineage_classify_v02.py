import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from spcx_lineage_classify_v02 import classify
def example():
    return {"futures":{"symbol":"SPCXSTOCK_USDT","status":"FUTURES_CONTRACT_METADATA_PRESENT",
       "indexOrigin":["BINANCE_FUTURE","BITGET_FUTURE","BINANCETICKER","PYTH","KAIKO"]},
     "index":{"symbol":"SPCXSTOCK_USDT","status":"PUBLIC_INDEX_PRICE_PRESENT"},
     "event":{"exact_matches":1,"minute_cycles":[10,30],
       "product_state":"PAUSE","status":"BLOCKED"}}
class Guards(unittest.TestCase):
 def test_real_pause(self):
  self.assertEqual(classify(example()),"EVENT_10M_PAUSED_OR_UNAVAILABLE")
 def test_online_but_reference_not_certified(self):
  a=example();a["event"]["product_state"]="ONLINE"
  a["event"]["status"]="EXACT_PUBLIC_EVENT_PRODUCT_10M_PRESENT"
  self.assertEqual(classify(a),"REFERENCE_PRICE_PARITY_NOT_CERTIFIED")
 def test_missing_10minute(self):
  a=example();a["event"]["minute_cycles"]=[30]
  self.assertEqual(classify(a),"EVENT_10M_NOT_PROVEN_AVAILABLE")
 def test_wrong_index(self):
  a=example();a["index"]["symbol"]="SPCX_USDT"
  self.assertEqual(classify(a),"INDEX_SOURCE_BLOCKED")
 def test_even_full_metadata_not_economic_go(self):
  a=example();a["event"]["product_state"]="ONLINE"
  a["event"]["status"]="EXACT_PUBLIC_EVENT_PRODUCT_10M_PRESENT"
  for k in ("provider_defined_cash_to_tracker_relation_certified",
            "provider_defined_tracker_to_event_expiry_index_certified",
            "actual_event_server_openprice_settlement_parity_certified"):a[k]=True
  self.assertEqual(classify(a),"PROSPECTIVE_SHADOW_SOURCE_ONLY__NOT_ECONOMIC_GO")
if __name__=="__main__":unittest.main()
