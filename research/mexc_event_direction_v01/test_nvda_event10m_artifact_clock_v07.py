import unittest,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from nvda_event10m_expiry_shadow_v06 import settle,digest
class PrecisionRegression(unittest.TestCase):
 def test_second_precision_artifact_metadata_is_not_falsely_rejected(self):
  d=1800000000500
  event={"study":"NVIDIA_EVENT10M_INTEGRATED_V05",
   "status":"PAPER_FORECAST_UNANCHORED_NOT_EVENT_FUTURES_EXECUTION",
   "decision_public_index":100,
   "forecast":{"study":"NVIDIA_EVENT10M_CASH_REF_V01",
     "candidate":"UP","asset":"NVIDIA_USDT","horizon_min":10,
     "decision_ts_ms":d,"expiry_target_ms":d+600000,
     "payout_up":0.80,"payout_down":0.80}}
  anchor={"decision_canonical_sha256":digest(event),
    "published_ms":d-500,"github_artifact_id":42,
    "github_artifact_digest_sha256":"a"*64}
  tick={"symbol":"NVIDIA_USDT","raw_sha256":"b"*64,
    "server_ts_ms":d+600000+500,"received_ms":d+600000+700,
    "index_price":101}
  row=settle(event,anchor,tick)
  self.assertEqual(row["index_shadow_outcome"],"WIN")
  self.assertFalse(row["custody_independently_authenticated"])
if __name__=="__main__":unittest.main()
