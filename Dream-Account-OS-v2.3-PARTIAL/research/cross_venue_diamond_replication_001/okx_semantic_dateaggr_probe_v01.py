from __future__ import annotations
import json,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_001_okx_semantic_date_diag_v01"
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
UA="CROSS-VENUE-DIAMOND-REPLICATION-001 semantic date diagnostic/1.0"
CANDIDATES=["D","M","day","month","daily","monthly","1d","1m","DAY","MONTH","0","6"]
def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
def clean(body):
    if not isinstance(body,dict): return body
    data=body.get("data")
    out={"code":body.get("code"),"msg":body.get("msg")}
    if isinstance(data,list):
        out["data_count"]=len(data)
        meta=[]
        for row in data:
            if isinstance(row,dict):
                kept={}
                for k,v in row.items():
                    if any(t in k.lower() for t in ["file","url","href","inst","date","begin","end","module","type","name","ts"]):
                        kept[k]=v
                meta.append(kept)
        out["metadata"]=meta
    return out
def probe(agg):
    params={"module":"1","instType":"SWAP","dateAggrType":agg,
            "begin":ms("2024-01-01T00:00:00Z"),"end":ms("2024-01-08T00:00:00Z"),
            "instIdList":"BTC-USDT-SWAP"}
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    rec={"dateAggrType":agg}
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read().decode("utf-8","replace");rec["http_status"]=r.status
            try: rec["body"]=clean(json.loads(raw))
            except Exception: rec["body_text"]=raw[:2000]
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace");rec["http_status"]=e.code
        try: rec["body"]=clean(json.loads(raw))
        except Exception: rec["body_text"]=raw[:2000]
    except Exception as e: rec["transport_error"]=repr(e)
    return rec
def main():
    receipt={"lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-001","stage":"OKX_SEMANTIC_DATE_AGGREGATION_DIAGNOSTIC",
             "outcome_blind":True,"archive_payload_opened":False,"signal_calculation_performed":False,
             "return_calculation_performed":False,"pnl_calculation_performed":False,"probes":[]}
    accepted=[]
    for a in CANDIDATES:
        rec=probe(a);receipt["probes"].append(rec)
        b=rec.get("body") if isinstance(rec.get("body"),dict) else {}
        if rec.get("http_status")==200 or b.get("code")=="0": accepted.append(rec)
        print(a,rec.get("http_status"),json.dumps(b,sort_keys=True)[:1600] if b else rec.get("transport_error"))
        time.sleep(.35)
    receipt["accepted"]=accepted
    (OUT/"OKX_SEMANTIC_DATE_AGGREGATION_DIAGNOSTIC_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print("ACCEPTED",json.dumps(accepted,sort_keys=True)[:8000])
    return 0
if __name__=="__main__": raise SystemExit(main())
