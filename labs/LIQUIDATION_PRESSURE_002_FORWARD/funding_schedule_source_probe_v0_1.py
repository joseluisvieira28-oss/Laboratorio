from __future__ import annotations

import json
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)
SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","BNBUSDT"]
BASE="https://api.bybit.com"

def get(path,params):
    url=BASE+path+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-LIQ-PRESSURE-002/0.1"})
    with urllib.request.urlopen(req,timeout=20) as r:
        body=json.loads(r.read().decode())
    if body.get("retCode")!=0:
        raise RuntimeError(str(body))
    return body

rows=[]
errors=[]
for sym in SYMBOLS:
    try:
        inst=get("/v5/market/instruments-info",{"category":"linear","symbol":sym})
        tick=get("/v5/market/tickers",{"category":"linear","symbol":sym})
        il=(inst.get("result") or {}).get("list") or []
        tl=(tick.get("result") or {}).get("list") or []
        if len(il)!=1 or len(tl)!=1:
            raise RuntimeError(f"unexpected rows instruments={len(il)} ticker={len(tl)}")
        i=il[0]; t=tl[0]
        rows.append({
            "symbol":sym,
            "contract_type":i.get("contractType"),
            "status":i.get("status"),
            "funding_interval_minutes":int(i["fundingInterval"]) if i.get("fundingInterval") else None,
            "next_funding_time_ms":int(t["nextFundingTime"]) if t.get("nextFundingTime") else None,
            "funding_rate":t.get("fundingRate"),
            "instrument_response_time_ms":inst.get("time"),
            "ticker_response_time_ms":tick.get("time"),
        })
    except Exception as e:
        errors.append({"symbol":sym,"error":type(e).__name__+":"+str(e)[:300]})

valid=[
    r for r in rows
    if r["status"]=="Trading"
    and r["contract_type"]=="LinearPerpetual"
    and isinstance(r["funding_interval_minutes"],int)
    and r["funding_interval_minutes"]>0
    and isinstance(r["next_funding_time_ms"],int)
]
receipt={
    "lab_id":"LIQUIDATION-PRESSURE-002-FORWARD",
    "phase":"FUNDING_SCHEDULE_SOURCE_PROBE_V0.1",
    "verdict":"FUNDING_SCHEDULE_SOURCE_PASS" if len(valid)==len(SYMBOLS) and not errors else "FUNDING_SCHEDULE_SOURCE_FAIL_CLOSED",
    "symbols_requested":SYMBOLS,
    "rows":rows,
    "error_count":len(errors),
    "errors":errors,
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "note":"Public market metadata only. Used prospectively to exclude any 30s holding interval that overlaps a funding timestamp."
}
(OUT/"funding_schedule_source_probe_v0_1.json").write_text(
    json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8"
)
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["verdict"]!="FUNDING_SCHEDULE_SOURCE_PASS":
    raise SystemExit(2)
