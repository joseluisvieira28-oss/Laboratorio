#!/usr/bin/env python3
"""Public/no-auth MEXC↔Hyperliquid SP500 source-binding probe.

SOURCE ONLY. No historical outcomes, accounts, wallets, orders, or mutation.
"""
from __future__ import annotations
import hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/hyperliquid_source_gate_v03")
HL="https://api.hyperliquid.xyz/info"
MEXC="https://api.mexc.com"
UA="CryptoLab-MEXC-HL-SourceGate/0.3"

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(b:bytes):
    return hashlib.sha256(b).hexdigest()

def post_hl(payload):
    r=requests.post(HL,json=payload,headers={"User-Agent":UA,"Content-Type":"application/json"},timeout=30)
    raw=r.content
    if r.status_code!=200:
        raise RuntimeError(f"HL HTTP {r.status_code}: {raw[:300]!r}")
    j=r.json()
    return raw,j,{"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw),"payload":payload}

def get_mexc(path):
    r=requests.get(MEXC+path,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    if r.status_code!=200:
        raise RuntimeError(f"MEXC HTTP {r.status_code}: {raw[:300]!r}")
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError(f"MEXC non-success: {j}")
    return raw,j,{"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw),"path":path}

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def semantic_score(name):
    n=name.upper()
    score=0
    reasons=[]
    if "SP500" in n or "SPX500" in n:
        score+=100; reasons.append("exact_sp500_token")
    if re.search(r"(^|:|[-_])SPX($|[-_])",n):
        score+=80; reasons.append("spx_token")
    if "S&P" in n or "SNP500" in n or "US500" in n:
        score+=90; reasons.append("sp500_alias")
    if "SPY" in n:
        score+=40; reasons.append("spy_proxy_token")
    if "500" in n:
        score+=10; reasons.append("contains_500")
    return score,reasons

def main():
    report={
        "lab":"MEXC_HYPERLIQUID_SP500_SOURCE_GATE_V0_3",
        "captured_at_utc":now(),
        "source_only":True,
        "outcomes_opened":0,
        "auth_used":False,
        "wallet_used":False,
        "account_reads":False,
        "orders":False,
        "exchange_mutation":False,
        "candidates":[],
    }

    raw, dexs, meta=post_hl({"type":"perpDexs"})
    save("hyperliquid_perpDexs.json",raw,meta)
    report["perp_dex_count"]=len(dexs) if isinstance(dexs,list) else None

    dex_names=[""]
    if isinstance(dexs,list):
        for x in dexs:
            if isinstance(x,dict) and x.get("name") and x["name"] not in dex_names:
                dex_names.append(x["name"])

    all_assets=[]
    for dex in dex_names:
        raw,m,mm=post_hl({"type":"meta","dex":dex})
        safe=dex or "primary"
        save(f"hyperliquid_meta_{safe}.json",raw,mm)
        universe=(m or {}).get("universe") or []
        for idx,a in enumerate(universe):
            name=str(a.get("name",""))
            sc,reasons=semantic_score(name)
            rec={"dex":dex,"index":idx,"name":name,"semantic_score":sc,"reasons":reasons,
                 "maxLeverage":a.get("maxLeverage"),"szDecimals":a.get("szDecimals")}
            all_assets.append(rec)
            if sc>0:
                report["candidates"].append(rec)
        time.sleep(0.05)

    report["all_asset_count"]=len(all_assets)
    report["candidates"].sort(key=lambda x:(-x["semantic_score"],x["dex"],x["name"]))

    # MEXC source identity + live index
    raw,detail,dm=get_mexc("/api/v1/contract/detail?symbol=SPX500_USDT")
    save("mexc_sp500_detail.json",raw,dm)
    d=detail.get("data")
    if isinstance(d,list):
        d=next((x for x in d if x.get("symbol")=="SPX500_USDT"),None)
    report["mexc_detail"]={
        "symbol": d.get("symbol") if isinstance(d,dict) else None,
        "indexOrigin": d.get("indexOrigin") if isinstance(d,dict) else None,
        "apiAllowed": d.get("apiAllowed") if isinstance(d,dict) else None,
        "isZeroFeeSymbol": d.get("isZeroFeeSymbol") if isinstance(d,dict) else None,
        "makerFeeRate": d.get("makerFeeRate") if isinstance(d,dict) else None,
        "takerFeeRate": d.get("takerFeeRate") if isinstance(d,dict) else None,
    }

    raw,idx,im=get_mexc("/api/v1/contract/index_price/SPX500_USDT")
    save("mexc_sp500_index_price.json",raw,im)
    md=idx.get("data") or {}
    mexc_px=None
    for key in ("indexPrice","price"):
        try:
            if md.get(key) is not None:
                mexc_px=float(md[key]); break
        except Exception:
            pass
    report["mexc_index_price"]=mexc_px
    report["mexc_index_payload"]=md

    # Only inspect live contexts for semantically plausible candidates.
    plausible=[x for x in report["candidates"] if x["semantic_score"]>=40]
    live=[]
    for c in plausible:
        dex=c["dex"]
        raw,mac,am=post_hl({"type":"metaAndAssetCtxs","dex":dex})
        safe=(dex or "primary")+"_"+re.sub(r"[^A-Za-z0-9_.-]+","_",c["name"])
        save(f"hyperliquid_metaAndAssetCtxs_{safe}.json",raw,am)
        universe=(mac[0] or {}).get("universe",[]) if isinstance(mac,list) and len(mac)>=2 else []
        ctxs=mac[1] if isinstance(mac,list) and len(mac)>=2 else []
        pos=next((i for i,a in enumerate(universe) if a.get("name")==c["name"]),None)
        ctx=ctxs[pos] if pos is not None and pos<len(ctxs) else {}
        vals={}
        for k in ("midPx","markPx","oraclePx"):
            try:
                vals[k]=float(ctx[k]) if ctx.get(k) is not None else None
            except Exception:
                vals[k]=None
        # public l2 book
        raw,b, bm=post_hl({"type":"l2Book","coin":c["name"]})
        save(f"hyperliquid_l2Book_{safe}.json",raw,bm)
        levels=(b or {}).get("levels") or [[],[]]
        bid=ask=None
        try: bid=float(levels[0][0]["px"]) if levels[0] else None
        except Exception: pass
        try: ask=float(levels[1][0]["px"]) if levels[1] else None
        except Exception: pass
        mid=(bid+ask)/2 if bid is not None and ask is not None else vals.get("midPx")
        rel_bps=None
        if mexc_px and mid and mid>0:
            rel_bps=10000*(mexc_px/mid-1)
        live.append({
            "dex":dex,"name":c["name"],"semantic_score":c["semantic_score"],
            "midPx":vals.get("midPx"),"markPx":vals.get("markPx"),"oraclePx":vals.get("oraclePx"),
            "best_bid":bid,"best_ask":ask,
            "book_time_ms":(b or {}).get("time"),
            "mexc_index_vs_hl_mid_bps":rel_bps,
        })
        time.sleep(0.05)
    report["live_candidates"]=live

    # Source-only verdict. Require unique strongest semantic candidate and sane scale.
    strong=[x for x in live if x["semantic_score"]>=80 and x.get("mexc_index_vs_hl_mid_bps") is not None]
    strong.sort(key=lambda x:abs(x["mexc_index_vs_hl_mid_bps"]))
    if len(strong)==1 and abs(strong[0]["mexc_index_vs_hl_mid_bps"])<500:
        report["bound_candidate"]=strong[0]
        report["verdict"]="HYPERLIQUID_SP500_SOURCE_PASS"
    elif strong and abs(strong[0]["mexc_index_vs_hl_mid_bps"])<100:
        # Multiple aliases are not automatically safe: require unique identity.
        report["best_candidate_only"]=strong[0]
        report["verdict"]="SOURCE_BLOCKED_HYPERLIQUID_ASSET_IDENTITY_AMBIGUOUS"
    else:
        report["verdict"]="SOURCE_BLOCKED_HYPERLIQUID_ASSET_IDENTITY"

    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_HYPERLIQUID_SP500_SOURCE_GATE_RECEIPT_V03.json").write_text(
        json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
        "verdict":report["verdict"],
        "perp_dex_count":report.get("perp_dex_count"),
        "all_asset_count":report.get("all_asset_count"),
        "candidate_count":len(report["candidates"]),
        "top_candidates":report["candidates"][:10],
        "live_candidates":live,
        "outcomes_opened":0,
        "live_trading_authorized":False,
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
