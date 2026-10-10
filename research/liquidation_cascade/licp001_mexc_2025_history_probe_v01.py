#!/usr/bin/env python3
import json,urllib.parse,urllib.request
from pathlib import Path

BASE="https://api.mexc.com/api/v1/contract/kline"
SYMS=("BTC_USDT","ETH_USDT","SOL_USDT")
WINDOWS={
 "2025-08-10":(1754784000,1754791200),
 "2025-10-10":(1760119200,1760126400),
 "2025-12-31":(1767218400,1767225540),
 "CONTROL_2026-09-01":(1788220800,1788228000),
 "CONTROL_2026-09-25":(1790294400,1790301600),
}

def fetch(sym,start,end):
    qs=urllib.parse.urlencode({"interval":"Min1","start":start,"end":end})
    url=f"{BASE}/{sym}?{qs}"
    req=urllib.request.Request(url,headers={"User-Agent":"Crypto-Lab-LICP-Hist/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        j=json.loads(r.read().decode())
    if not j.get("success"):raise RuntimeError(f"api_fail:{j.get('code')}")
    times=(j.get("data") or {}).get("time") or []
    return {"url":url,"count":len(times),"first_time":min(times) if times else None,"last_time":max(times) if times else None}

def main():
    out={"purpose":"MEXC HISTORICAL TIMESTAMP COVERAGE + RECENT CONTROL ONLY","windows":{}}
    all_nonempty=True
    for label,(start,end) in WINDOWS.items():
        out["windows"][label]={}
        for sym in SYMS:
            try:
                r=fetch(sym,start,end)
                out["windows"][label][sym]=r
                if r["count"]==0:all_nonempty=False
            except Exception as e:
                out["windows"][label][sym]={"error":repr(e)}
                all_nonempty=False
    historical_labels=[x for x in WINDOWS if x.startswith("2025-")]
    control_labels=[x for x in WINDOWS if x.startswith("CONTROL_")]
    hist_ok=all(out["windows"][d][s].get("count",0)>0 for d in historical_labels for s in SYMS)
    control_ok=all(out["windows"][d][s].get("count",0)>0 for d in control_labels for s in SYMS)
    out["historical_2025_gate"]="PASS_SAMPLE" if hist_ok else "BLOCKED"
    out["recent_control_gate"]="PASS_SAMPLE" if control_ok else "BLOCKED"
    out["gate"]="PASS_SAMPLE" if hist_ok else ("HISTORICAL_BLOCKED_RECENT_WORKS" if control_ok else "BLOCKED")
    p=Path("research/liquidation_cascade/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"licp001_mexc_2025_history_source_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))
    # Exit success when recent controls prove endpoint health even if 2025 is unavailable.
    raise SystemExit(0 if out["gate"] in {"PASS_SAMPLE","HISTORICAL_BLOCKED_RECENT_WORKS"} else 2)

if __name__=="__main__":main()
