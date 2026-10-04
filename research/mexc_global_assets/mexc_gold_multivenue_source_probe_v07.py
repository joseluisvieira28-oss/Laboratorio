#!/usr/bin/env python3
"""MEXC GOLD multi-venue public source gate V0.7."""
from __future__ import annotations
import hashlib,json,io,zipfile,csv,gzip
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/gold_multivenue_source_gate_v07")
UA="CryptoLab-MEXC-GOLD-MultiVenue/0.7"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def get(url,params=None):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    meta={"url":r.url,"status_code":r.status_code,"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw)}
    if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code}: {r.url}: {raw[:300]!r}")
    return raw,r.json(),meta

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def f(x):
    try: return float(x)
    except Exception: return None

def main():
    report={"lab":"MEXC_GOLD_MULTIVENUE_SOURCE_GATE_V0_7","captured_at_utc":now(),
            "source_only":True,"outcomes_opened":0,"auth_used":False,
            "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
            "orders":False,"exchange_mutation":False,"venues":{}}

    raw,j,m=get("https://api.mexc.com/api/v1/contract/detail",{"symbol":"XAU_USDT"})
    save("mexc_xau_detail.json",raw,m)
    if j.get("success") is not True: raise RuntimeError(f"MEXC detail non-success:{j}")
    d=j.get("data")
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="XAU_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_XAU_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in ["symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate","takerFeeRate","contractSize"]}

    raw,j,m=get("https://api.mexc.com/api/v1/contract/index_price/XAU_USDT")
    save("mexc_xau_index.json",raw,m)
    if j.get("success") is not True: raise RuntimeError(f"MEXC index non-success:{j}")
    md=j.get("data") or {}
    mexc=f(md.get("indexPrice") if md.get("indexPrice") is not None else md.get("price"))
    if not mexc: raise RuntimeError("MEXC_XAU_INDEX_MISSING")
    report["mexc_index_price"]=mexc
    report["mexc_index_timestamp"]=md.get("timestamp")

    # Binance official public archive. Direct fapi is geo-blocked from GitHub-hosted runners.
    burl="https://data.binance.vision/data/futures/um/daily/klines/XAUUSDT/1m/XAUUSDT-1m-2026-09-30.zip"
    br=requests.get(burl,headers={"User-Agent":UA},timeout=30)
    braw=br.content
    bm={"url":burl,"status_code":br.status_code,"captured_at_utc":now(),"sha256":sha(braw),"bytes":len(braw)}
    if br.status_code!=200: raise RuntimeError(f"BINANCE_VISION_HTTP_{br.status_code}:{braw[:200]!r}")
    save("binance_xau_2026-09-30_1m.zip",braw,bm)
    z=zipfile.ZipFile(io.BytesIO(braw))
    names=z.namelist()
    if len(names)!=1 or "XAUUSDT-1m-2026-09-30" not in names[0]:
        raise RuntimeError(f"BINANCE_VISION_ZIP_IDENTITY_FAIL:{names}")
    rows=list(csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")))
    if len(rows)<100: raise RuntimeError(f"BINANCE_VISION_TOO_FEW_ROWS:{len(rows)}")
    report["venues"]["BINANCE"]={"archive_url":burl,"archive_sha256":bm["sha256"],"csv_file":names[0],"row_count":len(rows),"verification_date":"2026-09-30","outcome_scored":False}

    # Bybit public trading-history archive. V5 API is geo-blocked from GitHub-hosted runners.
    yurl="https://public.bybit.com/trading/XAUUSDT/XAUUSDT2026-09-30.csv.gz"
    yr=requests.get(yurl,headers={"User-Agent":UA},timeout=60)
    yraw=yr.content
    ym={"url":yurl,"status_code":yr.status_code,"captured_at_utc":now(),"sha256":sha(yraw),"bytes":len(yraw)}
    if yr.status_code!=200: raise RuntimeError(f"BYBIT_PUBLIC_HTTP_{yr.status_code}:{yraw[:200]!r}")
    save("bybit_xau_2026-09-30_trades.csv.gz",yraw,ym)
    try:
        ytxt=gzip.decompress(yraw).decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"BYBIT_PUBLIC_GZIP_FAIL:{e!r}")
    yrows=list(csv.reader(io.StringIO(ytxt)))
    if len(yrows)<100: raise RuntimeError(f"BYBIT_PUBLIC_TOO_FEW_ROWS:{len(yrows)}")
    header=[x.strip().lower() for x in yrows[0]]
    if "price" not in header or "timestamp" not in header:
        raise RuntimeError(f"BYBIT_PUBLIC_SCHEMA_FAIL:{yrows[0]}")
    report["venues"]["BYBIT"]={"archive_url":yurl,"archive_sha256":ym["sha256"],"row_count":len(yrows)-1,
                                  "header":yrows[0],"verification_date":"2026-09-30","outcome_scored":False}

    # Bitget
    raw,g,m=get("https://api.bitget.com/api/v2/mix/market/ticker",{"symbol":"XAUUSDT","productType":"USDT-FUTURES"})
    save("bitget_xau_ticker.json",raw,m)
    if g.get("code")!="00000": raise RuntimeError(f"BITGET_NONZERO:{g}")
    gl=g.get("data") or []
    if not gl: raise RuntimeError("BITGET_XAU_MISSING")
    gg=gl[0]
    gb,ga=f(gg.get("bidPr")),f(gg.get("askPr"))
    gmid=(gb+ga)/2 if gb and ga else f(gg.get("lastPr"))
    report["venues"]["BITGET"]={"bid":gb,"ask":ga,"mid":gmid,"last":f(gg.get("lastPr")),"time":gg.get("ts")}

    # Historical transport verification day: 2026-09-30 only, outside future discovery.
    verify_start_ms=1790726400000
    verify_end_ms=1790729940000

    raw,bh,bhm=get("https://api.bitget.com/api/v2/mix/market/candles",{
        "symbol":"XAUUSDT","productType":"USDT-FUTURES","granularity":"1m",
        "startTime":str(verify_start_ms),"endTime":str(verify_end_ms),"limit":"1000"
    })
    save("bitget_xau_2026-09-30_history_probe.json",raw,bhm)
    if bh.get("code")!="00000": raise RuntimeError(f"BITGET_HISTORY_NONZERO:{bh}")
    bdata=bh.get("data") or []
    if len(bdata)<30: raise RuntimeError(f"BITGET_HISTORY_TOO_FEW_ROWS:{len(bdata)}")
    report["venues"]["BITGET"]["history_probe"]={
        "row_count":len(bdata),"verification_date":"2026-09-30","outcome_scored":False,
        "first_ts":bdata[-1][0] if bdata else None,"last_ts":bdata[0][0] if bdata else None
    }

    verify_start_s=verify_start_ms//1000
    verify_end_s=verify_end_ms//1000
    raw,mh,mhm=get("https://api.mexc.com/api/v1/contract/kline/XAU_USDT",{
        "interval":"Min1","start":str(verify_start_s),"end":str(verify_end_s)
    })
    save("mexc_xau_2026-09-30_history_probe.json",raw,mhm)
    if mh.get("success") is not True: raise RuntimeError(f"MEXC_HISTORY_NON_SUCCESS:{mh}")
    mdh=mh.get("data") or {}
    mts=mdh.get("time") or []
    mcl=mdh.get("close") or []
    if len(mts)<30 or len(mcl)!=len(mts):
        raise RuntimeError(f"MEXC_HISTORY_STRUCTURE_FAIL:{len(mts)}:{len(mcl)}")
    report["mexc_history_probe"]={
        "row_count":len(mts),"verification_date":"2026-09-30","outcome_scored":False,
        "first_ts":mts[0] if mts else None,"last_ts":mts[-1] if mts else None
    }

    expected={"BINANCE","BITGET","BYBIT"}
    raw_origin=[str(x).upper() for x in (d.get("indexOrigin") or [])]
    aliases={
      "BINANCE_FUTURE":"BINANCE",
      "BITGET_FUTURE":"BITGET",
      "BYBIT_FUTURE":"BYBIT",
      "BINANCETICKER":"BINANCE",
    }
    origin=set(aliases.get(x,x) for x in raw_origin)
    report["mexc_index_origin_raw"]=raw_origin
    report["mexc_index_origin_normalized"]=sorted(origin)
    report["expected_origins"]=sorted(expected)

    scale={
      "BITGET":10000*(mexc/gmid-1) if gmid and gmid>0 else None,
    }
    report["mexc_vs_external_mid_bps"]=scale

    gates={
      "index_origin_contains_expected": expected.issubset(origin),
      "binance_official_archive_accessible": report["venues"]["BINANCE"]["row_count"]>=100,
      "bybit_public_archive_accessible": report["venues"]["BYBIT"]["row_count"]>=100,
      "bitget_public_bbo": gmid is not None,
      "bitget_historical_1m_accessible": report["venues"]["BITGET"]["history_probe"]["row_count"]>=30,
      "mexc_historical_1m_accessible": report["mexc_history_probe"]["row_count"]>=30,
      "bitget_scale_within_500bps": scale["BITGET"] is not None and abs(scale["BITGET"])<500,
    }
    report["gates"]=gates
    report["verdict"]="MEXC_GOLD_MULTIVENUE_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_MEXC_GOLD_MULTIVENUE"
    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_GOLD_MULTIVENUE_SOURCE_GATE_RECEIPT_V07.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
