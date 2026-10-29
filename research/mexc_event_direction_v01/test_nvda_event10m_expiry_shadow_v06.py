import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from nvda_event10m_expiry_shadow_v06 import settle,digest
def setup():
    d=1793630110000
    obj={"study":"NVIDIA_EVENT10M_INTEGRATED_V05",
         "status":"PAPER_FORECAST_UNANCHORED_NOT_EVENT_FUTURES_EXECUTION",
         "decision_public_index":100.0,
         "forecast":{"study":"NVIDIA_EVENT10M_CASH_REF_V01",
         "candidate":"UP","asset":"NVIDIA_USDT","horizon_min":10,
         "decision_ts_ms":d,"expiry_target_ms":d+600000,
         "payout_up":0.8,"payout_down":0.85}}
    a={"decision_canonical_sha256":digest(obj),"published_ms":d+1000,
       "github_artifact_id":123,"github_artifact_digest_sha256":"a"*64}
    t={"symbol":"NVIDIA_USDT","raw_sha256":"b"*64,
       "server_ts_ms":d+600000+1000,
       "received_ms":d+600000+1200,"index_price":101}
    return obj,a,t
class Guards(unittest.TestCase):
    def test_win_shadow(self):
        x=settle(*setup());self.assertEqual((x["index_shadow_outcome"],x["index_shadow_unit_return"]),("WIN",.8))
        self.assertFalse(x["custody_independently_authenticated"])
    def test_loss_shadow(self):
        x,a,t=setup();t["index_price"]=99
        self.assertEqual(settle(x,a,t)["index_shadow_unit_return"],-1)
    def test_tie_shadow(self):
        x,a,t=setup();t["index_price"]=100
        self.assertEqual(settle(x,a,t)["index_shadow_unit_return"],0)
    def test_missing_preexpiry_anchor(self):
        x,a,t=setup();a["published_ms"]=x["forecast"]["expiry_target_ms"]
        with self.assertRaises(ValueError):settle(x,a,t)
    def test_decision_mutation_block(self):
        x,a,t=setup();x["forecast"]["candidate"]="DOWN"
        with self.assertRaises(ValueError):settle(x,a,t)
    def test_tick_before_target_block(self):
        x,a,t=setup();t["server_ts_ms"]=x["forecast"]["expiry_target_ms"]-1
        with self.assertRaises(ValueError):settle(x,a,t)
    def test_stale_tick_block(self):
        x,a,t=setup();t["server_ts_ms"]=x["forecast"]["expiry_target_ms"]+6000
        with self.assertRaises(ValueError):settle(x,a,t)
    def test_unsupported_source_block(self):
        x,a,t=setup();t["symbol"]="ETH_USDT"
        with self.assertRaises(ValueError):settle(x,a,t)
    def test_abstain_cannot_score(self):
        x,a,t=setup();x["forecast"]["candidate"]="ABSTAIN";a["decision_canonical_sha256"]=digest(x)
        with self.assertRaises(ValueError):settle(x,a,t)
if __name__=="__main__":unittest.main()
