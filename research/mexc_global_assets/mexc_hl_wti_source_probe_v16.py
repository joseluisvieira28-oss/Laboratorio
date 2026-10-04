#!/usr/bin/env python3
"""Public/no-auth source-only MEXC↔Hyperliquid WTI binding discovery."""
from __future__ import annotations
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/hl_wti_source_gate_v16")
HL="https://api.hyperliquid.xyz/info"
MEXC="https://api.mexc.com"
UA="CryptoLab-MEXC-HL-WTI-SourceGate/1.6"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def post(payload):
    r=requests.post(HL,json=payload,headers={"User-Agent":UA,"Content-Type":"application/json"},timeout=30)
    raw=r.content
    if r.status_code!=200: raise RuntimeError(f"HL_HTTP_{r.status_code}:{raw[:300]!r}")
    return raw,r.json(),{"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw),"payload":payload}

def get(path):
    r=requests.get(MEXC+path,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    if r.status_code!=200: raise RuntimeError(f"MEXC_HTTP_{r.status_code}:{raw[:300]!r}")
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
    return raw,j,{"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw),"path":path}

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def semantic(name):
    u=name.upper()
    score=0; reasons=[]
    if "WTI" in u:
        score+=120; reasons.append("WTI_TOKEN")
    if "USOIL" in u:
        score+=120; reasons.append("USOIL_TOKEN")
    if "CRUDE" in u:
        score+=100; reasons.append("CRUDE_TOKEN")
    if re.search(r"(^|:|[-_])OIL($|[-_])",u):
        score+=80; reasons.append("OIL_TOKEN")
    if re.search(r"(^|:|[-_])CL($|[-_])",u):
        score+=55; reasons.append("CL_TOKEN_REQUIRES_CONTEXT")
    return score,reasons

def main():
    rep={
      "lab":"MEXC_HL_WTI_SOURCE_GATE_V1_6",
      "captured_at_utc":now(),
      "source_only":True,
      "historical_outcomes_opened":0,
      "lead_lag_tested":False,
      "auth_used":False,
      "account_reads":False,
      "wallet_used":False,
      "orders":False,
      "exchange_mutation":False,
      "live_trading_authorized":False,
      "candidates":[]
    }

    raw,dexs,m=post({"type":"perpDexs"}); save("hl_perpDexs.json",raw,m)
    names=[""]
    if isinstance(dexs,list):
        for x in dexs:
            if isinstance(x,dict) and x.get("name") and x["name"] not in names:
                names.append(x["name"])
    rep["perp_dexes"]=names

    all_assets=[]
    for dex in names:
        raw,meta,mm=post({"type":"meta","dex":dex}); save("hl_meta_"+(dex or "primary")+".json",raw,mm)
        universe=(meta or {}).get("universe") or []
        for i,a in enumerate(universe):
            nm=str(a.get("name",""))
            sc,why=semantic(nm)
            row={"dex":dex,"index":i,"name":nm,"semantic_score":sc,"reasons":why,
                 "maxLeverage":a.get("maxLeverage"),"szDecimals":a.get("szDecimals")}
            all_assets.append(row)
            if sc>0: rep["candidates"].append(row)
        time.sleep(0.04)
    rep["all_asset_count"]=len(all_assets)
    rep["candidates"].sort(key=lambda x:(-x["semantic_score"],x["dex"],x["name"]))

    raw,detail,dm=get("/api/v1/contract/detail?symbol=USOIL_USDT"); save("mexc_usoil_detail.json",raw,dm)
    d=detail.get("data")
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="USOIL_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_USOIL_MISSING")
    rep["mexc_detail"]={k:d.get(k) for k in [
      "symbol","displayName","indexOrigin","apiAllowed","makerFeeRate","takerFeeRate","contractSize"
    ]}
    raw,idx,im=get("/api/v1/contract/index_price/USOIL_USDT"); save("mexc_usoil_index.json",raw,im)
    md=idx.get("data") or {}; mexc=float(md["indexPrice"])
    rep["mexc_index"]={"price":mexc,"timestamp":md.get("timestamp")}

    plausible=[x for x in rep["candidates"] if x["semantic_score"]>=55]
    live=[]
    for c in plausible:
        dex=c["dex"]; coin=c["name"]
        raw,mac,cm=post({"type":"metaAndAssetCtxs","dex":dex})
        safe=(dex or "primary")+"_"+re.sub(r"[^A-Za-z0-9_.-]+","_",coin)
        save("hl_ctx_"+safe+".json",raw,cm)
        uni=(mac[0] or {}).get("universe",[]) if isinstance(mac,list) and len(mac)>=2 else []
        ctxs=mac[1] if isinstance(mac,list) and len(mac)>=2 else []
        pos=next((i for i,a in enumerate(uni) if a.get("name")==coin),None)
        ctx=ctxs[pos] if pos is not None and pos<len(ctxs) else {}
        vals={}
        for k in ("midPx","markPx","oraclePx"):
            try: vals[k]=float(ctx[k]) if ctx.get(k) is not None else None
            except Exception: vals[k]=None

        raw,b,bm=post({"type":"l2Book","coin":coin}); save("hl_book_"+safe+".json",raw,bm)
        levels=(b or {}).get("levels") or [[],[]]
        bid=ask=None
        try: bid=float(levels[0][0]["px"]) if levels[0] else None
        except Exception: pass
        try: ask=float(levels[1][0]["px"]) if levels[1] else None
        except Exception: pass
        mid=(bid+ask)/2 if bid is not None and ask is not None else vals.get("midPx")
        rel=10000*(mexc/mid-1) if mid and mid>0 else None
        live.append({
          **c,
          "midPx":vals.get("midPx"),"markPx":vals.get("markPx"),"oraclePx":vals.get("oraclePx"),
          "best_bid":bid,"best_ask":ask,"mid":mid,
          "mexc_index_vs_hl_mid_bps":rel,
          "book_time_ms":(b or {}).get("time")
        })
        time.sleep(0.04)
    rep["live_candidates"]=live

    exact_origin=(
      isinstance(rep["mexc_detail"].get("indexOrigin"),list)
      and any("HYPERLIQUID" in str(x).upper() for x in rep["mexc_detail"]["indexOrigin"])
    )
    strong=[
      x for x in live
      if x["semantic_score"]>=80
      and x.get("best_bid") is not None and x.get("best_ask") is not None
      and x.get("mexc_index_vs_hl_mid_bps") is not None
      and abs(x["mexc_index_vs_hl_mid_bps"])<250
    ]
    strong.sort(key=lambda x:(-x["semantic_score"],abs(x["mexc_index_vs_hl_mid_bps"])))
    rep["gates"]={
      "mexc_exact_contract":rep["mexc_detail"].get("symbol")=="USOIL_USDT",
      "mexc_hyperliquid_origin":exact_origin,
      "unique_strong_hl_identity":len(strong)==1,
      "public_live_book":len(strong)==1,
      "scale_within_250bps":len(strong)==1
    }
    if all(rep["gates"].values()):
        rep["bound_candidate"]=strong[0]
        rep["verdict"]="HYPERLIQUID_WTI_SOURCE_PASS"
    elif not plausible:
        rep["verdict"]="SOURCE_BLOCKED_HYPERLIQUID_WTI_IDENTITY_NOT_FOUND"
    elif len(strong)>1:
        rep["verdict"]="SOURCE_BLOCKED_HYPERLIQUID_WTI_IDENTITY_AMBIGUOUS"
    else:
        rep["verdict"]="SOURCE_BLOCKED_HYPERLIQUID_WTI_TARGETED_PROOF"

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_HL_WTI_SOURCE_GATE_RECEIPT_V16.json").write_text(json.dumps(rep,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
      "verdict":rep["verdict"],
      "mexc_detail":rep["mexc_detail"],
      "mexc_index":rep["mexc_index"],
      "perp_dexes":rep["perp_dexes"],
      "candidate_count":len(rep["candidates"]),
      "candidates":rep["candidates"][:25],
      "live_candidates":live,
      "gates":rep["gates"],
      "historical_outcomes_opened":0,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
