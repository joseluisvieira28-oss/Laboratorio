"""Source-only archival feasibility for canonical Binance SPOT BTCUSDT aggTrades.

Never downloads market/trade rows; HEAD zip + checksum provenance only.
Preserves original source/side semantics; does not authorize a collector.
"""
from __future__ import annotations
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent
OUT=HERE/"BINANCE_SPOT_AGGTRADES_ARCHIVE_SOURCE_PROBE_2026-10-09.json"
PREFIX="https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"
DAYS=[date(2026,10,2)+timedelta(days=k) for k in range(7)]
MAX_ARCHIVE_BYTES=2_000_000_000 # operational transport cap only, NOT science parameter

def get(url,method="GET"):
    req=Request(url,headers={"User-Agent":"CryptoLab-Absorption-SourceOnly/0.1"},method=method)
    with urlopen(req,timeout=30) as resp:
        if resp.status!=200:
            raise RuntimeError(f"unexpected HTTP {resp.status} {url.split('/')[-1]}")
        return resp.headers,(b"" if method=="HEAD" else resp.read())

def probe():
    files=[]
    for d in DAYS:
        name="BTCUSDT-aggTrades-"+d.isoformat()+".zip"
        url=PREFIX+name
        meta,_=get(url,method="HEAD")
        n=int(meta.get("Content-Length","0"))
        if n<=0 or n>MAX_ARCHIVE_BYTES:
            raise RuntimeError("invalid archive size "+name+" bytes="+str(n))
        _,body=get(url+".CHECKSUM")
        token=body.decode("utf-8","strict").strip().split()
        if not token or not re.fullmatch("[0-9A-Fa-f]{64}",token[0]):
            raise RuntimeError("invalid official checksum "+name)
        if len(token)>1 and token[1].strip("*").split("/")[-1]!=name:
            raise RuntimeError("checksum mismatched target "+name)
        files.append({"utc_date":d.isoformat(),"filename":name,"compressed_bytes":n,"checksum_sha256":token[0].lower(),"data_source":"BINANCE_VISION_SPOT_DAILY_AGGTRADES"})
        print("SOURCE_METADATA_OK",d.isoformat(),n,flush=True)
    return {"state":"ARCHIVE_METADATA_SOURCE_POSSIBLE","lab_id":"ABSORPTION-FAILED-AUCTION-001",
        "instrument":"BINANCE BTCUSDT SPOT AGGTRADES",
        "dates":[x["utc_date"] for x in files],"archives":files,
        "total_compressed_bytes":sum(x["compressed_bytes"] for x in files),
        "zip_data_downloaded":False,"trade_rows_accessed":False,
        "archive_sha256_verified_against_download":False,
        "2026_10_09_current_day_archive_required":False,
        "source_only":True,"economic_outcomes_unlocked":False,"trading_authority":"NONE",
        "caveat":"HEAD+CHECKSUM availability is not a file-integrity gate: each future real ZIP must be downloaded and checked SHA256, parsed, deduped and joined to immutable 5m MM-V1 receipts. Requires source-specific feasibility/limits before new event classifier run."}

if __name__=="__main__":
    try:
        value=probe()
        code=0
    except Exception as exc:
        value={"state":"ARCHIVE_SOURCE_METADATA_BLOCKED","error":str(exc),
            "source_only":True,"economic_outcomes_unlocked":False,"trading_authority":"NONE"}
        code=2
    OUT.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in value.items() if k!="archives"},sort_keys=True,indent=2))
    raise SystemExit(code)
