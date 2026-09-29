#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,statistics,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

LAB="DLS-MARGINFI-SOL-SELL-PRESSURE-001"
SOL="So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2024,1,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2024,2,1,tzinfo=dt.timezone.utc)
FOLD_CUT=dt.datetime(2024,1,16,tzinfo=dt.timezone.utc)
HOLD_MIN=5
FEE_BPS=8.0
SLIP_BPS=2.0
STRESS_SLIP_BPS=5.0
BOOT_N=20000
BOOT_SEED=26092901

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--membership-root",required=True)
ap.add_argument("--workers",type=int,default=12)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_SELL_PRESSURE_RETURN_V01_DEVELOPMENT_RECEIPT.json"
LEDGER=OUT/"MARGINFI_SOL_SELL_PRESSURE_RETURN_V01_DEVELOPMENT_LEDGER.ndjson"
MANIFEST=OUT/"MARGINFI_SOL_SELL_PRESSURE_RETURN_V01_MARKET_DATA_MANIFEST.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def entry_minute(t):
    return t.replace(second=0,microsecond=0)+dt.timedelta(minutes=1)

def ms(t): return int(t.timestamp()*1000)

def addrkey(x): return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(sig,addr): return sig+"|"+addrkey(addr)

def http_bytes(url,retries=7):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-marginfi-sol-sell-pressure-v01/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:
                return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            last={"http":int(e.code)}
            if e.code in (429,500,502,503,504):
                time.sleep(min(20,2**i));continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]}
            time.sleep(min(20,2**i))
    return None,last

def acquire_day(day):
    ds=day.isoformat()
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    ss,sb=http_bytes(base+".CHECKSUM")
    zs,zb=http_bytes(base)
    rec={"date":ds,"checksum_http":ss,"zip_http":zs,"status":None,"bars":0}
    if ss!=200 or zs!=200 or not isinstance(sb,(bytes,bytearray)) or not isinstance(zb,(bytes,bytearray)):
        rec["status"]="TRANSPORT_FAIL";return rec,{}
    m=re.search(r"([0-9a-fA-F]{64})",sb.decode("utf-8","replace"))
    if not m:
        rec["status"]="CHECKSUM_FORMAT_INVALID";return rec,{}
    exp=m.group(1).lower();obs=hashlib.sha256(zb).hexdigest()
    rec["expected_sha256"]=exp;rec["observed_sha256"]=obs
    if exp!=obs:
        rec["status"]="CHECKSUM_MISMATCH";return rec,{}
    try:
        z=zipfile.ZipFile(io.BytesIO(zb))
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:
            rec["status"]="ZIP_MEMBER_COUNT_INVALID";return rec,{}
        day0=dt.datetime.combine(day,dt.time(0),tzinfo=dt.timezone.utc)
        lo=ms(day0);hi=lo+86400000
        bars={};prev=None;dup=0;nonmono=0
        with z.open(names[0]) as fh:
            rdr=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
            for row in rdr:
                if not row:continue
                if str(row[0]).strip().lower()=="open_time":continue
                t=int(row[0])
                if t>10**14:t//=1000
                if t%60000!=0 or not(lo<=t<hi):
                    rec["status"]="TIMESTAMP_INTEGRITY_FAIL";return rec,{}
                if prev is not None and t<=prev:
                    if t==prev:dup+=1
                    else:nonmono+=1
                prev=t
                if t in bars:dup+=1
                bars[t]=float(row[1])
        if dup or nonmono:
            rec.update({"status":"ARCHIVE_STRUCTURE_CONFLICT","duplicate_count":dup,"non_monotonic_count":nonmono});return rec,{}
        rec.update({"status":"PASS","bars":len(bars),"missing_minutes":1440-len(bars),"duplicate_count":0,"non_monotonic_count":0})
        return rec,bars
    except Exception as e:
        rec.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:240]})
        return rec,{}

def crosses_funding(a,x):
    d=a.date()-dt.timedelta(days=1)
    while d<=x.date():
        for h in (0,8,16):
            f=dt.datetime(d.year,d.month,d.day,h,tzinfo=dt.timezone.utc)
            if a<=f<=x:return True
        d+=dt.timedelta(days=1)
    return False

def short_return(entry_open,exit_open,slip_bps):
    slip=slip_bps/10000.0
    fee=FEE_BPS/10000.0
    entry_exec=entry_open*(1-slip)
    exit_exec=exit_open*(1+slip)
    ratio=exit_exec/entry_exec
    gross=1.0-(exit_open/entry_open)
    net=(1.0-ratio)-fee*(1.0+ratio)
    return gross,net

def metrics(rows,key):
    vals=[r[key] for r in rows]
    pos=sum(v for v in vals if v>0);neg=sum(v for v in vals if v<0)
    pf=(pos/abs(neg)) if neg<0 else (float("inf") if pos>0 else 0.0)
    return {
      "n":len(vals),
      "mean":sum(vals)/len(vals) if vals else None,
      "median":statistics.median(vals) if vals else None,
      "win_rate":sum(1 for v in vals if v>0)/len(vals) if vals else None,
      "profit_factor":pf,
      "cumulative_simple_return":sum(vals)
    }

def day_block_bootstrap(rows):
    by=defaultdict(list)
    for r in rows:by[r["entry_time"][:10]].append(r["nominal_net"])
    days=sorted(by)
    if len(days)<2:return {"replicates":0,"day_count":len(days),"lower":None,"upper":None}
    rng=random.Random(BOOT_SEED);vals=[]
    for _ in range(BOOT_N):
        sample=[]
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))]
            sample.extend(by[d])
        vals.append(sum(sample)/len(sample))
    vals.sort()
    def q(p):
        i=(len(vals)-1)*p;lo=int(math.floor(i));hi=int(math.ceil(i))
        if lo==hi:return vals[lo]
        return vals[lo]+(vals[hi]-vals[lo])*(i-lo)
    return {"replicates":BOOT_N,"day_count":len(days),"seed":BOOT_SEED,"lower":q(.025),"upper":q(.975)}

srec=find_one(args.source_root,"MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json")
srows=find_one(args.source_root,"MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_ROWS_V0.2.ndjson")
mrec=find_one(args.membership_root,"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_RECEIPT_V0.2.json")
mrows=find_one(args.membership_root,"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERS_V0.2.ndjson")
errors=[]
for p,n in [(srec,"source_receipt"),(srows,"source_rows"),(mrec,"membership_receipt"),(mrows,"membership_rows")]:
    if p is None:errors.append(n+"_missing_or_duplicate")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_SOURCE_BLOCKED","stage":"authority","errors":errors},indent=2)+"\n")
    raise SystemExit(2)

sr=json.loads(srec.read_text());mr=json.loads(mrec.read_text())
if sr.get("classification")!="MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_PASS":errors.append("signed_flow_source_not_pass")
if mr.get("classification")!="MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS":errors.append("membership_not_pass")
source=[json.loads(x) for x in srows.read_text().splitlines() if x.strip()]
membership=[json.loads(x) for x in mrows.read_text().splitlines() if x.strip()]
mem={}
for r in membership:
    k=ident(r["signature"],r["instructionAddress"])
    if k in mem:errors.append("membership_duplicate_identity")
    mem[k]=r
if len(source)!=int(sr.get("population_member_count",-1)):errors.append("source_population_count_mismatch")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_SOURCE_BLOCKED","stage":"authority","errors":sorted(set(errors))},indent=2)+"\n")
    raise SystemExit(2)

events=[]
for r in source:
    if r.get("asset_mint")!=SOL:continue
    if r.get("classification")!="DIRECTION_PROVEN":continue
    if r.get("route_semantic")!="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN":continue
    if r.get("asset_label")!="SIGNED_SELL_PRESSURE_PROVEN":continue
    k=ident(r["signature"],r["instructionAddress"])
    m=mem.get(k)
    if m is None:
        errors.append("source_member_missing_membership_identity");continue
    t0=parse_iso(m["timestamp"])
    if not(START<=t0<END):continue
    events.append({**r,"t0_dt":t0,"timestamp":m["timestamp"]})
events.sort(key=lambda x:(x["t0_dt"],x["signature"],addrkey(x["instructionAddress"])))
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_SOURCE_BLOCKED","stage":"source_join","errors":sorted(set(errors))},indent=2)+"\n")
    raise SystemExit(2)

# Derive only required market-data dates from source timestamps and frozen 5-minute exits.
required_dates=set()
for e in events:
    A=entry_minute(e["t0_dt"]);X=A+dt.timedelta(minutes=HOLD_MIN)
    required_dates.add(A.date());required_dates.add(X.date())

bars={};manifest=[];hard=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in sorted(required_dates)}
    for fut in as_completed(futs):
        rec,b=fut.result();manifest.append(rec)
        if rec["status"]!="PASS":hard.append(rec)
        else:bars.update(b)
manifest.sort(key=lambda x:x["date"])
with MANIFEST.open("w") as fh:
    for r in manifest:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
if hard:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_SOURCE_BLOCKED","stage":"market_data",
      "eligible_source_events":len(events),"hard_error_count":len(hard),"hard_errors":hard,
      "feb_mar_2024_oos_opened":False,"apr_jun_2024_holdout_opened":False,"market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

trades=[];counters=defaultdict(int);busy_until=None
for e in events:
    A=entry_minute(e["t0_dt"]);X=A+dt.timedelta(minutes=HOLD_MIN)
    if not(START<=A<END) or X>END:
        counters["boundary_excluded"]+=1;continue
    if busy_until is not None and A<busy_until:
        counters["overlap_ignored"]+=1;continue
    if crosses_funding(A,X):
        counters["funding_boundary_excluded"]+=1;continue
    eo=bars.get(ms(A));xo=bars.get(ms(X))
    if eo is None or xo is None or eo<=0 or xo<=0:
        counters["entry_exit_market_data_incomplete"]+=1;continue
    gross,net=short_return(eo,xo,SLIP_BPS)
    _,stress=short_return(eo,xo,STRESS_SLIP_BPS)
    fold="F1" if A<FOLD_CUT else "F2"
    tr={
      "signature":e["signature"],"instructionAddress":e["instructionAddress"],"source_timestamp":e["timestamp"],
      "entry_time":A.isoformat(),"exit_time":X.isoformat(),"fold":fold,"side":"SHORT_SOLUSDT",
      "hop_count":e.get("hop_count"),"liab_mint":e.get("liab_mint"),
      "entry_open":eo,"exit_open":xo,"gross_return":gross,"nominal_net":net,"stress_net":stress
    }
    trades.append(tr);busy_until=X;counters["trades"]+=1

with LEDGER.open("w") as fh:
    for r in trades:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

overall=metrics(trades,"nominal_net")
gross=metrics(trades,"gross_return")
stress=metrics(trades,"stress_net")
f1=metrics([r for r in trades if r["fold"]=="F1"],"nominal_net")
f2=metrics([r for r in trades if r["fold"]=="F2"],"nominal_net")
boot=day_block_bootstrap(trades)
days=len({r["entry_time"][:10] for r in trades})
gate={
 "n_ge_40":overall["n"]>=40,
 "mean_gt_0":overall["mean"] is not None and overall["mean"]>0,
 "median_gt_0":overall["median"] is not None and overall["median"]>0,
 "profit_factor_gt_1_10":overall["profit_factor"]>1.10,
 "distinct_utc_days_ge_5":days>=5,
 "f1_n_ge_10":f1["n"]>=10,
 "f2_n_ge_20":f2["n"]>=20,
 "f1_mean_gt_0":f1["mean"] is not None and f1["mean"]>0,
 "f2_mean_gt_0":f2["mean"] is not None and f2["mean"]>0,
 "bootstrap_lower_gt_0":boot["lower"] is not None and boot["lower"]>0
}
classification="MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_SURVIVES" if all(gate.values()) else "MARGINFI_SOL_SELL_PRESSURE_DEVELOPMENT_NO_EDGE"
receipt={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "freeze":"MARGINFI_SOL_SELL_PRESSURE_RETURN_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md",
 "source":{"signed_flow_run_id":36558125697,"signed_flow_artifact_id":11029321249,
           "membership_run_id":36546170744,"membership_artifact_id":11023669917,
           "eligible_sol_source_events":len(events)},
 "rule":{"symbol":SYMBOL,"side":"SHORT","hold_minutes":HOLD_MIN,
         "mexc_api_taker_fee_bps_per_side":FEE_BPS,"nominal_slippage_bps_per_side":SLIP_BPS,
         "nominal_approx_round_trip_cost_bps":20.0,"stress_slippage_bps_per_side":STRESS_SLIP_BPS,
         "stress_approx_round_trip_cost_bps":26.0},
 "market_data":{"authority":"Binance public USDT-M daily 1m archive","required_day_count":len(required_dates),
                "manifest_count":len(manifest),"pass_count":sum(1 for r in manifest if r["status"]=="PASS"),
                "missing_minute_count":sum(int(r.get("missing_minutes") or 0) for r in manifest),"hard_error_count":0},
 "counters":dict(counters),"distinct_utc_entry_days":days,
 "gross":gross,"nominal":overall,"stress":stress,"F1":f1,"F2":f2,
 "bootstrap_day_block_95ci":boot,"gate":gate,
 "future_boundaries":{"oos":"2024-02-01/2024-04-01","holdout":"2024-04-01/2024-07-01"},
 "firewall":{"feb_mar_2024_oos_opened":False,"apr_jun_2024_holdout_opened":False,
             "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,
             "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False,
             "post_outcome_tuning":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"eligible_sol_source_events":len(events),"counters":dict(counters),
  "distinct_utc_entry_days":days,"gross":gross,"nominal":overall,"stress":stress,"F1":f1,"F2":f2,
  "bootstrap":boot,"gate":gate},indent=2,sort_keys=True))
