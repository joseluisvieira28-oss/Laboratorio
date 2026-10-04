#!/usr/bin/env python3
from __future__ import annotations
import json, math, statistics, time
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://api.mexc.com"
SYMBOL="SPX500_USDT"
N=60
SLEEP=1.0
GROSS_EDGE_BPS=0.5177567737
OUT=Path("artifacts/mexc_global_assets/sp500_bbo_offhours_v03")
UA="CryptoLab-SP500-PublicBBO-OffHours/0.3"

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def pct(xs,p):
    if not xs: return None
    ys=sorted(xs)
    if len(ys)==1: return ys[0]
    pos=(len(ys)-1)*p
    lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi: return ys[lo]
    return ys[lo]*(hi-pos)+ys[hi]*(pos-lo)

def main():
    spreads=[]; bid_sizes=[]; ask_sizes=[]; rows=[]; invalid=[]
    for i in range(N):
        captured=utcnow()
        try:
            r=requests.get(
                f"{BASE}/api/v1/contract/depth/{SYMBOL}",
                params={"limit":5},
                headers={"User-Agent":UA},
                timeout=20,
            )
            if r.status_code!=200:
                raise RuntimeError(f"HTTP_{r.status_code}")
            j=r.json()
            if isinstance(j,dict) and j.get("success") is True and isinstance(j.get("data"),dict):
                d=j["data"]
            elif isinstance(j,dict) and "bids" in j and "asks" in j:
                d=j
            else:
                raise RuntimeError(f"UNEXPECTED_PAYLOAD:{str(j)[:160]}")
            bids=d.get("bids") or []
            asks=d.get("asks") or []
            if not bids or not asks:
                raise RuntimeError("EMPTY_BBO")
            bid=float(bids[0][0]); ask=float(asks[0][0])
            bsz=float(bids[0][1]) if len(bids[0])>1 else None
            asz=float(asks[0][1]) if len(asks[0])>1 else None
            if bid<=0 or ask<=0 or ask<bid:
                raise RuntimeError(f"INVALID_BBO:{bid}:{ask}")
            mid=(bid+ask)/2.0
            sbps=10000.0*(ask-bid)/mid
            spreads.append(sbps)
            if bsz is not None: bid_sizes.append(bsz)
            if asz is not None: ask_sizes.append(asz)
            rows.append({
                "i":i,"captured_at_utc":captured,
                "book_timestamp":d.get("timestamp"),
                "best_bid":bid,"best_ask":ask,
                "best_bid_size":bsz,"best_ask_size":asz,
                "spread_bps":sbps,
            })
        except Exception as e:
            invalid.append({"i":i,"captured_at_utc":captured,"error":repr(e)})
        if i < N-1:
            time.sleep(SLEEP)

    valid=len(spreads)
    if valid < 30:
        verdict="OFF_HOURS_BBO_SOURCE_INSUFFICIENT"
    else:
        med=statistics.median(spreads)
        verdict="OFF_HOURS_SPREAD_HOSTILE" if med>=GROSS_EDGE_BPS else "OFF_HOURS_SPREAD_NOT_OBVIOUSLY_FATAL"

    stats={
        "n_requested":N,
        "n_valid":valid,
        "n_invalid":len(invalid),
        "gross_edge_reference_bps":GROSS_EDGE_BPS,
        "spread_bps":{
            "mean":statistics.fmean(spreads) if spreads else None,
            "p10":pct(spreads,0.10),"p25":pct(spreads,0.25),
            "p50":pct(spreads,0.50),"p75":pct(spreads,0.75),
            "p90":pct(spreads,0.90),"max":max(spreads) if spreads else None,
            "min":min(spreads) if spreads else None,
        },
        "best_bid_size_median":statistics.median(bid_sizes) if bid_sizes else None,
        "best_ask_size_median":statistics.median(ask_sizes) if ask_sizes else None,
        "fraction_spread_below_gross_edge":(
            sum(x<GROSS_EDGE_BPS for x in spreads)/valid if valid else None
        ),
        "session_context":"SUNDAY_OFF_HOURS_DIAGNOSTIC_ONLY",
        "verdict":verdict,
        "scientific_signal_changed":False,
        "live_trading_authorized":False,
        "account_reads":False,
        "private_endpoints_used":False,
        "orders":False,
        "exchange_mutation":False,
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"SP500_PUBLIC_BBO_OFFHOURS_RECEIPT_V03.json").write_text(
        json.dumps({"generated_at_utc":utcnow(),"stats":stats,"snapshots":rows,"invalid":invalid},
                   indent=2,sort_keys=True),
        encoding="utf-8"
    )
    print(json.dumps(stats,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
