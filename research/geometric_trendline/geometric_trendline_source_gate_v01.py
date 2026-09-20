#!/usr/bin/env python3
import json, re, urllib.request, urllib.error
from pathlib import Path

BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
START=(2021,1)
END=(2024,12)
OUT=Path("research/geometric_trendline/GEOMETRIC_TRENDLINE_001_SOURCE_GATE_RECEIPT_V0_1.json")

def months():
    y,m=START
    while (y,m) <= END:
        yield y,m
        m += 1
        if m==13:
            y,m=y+1,1

def get_text(url):
    req=urllib.request.Request(url, headers={"User-Agent":"CryptoLab-SourceGate/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(4096).decode("utf-8","strict"), int(r.status)

def head(url):
    req=urllib.request.Request(url, method="HEAD", headers={"User-Agent":"CryptoLab-SourceGate/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return int(r.status), dict(r.headers)

rows=[]
errors=[]
for y,m in months():
    fn=f"BTCUSDT-1m-{y:04d}-{m:02d}.zip"
    zip_url=f"{BASE}/{fn}"
    checksum_url=zip_url+".CHECKSUM"
    row={"month":f"{y:04d}-{m:02d}","filename":fn,"zip_url":zip_url,"checksum_url":checksum_url}
    try:
        text,status=get_text(checksum_url)
        line=text.strip().splitlines()[0] if text.strip() else ""
        mm=re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
        if not mm or mm.group(2).strip()!=fn:
            raise RuntimeError("invalid checksum binding")
        zstatus,headers=head(zip_url)
        if zstatus < 200 or zstatus >= 400:
            raise RuntimeError(f"zip HEAD status {zstatus}")
        row.update({
            "checksum_status":status,
            "zip_head_status":zstatus,
            "sha256":mm.group(1).lower(),
            "content_length":headers.get("Content-Length"),
            "pass":True,
        })
    except Exception as e:
        row.update({"pass":False,"error":f"{type(e).__name__}: {e}"})
        errors.append({"month":row["month"],"error":row["error"]})
    rows.append(row)

expected=48
passed=sum(1 for r in rows if r["pass"])
receipt={
  "schema_version":"0.1",
  "lab_id":"GEOMETRIC-TRENDLINE-001",
  "gate":"SOURCE_METADATA_CHECKSUM_ONLY",
  "source":"Binance Data Vision official Spot BTCUSDT monthly 1m archives",
  "window":"2021-01 through 2024-12",
  "expected_months":expected,
  "passed_months":passed,
  "classification":"SOURCE_GATE_PASS" if passed==expected else "SOURCE_GATE_BLOCKED_INCOMPLETE",
  "rows":rows,
  "errors":errors,
  "guards":{
    "ohlcv_values_parsed":False,
    "pivots_computed":False,
    "trendlines_computed":False,
    "returns_computed":False,
    "pnl_computed":False,
    "2025_accessed":False,
    "2026_accessed":False,
    "live_trading":False,
    "exchange_mutation":False
  }
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
print(json.dumps({k:receipt[k] for k in ["lab_id","expected_months","passed_months","classification"]}, indent=2))
if receipt["classification"] != "SOURCE_GATE_PASS":
    raise SystemExit(2)
