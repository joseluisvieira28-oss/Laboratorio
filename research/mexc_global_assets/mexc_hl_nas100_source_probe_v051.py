#!/usr/bin/env python3
"""Targeted source-only proof for MEXC NAS100 <-> Hyperliquid xyz:XYZ100."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/hl_nas100_source_gate_v051")
HL="https://api.hyperliquid.xyz/info"
MEXC="https://api.mexc.com"
COIN="xyz:XYZ100"
UA="CryptoLab-MEXC-HL-NAS100-SourceGate/0.5.1"

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
    if not isinstance(j,dict) or j.get("success") is not True: raise RuntimeError(f"MEXC non-success:{j}")
    return raw,j,{"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw),"path":path}

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def main():
    report={"lab":"MEXC_HL_NAS100_SOURCE_GATE_V0_5_1","captured_at_utc":now(),
            "source_only":True,"outcomes_opened":0,"auth_used":False,"account_reads":False,
            "wallet_used":False,"orders":False,"exchange_mutation":False,
            "mexc_symbol":"NAS100_USDT","hyperliquid_coin":COIN,"hyperliquid_dex":"xyz"}

    raw,meta,mm=post({"type":"meta","dex":"xyz"}); save("hl_xyz_meta.json",raw,mm)
    universe=(meta or {}).get("universe") or []
    pos=next((i for i,a in enumerate(universe) if a.get("name")==COIN),None)
    if pos is None: raise RuntimeError("XYZ100_NOT_FOUND_IN_XYZ_META")
    report["hl_meta"]={"index":pos,**universe[pos]}

    raw,mac,cm=post({"type":"metaAndAssetCtxs","dex":"xyz"}); save("hl_xyz_ctx.json",raw,cm)
    u=(mac[0] or {}).get("universe",[]) if isinstance(mac,list) and len(mac)>=2 else []
    ctxs=mac[1] if isinstance(mac,list) and len(mac)>=2 else []
    p=next((i for i,a in enumerate(u) if a.get("name")==COIN),None)
    ctx=ctxs[p] if p is not None and p<len(ctxs) else {}
    vals={}
    for k in ("midPx","markPx","oraclePx"):
        try: vals[k]=float(ctx[k]) if ctx.get(k) is not None else None
        except Exception: vals[k]=None
    report["hl_context"]=vals

    raw,book,bm=post({"type":"l2Book","coin":COIN}); save("hl_xyz100_l2.json",raw,bm)
    levels=(book or {}).get("levels") or [[],[]]
    bid=ask=None
    try: bid=float(levels[0][0]["px"]) if levels[0] else None
    except Exception: pass
    try: ask=float(levels[1][0]["px"]) if levels[1] else None
    except Exception: pass
    mid=(bid+ask)/2 if bid is not None and ask is not None else vals.get("midPx")
    report["hl_book"]={"best_bid":bid,"best_ask":ask,"mid":mid,"time_ms":(book or {}).get("time")}

    raw,detail,dm=get("/api/v1/contract/detail?symbol=NAS100_USDT"); save("mexc_nas100_detail.json",raw,dm)
    d=detail.get("data")
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="NAS100_USDT"),None)
    report["mexc_detail"]={k:(d or {}).get(k) for k in
        ["symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate","takerFeeRate","contractSize"]}

    raw,idx,im=get("/api/v1/contract/index_price/NAS100_USDT"); save("mexc_nas100_index.json",raw,im)
    md=idx.get("data") or {}
    mexc_px=float(md["indexPrice"])
    report["mexc_index_price"]=mexc_px
    report["mexc_index_timestamp"]=md.get("timestamp")

    rel=None
    if mid and mid>0: rel=10000*(mexc_px/mid-1)
    report["mexc_vs_hl_mid_bps"]=rel

    identity_ok=(report["mexc_detail"].get("indexOrigin")==["HYPERLIQUID"])
    market_ok=(mid is not None and bid is not None and ask is not None)
    scale_ok=(rel is not None and abs(rel)<250)
    report["gates"]={"mexc_hyperliquid_origin":identity_ok,"public_live_book":market_ok,"scale_within_250bps":scale_ok}
    passed=all(report["gates"].values())
    report["verdict"]="HYPERLIQUID_NAS100_SOURCE_PASS__XYZ_XYZ100" if passed else "SOURCE_BLOCKED_HYPERLIQUID_NAS100_TARGETED_PROOF"
    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_HL_NAS100_SOURCE_GATE_RECEIPT_V051.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
