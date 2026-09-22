#!/usr/bin/env python3
import json, urllib.request, urllib.error
from pathlib import Path

ROOT="https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/market"
SYMBOLS=["BTC-PERP","SOL-PERP"]
DATES=["2023-08-15","2024-01-15"]
FAMILIES=["fundingRateRecords","liquidationRecords","tradeRecords"]
SUFFIXES=["",".csv"]

rows=[]
for symbol in SYMBOLS:
    for date in DATES:
        year=date[:4]
        for family in FAMILIES:
            for suffix in SUFFIXES:
                url=f"{ROOT}/{symbol}/{family}/{year}/{date}{suffix}"
                rec={"symbol":symbol,"date":date,"family":family,"suffix":suffix}
                try:
                    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"crypto-lab-dls-source-metadata/0.1"})
                    with urllib.request.urlopen(req,timeout=30) as resp:
                        rec["http_status"]=resp.status
                        rec["exists"]=resp.status==200
                        for h in ["Content-Length","Content-Type","ETag","Last-Modified"]:
                            if resp.headers.get(h) is not None:
                                rec[h.lower().replace("-","_")]=resp.headers.get(h)
                except urllib.error.HTTPError as e:
                    rec["http_status"]=e.code
                    rec["exists"]=False
                except Exception as e:
                    rec["http_status"]=None
                    rec["exists"]=False
                    rec["transport_error"]=type(e).__name__
                rows.append(rec)

controls=[r for r in rows if r["family"]=="fundingRateRecords" and r.get("exists")]
liq=[r for r in rows if r["family"]=="liquidationRecords" and r.get("exists")]
trade=[r for r in rows if r["family"]=="tradeRecords" and r.get("exists")]
transport=[r for r in rows if r.get("http_status") is None]

if not controls:
    classification="DRIFT_S3_HEAD_CALIBRATION_CONTROL_BLOCKED"
elif liq:
    classification="DRIFT_S3_HEAD_LIQUIDATION_ROUTE_PASS"
elif trade:
    classification="DRIFT_S3_HEAD_TRADE_ROUTE_ONLY"
else:
    classification="DRIFT_S3_HEAD_NO_CANDIDATE_ROUTE"

receipt={
  "schema_version":"0.1",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":classification,
  "head_requests":len(rows),
  "control_hits":len(controls),
  "liquidation_record_hits":len(liq),
  "trade_record_hits":len(trade),
  "transport_error_count":len(transport),
  "rows":rows,
  "firewall":{
    "http_head_only":True,"get_requests":False,"object_bodies":False,"event_rows":False,
    "prices":False,"funding_values":False,"returns":False,"pnl":False,"direction":False,
    "protected_market_outcomes_2025_2026":False,"credentials":False,"account_creation":False,
    "paid_source":False,"live_trading":False,"orders":False,"wallets":False,
    "exchange_mutation":False,"merge_main":False
  }
}
Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_HISTORICAL_S3_HEAD_CALIBRATION_RECEIPT_V0.1.json").write_text(
  json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
