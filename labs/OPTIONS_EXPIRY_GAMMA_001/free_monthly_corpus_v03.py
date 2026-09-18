#!/usr/bin/env python3
import argparse,csv,gzip,hashlib,io,json,math,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import requests

ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"FREE_MONTHLY_CORPUS_AUTHORITY_V0.3.json").read_text())
OUT=Path("artifacts/options_expiry_gamma_free_corpus_v03")
OUT.mkdir(parents=True,exist_ok=True)
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"SRC-Crypto-Lab-OEG-FreeCorpus/0.3","Accept":"application/gzip"})

def parse_num(v):
    if v is None:return None
    s=str(v).strip()
    if not s:return None
    try:
        x=float(s);return x if math.isfinite(x) else None
    except Exception:return None

def parse_int(v):
    x=parse_num(v);return None if x is None else int(x)

def probe(day):
    y,m,d=day.split("-")
    url=f"https://datasets.tardis.dev/v1/deribit/options_chain/{y}/{m}/{d}/OPTIONS.csv.gz"
    target=int(datetime.fromisoformat(day+"T12:00:00+00:00").timestamp()*1_000_000)
    max_stale=AUTH["snapshot_rule"]["maximum_staleness_minutes"]*60*1_000_000
    stop_after=target+AUTH["snapshot_rule"]["stop_reading_after_target_plus_minutes"]*60*1_000_000
    r=SESSION.get(url,stream=True,timeout=120)
    if r.status_code!=200:
        return {"date":day,"url":url,"http_status":r.status_code,"technical_error":f"HTTP {r.status_code}","pass":False}
    h=hashlib.sha256()
    class HashingReader(io.RawIOBase):
        def __init__(self,raw): self.raw=raw
        def readable(self): return True
        def readinto(self,b):
            n=self.raw.readinto(b)
            if n: h.update(memoryview(b)[:n])
            return n
    txt=io.TextIOWrapper(gzip.GzipFile(fileobj=io.BufferedReader(HashingReader(r.raw))),encoding="utf-8",newline="")
    reader=csv.DictReader(txt)
    latest={}; rows=0; btc_rows=0
    for row in reader:
        rows+=1
        ts=parse_int(row.get("timestamp"))
        if ts is None: continue
        if ts>stop_after: break
        sym=(row.get("symbol") or "").strip().upper()
        if not sym.startswith(AUTH["snapshot_rule"]["symbol_prefix"]): continue
        btc_rows+=1
        if ts<=target:
            prev=latest.get(sym)
            if prev is None or ts>prev["_ts"]:
                row["_ts"]=ts;latest[sym]=row
    snap=[row for row in latest.values() if 0<=target-row["_ts"]<=max_stale]
    n=len(snap)
    def cov(field):
        if n==0:return 0.0
        return sum(1 for x in snap if parse_num(x.get(field)) is not None)/n
    calls=sum(1 for x in snap if (x.get("type") or "").lower()=="call")
    puts=sum(1 for x in snap if (x.get("type") or "").lower()=="put")
    expiries={parse_int(x.get("expiration")) for x in snap if parse_int(x.get("expiration")) is not None}
    strikes={parse_num(x.get("strike_price")) for x in snap if parse_num(x.get("strike_price")) is not None}
    target_dt=datetime.fromtimestamp(target/1_000_000,tz=timezone.utc)
    near=0
    for e in expiries:
        edt=datetime.fromtimestamp(e/1_000_000,tz=timezone.utc)
        dte=(edt-target_dt).total_seconds()/86400.0
        if 0<dte<=14:near+=1
    freshness=(sum(1 for x in snap if 0<=target-x["_ts"]<=max_stale)/n) if n else 0.0
    metrics={
      "snapshot_instruments":n,"calls":calls,"puts":puts,"distinct_expiries":len(expiries),
      "distinct_strikes":len(strikes),"expiries_within_14d":near,
      "open_interest_coverage":cov("open_interest"),"gamma_coverage":cov("gamma"),
      "delta_coverage":cov("delta"),"mark_iv_coverage":cov("mark_iv"),
      "underlying_price_coverage":cov("underlying_price"),"freshness_coverage":freshness
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
      "rows_scanned":rows,"btc_rows_scanned":btc_rows,"metrics":metrics,"gate_checks":checks,"pass":all(checks.values())}

def shard_mode(idx):
    dates=[d for i,d in enumerate(AUTH["deterministic_dates"]) if i%AUTH["shard_count"]==idx]
    probes=[]
    for i,day in enumerate(dates,1):
        try:p=probe(day)
        except Exception as e:p={"date":day,"technical_error":repr(e),"pass":False}
        probes.append(p);print(f"FREE_GAMMA_CORPUS_PROGRESS shard={idx} {i}/{len(dates)} {day} pass={p.get('pass')}",flush=True)
    result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"shard":idx,"dates":dates,"probes":probes,
      "access_2025":False,"access_2026":False,"api_key_used":False,"subscription_purchase":False,
      "open_interest_values_retained":False,"gamma_values_retained":False,"gamma_exposure_computed":False,
      "dealer_position_sign_computed":False,"btc_price_outcomes_opened":False,"returns_opened":False,"pnl_opened":False,
      "live_trading":False,"exchange_mutation":False,"merge_to_main":False}
    p=OUT/f"shard_{idx}.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return 0

def aggregate_mode(input_dir):
    files=sorted(Path(input_dir).rglob("shard_*.json"))
    if len(files)!=AUTH["shard_count"]:raise RuntimeError(f"expected {AUTH['shard_count']} shards, found {len(files)}")
    probes=[];seen=set()
    for f in files:
        obj=json.loads(f.read_text())
        for p in obj["probes"]:
            if p["date"] in seen:raise RuntimeError(f"duplicate date {p['date']}")
            seen.add(p["date"]);probes.append(p)
    probes=sorted(probes,key=lambda x:x["date"])
    if [p["date"] for p in probes]!=AUTH["deterministic_dates"]:raise RuntimeError("date coverage mismatch")
    passing=[p for p in probes if p.get("pass") is True]
    byyear=Counter(p["date"][:4] for p in passing)
    near=sum(1 for p in probes if (p.get("metrics") or {}).get("expiries_within_14d",0)>0)
    agg_inst=sum((p.get("metrics") or {}).get("snapshot_instruments",0) for p in probes)
    technical=sum(1 for p in probes if p.get("technical_error"))
    g=AUTH["aggregate_gates"]
    checks={
      "passing_dates_ge_min":len(passing)>=g["minimum_total_passing_dates"],
      "passing_dates_per_year_ge_min":all(byyear.get(str(y),0)>=g["minimum_passing_dates_per_calendar_year"] for y in range(2021,2025)),
      "near_expiry_dates_ge_min":near>=g["minimum_dates_with_near_expiry"],
      "distinct_years_ge_min":len([y for y,n in byyear.items() if n>0])>=g["minimum_distinct_calendar_years"],
      "aggregate_instruments_ge_min":agg_inst>=g["minimum_aggregate_snapshot_instruments"],
      "technical_errors_eq_zero":technical==0
    }
    cls=AUTH["classifications"]["pass"] if all(checks.values()) else AUTH["classifications"]["insufficient"]
    result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":cls,
      "total_dates":len(probes),"passing_dates":len(passing),"passing_dates_by_year":dict(sorted(byyear.items())),
      "dates_with_near_expiry":near,"aggregate_snapshot_instruments":agg_inst,"technical_error_dates":technical,
      "aggregate_gate_checks":checks,
      "access_2025":False,"access_2026":False,"api_key_used":False,"subscription_purchase":False,
      "open_interest_values_retained":False,"gamma_values_retained":False,"gamma_exposure_computed":False,
      "dealer_position_sign_computed":False,"btc_price_outcomes_opened":False,"returns_opened":False,"pnl_opened":False,
      "live_trading":False,"exchange_mutation":False,"merge_to_main":False}
    p=OUT/"aggregate.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    manifest={"authority_sha256":hashlib.sha256((ROOT/"FREE_MONTHLY_CORPUS_AUTHORITY_V0.3.json").read_bytes()).hexdigest(),
      "result_sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--shard",type=int);ap.add_argument("--aggregate-dir")
    a=ap.parse_args()
    if a.aggregate_dir:return aggregate_mode(a.aggregate_dir)
    if a.shard is None or not (0<=a.shard<AUTH["shard_count"]):raise SystemExit("valid --shard required")
    return shard_mode(a.shard)
if __name__=="__main__":sys.exit(main())
