#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "local_data" / "bnb_launchpool_cross_venue_source_v01"
OUT.mkdir(parents=True, exist_ok=True)

ANCHORS = [
    "2020-09-01T00:00:00Z",
    "2021-01-01T00:00:00Z",
    "2022-01-01T00:00:00Z",
    "2023-01-01T00:00:00Z",
    "2024-01-01T00:00:00Z",
    "2025-01-01T00:00:00Z",
    "2025-12-01T00:00:00Z",
]
BYBIT_HOSTS = ("https://api.bybit.com", "https://api.bytick.com")
OKX = "https://www.okx.com"
UA = "BNB-LAUNCHPOOL-DEMAND-001 cross-venue-source/0.1"
OKX_MIN_INTERVAL = 0.30
_last_okx = 0.0

def ms(x: str) -> int:
    return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)

def sha(x) -> str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def summary(times):
    xs=sorted(set(int(x) for x in times))
    return {
        "count":len(xs),
        "min_ts":xs[0] if xs else None,
        "max_ts":xs[-1] if xs else None,
        "timestamps_sha256":sha(xs),
    }

def get_json(base: str, params: dict, *, okx=False, retries=3):
    global _last_okx
    if okx:
        elapsed=time.monotonic()-_last_okx
        if elapsed<OKX_MIN_INTERVAL:
            time.sleep(OKX_MIN_INTERVAL-elapsed)
    url=base+"?"+urllib.parse.urlencode(params)
    last=None
    for k in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=20) as r:
                raw=r.read()
                if okx: _last_okx=time.monotonic()
                return json.loads(raw.decode("utf-8","replace"))
        except urllib.error.HTTPError as e:
            if okx: _last_okx=time.monotonic()
            last=f"HTTP_{e.code}"
            if e.code==429 and k+1<retries:
                time.sleep(1.0*(k+1))
                continue
            raise RuntimeError(last)
        except Exception as e:
            if okx: _last_okx=time.monotonic()
            last=f"{type(e).__name__}:{e}"
            if k+1<retries:
                time.sleep(0.5*(k+1))
                continue
            raise RuntimeError(last)
    raise RuntimeError(str(last))

def near(times, target, tolerance=15*60_000):
    return any(abs(int(x)-target)<=tolerance for x in times)

def bybit():
    result={"instrument":{},"anchors":{},"host_transport":{}}
    usable_host=None
    for host in BYBIT_HOSTS:
        rec={}
        try:
            j=get_json(host+"/v5/market/instruments-info",{"category":"spot","symbol":"BNBBTC"},retries=2)
            rows=((j.get("result") or {}).get("list") or [])
            present=j.get("retCode")==0 and any(r.get("symbol")=="BNBBTC" for r in rows)
            rec={"transport_ok":True,"retCode":j.get("retCode"),"retMsg":j.get("retMsg"),"instrument_present":present}
            if present and usable_host is None:
                usable_host=host
        except Exception as e:
            rec={"transport_ok":False,"error":str(e),"instrument_present":False}
        result["host_transport"][host]=rec

    if usable_host is None:
        errs=[v.get("error") for v in result["host_transport"].values()]
        if errs and all(x=="HTTP_403" for x in errs):
            result["classification"]="SOURCE_BLOCKED_ENVIRONMENT"
        else:
            result["classification"]="SOURCE_BINDING_BLOCKED"
        result["instrument"]={"present":False}
        return result

    result["instrument"]={"present":True,"host":usable_host}
    for a in ANCHORS:
        t=ms(a)
        try:
            j=get_json(usable_host+"/v5/market/kline",{
                "category":"spot","symbol":"BNBBTC","interval":"15",
                "start":t-60*60_000,"end":t+60*60_000,"limit":20
            },retries=2)
            if j.get("retCode")!=0:
                raise RuntimeError(f"BYBIT_RET_{j.get('retCode')}:{j.get('retMsg')}")
            rows=((j.get("result") or {}).get("list") or [])
            times=[int(r[0]) for r in rows]
            result["anchors"][a]={**summary(times),"anchor_present":near(times,t)}
        except Exception as e:
            result["anchors"][a]={"anchor_present":False,"error":str(e)}
    allpass=all(x.get("anchor_present") for x in result["anchors"].values())
    anypass=any(x.get("anchor_present") for x in result["anchors"].values())
    result["classification"]="EXACT_SOURCE_ANCHOR_PASS" if allpass else ("SOURCE_PARTIAL" if anypass else "SOURCE_BINDING_BLOCKED")
    return result

def okx():
    result={"instrument":{},"anchors":{}}
    try:
        j=get_json(OKX+"/api/v5/public/instruments",{"instType":"SPOT","instId":"BNB-BTC"},okx=True)
        rows=j.get("data") or []
        present=j.get("code")=="0" and any(r.get("instId")=="BNB-BTC" for r in rows)
        result["instrument"]={"present":present,"count":len(rows),"provider_code":j.get("code"),"provider_msg":j.get("msg")}
    except Exception as e:
        result["instrument"]={"present":False,"error":str(e)}
        result["classification"]="SOURCE_BLOCKED_ENVIRONMENT" if "HTTP_403" in str(e) else "SOURCE_BINDING_BLOCKED"
        return result

    if not result["instrument"]["present"]:
        result["classification"]="SOURCE_BINDING_BLOCKED"
        return result

    for a in ANCHORS:
        t=ms(a)
        try:
            j=get_json(OKX+"/api/v5/market/history-candles",{
                "instId":"BNB-BTC","bar":"15m","after":str(t+60*60_000),"limit":"100"
            },okx=True)
            if j.get("code")!="0":
                raise RuntimeError(f"OKX_CODE_{j.get('code')}:{j.get('msg')}")
            times=[int(r[0]) for r in (j.get("data") or [])]
            result["anchors"][a]={**summary(times),"anchor_present":near(times,t)}
        except Exception as e:
            result["anchors"][a]={"anchor_present":False,"error":str(e)}
    allpass=all(x.get("anchor_present") for x in result["anchors"].values())
    anypass=any(x.get("anchor_present") for x in result["anchors"].values())
    result["classification"]="EXACT_SOURCE_ANCHOR_PASS" if allpass else ("SOURCE_PARTIAL" if anypass else "SOURCE_BINDING_BLOCKED")
    return result

def main():
    venues={"BYBIT_SPOT_BNBBTC":bybit(),"OKX_SPOT_BNB_BTC":okx()}
    classes={k:v["classification"] for k,v in venues.items()}
    if all(x=="EXACT_SOURCE_ANCHOR_PASS" for x in classes.values()):
        status="SOURCE_DATA_PASS_BOTH_VENUES"
    elif any(x=="EXACT_SOURCE_ANCHOR_PASS" for x in classes.values()):
        status="SOURCE_DATA_PARTIAL_PASS"
    else:
        status="SOURCE_DATA_BLOCKED_OR_PARTIAL"
    receipt={
        "lab_id":"BNB-LAUNCHPOOL-DEMAND-001-CROSS-VENUE",
        "stage":"SOURCE_ONLY_V0.1",
        "candidate_identity":"LONG_BNBBTC_SPOT__FIRST_15M_OPEN_AFTER_CANONICAL_LAUNCHPOOL_ANNOUNCEMENT__HOLD_24H",
        "outcome_blind":True,
        "returns_computed":False,
        "pnl_computed":False,
        "strategy_outcomes_opened":False,
        "anchors":ANCHORS,
        "venues":venues,
        "status":status,
    }
    receipt["fingerprint"]=sha(receipt)
    p=OUT/"BNB_LAUNCHPOOL_DEMAND_001_CROSS_VENUE_SOURCE_RECEIPT_V0.1.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":status,"venue_classifications":classes,"fingerprint":receipt["fingerprint"]},sort_keys=True))

if __name__=="__main__":
    main()
