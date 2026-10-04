#!/usr/bin/env python3
"""MEXC↔Hyperliquid NAS100 source-binding probe. SOURCE ONLY."""
from __future__ import annotations
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/hl_nas100_source_gate_v05")
HL="https://api.hyperliquid.xyz/info"
MEXC="https://api.mexc.com"
UA="CryptoLab-MEXC-HL-NAS100-SourceGate/0.5"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def post(payload):
    r=requests.post(HL,json=payload,headers={"User-Agent":UA,"Content-Type":"application/json"},timeout=30)
    raw=r.content
    if r.status_code!=200: raise RuntimeError(f"HL HTTP {r.status_code}: {raw[:300]!r}")
    return raw,r.json(),{"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw),"payload":payload}

def get(path):
    r=requests.get(MEXC+path,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    if r.status_code!=200: raise RuntimeError(f"MEXC HTTP {r.status_code}: {raw[:300]!r}")
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError(f"MEXC non-success: {j}")
    return raw,j,{"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw),"path":path}

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def semantic(name):
    u=name.upper()
    score=0; reasons=[]
    tests=[
      ("NAS100",100,"nas100_exact"),
      ("NASDAQ100",100,"nasdaq100_exact"),
      ("NASDAQ",70,"nasdaq_token"),
      ("USTECH",85,"ustech_alias"),
      ("US100",85,"us100_alias"),
      ("TECH100",80,"tech100_alias"),
      ("NDX",75,"ndx_alias"),
    ]
    for t,s,r in tests:
        if t in u: score=max(score,s); reasons.append(r)
    return score,reasons

def main():
    report={"lab":"MEXC_HL_NAS100_SOURCE_GATE_V0_5","captured_at_utc":now(),
            "source_only":True,"outcomes_opened":0,"auth_used":False,"wallet_used":False,
            "account_reads":False,"orders":False,"exchange_mutation":False}

    raw,dexs,m=post({"type":"perpDexs"}); save("hl_perpDexs.json",raw,m)
    dex_names=[""]
    if isinstance(dexs,list):
        for x in dexs:
            if isinstance(x,dict) and x.get("name") and x["name"] not in dex_names:
                dex_names.append(x["name"])
    report["perp_dex_count"]=len(dex_names)

    candidates=[]
    for dex in dex_names:
        raw,meta,mm=post({"type":"meta","dex":dex})
        save(f"hl_meta_{dex or 'primary'}.json",raw,mm)
        for idx,a in enumerate((meta or {}).get("universe") or []):
            name=str(a.get("name",""))
            sc,reasons=semantic(name)
            if sc>0:
                candidates.append({"dex":dex,"index":idx,"name":name,"semantic_score":sc,
                                   "reasons":reasons,"maxLeverage":a.get("maxLeverage"),
                                   "szDecimals":a.get("szDecimals")})
        time.sleep(0.03)
    candidates.sort(key=lambda x:(-x["semantic_score"],x["dex"],x["name"]))
    report["candidates"]=candidates

    raw,detail,dm=get("/api/v1/contract/detail?symbol=NAS100_USDT")
    save("mexc_nas100_detail.json",raw,dm)
    d=detail.get("data")
    if isinstance(d,list):
        d=next((x for x in d if x.get("symbol")=="NAS100_USDT"),None)
    report["mexc_detail"]={k:(d or {}).get(k) for k in
        ["symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate","takerFeeRate","contractSize"]}

    raw,idx,im=get("/api/v1/contract/index_price/NAS100_USDT")
    save("mexc_nas100_index.json",raw,im)
    md=idx.get("data") or {}
    mexc_px=None
    for k in ("indexPrice","price"):
        try:
            if md.get(k) is not None:
                mexc_px=float(md[k]); break
        except Exception: pass
    report["mexc_index_price"]=mexc_px
    report["mexc_index_payload"]=md

    live=[]
    for c in candidates:
        raw,mac,am=post({"type":"metaAndAssetCtxs","dex":c["dex"]})
        safe=(c["dex"] or "primary")+"_"+re.sub(r"[^A-Za-z0-9_.-]+","_",c["name"])
        save(f"hl_ctx_{safe}.json",raw,am)
        universe=(mac[0] or {}).get("universe",[]) if isinstance(mac,list) and len(mac)>=2 else []
        ctxs=mac[1] if isinstance(mac,list) and len(mac)>=2 else []
        pos=next((i for i,a in enumerate(universe) if a.get("name")==c["name"]),None)
        ctx=ctxs[pos] if pos is not None and pos<len(ctxs) else {}
        vals={}
        for k in ("midPx","markPx","oraclePx"):
            try: vals[k]=float(ctx[k]) if ctx.get(k) is not None else None
            except Exception: vals[k]=None
        raw,b,bm=post({"type":"l2Book","coin":c["name"]})
        save(f"hl_l2_{safe}.json",raw,bm)
        levels=(b or {}).get("levels") or [[],[]]
        bid=ask=None
        try: bid=float(levels[0][0]["px"]) if levels[0] else None
        except Exception: pass
        try: ask=float(levels[1][0]["px"]) if levels[1] else None
        except Exception: pass
        mid=(bid+ask)/2 if bid is not None and ask is not None else vals.get("midPx")
        diff=None
        if mexc_px and mid and mid>0: diff=10000*(mexc_px/mid-1)
        live.append({**c,"midPx":vals.get("midPx"),"markPx":vals.get("markPx"),
                     "oraclePx":vals.get("oraclePx"),"best_bid":bid,"best_ask":ask,
                     "book_time_ms":(b or {}).get("time"),"mexc_index_vs_hl_mid_bps":diff})
        time.sleep(0.03)
    report["live_candidates"]=live

    plausible=[x for x in live if x.get("mexc_index_vs_hl_mid_bps") is not None and x["semantic_score"]>=70]
    close=[x for x in plausible if abs(x["mexc_index_vs_hl_mid_bps"])<250]
    close.sort(key=lambda x:abs(x["mexc_index_vs_hl_mid_bps"]))
    if len(close)==1:
        report["bound_candidate"]=close[0]
        report["verdict"]="HYPERLIQUID_NAS100_SOURCE_PASS"
    elif len(close)>1:
        # Allow unique overwhelming scale/price match: nearest must be >=5x closer than runner-up
        a,b=abs(close[0]["mexc_index_vs_hl_mid_bps"]),abs(close[1]["mexc_index_vs_hl_mid_bps"])
        if a < 50 and b > max(100,5*a):
            report["bound_candidate"]=close[0]
            report["verdict"]="HYPERLIQUID_NAS100_SOURCE_PASS"
        else:
            report["best_candidate_only"]=close[0]
            report["verdict"]="SOURCE_BLOCKED_HYPERLIQUID_NAS100_IDENTITY_AMBIGUOUS"
    else:
        report["verdict"]="SOURCE_BLOCKED_HYPERLIQUID_NAS100_IDENTITY"

    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_HL_NAS100_SOURCE_GATE_RECEIPT_V05.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"verdict":report["verdict"],"mexc_index_price":mexc_px,
                      "candidates":candidates,"live_candidates":live,
                      "outcomes_opened":0,"live_trading_authorized":False},
                     indent=2,sort_keys=True))

if __name__=="__main__": main()
