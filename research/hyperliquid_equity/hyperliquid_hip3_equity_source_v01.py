#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone
import requests

OUT=Path("artifacts/hyperliquid_equity/hip3_equity_source_v01"); OUT.mkdir(parents=True,exist_ok=True)
URL="https://api.hyperliquid.xyz/info"
UA="CryptoLab-Hyperliquid-HIP3-Equity-Source/0.1"
TICKERS=["NVDA","TSLA","AAPL","PLTR","META","AMZN","MSFT","AMD","NFLX","BABA","GOOGL","ORCL"]
SOURCE_DAY="2026-10-03"

def sha(b): return hashlib.sha256(b).hexdigest()
def post(name,payload,timeout=60):
    r=requests.post(URL,json=payload,headers={"User-Agent":UA,"Content-Type":"application/json"},timeout=timeout)
    (OUT/f"{name}.bin").write_bytes(r.content)
    (OUT/f"{name}.meta.json").write_text(json.dumps({
        "payload":payload,"status":r.status_code,"sha256":sha(r.content),
        "captured_at_utc":datetime.now(timezone.utc).isoformat()
    },indent=2,sort_keys=True))
    if r.status_code!=200:
        return None,r.status_code
    try:return r.json(),r.status_code
    except:return None,r.status_code

def main():
    rep={
      "lab":"HYPERLIQUID_HIP3_EQUITY_SOURCE_CENSUS_V0_1",
      "source_only":True,"historical_outcomes_opened":0,"signal_tested":False,
      "source_verification_date":SOURCE_DAY,"tickers":TICKERS,
      "private_user_endpoints_used":False,"wallet_address_supplied":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }

    dexs,status=post("perpDexs",{"type":"perpDexs"})
    allmetas,_=post("allPerpMetas",{"type":"allPerpMetas"})
    cats,_=post("perpCategories",{"type":"perpCategories"})
    rep["perpDexs_status"]=status
    if not isinstance(dexs,list):
        rep["verdict"]="SOURCE_BLOCKED_HIP3_PERPDEX_ENUMERATION"
        (OUT/"HYPERLIQUID_HIP3_EQUITY_SOURCE_RECEIPT_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
        print(json.dumps(rep,indent=2,sort_keys=True)); return

    dexnames=[]
    for x in dexs:
        if isinstance(x,dict) and x.get("name"): dexnames.append(str(x["name"]))
    rep["dex_names"]=dexnames
    rep["dex_count"]=len(dexnames)
    matches=[]

    source_start=int(datetime.fromisoformat(SOURCE_DAY+"T14:30:00+00:00").timestamp()*1000)
    source_end=int(datetime.fromisoformat(SOURCE_DAY+"T19:00:00+00:00").timestamp()*1000)

    for dex in dexnames:
        meta,_=post(f"meta_{dex}",{"type":"meta","dex":dex})
        ctx,_=post(f"metaAndAssetCtxs_{dex}",{"type":"metaAndAssetCtxs","dex":dex})
        dstatus,_=post(f"perpDexStatus_{dex}",{"type":"perpDexStatus","dex":dex})
        dlimits,_=post(f"perpDexLimits_{dex}",{"type":"perpDexLimits","dex":dex})
        time.sleep(.03)

        universe=[]
        if isinstance(meta,dict): universe=meta.get("universe") or []
        for idx,u in enumerate(universe):
            if not isinstance(u,dict): continue
            name=str(u.get("name",""))
            bare=name.split(":",1)[-1].upper()
            ticker=next((t for t in TICKERS if bare==t or bare.startswith(t+"-") or bare.startswith(t+"_")),None)
            if not ticker: continue

            item={
              "ticker":ticker,"dex":dex,"coin":name,"meta_index":idx,
              "szDecimals":u.get("szDecimals"),"maxLeverage":u.get("maxLeverage"),
              "marginMode":u.get("marginMode"),"onlyIsolated":u.get("onlyIsolated"),
              "isDelisted":u.get("isDelisted"),
              "dex_descriptor":next((x for x in dexs if isinstance(x,dict) and x.get("name")==dex),None),
              "perpDexStatus":dstatus,"perpDexLimits":dlimits
            }

            l2,l2status=post(f"l2_{dex}_{ticker}",{"type":"l2Book","coin":name})
            item["l2_status"]=l2status
            item["l2_ok"]=isinstance(l2,dict) and bool(l2.get("levels"))

            candles,cstatus=post(f"candles_{dex}_{ticker}",{
              "type":"candleSnapshot",
              "req":{"coin":name,"interval":"1m","startTime":source_start,"endTime":source_end}
            })
            item["candle_status"]=cstatus
            item["candle_rows"]=len(candles) if isinstance(candles,list) else 0
            item["historical_1m_ok"]=item["candle_rows"]>=200
            if isinstance(candles,list) and candles:
                item["candle_first_t"]=candles[0].get("t")
                item["candle_last_t"]=candles[-1].get("t")
            matches.append(item)
            time.sleep(.03)

    rep["matches"]=matches
    rep["match_count"]=len(matches)
    by={}
    for t in TICKERS:
        ms=[m for m in matches if m["ticker"]==t]
        by[t]={
          "matches":[{"dex":m["dex"],"coin":m["coin"],"l2_ok":m["l2_ok"],
                      "historical_1m_ok":m["historical_1m_ok"],"candle_rows":m["candle_rows"],
                      "maxLeverage":m["maxLeverage"]} for m in ms],
          "active_historical_matches":sum(bool(m["l2_ok"] and m["historical_1m_ok"]) for m in ms)
        }
    rep["ticker_summary"]=by
    rep["active_historical_tickers"]=[t for t,x in by.items() if x["active_historical_matches"]>0]

    # Preserve possible fee-related public fields without guessing schema.
    def fee_fields(obj,path="root",out=None):
        if out is None: out=[]
        if isinstance(obj,dict):
            for k,v in obj.items():
                lk=str(k).lower()
                np=f"{path}.{k}"
                if any(s in lk for s in ("fee","growth","deployer","aligned","quote")):
                    out.append({"path":np,"value":v})
                fee_fields(v,np,out)
        elif isinstance(obj,list):
            for i,v in enumerate(obj): fee_fields(v,f"{path}[{i}]",out)
        return out
    rep["public_fee_related_fields"]=fee_fields({"perpDexs":dexs,"allPerpMetas":allmetas,"categories":cats})[:500]

    rep["verdict"]="HIP3_EQUITY_PUBLIC_SOURCE_PASS" if rep["active_historical_tickers"] else "SOURCE_BLOCKED_HIP3_EQUITY_HISTORY"
    (OUT/"HYPERLIQUID_HIP3_EQUITY_SOURCE_RECEIPT_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({
      "verdict":rep["verdict"],"dex_count":rep["dex_count"],
      "active_historical_tickers":rep["active_historical_tickers"],
      "ticker_summary":rep["ticker_summary"],
      "fee_fields_sample":rep["public_fee_related_fields"][:40]
    },indent=2,sort_keys=True))

if __name__=="__main__": main()
