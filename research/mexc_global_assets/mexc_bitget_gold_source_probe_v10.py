#!/usr/bin/env python3
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import requests
OUT=Path("artifacts/mexc_global_assets/gold_bitget_source_gate_v10")
MEXC="https://api.mexc.com"; BITGET="https://api.bitget.com"; UA="CryptoLab-Gold-Bitget-SourceGate/1.0"
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def get(url,params=None):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30); raw=r.content
    meta={"url":r.url,"status_code":r.status_code,"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw)}
    if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{raw[:250]!r}")
    return raw,r.json(),meta
def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True); (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True))
def ff(x):
    try:return float(x)
    except:return None
def main():
    rep={"lab":"MEXC_BITGET_GOLD_SOURCE_GATE_V1_0","source_only":True,"outcomes_opened":0,
         "auth_used":False,"account_reads":False,"orders":False,"exchange_mutation":False}
    raw,j,m=get(MEXC+"/api/v1/contract/detail",{"symbol":"XAU_USDT"}); save("mexc_detail.json",raw,m)
    d=j.get("data"); 
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="XAU_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_XAU_MISSING")
    rep["mexc_detail"]={k:d.get(k) for k in ["symbol","displayName","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate","takerFeeRate","contractSize"]}
    raw,j,m=get(MEXC+"/api/v1/contract/index_price/XAU_USDT"); save("mexc_index.json",raw,m)
    mi=j.get("data") or {}; mp=ff(mi.get("indexPrice")); rep["mexc_index"]={"price":mp,"timestamp":mi.get("timestamp")}
    now_s=int(time.time())
    raw,j,m=get(MEXC+"/api/v1/contract/kline/XAU_USDT",{"interval":"Min1","start":now_s-900,"end":now_s}); save("mexc_kline.json",raw,m)
    mr=len((j.get("data") or {}).get("time") or []); rep["mexc_kline_rows"]=mr

    raw,j,m=get(BITGET+"/api/v2/mix/market/contracts",{"productType":"USDT-FUTURES","symbol":"XAUUSDT"}); save("bitget_contract.json",raw,m)
    data=j.get("data") if isinstance(j,dict) and j.get("code")=="00000" else []
    exact=[x for x in (data or []) if str(x.get("symbol","")).upper()=="XAUUSDT"]
    if len(exact)!=1: raise RuntimeError(f"BITGET_XAU_IDENTITY_FAIL:{len(exact)}")
    bc=exact[0]; rep["bitget_contract"]={k:bc.get(k) for k in ["symbol","baseCoin","quoteCoin","symbolType","symbolStatus","makerFeeRate","takerFeeRate","isRwa","minTradeUSDT"]}
    raw,j,m=get(BITGET+"/api/v2/mix/market/ticker",{"productType":"USDT-FUTURES","symbol":"XAUUSDT"}); save("bitget_ticker.json",raw,m)
    tr=(j.get("data") or [{}])[0]; bid=ff(tr.get("bidPr")); ask=ff(tr.get("askPr")); last=ff(tr.get("lastPr")); mid=(bid+ask)/2 if bid and ask else last
    rep["bitget_ticker"]={"bid":bid,"ask":ask,"last":last,"mid":mid,"ts":tr.get("ts")}
    raw,j,m=get(BITGET+"/api/v2/mix/market/candles",{"productType":"USDT-FUTURES","symbol":"XAUUSDT","granularity":"1m","limit":"5"}); save("bitget_kline.json",raw,m)
    br=len(j.get("data") or []) if isinstance(j,dict) and j.get("code")=="00000" else 0; rep["bitget_kline_rows"]=br
    rel=10000*(mp/mid-1) if mp and mid else None; rep["mexc_index_vs_bitget_mid_bps"]=rel
    origin=rep["mexc_detail"].get("indexOrigin")
    gates={
      "mexc_exact":rep["mexc_detail"].get("symbol")=="XAU_USDT",
      "bitget_exact":bc.get("symbol")=="XAUUSDT",
      "bitget_xau_identity":str(bc.get("baseCoin","")).upper()=="XAU",
      "mexc_origin_contains_bitget":isinstance(origin,list) and any("BITGET" in str(x).upper() for x in origin),
      "mexc_live":mp is not None and mp>0,
      "bitget_live":mid is not None and mid>0,
      "scale_within_500bps":rel is not None and abs(rel)<500,
      "mexc_1m":mr>0,"bitget_1m":br>0
    }
    rep["gates"]=gates; rep["verdict"]="MEXC_BITGET_GOLD_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_MEXC_BITGET_GOLD"
    rep["live_trading_authorized"]=False
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_BITGET_GOLD_SOURCE_GATE_RECEIPT_V10.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps(rep,indent=2,sort_keys=True))
if __name__=="__main__": main()
