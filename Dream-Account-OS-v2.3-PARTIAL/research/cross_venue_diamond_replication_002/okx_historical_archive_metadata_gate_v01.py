from __future__ import annotations
import hashlib, json, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_002_okx_archive_metadata_v01"
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
INST="AVAX-USDT-SWAP"
MONTHS=["2024-09","2024-10","2024-11","2024-12"]+[f"2025-{m:02d}" for m in range(1,13)]
MODULES={"PRICE_1M":"2","FUNDING":"3"}
UA="CROSS-VENUE-DIAMOND-REPLICATION-002 OKX archive metadata/1.0"

def month_bounds(label):
    y,m=map(int,label.split("-"))
    b=datetime(y,m,1,tzinfo=timezone.utc)
    e=datetime(y+1,1,1,tzinfo=timezone.utc) if m==12 else datetime(y,m+1,1,tzinfo=timezone.utc)
    return int(b.timestamp()*1000),int(e.timestamp()*1000)

def fingerprint(o):
    return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def clean(body):
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

def call(module,begin,end):
    params={"module":module,"instType":"SWAP","dateAggrType":"monthly","begin":begin,"end":end,"instIdList":INST}
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    rec={}
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            rec["http_status"]=r.status
            rec["body"]=clean(json.loads(r.read().decode("utf-8","replace")))
    except urllib.error.HTTPError as e:
        rec["http_status"]=e.code
        raw=e.read().decode("utf-8","replace")
        try: rec["body"]=clean(json.loads(raw))
        except Exception: rec["body_text"]=raw[:1000]
    except Exception as e:
        rec["transport_error"]=repr(e)
    return rec

def metadata_available(rec):
    b=rec.get("body") or {}
    return rec.get("http_status")==200 and b.get("code")=="0" and int(b.get("data_count") or 0)>0

def main():
    receipt={
      "lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-002",
      "candidate":"CED1D-0031-AVAX20-CONTINUATION-H1",
      "stage":"OKX_HISTORICAL_ARCHIVE_METADATA_GATE_V01",
      "source_binding":{"instId":INST,"instType":"SWAP","dateAggrType":"monthly","modules":MODULES},
      "outcome_blind":True,
      "archive_payload_opened":False,
      "signal_calculation_performed":False,
      "return_calculation_performed":False,
      "pnl_calculation_performed":False,
      "2026_plus_accessed":False,
      "months":{}
    }
    for month in MONTHS:
        b,e=month_bounds(month)
        row={}
        for label,module in MODULES.items():
            rec=call(module,b,e)
            rec["metadata_available"]=metadata_available(rec)
            row[label]=rec
            time.sleep(0.35)
        receipt["months"][month]=row
    required=len(MONTHS)*len(MODULES)
    present=sum(int(v["metadata_available"]) for m in receipt["months"].values() for v in m.values())
    receipt["required_packages"]=required
    receipt["metadata_available_packages"]=present
    receipt["metadata_coverage_rate"]=present/required
    receipt["classification"]="OKX_ARCHIVE_METADATA_PASS" if present==required else ("OKX_ARCHIVE_METADATA_PARTIAL" if present else "OKX_ARCHIVE_METADATA_BLOCKED")
    receipt["source_fingerprint"]=fingerprint(receipt)
    p=OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_ARCHIVE_METADATA_RECEIPT_V0.1.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"packages":f"{present}/{required}","source_fingerprint":receipt["source_fingerprint"]},sort_keys=True))

if __name__=="__main__":
    main()
