import datetime as dt,hashlib,io,json,pathlib,sys,unittest,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from nvda_event10m_expiry_shadow_v06 import digest
from nvda_event10m_anchor_v07 import verify_metadata,verify_zip,parse_utc
from nvda_event10m_custody_expiry_v07 import validate_before_outcome
D=1793626500000
def decision():
    return {"study":"NVIDIA_EVENT10M_INTEGRATED_V05",
      "status":"PAPER_FORECAST_UNANCHORED_NOT_EVENT_FUTURES_EXECUTION",
      "forecast":{"study":"NVIDIA_EVENT10M_CASH_REF_V01","candidate":"UP",
         "decision_ts_ms":D,"expiry_target_ms":D+600000}}
def archive(raw):
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",compression=zipfile.ZIP_DEFLATED) as f:f.writestr("decision.json",raw)
    return mem.getvalue()
def info(obj,created_ms=None):
    when=(created_ms if created_ms is not None else D+1000)
    date=dt.datetime.fromtimestamp(when/1000,dt.timezone.utc).isoformat().replace("+00:00","Z")
    z=archive(json.dumps(obj).encode())
    return {"id":42,"name":"nvda-event10m-preoutcome-decision","expired":False,
      "workflow_run":{"id":99},"created_at":date,"digest":"sha256:"+hashlib.sha256(z).hexdigest()},z
class CustodyUnit(unittest.TestCase):
    def test_server_metadata_and_zip_pass(self):
        o=decision();m,z=info(o);raw=json.dumps(o).encode()
        time,hash_zip=verify_metadata(m,o,99,42)
        self.assertTrue(time<D+600000)
        self.assertEqual(verify_zip(z,hash_zip,raw),hashlib.sha256(raw).hexdigest())
    def test_late_artifact_blocked(self):
        o=decision();m,z=info(o,D+600000)
        with self.assertRaises(ValueError):verify_metadata(m,o,99,42)
    def test_wrong_run_blocked(self):
        o=decision();m,z=info(o);m["workflow_run"]["id"]=100
        with self.assertRaises(ValueError):verify_metadata(m,o,99,42)
    def test_mutated_decision_bytes_rejected(self):
        o=decision();m,z=info(o);_,sha=verify_metadata(m,o,99,42)
        with self.assertRaises(ValueError):verify_zip(z,sha,json.dumps({"wrong":1}).encode())
    def test_modified_zip_rejected(self):
        o=decision();m,z=info(o);_,sha=verify_metadata(m,o,99,42)
        with self.assertRaises(ValueError):verify_zip(z+b"bad",sha,json.dumps(o).encode())
    def test_wrong_artifact_name_rejected(self):
        o=decision();m,z=info(o);m["name"]="different"
        with self.assertRaises(ValueError):verify_metadata(m,o,99,42)
    def test_self_asserted_anchor_rejected(self):
        o=decision()
        with self.assertRaises(ValueError):validate_before_outcome(o,{"custody_independently_authenticated":True})
    def test_valid_anchor_at_pre_expiry_clock(self):
        # Patch module ms(), no actual external source.
        from unittest.mock import patch
        o=decision()
        a={"anchor_protocol":"GITHUB_API_ZIP_BYTE_CUSTODY_V07",
            "custody_independently_authenticated":True,
            "decision_canonical_sha256":digest(o),"published_ms":D+1000,
            "expiry_target_ms":D+600000,"github_repository":"joseluisvieira28-oss/Laboratorio"}
        with patch("nvda_event10m_custody_expiry_v07.ms",return_value=D+2000):
            self.assertEqual(validate_before_outcome(o,a),D+600000)
        with patch("nvda_event10m_custody_expiry_v07.ms",return_value=D+600001):
            with self.assertRaises(ValueError):validate_before_outcome(o,a)
if __name__=="__main__":unittest.main()
