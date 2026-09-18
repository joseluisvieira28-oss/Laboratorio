#!/usr/bin/env python3
import csv, gzip, hashlib, io, json, math, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"TARDIS_SOURCE_AUTHORITY_V0.2.json").read_text())
OUT=Path("artifacts/options_expiry_gamma_tardis_source_v02")
OUT.mkdir(parents=True,exist_ok=True)
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"SRC-Crypto-Lab-OEG-TardisSource/0.2","Accept":"application/gzip"})
REQ=AUTH["required_fields"]

def sha256_filelike_bytes(chunks):
    h=hashlib.sha256()
    total=0
    for c in chunks:
        h.update(c); total+=len(c)
    return h.hexdigest(), total

def parse_num(v):
    if v is None:return None
    s=str(v).strip()
    if s=="":return None
    try:
        x=float(s)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def parse_int(v):
    x=parse_num(v)
    return None if x is None else int(x)

def probe(day):
    y,m,d=day.split("-")
    url=f"https://datasets.tardis.dev/v1/deribit/options_chain/{y}/{m}/{d}/OPTIONS.csv.gz"
    target=int(datetime.fromisoformat(day+"T12:00:00+00:00").timestamp()*1_000_000)
    max_stale=AUTH["snapshot_rule"]["maximum_staleness_minutes"]*60*1_000_000
    stop_after=target+AUTH["snapshot_rule"]["stop_reading_after_target_plus_minutes"]*60*1_000_000

    r=SESSION.get(url,stream=True,timeout=90)
    if r.status_code!=200:
        raise RuntimeError(f"HTTP {r.status_code} for {url}")
    h=hashlib.sha256()
    class HashingReader(io.RawIOBase):
        def __init__(self,raw): self.raw=raw
        def readable(self): return True
        def readinto(self,b):
            n=self.raw.readinto(b)
            if n:
                h.update(memoryview(b)[:n])
            return n
    raw=HashingReader(r.raw)
    gz=gzip.GzipFile(fileobj=io.BufferedReader(raw))
    txt=io.TextIOWrapper(gz,encoding="utf-8",newline="")
    reader=csv.DictReader(txt)

    latest={}
    rows=0
    btc_rows=0
    saw_after=False
    for row in reader:
        rows+=1
        ts=parse_int(row.get("timestamp"))
        if ts is None: continue
        if ts>stop_after:
            saw_after=True
            break
        sym=(row.get("symbol") or "").strip().upper()
        if not sym.startswith(AUTH["snapshot_rule"]["symbol_prefix"]): continue
        btc_rows+=1
        if ts<=target:
            prev=latest.get(sym)
            if prev is None or ts>prev["_ts"]:
                row["_ts"]=ts
                latest[sym]=row

    snap=[]
    for sym,row in latest.items():
        stale=target-row["_ts"]
        if stale<0 or stale>max_stale: continue
        snap.append(row)

    n=len(snap)
    if n==0:
        metrics={"snapshot_instruments":0}
        checks={k:False for k in [
          "snapshot_size","expiries","strikes","calls","puts","near_expiry",
          "oi_coverage","gamma_coverage","delta_coverage","mark_iv_coverage",
          "underlying_coverage","freshness_coverage"
        ]}
        return {"date":day,"url":url,"http_status":r.status_code,"compressed_sha256":h.hexdigest(),
                "rows_scanned":rows,"btc_rows_scanned":btc_rows,"metrics":metrics,"gate_checks":checks}

    calls=sum(1 for x in snap if (x.get("type") or "").lower()=="call")
    puts=sum(1 for x in snap if (x.get("type") or "").lower()=="put")
    expiries={parse_int(x.get("expiration")) for x in snap if parse_int(x.get("expiration")) is not None}
    strikes={parse_num(x.get("strike_price")) for x in snap if parse_num(x.get("strike_price")) is not None}
    target_dt=datetime.fromtimestamp(target/1_000_000,tz=timezone.utc)
    near=0
    for e in expiries:
        edt=datetime.fromtimestamp(e/1_000_000,tz=timezone.utc)
        dte=(edt-target_dt).total_seconds()/86400.0
        if 0<dte<=14: near+=1

    def cov(field):
        if field in ("type","symbol"):
            return sum(1 for x in snap if str(x.get(field) or "").strip()!="")/n
        return sum(1 for x in snap if parse_num(x.get(field)) is not None)/n

    freshness=sum(1 for x in snap if 0<=target-x["_ts"]<=max_stale)/n
    metrics={
      "snapshot_instruments":n,
      "calls":calls,
      "puts":puts,
      "distinct_expiries":len(expiries),
      "distinct_strikes":len(strikes),
      "expiries_within_14d":near,
      "open_interest_coverage":cov("open_interest"),
      "gamma_coverage":cov("gamma"),
      "delta_coverage":cov("delta"),
      "mark_iv_coverage":cov("mark_iv"),
      "underlying_price_coverage":cov("underlying_price"),
      "freshness_coverage":freshness
    }
    g=AUTH["per_date_gates"]
    checks={
      "snapshot_size":n>=g["minimum_snapshot_instruments"],
      "expiries":len(expiries)>=g["minimum_distinct_expiries"],
      "strikes":len(strikes)>=g["minimum_distinct_strikes"],
      "calls":calls>0 if g["require_calls"] else True,
      "puts":puts>0 if g["require_puts"] else True,
      "near_expiry":near>0 if g["require_expiry_within_14_days"] else True,
      "oi_coverage":metrics["open_interest_coverage"]>=g["open_interest_coverage_minimum"],
      "gamma_coverage":metrics["gamma_coverage"]>=g["gamma_coverage_minimum"],
      "delta_coverage":metrics["delta_coverage"]>=g["delta_coverage_minimum"],
      "mark_iv_coverage":metrics["mark_iv_coverage"]>=g["mark_iv_coverage_minimum"],
      "underlying_coverage":metrics["underlying_price_coverage"]>=g["underlying_price_coverage_minimum"],
      "freshness_coverage":metrics["freshness_coverage"]>=g["freshness_coverage_minimum"]
    }
    return {"date":day,"url":url,"http_status":r.status_code,"compressed_sha256":h.hexdigest(),
            "rows_scanned":rows,"btc_rows_scanned":btc_rows,"stopped_after_target":saw_after,
            "metrics":metrics,"gate_checks":checks}

result={
 "lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":None,
 "api_key_used":False,"subscription_purchase":False,"open_interest_values_retained":False,
 "gamma_values_retained":False,"gamma_exposure_computed":False,"dealer_position_sign_computed":False,
 "btc_price_outcomes_opened":False,"returns_opened":False,"pnl_opened":False,
 "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False
}
try:
    probes=[]
    for i,day in enumerate(AUTH["deterministic_probe_dates"],1):
        p=probe(day);probes.append(p)
        print(f"TARDIS_GAMMA_SOURCE_PROGRESS {i}/{len(AUTH['deterministic_probe_dates'])} {day} pass={all(p['gate_checks'].values())}",flush=True)
    ok=all(all(p["gate_checks"].values()) for p in probes)
    result["classification"]=AUTH["classifications"]["pass"] if ok else AUTH["classifications"]["insufficient"]
    result["all_probe_dates_pass"]=ok
    result["probe_count"]=len(probes)
    result["probes"]=probes
except Exception as e:
    result["classification"]=AUTH["classifications"]["technical_failure"]
    result["error"]=repr(e)

p=OUT/"tardis_source_probe_result.json"
p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
manifest={
 "authority_sha256":hashlib.sha256((ROOT/"TARDIS_SOURCE_AUTHORITY_V0.2.json").read_bytes()).hexdigest(),
 "result_sha256":hashlib.sha256(p.read_bytes()).hexdigest()
}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="probes"},indent=2,sort_keys=True))
if "probes" in result:
    for p0 in result["probes"]:
        print(json.dumps({"date":p0["date"],"metrics":p0["metrics"],"gate_checks":p0["gate_checks"]},sort_keys=True))
sys.exit(2 if result["classification"]==AUTH["classifications"]["technical_failure"] else 0)
