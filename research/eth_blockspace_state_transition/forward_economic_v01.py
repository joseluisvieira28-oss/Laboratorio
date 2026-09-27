#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, urllib.parse, urllib.request, hashlib, statistics, sys
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

LAB="ETH-BLOCKSPACE-STATE-TRANSITION-001"
CANDIDATE="EBST-L1BLOB-PERSIST-ETHBTC-H72-001"
BOUNDARY=datetime(2026,9,28,tzinfo=timezone.utc)
MARKET="https://data-api.binance.vision"
SYMBOL="ETHBTC"
BASE_COST=20.0
STRESS_COST=30.0
STATE=Path("forward_state/ebst_economic")
LEDGER=STATE/"EBST_FORWARD_EVENT_LEDGER_V0_1.json"
RECEIPT=STATE/"EBST_FORWARD_ECONOMIC_STATE_V0_1.json"

def dt(s): return datetime.fromisoformat(s+"T00:00:00+00:00")
def pf(vals):
    pos=sum(x for x in vals if x>0); neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else None

def fetch_daily_open(day):
    start=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    end=start+24*3600*1000
    q=urllib.parse.urlencode({"symbol":SYMBOL,"interval":"1d","startTime":start,"endTime":end,"limit":2})
    req=urllib.request.Request(MARKET+"/api/v3/klines?"+q,headers={"User-Agent":"EBST-forward-economic-v0.1"})
    with urllib.request.urlopen(req,timeout=30) as r: o=json.loads(r.read().decode())
    if not isinstance(o,list) or not o: raise RuntimeError(f"missing market day {day.isoformat()}")
    x=o[0]
    if int(x[0])!=start: raise RuntimeError(f"market alignment {day.isoformat()}")
    return float(x[1])

def load_ledger():
    if not LEDGER.exists(): return []
    return json.loads(LEDGER.read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-receipt",default="EBST_SOURCE_WARMUP_V0_1.json")
    ap.add_argument("--preflight",action="store_true")
    a=ap.parse_args()
    out={"lab_id":LAB,"candidate_id":CANDIDATE,"classification":"FORWARD_ECONOMIC_ERROR",
         "boundary_utc":"2026-09-28T00:00:00Z","mode":"RESEARCH_SHADOW_ONLY",
         "execution_authority":False,"safety":{"preboundary_market_access":False,"live_trading":False,
         "orders":False,"exchange_mutation":False,"wallets":False}}
    try:
        now=datetime.now(timezone.utc)
        if a.preflight:
            if now<BOUNDARY:
                out["classification"]="PRE_BOUNDARY_ARMED"
                out["market_prices_opened"]=False
            else:
                out["classification"]="PREFLIGHT_PASS"
                out["market_prices_opened"]=False
        else:
            src=json.loads(Path(a.source_receipt).read_text(encoding="utf-8"))
            if src.get("classification")!="SOURCE_WARMUP_PASS":
                raise RuntimeError("source warmup not PASS")
            transitions=list(src.get("source_only_transition_dates") or [])
            ledger=load_ledger()
            bydate={x["transition_date"]:x for x in ledger}
            market_access_count=0
            today=now.date()
            for s in transitions:
                td=date.fromisoformat(s)
                entry=td+timedelta(days=1)
                exitd=entry+timedelta(days=3)
                if datetime(entry.year,entry.month,entry.day,tzinfo=timezone.utc)<BOUNDARY:
                    continue
                rec=bydate.get(s) or {"transition_date":s,"entry_date":entry.isoformat(),"exit_date":exitd.isoformat(),
                                     "status":"PENDING","source_receipt_sha256":src.get("receipt_sha256")}
                # Only completed market days may be read. This is conservative shadow accounting.
                if entry<today and "entry_price" not in rec:
                    rec["entry_price"]=fetch_daily_open(entry); market_access_count+=1
                    rec["status"]="OPEN"
                if exitd<today and "entry_price" in rec and "exit_price" not in rec:
                    rec["exit_price"]=fetch_daily_open(exitd); market_access_count+=1
                    gross=(rec["exit_price"]/rec["entry_price"]-1.0)*10000.0
                    rec.update({"gross_bps":gross,"base_net_bps":gross-BASE_COST,
                                "stress_net_bps":gross-STRESS_COST,"status":"RESOLVED"})
                bydate[s]=rec
            ledger=sorted(bydate.values(),key=lambda x:x["transition_date"])
            if any(datetime.fromisoformat(x["entry_date"]+"T00:00:00+00:00")<BOUNDARY for x in ledger):
                out["safety"]["preboundary_market_access"]=True
                raise RuntimeError("BOUNDARY_BREACH")
            STATE.mkdir(parents=True,exist_ok=True)
            LEDGER.write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n",encoding="utf-8")
            resolved=[x for x in ledger if x.get("status")=="RESOLVED"]
            base=[x["base_net_bps"] for x in resolved]; stress=[x["stress_net_bps"] for x in resolved]
            out.update({"classification":"INSUFFICIENT_MATURITY","market_prices_opened":market_access_count>0,
                        "market_access_count":market_access_count,"source_transition_count_current_window":len(transitions),
                        "ledger_events":len(ledger),"resolved_n":len(resolved),"open_or_pending_n":len(ledger)-len(resolved),
                        "metrics":{"base_mean_bps":statistics.mean(base) if base else None,"base_pf":pf(base) if base else None,
                                   "stress_mean_bps":statistics.mean(stress) if stress else None,
                                   "represented_symbol_count":1 if resolved else 0}})
            if len(resolved)>=25:
                out["classification"]="FORMAL_REVIEW_SAMPLE_READY"
            RECEIPT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    except Exception as e:
        out["failure"]=f"{type(e).__name__}:{e}"
    out["receipt_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(json.dumps({"classification":out["classification"],"market_prices_opened":out.get("market_prices_opened",False),
                      "ledger_events":out.get("ledger_events"),"resolved_n":out.get("resolved_n"),
                      "execution_authority":False,"failure":out.get("failure")},sort_keys=True))
    return 0 if out["classification"]!="FORWARD_ECONOMIC_ERROR" else 2

if __name__=="__main__": sys.exit(main())
