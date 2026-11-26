#!/usr/bin/env python3
"""Inspect TWO pre-frozen free Parquet files. NO TRADES, NO USER ROWS WRITTEN.\nZero wallets exposed. Schema evidence is source-only, never a performance result.\n"""
import collections
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import urllib.request

import pyarrow as pa
import pyarrow.parquet as pq

OUT=pathlib.Path(__file__).resolve().parent/"schema_results"
BASE="https://huggingface.co/datasets/ProbioticFarmer/hyperliquid-augmented-copytrading/resolve/main/"
FILES=(
 ("2025-07-29","snapshots_perp/date=2025-07-29/678380000_1753747400783.parquet",12794566,
  "8e2bc43fd724335d6bf4e4e6aa990d4f491f15450f004172050190277a2f0262"),
 ("2026-10-13","snapshots_perp/date=2026-10-13/1181670000_1791850169837.parquet",23141592,
  "64699678e3b67332ad40f060862bda35ee3f610b56c9903fa515bb3e1e25d77c"),
)
def fetch(path,maxn):
    url=BASE+path+"?download=true"
    begin=dt.datetime.now(dt.timezone.utc).isoformat()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-LIQMAP003-Public-Parquet-Schema-ReadOnly/1.0"})
    with urllib.request.urlopen(req,timeout=100) as res:
        raw=res.read(maxn+1)
    end=dt.datetime.now(dt.timezone.utc).isoformat()
    if len(raw)>maxn:raise ValueError("SOURCE_BLOCKED size over limit")
    return raw,{"url":url,"start_utc":begin,"end_utc":end,"bytes":len(raw),
                "raw_sha256":hashlib.sha256(raw).hexdigest()}

def safe_stats(table):
    names=table.schema.names
    fields=[{"name":field.name,"type":str(field.type)} for field in table.schema]
    result={"num_rows":table.num_rows,"num_columns":table.num_columns,"schema":fields}
    liq=[x for x in names if "liq" in x.lower() and ("price" in x.lower() or "px" in x.lower())]
    coincols=[x for x in names if any(k==x.lower() for k in ("market","coin","symbol","asset","ticker","instrument"))]
    clocks=[x for x in names if any(a in x.lower() for a in ("timestamp","as_of","snapshot","observed_at","time"))]
    values=[x for x in names if any(z in x.lower() for z in ("size","notional","value","position"))]
    result.update({"liq_price_columns":liq,"market_columns":coincols,
                   "time_columns":clocks,"position_size_columns":values})
    # Aggregate BTC counts without exposing any wallet/user contents.
    cstat={}
    for col in coincols:
        try:
            vals=table[col].to_pylist()
            c=collections.Counter(str(v) for v in vals if v is not None)
            cstat[col]={"distinct":len(c),"top_markets":[{"value":v,"rows":n} for v,n in c.most_common(12)],
                        "BTC_rows":sum(n for v,n in c.items() if v.upper().split(":")[-1] in ("BTC","BTCUSDT","BTC-PERP"))}
        except Exception as e:cstat[col]={"error":str(e)[:100]}
    result["market_coverage"]=cstat
    clocksafe={}
    for col in clocks[:6]:
        try:
            x=table[col].to_pylist()
            q=[v for v in x if v is not None]
            if not q:continue
            kinds=collections.Counter(type(v).__name__ for v in q)
            clocksafe[col]={"count":len(q),"type_counts":dict(kinds),
              "minimum":str(min(q))[:80],"maximum":str(max(q))[:80],
              "n_unique":len(set(map(str,q)))}
        except Exception as e:clocksafe[col]={"error":str(e)[:100]}
    result["time_coverage"]=clocksafe
    liqstats={}
    for col in liq[:3]:
        try:
            z=table[col].to_pylist()
            valid=[float(v) for v in z if v is not None and isinstance(v,(int,float)) and math.isfinite(float(v)) and float(v)>0]
            liqstats[col]={"nonnull_finite_positive":len(valid),
                           "min_price":min(valid) if valid else None,
                           "max_price":max(valid) if valid else None}
        except Exception as e:liqstats[col]={"error":str(e)[:100]}
    result["liq_coverage"]=liqstats
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={"experiment":"LIQMAP003-PARQUET-SCHEMA","no_trades":True,
            "files":[],"result":"SOURCE_BLOCKED"}
    for day,path,size,oid in FILES:
        item={"date":day,"path":path,"metadata_bytes":size,"metadata_lfs_sha256":oid}
        try:
            raw,receipt=fetch(path,35_000_000)
            item["receipt"]=receipt
            if len(raw)!=size:raise ValueError("SOURCE_BLOCKED hf byte count disagreement")
            if receipt["raw_sha256"]!=oid:raise ValueError("SOURCE_BLOCKED hf LFS hash disagreement")
            t=pq.read_table(io.BytesIO(raw))
            item["structure"]=safe_stats(t)
            item["status"]="SCHEMA_PASS" if item["structure"]["liq_price_columns"] and item["structure"]["market_columns"] else "NO_LIQ_PRICE_OR_MARKET"
        except Exception as e:
            item["status"]="SOURCE_BLOCKED"
            item["error"]=type(e).__name__+": "+str(e)[:450]
        result["files"].append(item)
        (OUT/"SCHEMA_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
        print("SCHEMA",day,item["status"],"columns",
             [f["name"] for f in item.get("structure",{}).get("schema",[])][:35],
             "BTC",item.get("structure",{}).get("market_coverage"),flush=True)
    result["result"]="TWO_FILE_SCHEMA_PASS" if all(x["status"]=="SCHEMA_PASS" for x in result["files"]) else "SCHEMA_OR_SOURCE_BLOCKED"
    (OUT/"SCHEMA_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# LIQMAP003 real positions schema audit — two sample dates","",
       "Files are public HF Parquet; not HyperQuant map timestamps, not Neuron.",
       "No raw private identifiers or wallet rows archived; source byte LFS hashes verified.",
       ""]
    for f in result["files"]:
        s=f.get("structure",{})
        lines += ["- "+f["date"]+": "+f["status"]+
           ", records "+str(s.get("num_rows"))+", liq fields "+str(s.get("liq_price_columns"))+
           ", time fields "+str(s.get("time_columns")),
           "  Markets: "+str(s.get("market_coverage"))[:600],
           "  timestamp coverage: "+str(s.get("time_coverage"))[:600]]
    lines+=["", "**Outcome: "+result["result"]+"**",
           "No historical PnL or map predictor GO inferred from file presence."]
    (OUT/"SCHEMA_REPORT.md").write_text("\n".join(lines)+"\n")
    if result["result"]!="TWO_FILE_SCHEMA_PASS":raise RuntimeError(result["result"])
if __name__=="__main__":main()
