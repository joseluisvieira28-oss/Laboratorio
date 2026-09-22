#!/usr/bin/env python3
import json, urllib.request, urllib.error, urllib.parse
from pathlib import Path

ROOT="https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
URLS=[
  ("documented_market_trade_control",f"{ROOT}/market/SOL-PERP/tradeRecords/2024/20240101"),
  ("documented_funding_control_sol",f"{ROOT}/market/SOL-PERP/fundingRateRecords/2024/20240101"),
  ("academic_funding_control_btc",f"{ROOT}/market/BTC-PERP/fundingRateRecords/2023/20230801"),
]
ALLOWED_HOST="drift-historical-data-v2.s3.eu-west-1.amazonaws.com"
rows=[]
body_bytes_read=0

for label,url in URLS:
    rec={"label":label,"url":url}
    try:
        req=urllib.request.Request(url,method="GET",headers={
          "User-Agent":"crypto-lab-dls-source-transport/0.3",
          "Accept":"text/csv,*/*;q=0.1"
        })
        with urllib.request.urlopen(req,timeout=45) as resp:
            final=resp.geturl()
            parsed=urllib.parse.urlparse(final)
            if parsed.hostname!=ALLOWED_HOST:
                raise RuntimeError(f"UNEXPECTED_REDIRECT_HOST:{parsed.hostname}")
            # Critical contract: do not call read() at all.
            rec["http_status"]=int(resp.status)
            rec["exists"]=resp.status in (200,206)
            rec["final_url"]=final
            for h in ["Content-Length","Content-Type","ETag","Last-Modified","Accept-Ranges","Content-Encoding"]:
                if resp.headers.get(h) is not None:
                    rec[h.lower().replace("-","_")]=resp.headers.get(h)
    except urllib.error.HTTPError as e:
        rec["http_status"]=int(e.code)
        rec["exists"]=False
    except Exception as e:
        rec["http_status"]=None
        rec["exists"]=False
        rec["transport_error"]=type(e).__name__
        rec["transport_detail"]=str(e)[:300]
    rows.append(rec)

hits=[r for r in rows if r.get("exists")]
transport=[r for r in rows if r.get("http_status") is None]

if body_bytes_read!=0:
    classification="DRIFT_S3_GET_STATUS_SOURCE_ANOMALY_FAIL_CLOSED"
elif hits:
    classification="DRIFT_S3_GET_STATUS_CONTROL_PASS"
elif transport:
    classification="DRIFT_S3_GET_STATUS_CONTROL_BLOCKED"
else:
    classification="DRIFT_S3_GET_STATUS_CONTROL_NOT_FOUND"

receipt={
  "schema_version":"0.3",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "classification":classification,
  "technical_supersession_of":["DRIFT_HISTORICAL_S3_HEAD_CALIBRATION_V0.1","DRIFT_HISTORICAL_S3_HEAD_CALIBRATION_V0.2"],
  "source_correction":"liquidationRecords are user-scoped, not market-scoped",
  "request_method":"GET",
  "response_body_bytes_read":body_bytes_read,
  "control_hits":len(hits),
  "transport_error_count":len(transport),
  "rows":rows,
  "firewall":{
    "body_parsing":False,"event_rows":False,"prices":False,"funding_values":False,
    "returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
    "protected_market_outcomes_2025_2026":False,"credentials":False,
    "account_creation":False,"paid_source":False,"live_trading":False,
    "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False
  }
}
Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_HISTORICAL_S3_GET_STATUS_CONTROL_RECEIPT_V0.3.json").write_text(
    json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
