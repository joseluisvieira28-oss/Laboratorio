import datetime as dt,hashlib,io,json,pathlib,sys,unittest,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from btc_event10m_custody_v05 import server_metadata,verify_archive,FILES,hash_bytes
from btc_event10m_source_gates_v04 import asof
from event10m_spot_depth_divergence_v03 import decide
D=int(dt.datetime(2026,11,2,12,0,25,tzinfo=dt.timezone.utc).timestamp()*1000)
def fixture():
    payload={}
    pairs=[]
    for i,delta in enumerate((12000,7000,1500)):
        t=D-delta
        books={}
        for v,key in (("OKX_SPOT","okx_spot"),("MEXC_PERPETUAL","mexc_futures")):
            name=("okx_book_" if v=="OKX_SPOT" else "mexc_book_")+str(i)+".json"
            raw=json.dumps({"i":i,"venue":v}).encode();payload[name]=raw
            books[key]={"venue":v,"imbalance":.4 if v=="OKX_SPOT" else -.5,
              "spread_bps":.5,"received_ms":t-100,"sha256":hash_bytes(raw),
              "raw_file":name}
            if v=="OKX_SPOT":books[key]["server_ms"]=t-300
        pairs.append({"asset":"BTC_USDT","received_ms":t,**books})
    p_raw=b'{"event":"BTC_USDT"}';i_raw=b'{"index":"BTC_USDT"}'
    payload["mexc_event_contract_detail.json"]=p_raw
    payload["mexc_index.json"]=i_raw
    prod={"symbol":"BTC_USDT","duration_min":10,"state":"ONLINE",
      "received_ms":D-4000,"up_pay_rate":.7,"down_pay_rate":.7,
      "sha256":hash_bytes(p_raw),"raw_file":"mexc_event_contract_detail.json"}
    ind={"symbol":"BTC_USDT","received_ms":D-300,"server_ms":D-500,
      "index_price":70000.,"sha256":hash_bytes(i_raw),"raw_file":"mexc_index.json"}
    source={"samples":pairs,"product":prod,"index":ind,"asof_ms":D,
      "source_gate_all_pass":True}
    forecast=decide("BTC_USDT",D,pairs,prod,ind)
    o={"study":"BTC_EVENT10M_V05_FROZEN_PROSPECTIVE_PAPER_ONLY",
      "status":"PAPER_FORECAST_UNANCHORED","source_receipt":source,
      "decision_ms":D,"expiry_target_ms":D+600000,"forecast":forecast}
    return o,payload
def zipped(obj,payload):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("decision.json",json.dumps(obj,sort_keys=True).encode())
        for k,v in payload.items():z.writestr("raw/"+k,v)
    return b.getvalue()
class Custody(unittest.TestCase):
 def test_archive_exact_source_bytes_pass(self):
    obj,p=fixture();raw=json.dumps(obj,sort_keys=True).encode();zipraw=zipped(obj,p)
    self.assertEqual(verify_archive(zipraw,hash_bytes(zipraw),raw),hash_bytes(raw))
 def test_source_mutated_after_decision_rejected(self):
    obj,p=fixture();raw=json.dumps(obj,sort_keys=True).encode()
    p["okx_book_0.json"]=b"tampered";blob=zipped(obj,p)
    with self.assertRaises(ValueError):verify_archive(blob,hash_bytes(blob),raw)
 def test_server_published_preexpiry(self):
    obj,_=fixture()
    m={"id":42,"name":"btc-event10m-preexpiry-source-and-decision","expired":False,
       "workflow_run":{"id":99},"created_at":dt.datetime.fromtimestamp((D+1000)/1000,dt.timezone.utc).isoformat(),
       "digest":"sha256:"+"a"*64}
    self.assertEqual(server_metadata(m,obj,99,42)[1],"a"*64)
 def test_late_upload_block(self):
    obj,_=fixture()
    m={"id":42,"name":"btc-event10m-preexpiry-source-and-decision","expired":False,
       "workflow_run":{"id":99},"created_at":dt.datetime.fromtimestamp((D+600000)/1000,dt.timezone.utc).isoformat(),
       "digest":"sha256:"+"a"*64}
    with self.assertRaises(ValueError):server_metadata(m,obj,99,42)
 def test_decision_tampering_rejected(self):
    obj,p=fixture();raw=json.dumps(obj,sort_keys=True).encode();z=zipped(obj,p)
    with self.assertRaises(ValueError):verify_archive(z,hash_bytes(z),b"{}")
if __name__=="__main__":unittest.main()
