from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from typing import Any

BASE = "https://www.deribit.com/api/v2/public/get_last_trades_by_currency_and_time"
ASSETS = ("ETH", "SOL", "XRP")
COUNT = 1000

class ProbeError(RuntimeError):
    pass

def get(asset: str, start_ms: int, end_ms: int) -> dict[str, Any]:
    q = urllib.parse.urlencode({
        "currency": asset,
        "kind": "option",
        "start_timestamp": start_ms,
        "end_timestamp": end_ms,
        "count": COUNT,
        "sorting": "asc",
    })
    req = urllib.request.Request(BASE + "?" + q, headers={"User-Agent":"crypto-edge-radar/multiasset-source-probe-v01"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise ProbeError("HTTP_%s" % r.status)
        return json.loads(r.read().decode("utf-8"))

def parse_name(asset: str, name: str) -> dict[str, Any]:
    parts = name.split("-")
    # Inverse family: ETH-DDMMMYY-STRIKE-C/P
    if len(parts) == 4 and parts[0] == asset and parts[3] in ("C","P"):
        return {"convention":"INVERSE_STYLE","expiry":parts[1],"strike":float(parts[2]),"side":parts[3]}
    # Linear family documented as ASSET_USDC-DDMMMYY-STRIKE-C/P.
    if len(parts) == 4 and parts[0] == asset + "_USDC" and parts[3] in ("C","P"):
        return {"convention":"LINEAR_USDC","expiry":parts[1],"strike":float(parts[2]),"side":parts[3]}
    raise ProbeError("UNSUPPORTED_INSTRUMENT_NAME:" + name)

def probe(asset: str, start_ms: int, end_ms: int) -> dict[str, Any]:
    payload = get(asset,start_ms,end_ms)
    result = payload.get("result")
    if not isinstance(result,dict) or not isinstance(result.get("trades"),list):
        raise ProbeError("INVALID_DERIBIT_PAYLOAD")
    rows=result["trades"]
    valid=0
    invalid_signal=0
    conventions=Counter()
    sides=Counter()
    instruments=set()
    ids=set()
    duplicate_ids=0
    samples=[]
    for row in rows:
        for k in ("timestamp","instrument_name","trade_id"):
            if k not in row:
                raise ProbeError("MISSING_REQUIRED_FIELD:"+k)
        ts=int(row["timestamp"])
        if not start_ms <= ts <= end_ms:
            raise ProbeError("TIMESTAMP_OUTSIDE_WINDOW")
        tid=str(row["trade_id"])
        if tid in ids:
            duplicate_ids += 1
        ids.add(tid)
        parsed=parse_name(asset,str(row["instrument_name"]))
        conventions[parsed["convention"]]+=1
        sides[parsed["side"]]+=1
        instruments.add(str(row["instrument_name"]))
        try:
            iv=float(row["iv"])
            index=float(row["index_price"])
            if not (math.isfinite(iv) and iv>0 and math.isfinite(index) and index>0):
                raise ValueError
            valid += 1
        except Exception:
            invalid_signal += 1
        if len(samples)<5:
            samples.append({
                "instrument_name":row["instrument_name"],
                "timestamp":ts,
                "has_iv":"iv" in row,
                "has_index_price":"index_price" in row,
                "convention":parsed["convention"],
            })
    return {
        "asset":asset,
        "status":"SOURCE_SCHEMA_PASS" if rows and valid else ("SOURCE_EMPTY_WINDOW" if not rows else "SOURCE_SCHEMA_BLOCKED"),
        "requested_start_ms":start_ms,
        "requested_end_ms":end_ms,
        "rows":len(rows),
        "has_more":bool(result.get("has_more",False)),
        "valid_signal_rows":valid,
        "invalid_iv_index_rows":invalid_signal,
        "distinct_trade_ids":len(ids),
        "duplicate_trade_ids_in_page":duplicate_ids,
        "distinct_instruments":len(instruments),
        "sides":dict(sides),
        "instrument_conventions":dict(conventions),
        "samples":samples,
        "outcomes_accessed":False,
        "orders_created":False,
        "authenticated_api_used":False,
    }

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--start",required=True,help="UTC ISO, e.g. 2026-10-01T00:00:00Z")
    p.add_argument("--end",required=True)
    p.add_argument("--output",default="options_multiasset_source_probe_receipt_v01.json")
    a=p.parse_args()
    start=int(datetime.fromisoformat(a.start.replace("Z","+00:00")).timestamp()*1000)
    end=int(datetime.fromisoformat(a.end.replace("Z","+00:00")).timestamp()*1000)
    if end < start: raise ProbeError("INVALID_WINDOW")
    receipt={
      "probe_id":"OPTIONS_MULTI_ASSET_SOURCE_PROBE_V0.1",
      "created_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "assets":[probe(x,start,end) for x in ASSETS],
      "scope":"SOURCE_SCHEMA_ONLY_NO_OUTCOMES",
    }
    with open(a.output,"w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if all(x["status"]=="SOURCE_SCHEMA_PASS" for x in receipt["assets"]) else 3

if __name__=="__main__":
    raise SystemExit(main())
