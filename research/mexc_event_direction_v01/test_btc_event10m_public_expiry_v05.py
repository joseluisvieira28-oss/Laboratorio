import datetime as dt,unittest,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from btc_event10m_public_expiry_v05 import check_before_expiry,score_index_shadow
D=int(dt.datetime(2026,11,2,12,0,25,tzinfo=dt.timezone.utc).timestamp()*1000)
def fixture(side="UP"):
 x={"study":"BTC_EVENT10M_V05_FROZEN_PROSPECTIVE_PAPER_ONLY",
     "status":"PAPER_FORECAST_UNANCHORED",
     "forecast":{"side":side,"decision_ms":D,"target_ms":D+600000,"side_payout":.7},
     "source_receipt":{"index":{"index_price":70000.}}}
 a={"status":"GITHUB_SERVER_ARCHIVE_VERIFIED","independent_custody_proven":True,
    "repo":"joseluisvieira28-oss/Laboratorio","decision_ms":D,
    "expiry_target_ms":D+600000,"artifact_created_ms":D+1000}
 t={"symbol":"BTC_USDT","server_ms":D+600001,"received_ms":D+600100,"index_price":70001.}
 return x,a,t
class Guards(unittest.TestCase):
 def test_preexpiry(self):
  x,a,_=fixture();self.assertEqual(check_before_expiry(x,a,D+2000),D+600000)
 def test_wrong_anchor(self):
  x,a,_=fixture();a["independent_custody_proven"]=False
  with self.assertRaises(ValueError):check_before_expiry(x,a,D+1000)
 def test_late_anchor(self):
  x,a,_=fixture();a["artifact_created_ms"]=D+600000
  with self.assertRaises(ValueError):check_before_expiry(x,a,D+2000)
 def test_abstain_never_expiry(self):
  x,a,_=fixture("ABSTAIN")
  with self.assertRaises(ValueError):check_before_expiry(x,a,D+2000)
 def test_win(self):
  x,a,t=fixture();y=score_index_shadow(x,t)
  self.assertEqual((y["proxy_result"],y["hypothetical_q_unit_payoff"]),("WIN",.7))
  self.assertIsNone(y["event_futures_realized_PnL"])
 def test_loss(self):
  x,a,t=fixture();t["index_price"]=69999.
  self.assertEqual(score_index_shadow(x,t)["proxy_result"],"LOSS")
 def test_wrong_tick_time(self):
  x,a,t=fixture();t["server_ms"]=D+599999
  with self.assertRaises(ValueError):score_index_shadow(x,t)
 def test_stale_tick(self):
  x,a,t=fixture();t["server_ms"]=D+606000
  with self.assertRaises(ValueError):score_index_shadow(x,t)
if __name__=="__main__":unittest.main()
