#!/usr/bin/env python3
"""ARQ-002-CSP-001 official Binance source-only probe.

Strictly outcome-blind:
- verifies checksums, ZIP/CSV structure, identities and timestamps only;
- never reports price, quantity, OI, funding, CVD or return values;
- never requests 2025/2026.
"""
from __future__ import annotations

import csv, hashlib, io, json, re, statistics, sys, time, urllib.error, urllib.request, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um"
SYMBOL="BTCUSDT"
DATES=("2022-06-15","2023-06-15","2024-06-15")
OUT=Path("arq002_csp_source_probe_receipt.json")
UA="Crypto-Lab-ARQ002-CSP-SourceProbe/0.1"
PROTECTED_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)

METRICS_REQUIRED={
    "create_time","symbol","sum_open_interest","sum_open_interest_value",
    "count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio",
    "count_long_short_ratio","sum_taker_long_short_vol_ratio",
}
FUND_TIME=("calc_time","fundingTime","funding_time")
FUND_RATE=("last_funding_rate","fundingRate","funding_rate")

class GateError(RuntimeError): pass

def req(url:str, attempts:int=5)->bytes:
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=90) as x:
                if x.status!=200: raise GateError(f"HTTP_{x.status}:{url}")
                return x.read()
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(8,1.5*(i+1)))
    code=getattr(last,"code",None)
    raise GateError(f"DOWNLOAD_FAILED:{code}:{url}:{type(last).__name__}:{last}")

def checksum(url:str)->str:
    raw=req(url+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",raw)
    if not m: raise GateError(f"CHECKSUM_PARSE:{url}")
    return m.group(1).lower()

def verified(url:str)->tuple[bytes,str]:
    raw=req(url)
    pub=checksum(url)
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=pub: raise GateError(f"CHECKSUM_MISMATCH:{url}")
    return raw,actual

def one_csv(raw:bytes,url:str)->list[list[str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            bad=z.testzip()
            if bad: raise GateError(f"ZIP_CRC:{url}:{bad}")
            names=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
            if len(names)!=1: raise GateError(f"CSV_COUNT:{url}:{len(names)}")
            text=z.read(names[0]).decode("utf-8-sig","strict")
    except zipfile.BadZipFile as e:
        raise GateError(f"BAD_ZIP:{url}:{e}")
    return [r for r in csv.reader(io.StringIO(text)) if r and any(c.strip() for c in r)]

def to_ms(v:str)->int:
    s=v.strip()
    try:
        x=float(s)
        if x>1e14: return int(x/1000)
        if x>1e11: return int(x)
        if x>1e9: return int(x*1000)
    except ValueError:
        pass
    dt=datetime.fromisoformat(s.replace("Z","+00:00"))
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp()*1000)

def iso(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")

def quantiles_ms(ts:list[int])->dict:
    if len(ts)<2: return {"median_ms":None,"p95_ms":None}
    diffs=[b-a for a,b in zip(ts,ts[1:]) if b>=a]
    if not diffs: return {"median_ms":None,"p95_ms":None}
    s=sorted(diffs)
    med=statistics.median(s)
    p95=s[min(len(s)-1,max(0,int(0.95*len(s))-1))]
    return {"median_ms":med,"p95_ms":p95}

def exact_duplicate_conflicts(rows:list[list[str]], key_index:int)->tuple[int,int]:
    groups={}
    for r in rows:
        k=r[key_index]
        groups.setdefault(k,[]).append(r)
    exact_removed=0
    conflicts=0
    for rs in groups.values():
        if len(rs)<=1: continue
        u={tuple(x) for x in rs}
        if len(u)==1: exact_removed+=len(rs)-1
        else: conflicts+=1
    return exact_removed,conflicts

def parse_agg(raw:bytes,url:str,day:str)->dict:
    rows=one_csv(raw,url)
    if not rows: raise GateError(f"AGG_EMPTY:{day}")
    body=rows
    headerless=True
    try: int(float(rows[0][0]))
    except Exception:
        headerless=False
        body=rows[1:]
    if not body or any(len(r)<7 for r in body): raise GateError(f"AGG_SCHEMA:{day}")
    ids=[]
    ts=[]
    bool_ok=True
    for r in body:
        ids.append(int(float(r[0])))
        ts.append(to_ms(r[5]))
        bool_ok &= r[6].strip().lower() in {"true","false"}
    if any(x>=PROTECTED_MS for x in ts): raise GateError(f"PROTECTED_TS:agg:{day}")
    if ids!=sorted(ids): raise GateError(f"AGG_ID_ORDER:{day}")
    if len(ids)!=len(set(ids)): raise GateError(f"AGG_DUP_ID:{day}")
    lo=to_ms(day+"T00:00:00Z"); hi=lo+86_400_000
    if min(ts)<lo or max(ts)>=hi: raise GateError(f"AGG_DAY_SCOPE:{day}")
    q=quantiles_ms(ts)
    return {
        "dataset":"aggTrades","date":day,"row_count":len(body),
        "headerless":headerless,"columns_per_row_min":min(len(r) for r in body),
        "first_timestamp_utc":iso(min(ts)),"last_timestamp_utc":iso(max(ts)),
        "aggregate_trade_id_unique":True,"buyer_maker_boolean_parseable":bool_ok,
        "timestamp_duplicate_count":len(ts)-len(set(ts)),
        "interarrival_median_ms":q["median_ms"],"interarrival_p95_ms":q["p95_ms"],
        "economic_values_reported":False
    }

def parse_kline(raw:bytes,url:str,day:str)->dict:
    rows=one_csv(raw,url)
    body=rows
    headerless=True
    try: to_ms(rows[0][0])
    except Exception:
        headerless=False; body=rows[1:]
    if not body or any(len(r)<12 for r in body): raise GateError(f"KLINE_SCHEMA:{day}")
    ts=[to_ms(r[0]) for r in body]
    if any(x>=PROTECTED_MS for x in ts): raise GateError(f"PROTECTED_TS:kline:{day}")
    lo=to_ms(day+"T00:00:00Z")
    expected=[lo+i*60_000 for i in range(1440)]
    if ts!=expected: raise GateError(f"KLINE_GRID:{day}:{len(ts)}/1440")
    return {
        "dataset":"klines_1m","date":day,"row_count":len(body),
        "headerless":headerless,"columns_per_row_min":min(len(r) for r in body),
        "first_timestamp_utc":iso(ts[0]),"last_timestamp_utc":iso(ts[-1]),
        "duplicate_timestamp_count":0,"exact_1m_grid":True,
        "economic_values_reported":False
    }

def parse_metrics(raw:bytes,url:str,day:str)->dict:
    rows=one_csv(raw,url)
    if len(rows)<2: raise GateError(f"METRICS_EMPTY:{day}")
    h=[x.strip() for x in rows[0]]
    miss=sorted(METRICS_REQUIRED.difference(h))
    if miss: raise GateError(f"METRICS_SCHEMA:{day}:{miss}")
    ti=h.index("create_time"); si=h.index("symbol")
    body=rows[1:]
    if any(len(r)<=max(ti,si) for r in body): raise GateError(f"METRICS_WIDTH:{day}")
    if any(r[si].strip()!=SYMBOL for r in body): raise GateError(f"METRICS_SYMBOL:{day}")
    ts=[to_ms(r[ti]) for r in body]
    if any(x>=PROTECTED_MS for x in ts): raise GateError(f"PROTECTED_TS:metrics:{day}")
    lo=to_ms(day+"T00:00:00Z"); hi=lo+86_400_000
    if min(ts)<lo or max(ts)>=hi: raise GateError(f"METRICS_DAY_SCOPE:{day}")
    exact_removed,conflicts=exact_duplicate_conflicts(body,ti)
    if conflicts: raise GateError(f"METRICS_CONFLICTING_DUP_GROUPS:{day}:{conflicts}")
    unique_ts=sorted(set(ts))
    q=quantiles_ms(unique_ts)
    return {
        "dataset":"metrics","date":day,"raw_row_count":len(body),
        "unique_timestamp_count":len(unique_ts),
        "exact_duplicate_rows":exact_removed,"conflicting_duplicate_group_count":conflicts,
        "first_timestamp_utc":iso(min(unique_ts)),"last_timestamp_utc":iso(max(unique_ts)),
        "cadence_median_ms":q["median_ms"],"cadence_p95_ms":q["p95_ms"],
        "required_oi_schema_present":True,"economic_values_reported":False
    }

def find_alias(h:list[str],aliases:tuple[str,...],label:str)->int:
    for a in aliases:
        if a in h: return h.index(a)
    raise GateError(f"{label}_MISSING:{h}")

def parse_funding(raw:bytes,url:str,ym:str)->dict:
    rows=one_csv(raw,url)
    if len(rows)<2: raise GateError(f"FUND_EMPTY:{ym}")
    h=[x.strip() for x in rows[0]]
    ti=find_alias(h,FUND_TIME,"FUND_TIME")
    find_alias(h,FUND_RATE,"FUND_RATE")
    body=rows[1:]
    if any(len(r)<=ti for r in body): raise GateError(f"FUND_WIDTH:{ym}")
    ts=[to_ms(r[ti]) for r in body]
    if any(x>=PROTECTED_MS for x in ts): raise GateError(f"PROTECTED_TS:fund:{ym}")
    if len(ts)!=len(set(ts)): raise GateError(f"FUND_DUP_TS:{ym}")
    q=quantiles_ms(sorted(ts))
    return {
        "dataset":"fundingRate","month":ym,"row_count":len(body),
        "first_timestamp_utc":iso(min(ts)),"last_timestamp_utc":iso(max(ts)),
        "timestamp_unique":True,"cadence_median_ms":q["median_ms"],"cadence_p95_ms":q["p95_ms"],
        "rate_column_present":True,"economic_values_reported":False
    }

def main()->int:
    rec={
        "lab_id":"ARQ-002-CSP-001","gate":"SOURCE_PROBE_V0.1",
        "classification":"RUNNING","objects":[],
        "economic_values_reported":False,"outcomes_opened":False,
        "protected_2025_accessed":False,"protected_2026_accessed":False,
        "live_trading":False,"exchange_mutation":False,"errors":[]
    }
    try:
        seen_funding=set()
        for day in DATES:
            ym=day[:7]
            urls=[
                ("agg",f"{BASE}/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{day}.zip"),
                ("kline",f"{BASE}/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{day}.zip"),
                ("metrics",f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{day}.zip"),
            ]
            for typ,url in urls:
                raw,sha=verified(url)
                if typ=="agg": meta=parse_agg(raw,url,day)
                elif typ=="kline": meta=parse_kline(raw,url,day)
                else: meta=parse_metrics(raw,url,day)
                meta.update({"url":url,"sha256":sha,"checksum_verified":True})
                rec["objects"].append(meta)
            if ym not in seen_funding:
                seen_funding.add(ym)
                url=f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"
                raw,sha=verified(url)
                meta=parse_funding(raw,url,ym)
                meta.update({"url":url,"sha256":sha,"checksum_verified":True})
                rec["objects"].append(meta)
        if len(rec["objects"])!=12: raise GateError(f"OBJECT_COUNT:{len(rec['objects'])}/12")
        if not all(x.get("checksum_verified") for x in rec["objects"]): raise GateError("CHECKSUM_GATE")
        if not all(x.get("economic_values_reported") is False for x in rec["objects"]): raise GateError("ECON_FIREWALL")
        rec["classification"]="SOURCE_DATA_PASS"
    except Exception as e:
        rec["classification"]="SOURCE_OR_TECHNICAL_FAIL_CLOSED"
        rec["errors"].append(f"{type(e).__name__}:{e}")
    rec["receipt_sha256"]=hashlib.sha256(
        json.dumps(rec,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()
    OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "lab_id":rec["lab_id"],"classification":rec["classification"],
        "verified_object_count":sum(1 for x in rec["objects"] if x.get("checksum_verified")),
        "economic_values_reported":False,"outcomes_opened":False,
        "protected_2025_accessed":False,"protected_2026_accessed":False,
        "errors":rec["errors"],"receipt_sha256":rec["receipt_sha256"]
    },sort_keys=True))
    return 0 if rec["classification"]=="SOURCE_DATA_PASS" else 1

if __name__=="__main__":
    sys.exit(main())
