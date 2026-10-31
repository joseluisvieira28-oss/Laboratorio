import datetime as dt,hashlib,io,json,pathlib,sys,unittest,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from btc_event10m_custody_v05 import server_metadata,verify_archive,hash_bytes
from btc_event10m_raw_replay_v06 import validate_eight,bstats
from event10m_spot_depth_divergence_v03 import decide
D=int(dt.datetime(2026,11,2,12,0,25,tzinfo=dt.timezone.utc).timestamp()*1000)
def rawjson(v):return json.dumps(v,separators=(",",":")).encode()
def books(venue):
    bid_qty=1.7 if venue=="OKX_SPOT" else .5
    ask_qty=.6 if venue=="OKX_SPOT" else 1.7
    b=[[69999-i,bid_qty] for i in range(20)]
    a=[[70000+i,ask_qty] for i in range(20)]
    return b,a
def fixture():
    raw={};pairs=[]
    for i,delta in enumerate((12000,7000,1500)):
        t=D-delta;packets={}
        for key,venue,prefix in (("okx_spot","OKX_SPOT","okx_book_"),
                                 ("mexc_futures","MEXC_PERPETUAL","mexc_book_")):
            bids,asks=books(venue);filename=f"{prefix}{i}.json"
            if venue=="OKX_SPOT":
                content={"code":"0","data":[{"ts":str(t-300),"bids":bids,"asks":asks}]}
            else:
                content={"success":True,"data":{"bids":bids,"asks":asks,"timestamp":t-300}}
            blob=rawjson(content);raw[filename]=blob
            packets[key]={"venue":venue,"received_ms":t-100,
                "sha256":hash_bytes(blob),"raw_file":filename,**bstats(bids,asks)}
            if venue=="OKX_SPOT":packets[key]["server_ms"]=t-300
            else:packets[key]["book_server_ms_unverified"]=t-300
        pairs.append({"asset":"BTC_USDT","received_ms":t,**packets})
    pr=rawjson({"success":True,"data":[{"symbol":"BTC_USDT","contractId":10,
         "state":"ONLINE","cycleConfigMap":{"MINUTE":[{"val":10,"upPayRate":.7,"downPayRate":.7}]}}]})
    ix=rawjson({"success":True,"data":{"symbol":"BTC_USDT","timestamp":D-500,"indexPrice":70000.}})
    raw["mexc_event_contract_detail.json"]=pr;raw["mexc_index.json"]=ix
    product={"symbol":"BTC_USDT","duration_min":10,"state":"ONLINE","contract_id":10,
       "received_ms":D-4000,"sha256":hash_bytes(pr),"raw_file":"mexc_event_contract_detail.json",
       "up_pay_rate":.7,"down_pay_rate":.7}
    index={"symbol":"BTC_USDT","received_ms":D-300,"server_ms":D-500,
      "index_price":70000.,"sha256":hash_bytes(ix),"raw_file":"mexc_index.json"}
    source={"samples":pairs,"product":product,"index":index,
      "asof_ms":D,"source_gate_all_pass":True}
    model=decide("BTC_USDT",D,pairs,product,index)
    obj={"study":"BTC_EVENT10M_V05_FROZEN_PROSPECTIVE_PAPER_ONLY",
      "status":"PAPER_FORECAST_UNANCHORED","source_receipt":source,
      "decision_ms":D,"expiry_target_ms":D+600000,"forecast":model}
    return obj,raw
def zipped(obj,raw):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("decision.json",rawjson(obj))
        for k,v in raw.items():z.writestr("raw/"+k,v)
    return b.getvalue()
def raw_zip(raw):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        for k,v in raw.items():z.writestr("raw/"+k,v)
    b.seek(0)
    return zipfile.ZipFile(b)
class Science(unittest.TestCase):
 def test_eight_sources_replay_raw_pass(self):
    d,raw=fixture()
    with raw_zip(raw) as z:self.assertTrue(validate_eight(z,d))
 def test_complete_preexpiry_zip_pass(self):
    d,raw=fixture();decision=rawjson(d);archive=zipped(d,raw)
    self.assertEqual(verify_archive(archive,hash_bytes(archive),decision),hash_bytes(decision))
 def test_false_imbalance_even_with_valid_zip_sha_blocked(self):
    d,raw=fixture();d["source_receipt"]["samples"][0]["okx_spot"]["imbalance"]=.99
    with raw_zip(raw) as z:
      with self.assertRaisesRegex(ValueError,"BOOK_FEATURE_NOT_REPRODUCED"):validate_eight(z,d)
 def test_false_payout_same_raw_bytes_blocked(self):
    d,raw=fixture();d["source_receipt"]["product"]["up_pay_rate"]=.8
    with raw_zip(raw) as z:
      with self.assertRaisesRegex(ValueError,"DYNAMIC_PAYOUT_NOT_IN_RAW"):validate_eight(z,d)
 def test_false_index_same_raw_bytes_blocked(self):
    d,raw=fixture();d["source_receipt"]["index"]["index_price"]=70005.
    with raw_zip(raw) as z:
      with self.assertRaisesRegex(ValueError,"INDEX_PRICE_NOT_IN_RAW"):validate_eight(z,d)
 def test_okx_forged_server_time_blocked(self):
    d,raw=fixture();d["source_receipt"]["samples"][1]["okx_spot"]["server_ms"]+=1
    with raw_zip(raw) as z:
      with self.assertRaisesRegex(ValueError,"OKX_SERVER_TIME_NOT_IN_RAW"):validate_eight(z,d)
 def test_false_product_state_blocked(self):
    d,raw=fixture();d["source_receipt"]["product"]["state"]="PAUSE"
    with raw_zip(raw) as z:
      with self.assertRaisesRegex(ValueError,"PRODUCT_STATE_OR_CONTRACT_NOT_IN_RAW"):validate_eight(z,d)
 def test_raw_http_tamper_hash_fail(self):
    d,raw=fixture();decision=rawjson(d)
    raw["okx_book_0.json"]=b"tampered";archive=zipped(d,raw)
    with self.assertRaisesRegex(ValueError,"SOURCE_RAW_BYTES_NOT_MATCHING_DECISION"):
      verify_archive(archive,hash_bytes(archive),decision)
 def test_server_metadata_before_expiry(self):
    d,_=fixture()
    meta={"id":42,"name":"btc-event10m-preexpiry-source-and-decision",
          "expired":False,"workflow_run":{"id":99},
          "created_at":dt.datetime.fromtimestamp((D+1000)/1000,dt.timezone.utc).isoformat(),
          "digest":"sha256:"+"a"*64}
    self.assertEqual(server_metadata(meta,d,99,42)[1],"a"*64)
 def test_late_artifact_blocked(self):
    d,_=fixture()
    meta={"id":42,"name":"btc-event10m-preexpiry-source-and-decision",
          "expired":False,"workflow_run":{"id":99},
          "created_at":dt.datetime.fromtimestamp((D+600000)/1000,dt.timezone.utc).isoformat(),
          "digest":"sha256:"+"a"*64}
    with self.assertRaisesRegex(ValueError,"GITHUB_ARTIFACT_NOT_PUBLISHED_BEFORE_EXPIRY"):
      server_metadata(meta,d,99,42)
 def test_wrong_decision_bytes_rejected(self):
    d,raw=fixture();archive=zipped(d,raw)
    with self.assertRaises(ValueError):verify_archive(archive,hash_bytes(archive),b"{}")
if __name__=="__main__":unittest.main()
