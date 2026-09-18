#!/usr/bin/env python3
"""CED1D AVAX20 V3 bookDepth capacity corroboration V0.1.

Orthogonal capacity evidence for the immutable 357-event 2025 OOS population.
Does not rewrite the prior aggTrades print-visibility FAIL.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,statistics,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,date,timedelta,timezone
from pathlib import Path

SYMBOL="AVAXUSDT"
TARGET="CED1D-0031"
BASE="https://data.binance.vision/data/futures/um/daily/bookDepth"
UA="CED1D-AVAX20-BOOKDEPTH-CAPACITY/0.1"
NOTIONAL=100.0
MAX_AGE_MS=60000
FIRST_WEEK=date(2025,1,6)
END_WEEK_EXCL=date(2025,12,29)

class GateError(RuntimeError): pass

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def pct(xs,p):
    a=sorted(xs)
    if not a:return None
    q=(len(a)-1)*p; lo=math.floor(q); hi=math.ceil(q)
    return a[lo]+(a[hi]-a[lo])*(q-lo)
def week_start(d): return d-timedelta(days=d.weekday())
def complete_week(d): return FIRST_WEEK<=week_start(d)<END_WEEK_EXCL

def parse_ts(v):
    s=str(v).strip()
    if not s: raise GateError("EMPTY_TIMESTAMP")
    try:
        n=int(float(s))
        while n>10**14:n//=1000
        if n>10**11:return n
    except Exception:
        pass
    ss=s.replace("Z","+00:00")
    try:
        dt=datetime.fromisoformat(ss)
    except Exception as e:
        raise GateError(f"TIMESTAMP_PARSE:{s}") from e
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    else: dt=dt.astimezone(timezone.utc)
    return int(dt.timestamp()*1000)

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=120) as r:
            if r.status!=200: raise GateError(f"HTTP_{r.status}:{url}")
            return r.read()
    except Exception as e:
        if isinstance(e,GateError): raise
        raise GateError(f"FETCH_FAIL:{type(e).__name__}:{e}:{url}") from e

def verified_zip(url):
    raw=fetch(url); check=fetch(url+".CHECKSUM").decode("utf-8",errors="replace")
    m=re.search(r"([0-9a-fA-F]{64})",check)
    if not m: raise GateError(f"CHECKSUM_PARSE:{url}")
    expected=m.group(1).lower(); got=sha256_bytes(raw)
    if got!=expected: raise GateError(f"CHECKSUM_MISMATCH:{url}:{got}:{expected}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad is not None: raise GateError(f"ZIP_CRC:{url}:{bad}")
        members=[n for n in z.namelist() if not n.endswith("/")]
        if len(members)!=1: raise GateError(f"ZIP_MEMBER_COUNT:{url}:{len(members)}")
    return raw,got

def scan_bookdepth_zip(raw:bytes,expected_date:date,target_ts:int):
    """Return latest prior snapshot rows at/before target, validating stream."""
    start=int(datetime(expected_date.year,expected_date.month,expected_date.day,tzinfo=timezone.utc).timestamp()*1000)
    end=start+86400000
    best_ts=None; best={}
    last_ts=None; cur_ts=None; cur_pcts=set()
    row_count=0; snapshots=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member=[n for n in z.namelist() if not n.endswith("/")][0]
        rdr=csv.reader(io.TextIOWrapper(z.open(member),encoding="utf-8-sig",newline=""))
        first=True
        for r in rdr:
            if not r or all(not str(x).strip() for x in r): continue
            if first:
                first=False
                if str(r[0]).strip().lower()=="timestamp":
                    if [str(x).strip().lower() for x in r[:4]] != ["timestamp","percentage","depth","notional"]:
                        raise GateError(f"SCHEMA_HEADER:{r[:4]}")
                    continue
            if len(r)<4: raise GateError(f"SHORT_ROW:{r}")
            ts=parse_ts(r[0]); per=float(r[1]); depth=float(r[2]); notion=float(r[3])
            if not(start<=ts<end): raise GateError(f"DATE_BOUNDS:{expected_date}:{ts}")
            if not(math.isfinite(per) and math.isfinite(depth) and math.isfinite(notion) and depth>=0 and notion>=0):
                raise GateError(f"NUMERIC_INVALID:{r[:4]}")
            if last_ts is not None and ts<last_ts: raise GateError(f"TIME_REVERSED:{last_ts}:{ts}")
            if cur_ts!=ts:
                cur_ts=ts; cur_pcts=set(); snapshots+=1
            if per in cur_pcts: raise GateError(f"DUP_PERCENTAGE:{ts}:{per}")
            cur_pcts.add(per); last_ts=ts; row_count+=1
            if ts<=target_ts:
                if best_ts is None or ts>best_ts:
                    best_ts=ts; best={}
                if ts==best_ts:
                    best[per]={"depth":depth,"notional":notion}
    return {"best_ts":best_ts,"bands":best,"rows":row_count,"snapshots":snapshots}

def load_events(ledger:Path):
    rows=[]
    with ledger.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("combination_id")!=TARGET or r.get("status")!="TRADE": continue
            sd=date.fromisoformat(r["signal_day"])
            if not complete_week(sd): continue
            direction=int(float(r["direction"]))
            if direction not in (-1,1): raise GateError("BAD_DIRECTION")
            entry_day=date.fromisoformat(r["entry_day"]); exit_day=date.fromisoformat(r["exit_day"])
            ets=int(datetime(entry_day.year,entry_day.month,entry_day.day,0,1,tzinfo=timezone.utc).timestamp()*1000)
            xts=int(datetime(exit_day.year,exit_day.month,exit_day.day,0,1,tzinfo=timezone.utc).timestamp()*1000)
            rows.append({"event_id":f"{TARGET}:{r['signal_day']}","signal_day":r["signal_day"],"direction":direction,
                         "entry_day":entry_day.isoformat(),"exit_day":exit_day.isoformat(),
                         "entry_ts_ms":ets,"exit_ts_ms":xts})
    rows.sort(key=lambda x:x["signal_day"])
    if len(rows)!=357: raise GateError(f"EVENT_COUNT_NOT_357:{len(rows)}")
    return rows

def make_legs(events):
    legs=[]
    for e in events:
        legs.append({"event_id":e["event_id"],"leg":"ENTRY","day":e["entry_day"],"target_ts_ms":e["entry_ts_ms"],
                     "side":"BUY" if e["direction"]==1 else "SELL"})
        legs.append({"event_id":e["event_id"],"leg":"EXIT","day":e["exit_day"],"target_ts_ms":e["exit_ts_ms"],
                     "side":"SELL" if e["direction"]==1 else "BUY"})
    if len(legs)!=714: raise GateError("LEG_COUNT_NOT_714")
    return legs

def process_day(day_s,day_legs):
    d=date.fromisoformat(day_s)
    if d.year!=2025: raise GateError(f"NON_2025_DAY:{day_s}")
    name=f"{SYMBOL}-bookDepth-{day_s}.zip"; url=f"{BASE}/{SYMBOL}/{name}"
    target=max(int(x["target_ts_ms"]) for x in day_legs)
    try:
        raw,h=verified_zip(url)
        scan=scan_bookdepth_zip(raw,d,target)
        return {"day":day_s,"status":"PASS","sha256":h,"url":url,**scan}
    except Exception as e:
        return {"day":day_s,"status":"FAIL","url":url,"error":f"{type(e).__name__}:{e}",
                "best_ts":None,"bands":{},"rows":0,"snapshots":0}

def load_prior_misses(path):
    misses=set()
    if not path:return misses
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            v=str(r.get("filled","")).strip().lower()
            filled=v in ("true","1")
            if not filled: misses.add((r["event_id"],r["leg"]))
    return misses

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ledger",required=True)
    ap.add_argument("--prior-execution-receipt",required=True)
    ap.add_argument("--prior-execution-legs",required=True)
    ap.add_argument("--one-shot-receipt",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--workers",type=int,default=8)
    a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("OUTPUT_EXISTS")
    out.mkdir(parents=True)

    events=load_events(Path(a.ledger)); legs=make_legs(events); prior_misses=load_prior_misses(a.prior_execution_legs)
    byday=defaultdict(list)
    for x in legs: byday[x["day"]].append(x)

    day_results={}
    with ThreadPoolExecutor(max_workers=max(1,a.workers)) as ex:
        futs={ex.submit(process_day,d,ls):d for d,ls in byday.items()}
        for f in as_completed(futs):
            r=f.result(); day_results[r["day"]]=r
            print(r["day"],r["status"],flush=True)

    assessed=[]
    for leg in legs:
        dr=day_results[leg["day"]]
        best=dr.get("best_ts"); age=(leg["target_ts_ms"]-best) if best is not None else None
        band=1.0 if leg["side"]=="BUY" else -1.0
        row=dr.get("bands",{}).get(band)
        snapshot_ok=dr["status"]=="PASS" and best is not None and 0<=age<=MAX_AGE_MS
        capacity=(float(row["notional"]) if row is not None else None)
        cap_ok=bool(snapshot_ok and capacity is not None and capacity>=NOTIONAL)
        assessed.append({**leg,"source_status":dr["status"],"snapshot_ts_ms":best,"snapshot_age_ms":age,
                         "required_percentage":band,"capacity_notional":capacity,
                         "snapshot_ok":snapshot_ok,"capacity_observed":cap_ok,
                         "prior_aggtrade_print_miss":(leg["event_id"],leg["leg"]) in prior_misses})

    n=len(assessed); snap=sum(x["snapshot_ok"] for x in assessed); cap=sum(x["capacity_observed"] for x in assessed)
    valid_caps=[float(x["capacity_notional"]) for x in assessed if x["capacity_observed"]]
    ages=[float(x["snapshot_age_ms"]) for x in assessed if x["snapshot_ok"]]
    monthly={}
    for m in range(1,13):
        xs=[x for x in assessed if date.fromisoformat(x["day"]).month==m]
        if not xs: continue
        monthly[f"2025-{m:02d}"]={"legs":len(xs),"snapshot_ok":sum(x["snapshot_ok"] for x in xs),
                                  "capacity_ok":sum(x["capacity_observed"] for x in xs),
                                  "capacity_rate":sum(x["capacity_observed"] for x in xs)/len(xs)}
    miss=[x for x in assessed if x["prior_aggtrade_print_miss"]]
    metrics={"legs_required":n,"snapshot_ok":snap,"snapshot_coverage":snap/n,
             "capacity_ok":cap,"capacity_rate":cap/n,
             "min_capacity_notional":min(valid_caps) if valid_caps else None,
             "p05_capacity_notional":pct(valid_caps,.05),"median_capacity_notional":statistics.median(valid_caps) if valid_caps else None,
             "p95_capacity_notional":pct(valid_caps,.95),
             "median_snapshot_age_ms":statistics.median(ages) if ages else None,
             "p95_snapshot_age_ms":pct(ages,.95),"max_snapshot_age_ms":max(ages) if ages else None,
             "months":monthly,
             "prior_print_miss_legs":len(miss),
             "prior_print_miss_capacity_ok":sum(x["capacity_observed"] for x in miss),
             "prior_print_miss_capacity_rate":sum(x["capacity_observed"] for x in miss)/len(miss) if miss else None,
             "daily_source_failures":sum(1 for r in day_results.values() if r["status"]!="PASS")}

    gates={"snapshot_coverage_ge_099":metrics["snapshot_coverage"]>=.99,
           "capacity_rate_ge_099":metrics["capacity_rate"]>=.99,
           "every_active_month_ge_095":all(v["capacity_rate"]>=.95 for v in monthly.values()),
           "no_source_failures":metrics["daily_source_failures"]==0}
    book_pass=all(gates.values())

    prior=json.load(open(a.prior_execution_receipt))
    pm=prior["metrics"]
    prior_econ=(pm["events_complete"]>=300 and pm["mean_base_executable_funded_bps"]>0 and
                pm["pf_base_executable_funded"]>1 and pm["mean_stress_executable_funded_bps"]>=0 and
                pm["mean_total_nonfunding_base_proxy_bps"]<=14 and pm["p95_total_nonfunding_base_proxy_bps"]<=20 and
                pm["median_leg_latency_ms"]<=1000 and pm["p95_leg_latency_ms"]<=5000 and
                pm["concentration"]["ratio"]<=1)
    one=json.load(open(a.one_shot_receipt)); o=one["results"][TARGET]["lower"]
    oos=(one["results"][TARGET]["inference_events"]==357 and o["mean_base_bps"]>0 and o["profit_factor_base"]>1)
    composite=bool(book_pass and prior_econ and oos)

    def write_csv(name,rows):
        fields=sorted({k for r in rows for k in r})
        with (out/name).open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)
    write_csv("AVAX20_BOOKDEPTH_CAPACITY_LEGS.csv",assessed)
    (out/"AVAX20_BOOKDEPTH_SOURCE_DAYS.json").write_text(json.dumps([day_results[k] for k in sorted(day_results)],indent=2,sort_keys=True)+"\n")

    receipt={"document_id":"CED_1D_AVAX20_V3_BOOKDEPTH_CAPACITY_RECEIPT_V0.1",
             "status":"BOOKDEPTH_CAPACITY_PASS" if book_pass else "BOOKDEPTH_CAPACITY_FAIL",
             "candidate":TARGET,"target_notional_usdt":NOTIONAL,"max_snapshot_age_ms":MAX_AGE_MS,
             "metrics":metrics,"gates":gates,
             "prior_aggtrades_proxy_status":prior["status"],
             "prior_aggtrades_economic_latency_subgates_pass":prior_econ,
             "one_shot_oos_positive_pf_gt_1":oos,
             "composite_execution_feasible":composite,
             "prior_print_fill_proxy_fail_preserved":True,
             "governance":{"year_2026_accessed":False,"live_trading":False,"orders":False,
                           "exchange_mutation":False,"signal_changed":False,"events_changed":False,
                           "aggtrades_5s_rule_changed":False}}
    receipt["fingerprint"]=sha256_bytes(canonical(receipt))
    (out/"CED_1D_AVAX20_V3_BOOKDEPTH_CAPACITY_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":receipt["status"],"composite_execution_feasible":composite,
                      "metrics":metrics,"gates":gates,"fingerprint":receipt["fingerprint"]},indent=2,sort_keys=True))

if __name__=="__main__": main()
