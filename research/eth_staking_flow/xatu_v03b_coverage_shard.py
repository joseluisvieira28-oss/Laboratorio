#!/usr/bin/env python3
from __future__ import annotations
import json,os,sys,time
from datetime import date,timedelta
from pathlib import Path
import requests

LAB_ID="ETH-STAKING-FLOW-001"
MVE_ID="ESF-NETQUEUE-XATU-7D-003"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
GLOBAL_START=date(2023,4,12); GLOBAL_END=date(2024,12,31)
TRANSIENT={429,500,502,503,504,529}

def url_for(d):
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def probe(url):
    last=None
    for attempt in range(5):
        try:
            with requests.get(url,headers={"Range":"bytes=0-3","User-Agent":f"{LAB_ID}/{MVE_ID}/coverage-v0.3b"},stream=True,timeout=(15,45),allow_redirects=True) as r:
                row={"http_status":r.status_code}
                for h in ["Content-Length","Content-Range","ETag","Last-Modified","Accept-Ranges","Content-Type"]:
                    if r.headers.get(h) is not None: row[h.lower().replace("-","_")]=r.headers.get(h)
                if r.status_code in TRANSIENT and attempt<4:
                    last=RuntimeError(f"transient HTTP {r.status_code}"); time.sleep(1.5*(attempt+1)); continue
                prefix=b""
                if r.status_code in (200,206):
                    try: prefix=next(r.iter_content(chunk_size=4))[:4]
                    except StopIteration: prefix=b""
                row["prefix_hex"]=prefix.hex(); row["prefix_ascii"]=prefix.decode("ascii","replace")
                return row
        except Exception as exc:
            last=exc
            if attempt<4: time.sleep(1.5*(attempt+1)); continue
    return {"transport_error":f"{type(last).__name__}: {str(last)[:500]}" if last else "unknown transport error"}

def main():
    sid=os.environ["SHARD_ID"]; start=date.fromisoformat(os.environ["SHARD_START"]); end=date.fromisoformat(os.environ["SHARD_END"])
    if not (GLOBAL_START<=start<=end<=GLOBAL_END): raise SystemExit("invalid shard range")
    out=Path("xatu_v03b_coverage_shards");out.mkdir(parents=True,exist_ok=True)
    dst=out/f"coverage_{sid}.json"
    rows=[];d=start
    while d<=end:
        url=url_for(d); r={"date":d.isoformat(),"url":url}; r.update(probe(url)); rows.append(r); d+=timedelta(days=1)
    if any(x.get("transport_error") for x in rows):
        cls="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; fail="one or more unresolved transport errors"
    elif any(x.get("http_status") not in (200,206) for x in rows):
        cls="DATA_FAILURE"; fail="one or more exact hour-0 objects unavailable"
    elif any(x.get("prefix_ascii")!="PAR1" for x in rows):
        cls="PROVENANCE_FAILURE"; fail="one or more objects lacks PAR1 signature"
    else:
        cls="SHARD_PASS"; fail=None
    receipt={"lab_id":LAB_ID,"mve_id":MVE_ID,"phase":"XATU_FULL_COVERAGE_SHARD_V0_3B",
             "classification":cls,"failure":fail,"shard_id":sid,"start":start.isoformat(),"end":end.isoformat(),
             "expected_dates":(end-start).days+1,"probes":rows,
             "status_values_opened":False,"queue_counts_computed":False,"market_prices_opened":False,
             "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"shard":sid,"classification":cls,"dates":len(rows),"pass_objects":sum(1 for x in rows if x.get("http_status") in (200,206) and x.get("prefix_ascii")=="PAR1"),"queue_counts":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if cls=="SHARD_PASS" else 2
if __name__=="__main__":sys.exit(main())
