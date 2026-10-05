#!/usr/bin/env python3
from __future__ import annotations
import json,time,math,hashlib
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
B=json.loads((HERE/"MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SOURCE_BINDING_V1.0.json").read_text())
OUT=Path("artifacts/mexc_global_assets/intraday_overshoot_exec_v01")
UA="CryptoLab-Overshoot-ExecSource/0.1"
BASE="https://api.mexc.com/api/v1/contract"

def req(url,params=None,timeout=20):
    t=time.perf_counter()
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
    ms=(time.perf_counter()-t)*1000
    return r,ms

def px(level):
    if isinstance(level,(list,tuple)) and level:
        return float(level[0])
    if isinstance(level,dict):
        for k in ("price","p"):
            if k in level:return float(level[k])
    raise ValueError("BAD_LEVEL")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    details={}
    try:
        dr,dms=req(BASE+"/detail")
        dj=dr.json()
        for x in (dj.get("data") or []):
            if isinstance(x,dict) and x.get("symbol"):details[x["symbol"]]=x
        detail_meta={"http":dr.status_code,"latency_ms":dms,"success":dj.get("success"),
                     "symbols":len(details),"sha256":hashlib.sha256(dr.content).hexdigest()}
    except Exception as e:
        detail_meta={"error":str(e)}
    rows=[]
    for c in B["candidates"]:
        s=c["target"];rec={"symbol":s}
        try:
            r,ms=req(BASE+"/depth/"+s)
            j=r.json();d=j.get("data") or {}
            bids=d.get("bids") or [];asks=d.get("asks") or []
            bp=max(px(x) for x in bids) if bids else None
            ap=min(px(x) for x in asks) if asks else None
            mid=(bp+ap)/2 if bp and ap else None
            spread=10000*(ap-bp)/mid if mid and ap>bp else None
            rec.update({"http":r.status_code,"latency_ms":ms,"success":j.get("success"),
                        "bid_levels":len(bids),"ask_levels":len(asks),
                        "best_bid":bp,"best_ask":ap,"spread_bps":spread,
                        "depth_sha256":hashlib.sha256(r.content).hexdigest(),
                        "detail":{k:details.get(s,{}).get(k) for k in ("contractSize","minVol","volUnit","priceUnit","apiAllowed")}})
            rec["route_pass"]=bool(r.status_code==200 and j.get("success") is True and bids and asks and
                                   bp is not None and ap is not None and ap>bp and spread is not None and math.isfinite(spread))
        except Exception as e:
            rec.update({"route_pass":False,"error":str(e)})
        rows.append(rec)
        print(json.dumps({"symbol":s,"route_pass":rec["route_pass"],"spread_bps":rec.get("spread_bps"),
                          "latency_ms":rec.get("latency_ms")},sort_keys=True))
        time.sleep(.03)
    passes=[x for x in rows if x["route_pass"]]
    spreads=[x["spread_bps"] for x in passes if x.get("spread_bps") is not None]
    lats=[x["latency_ms"] for x in passes if x.get("latency_ms") is not None]
    rep={"gate_id":"MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_EXEC_SOURCE_V0_1",
         "source_only":True,"detail_meta":detail_meta,"symbols":rows,
         "pass_count":len(passes),"candidate_count":len(rows),
         "median_spread_bps":sorted(spreads)[len(spreads)//2] if spreads else None,
         "max_spread_bps":max(spreads) if spreads else None,
         "median_latency_ms":sorted(lats)[len(lats)//2] if lats else None,
         "max_latency_ms":max(lats) if lats else None,
         "verdict":"PUBLIC_EXEC_ROUTE_SOURCE_PASS" if len(passes)==len(rows)==35 else "PUBLIC_EXEC_ROUTE_SOURCE_BLOCKED",
         "account_reads":False,"private_endpoints_used":False,"orders":False,"exchange_mutation":False,"live_trading":False}
    body=json.dumps(rep,indent=2,sort_keys=True)
    (OUT/"MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_EXEC_SOURCE_V01.json").write_text(body)
    print("REPORT_SHA256",hashlib.sha256(body.encode()).hexdigest())
    print(json.dumps({k:rep[k] for k in ("verdict","pass_count","candidate_count","median_spread_bps","max_spread_bps","median_latency_ms","max_latency_ms")},sort_keys=True))
if __name__=="__main__":main()
