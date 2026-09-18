#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime
from pathlib import Path
import requests

LAB_ID="ETH-STAKING-FLOW-001"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
DATES=["2023-04-12","2023-09-01","2024-06-15","2024-12-31"]

def url_for(ds):
    d=datetime.strptime(ds,"%Y-%m-%d")
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def main():
    out=Path("xatu_http_transport_v02b_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_HTTP_TRANSPORT_V0_2B.json"
    probes=[]; classification=None; failure=None
    try:
        for ds in DATES:
            if ds[:4] in {"2025","2026"}: raise RuntimeError("protected-period date")
            url=url_for(ds)
            row={"date":ds,"url":url}
            try:
                with requests.get(url,headers={"Range":"bytes=0-3","User-Agent":f"{LAB_ID}/xatu-http-v0.2b"},stream=True,timeout=(15,45),allow_redirects=True) as r:
                    row["http_status"]=r.status_code
                    for h in ["Content-Length","Content-Range","ETag","Last-Modified","Accept-Ranges","Content-Type"]:
                        if r.headers.get(h) is not None: row[h.lower().replace("-","_")]=r.headers.get(h)
                    prefix=b""
                    if r.status_code in (200,206):
                        try:
                            prefix=next(r.iter_content(chunk_size=4))[:4]
                        except StopIteration:
                            prefix=b""
                    row["prefix_hex"]=prefix.hex()
                    row["prefix_ascii"]=prefix.decode("ascii","replace")
            except Exception as exc:
                row["transport_error"]=f"{type(exc).__name__}: {str(exc)[:500]}"
            probes.append(row)
        if any(x.get("transport_error") for x in probes):
            classification="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"; failure="one or more HTTP transport errors"
        elif any(x.get("http_status") not in (200,206) for x in probes):
            classification="XATU_SOURCE_PATH_NOT_FOUND"; failure="one or more exact hourly paths unavailable"
        elif any(x.get("prefix_hex") and x.get("prefix_ascii")!="PAR1" for x in probes):
            classification="XATU_HTTP_PROVENANCE_FAILURE"; failure="unexpected non-Parquet prefix"
        else:
            classification="XATU_HTTP_TRANSPORT_PASS"
    except Exception as exc:
        classification="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"; failure=f"{type(exc).__name__}: {str(exc)[:1000]}"
    receipt={"lab_id":LAB_ID,"phase":"XATU_HTTP_TRANSPORT_V0_2B_OUTCOME_BLIND",
             "classification":classification,"failure":failure,"probes":probes,
             "validator_values_opened":False,"queue_counts_computed":False,
             "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
             "accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"probes":[{"date":x["date"],"http":x.get("http_status"),"prefix":x.get("prefix_ascii")} for x in probes],"prices":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if classification=="XATU_HTTP_TRANSPORT_PASS" else 2
if __name__=="__main__": sys.exit(main())
