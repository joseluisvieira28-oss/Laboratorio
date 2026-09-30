from __future__ import annotations

from datetime import datetime, timezone
import json
from math import isfinite
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE="https://www.deribit.com"
PATH="/api/v2/public/get_last_trades_by_currency_and_time"
COUNT=1000

def get_json(query):
    url=f"{BASE}{PATH}?{urlencode(query)}"
    req=Request(url,method="GET",headers={"User-Agent":"crypto-lab-options-v21-schema-probe/0.1"})
    with urlopen(req,timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def inspect_day(day_start_ms:int, day_end_ms:int):
    cursor=day_start_ms
    invalid=[]
    total=0
    pages=0
    while cursor<=day_end_ms:
        payload=get_json({
            "currency":"BTC",
            "kind":"option",
            "start_timestamp":cursor,
            "end_timestamp":day_end_ms,
            "count":COUNT,
            "sorting":"asc",
        })
        result=payload.get("result") or {}
        rows=result.get("trades") or []
        pages+=1
        if not rows:
            break
        for row in rows:
            total+=1
            raw_iv=row.get("iv")
            raw_index=row.get("index_price")
            ok=True
            try:
                iv=float(raw_iv)
                idx=float(raw_index)
                ok=isfinite(iv) and iv>0 and isfinite(idx) and idx>0
            except Exception:
                ok=False
            if not ok and len(invalid)<25:
                invalid.append({
                    "timestamp":row.get("timestamp"),
                    "trade_id":row.get("trade_id"),
                    "instrument_name":row.get("instrument_name"),
                    "iv":raw_iv,
                    "index_price":raw_index,
                    "block_trade_id":row.get("block_trade_id"),
                    "combo_trade_id":row.get("combo_trade_id"),
                    "combo_id":row.get("combo_id"),
                    "trade_seq":row.get("trade_seq"),
                })
        last=max(int(r.get("timestamp",0)) for r in rows)
        if last<cursor:
            raise RuntimeError("pagination did not advance")
        if len(rows)<COUNT and not result.get("has_more",False):
            break
        cursor=last+1
    return {"total_rows":total,"pages":pages,"invalid_sample_count":len(invalid),"invalid_samples":invalid}

def main():
    now=datetime.now(timezone.utc)
    start=datetime(now.year,now.month,now.day,tzinfo=timezone.utc)
    start_ms=int(start.timestamp()*1000)
    end_ms=int(now.timestamp()*1000)
    report={
        "probe_id":"OPTIONS_V21_DERIBIT_INVALID_ROW_PROBE_V0.1",
        "probed_at_utc":now.isoformat().replace("+00:00","Z"),
        "window_start_utc":start.isoformat().replace("+00:00","Z"),
        "window_end_utc":now.isoformat().replace("+00:00","Z"),
        "provider":"DERIBIT_PUBLIC_HTTP",
        "endpoint":PATH,
        "result":inspect_day(start_ms,end_ms),
        "authenticated_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
    }
    Path("options-v21-deribit-probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
