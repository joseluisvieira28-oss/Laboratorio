from __future__ import annotations
import json,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_001_okx_archive_status_v01"
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
UA="CROSS-VENUE-DIAMOND-REPLICATION-001 exact archive status/1.0"
def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)

def clean(body):
    if not isinstance(body,dict): return body
    out={"code":body.get("code"),"msg":body.get("msg")}
    data=body.get("data")
    if isinstance(data,list):
        out["data_count"]=len(data)
        meta=[]
        for row in data:
            if isinstance(row,dict):
                keep={}
                for k,v in row.items():
                    lk=k.lower()
                    if any(t in lk for t in ["file","url","href","state","status","inst","date","begin","end","module","type","name","ts","result"]):
                        keep[k]=v
                meta.append(keep)
            else:
                meta.append({"row_type":type(row).__name__})
        out["metadata"]=meta
    return out

def call(module):
    params={
      "module":str(module),
      "instType":"SWAP",
      "dateAggrType":"monthly",
      "begin":ms("2024-01-01T00:00:00Z"),
      "end":ms("2024-02-01T00:00:00Z"),
      "instIdList":"BTC-USDT-SWAP",
    }
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    rec={"module":str(module)}
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read().decode("utf-8","replace"); rec["http_status"]=r.status
            try: rec["body"]=clean(json.loads(raw))
            except Exception: rec["body_text"]=raw[:3000]
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace"); rec["http_status"]=e.code
        try: rec["body"]=clean(json.loads(raw))
        except Exception: rec["body_text"]=raw[:3000]
    except Exception as e:
        rec["transport_error"]=repr(e)
    return rec

def main():
    receipt={
      "lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-001",
      "stage":"OKX_EXACT_ARCHIVE_STATUS_PROBE",
      "source_binding":{"price_module":"2","funding_module":"3","dateAggrType":"monthly","instType":"SWAP"},
      "outcome_blind":True,
      "archive_payload_opened":False,
      "signal_calculation_performed":False,
      "return_calculation_performed":False,
      "pnl_calculation_performed":False,
      "polls":[]
    }
    for poll in range(1,6):
        row={"poll":poll,"module2":call(2),"module3":call(3)}
        receipt["polls"].append(row)
        print("POLL",poll,json.dumps(row,sort_keys=True)[:8000],flush=True)
        if poll<5: time.sleep(2)
    (OUT/"OKX_EXACT_ARCHIVE_STATUS_PROBE_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
