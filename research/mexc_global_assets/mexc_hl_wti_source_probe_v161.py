#!/usr/bin/env python3
"""Targeted source-only proof for MEXC USOIL_USDT <-> Hyperliquid xyz:CL."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/hl_wti_source_gate_v161")
HL="https://api.hyperliquid.xyz/info"
MEXC="https://api.mexc.com"
COIN="xyz:CL"
UA="CryptoLab-MEXC-HL-WTI-SourceGate/1.6.1"

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

def main():
    rep={
      "lab":"MEXC_HL_WTI_SOURCE_GATE_V1_6_1",
      "captured_at_utc":now(),
      "source_only":True,
      "mexc_symbol":"USOIL_USDT",
      "hyperliquid_coin":COIN,
      "hyperliquid_dex":"xyz",
      "external_identity_authority":"PRE_FROZEN_AMENDMENT_V1.6.1__XYZ_CL_EQUALS_CRUDE_OIL_WTI",
      "historical_outcomes_opened":0,
      "lead_lag_tested":False,
      "auth_used":False,
      "account_reads":False,
      "wallet_used":False,
      "orders":False,
      "exchange_mutation":False,
      "live_trading_authorized":False
    }

    raw,meta,mm=post({"type":"meta","dex":"xyz"}); save("hl_xyz_meta.json",raw,mm)
    universe=(meta or {}).get("universe") or []
    pos=next((i for i,a in enumerate(universe) if a.get("name")==COIN),None)
    if pos is None: raise RuntimeError("XYZ_CL_NOT_FOUND")
    rep["hl_meta"]={"index":pos,**universe[pos]}

    raw,mac,cm=post({"type":"metaAndAssetCtxs","dex":"xyz"}); save("hl_xyz_ctx.json",raw,cm)
    u=(mac[0] or {}).get("universe",[]) if isinstance(mac,list) and len(mac)>=2 else []
    ctxs=mac[1] if isinstance(mac,list) and len(mac)>=2 else []
    p=next((i for i,a in enumerate(u) if a.get("name")==COIN),None)
    ctx=ctxs[p] if p is not None and p<len(ctxs) else {}
    vals={}
    for k in ("midPx","markPx","oraclePx"):
        try: vals[k]=float(ctx[k]) if ctx.get(k) is not None else None
        except Exception: vals[k]=None
    rep["hl_context"]=vals

    raw,book,bm=post({"type":"l2Book","coin":COIN}); save("hl_xyz_cl_l2.json",raw,bm)
    levels=(book or {}).get("levels") or [[],[]]
    bid=ask=None
    try: bid=float(levels[0][0]["px"]) if levels[0] else None
    except Exception: pass
    try: ask=float(levels[1][0]["px"]) if levels[1] else None
    except Exception: pass
    mid=(bid+ask)/2 if bid is not None and ask is not None else vals.get("midPx")
    rep["hl_book"]={"best_bid":bid,"best_ask":ask,"mid":mid,"time_ms":(book or {}).get("time")}

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

    rel=10000*(mexc/mid-1) if mid and mid>0 else None
    origin=rep["mexc_detail"].get("indexOrigin")
    rep["mexc_index_vs_hl_mid_bps"]=rel
    rep["gates"]={
      "xyz_cl_exists":pos is not None,
      "external_identity_frozen":True,
      "mexc_exact_contract":rep["mexc_detail"].get("symbol")=="USOIL_USDT",
      "mexc_hyperliquid_origin":isinstance(origin,list) and any("HYPERLIQUID" in str(x).upper() for x in origin),
      "public_live_book":bid is not None and ask is not None and ask>=bid,
      "scale_within_250bps":rel is not None and abs(rel)<250
    }
    rep["verdict"]="HYPERLIQUID_WTI_SOURCE_PASS__XYZ_CL" if all(rep["gates"].values()) else "SOURCE_BLOCKED_HYPERLIQUID_WTI_TARGETED_PROOF"

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_HL_WTI_SOURCE_GATE_RECEIPT_V161.json").write_text(json.dumps(rep,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
