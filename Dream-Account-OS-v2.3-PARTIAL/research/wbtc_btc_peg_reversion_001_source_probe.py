#!/usr/bin/env python3
import json, requests
from pathlib import Path

BASE="https://data.binance.vision/data/spot/monthly/klines/WBTCBTC/1h"
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/wbtc_btc_peg_reversion_001_source_receipt.json")
controls=["2022-01","2022-06","2022-12","2023-01","2023-06","2023-12","2024-01","2024-06","2024-12"]
rows=[]
for ym in controls:
    url=f"{BASE}/WBTCBTC-1h-{ym}.zip"
    r=requests.head(url,headers={"User-Agent":"CryptoLab-WBTC-MR-001/1.0"},timeout=30,allow_redirects=True)
    rows.append({"month":ym,"url":url,"status":r.status_code,"content_length":r.headers.get("Content-Length"),"etag":r.headers.get("ETag")})
passed=all(x["status"]==200 for x in rows)
receipt={
 "lab_id":"WBTC-BTC-PEG-REVERSION-001",
 "classification":"WBTCBTC_1H_SOURCE_COVERAGE_PASS" if passed else "SOURCE_COVERAGE_INSUFFICIENT",
 "controls":rows,
 "price_rows_parsed":False,
 "price_values_opened":False,
 "returns_opened":False,
 "pnl_opened":False,
 "protected_2024_outcomes_opened":False,
 "protected_2025_2026_opened":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
raise SystemExit(0 if passed else 2)
