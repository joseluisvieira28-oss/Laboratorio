#!/usr/bin/env python3
import csv, gzip, io, json, sys, urllib.request
from pathlib import Path

CANDIDATES=[
 "https://public.bybit.com/trading/BTCUSDT/BTCUSDT2023-01-18.csv.gz",
 "https://public.bybit.com/trading/BTCUSDT/BTCUSDT2023-01-18.csv",
]
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-Maker-Source-Gate/0.1"}

def fetch(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.status,dict(r.headers),r.read()

def inspect_bytes(url,body):
    raw=body
    if url.endswith(".gz"):
        raw=gzip.decompress(body)
    text=raw.decode("utf-8","replace")
    lines=text.splitlines()
    out={"url":url,"compressed_bytes":len(body),"decoded_bytes":len(raw),"lines_seen":min(len(lines),2000)}
    if not lines:
        raise RuntimeError("empty_file")
    reader=csv.DictReader(io.StringIO("\\n".join(lines[:2000])))
    rows=list(reader)
    out["columns"]=reader.fieldnames
    out["sample_rows"]=rows[:3]
    out["row_count_sample"]=len(rows)
    return out

def main():
    receipt={"purpose":"HISTORICAL PUBLIC TRADE SOURCE GATE ONLY — NO STRATEGY OUTCOMES","attempts":[]}
    success=None
    for u in CANDIDATES:
        try:
            status,headers,body=fetch(u)
            info=inspect_bytes(u,body)
            info["http_status"]=status
            info["content_type"]=headers.get("Content-Type")
            receipt["attempts"].append({"url":u,"ok":True})
            success=info
            break
        except Exception as e:
            receipt["attempts"].append({"url":u,"ok":False,"error":repr(e)})
    receipt["source"]=success
    if success:
        cols={c.lower() for c in (success.get("columns") or [])}
        # Bybit historical schemas have changed over time; preserve raw columns.
        required_any=[
          {"timestamp","symbol","side","size","price"},
          {"timestamp","side","size","price"},
        ]
        receipt["schema_has_core_trade_fields"]=any(req.issubset(cols) for req in required_any)
        receipt["gate"]="PASS_SAMPLE" if receipt["schema_has_core_trade_fields"] else "SCHEMA_REVIEW_REQUIRED"
    else:
        receipt["gate"]="BLOCKED"
    out=Path("research/microstructure_scalping/receipts")
    out.mkdir(parents=True,exist_ok=True)
    (out/"bybit_trade_source_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if receipt["gate"] in {"PASS_SAMPLE","SCHEMA_REVIEW_REQUIRED"} else 2

if __name__=="__main__":
    sys.exit(main())
