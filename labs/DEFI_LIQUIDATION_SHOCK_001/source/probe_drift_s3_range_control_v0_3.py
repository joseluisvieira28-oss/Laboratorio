#!/usr/bin/env python3
import json, urllib.request, urllib.error
from pathlib import Path

ROOT="https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/market"
MARKETS=["BTC-PERP","SOL-PERP"]
DATES=["2023-08-15","2023-09-15","2024-01-15","2024-04-01"]

rows=[]
for market in MARKETS:
    for date in DATES:
        year=date[:4]
        key=date.replace("-","")
        url=f"{ROOT}/{market}/fundingRateRecords/{year}/{key}"
        rec={"market":market,"date":date,"path_suffix":f"{market}/fundingRateRecords/{year}/{key}"}
        try:
            req=urllib.request.Request(url,headers={
                "Range":"bytes=0-0",
                "User-Agent":"crypto-lab-dls-source-transport/0.3"
            })
            with urllib.request.urlopen(req,timeout=30) as resp:
                body=resp.read()
                rec["http_status"]=resp.status
                rec["returned_body_bytes"]=len(body)
                rec["body_interpreted"]=False
                for h in ["Content-Range","Content-Length","Content-Type","ETag","Last-Modified"]:
                    if resp.headers.get(h) is not None:
                        rec[h.lower().replace("-","_")]=resp.headers.get(h)
        except urllib.error.HTTPError as e:
            rec["http_status"]=e.code
            rec["returned_body_bytes"]=0
            rec["body_interpreted"]=False
        except Exception as e:
            rec["http_status"]=None
            rec["returned_body_bytes"]=0
            rec["body_interpreted"]=False
            rec["transport_error"]=type(e).__name__
        rows.append(rec)

ok=[r for r in rows if r.get("http_status") in (200,206)]
forbidden=[r for r in rows if r.get("http_status")==403]
transport=[r for r in rows if r.get("http_status") is None]

if ok:
    classification="DRIFT_S3_RANGE_CONTROL_PASS"
elif forbidden:
    classification="DRIFT_S3_RANGE_CONTROL_ACCESS_BLOCKED"
elif all(r.get("http_status")==404 for r in rows):
    classification="DRIFT_S3_RANGE_CONTROL_PATH_OR_AVAILABILITY_BLOCKED"
else:
    classification="DRIFT_S3_RANGE_CONTROL_FAIL_CLOSED"

receipt={
  "schema_version":"0.3",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":classification,
  "requests":len(rows),
  "control_hits":len(ok),
  "rows":rows,
  "firewall":{
    "body_bytes_interpreted":0,"funding_values":False,"liquidation_rows":False,
    "prices":False,"returns":False,"pnl":False,"direction":False,
    "protected_market_outcomes_2025_2026":False,"credentials":False,
    "account_creation":False,"paid_source":False,"live_trading":False,
    "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False
  }
}
Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_S3_RANGE_CONTROL_PROBE_RECEIPT_V0.3.json").write_text(
  json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
