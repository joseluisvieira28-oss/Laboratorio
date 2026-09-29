#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,statistics,time,urllib.error,urllib.request,zipfile
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

LAB="DLS-MARGINFI-SOL-POST-CASCADE-REVERSION-001"
SOL="So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2024,2,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2024,4,1,tzinfo=dt.timezone.utc)
LINK_MIN=5
HOLD_MIN=15
FEE_BPS=8.0
SLIP_BPS=2.0
STRESS_SLIP_BPS=5.0
BOOT_N=20000
BOOT_SEED=26092915

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--workers",type=int,default=12)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_POST_CASCADE_REVERSION_V01_DEVELOPMENT_RECEIPT.json"
LEDGER=OUT/"MARGINFI_SOL_POST_CASCADE_REVERSION_V01_DEVELOPMENT_LEDGER.ndjson"
CASCADE=OUT/"MARGINFI_SOL_POST_CASCADE_REVERSION_V01_SOURCE_CASCADES.ndjson"
MANIFEST=OUT/"MARGINFI_SOL_POST_CASCADE_REVERSION_V01_MARKET_DATA_MANIFEST.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def identity(x):return x["signature"]+"|"+addrkey(x["instructionAddress"])

def entry_minute(t):
    return t.replace(second=0,microsecond=0)+dt.timedelta(minutes=1)

def ms(t):return int(t.timestamp()*1000)

def http_bytes(url,retries=7):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-marginfi-sol-reversion-v01/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
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

def long_return(entry_open,exit_open,slip_bps):
    slip=slip_bps/10000.0;fee=FEE_BPS/10000.0
    entry_exec=entry_open*(1+slip);exit_exec=exit_open*(1-slip)
    ratio=exit_exec/entry_exec
    gross=exit_open/entry_open-1.0
    net=(ratio-1.0)-fee*(1.0+ratio)
    return gross,net

def metrics(rows,key):
    vals=[r[key] for r in rows]
    pos=sum(v for v in vals if v>0);neg=sum(v for v in vals if v<0)
    pf=(pos/abs(neg)) if neg<0 else (float("inf") if pos>0 else 0.0)
    return {"n":len(vals),"mean":sum(vals)/len(vals) if vals else None,
            "median":statistics.median(vals) if vals else None,
            "win_rate":sum(1 for v in vals if v>0)/len(vals) if vals else None,
            "profit_factor":pf,"cumulative_simple_return":sum(vals)}

def day_boot(rows):
    by=defaultdict(list)
    for r in rows:by[r["entry_time"][:10]].append(r["nominal_net"])
    days=sorted(by)
    if len(days)<2:return {"replicates":0,"day_count":len(days),"lower":None,"upper":None}
    rng=random.Random(BOOT_SEED);vals=[]
    for _ in range(BOOT_N):
        sample=[]
        for __ in range(len(days)):
            d=days[rng.randrange(len(days))];sample.extend(by[d])
        vals.append(sum(sample)/len(sample))
    vals.sort()
    def q(p):
        i=(len(vals)-1)*p;lo=int(math.floor(i));hi=int(math.ceil(i))
        if lo==hi:return vals[lo]
        return vals[lo]+(vals[hi]-vals[lo])*(i-lo)
    return {"replicates":BOOT_N,"day_count":len(days),"seed":BOOT_SEED,"lower":q(.025),"upper":q(.975)}

srec=find_one(args.source_root,"MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json")
srows=find_one(args.source_root,"MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_ROWS_V0.2.ndjson")
if srec is None or srows is None:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_REVERSION_DEVELOPMENT_SOURCE_BLOCKED",
      "stage":"source_authority","errors":["source_receipt_or_rows_missing"]},indent=2)+"\n")
    raise SystemExit(2)
sr=json.loads(srec.read_text())
if sr.get("classification")!="MARGINFI_SOL_FEBMAR_SIGNED_FLOW_SOURCE_PASS":
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_REVERSION_DEVELOPMENT_SOURCE_BLOCKED",
      "stage":"source_authority","source_classification":sr.get("classification"),
      "market_data_opened":False},indent=2)+"\n")
    raise SystemExit(2)

rows=[json.loads(x) for x in srows.read_text().splitlines() if x.strip()]
eligible=[]
for r in rows:
    if r.get("classification")!="DIRECTION_PROVEN":continue
    if r.get("route_semantic")!="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN":continue
    if r.get("asset_label")!="SIGNED_SELL_PRESSURE_PROVEN":continue
    if r.get("asset_mint")!=SOL:continue
    t=parse_iso(r["timestamp"])
    if START<=t<END:
        eligible.append({**r,"t":t})
eligible.sort(key=lambda r:(r["t"],r["signature"],addrkey(r["instructionAddress"])))

# Frozen source-only cascade construction.
cascades=[]
for e in eligible:
    if not cascades or e["t"]>cascades[-1]["last_event_time"]+dt.timedelta(minutes=LINK_MIN):
        cascades.append({"first_event_time":e["t"],"last_event_time":e["t"],"events":[e]})
    else:
        cascades[-1]["events"].append(e);cascades[-1]["last_event_time"]=e["t"]

casrows=[]
for i,c in enumerate(cascades,1):
    casrows.append({
      "cascade_id":f"fm-cascade-{i:05d}",
      "first_event_time":c["first_event_time"].isoformat(),
      "last_event_time":c["last_event_time"].isoformat(),
      "source_event_count":len(c["events"]),
      "member_identities":[identity(x) for x in c["events"]]
    })
with CASCADE.open("w") as fh:
    for r in casrows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

# Only after source PASS and frozen cascade construction do we acquire market data.
required_dates=set()
for c in cascades:
    A=entry_minute(c["last_event_time"]);X=A+dt.timedelta(minutes=HOLD_MIN)
    if START<=A<END and X<=END:
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
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_REVERSION_DEVELOPMENT_SOURCE_BLOCKED",
      "stage":"market_data","eligible_source_events":len(eligible),"source_cascade_count":len(cascades),
      "hard_error_count":len(hard),"hard_errors":hard,"apr_jun_2024_opened":False,
      "market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

trades=[];counters=defaultdict(int);busy_until=None
for idx,c in enumerate(cascades,1):
    A=entry_minute(c["last_event_time"]);X=A+dt.timedelta(minutes=HOLD_MIN)
    if not(START<=A<END) or X>END:
        counters["boundary_excluded"]+=1;continue
    if busy_until is not None and A<busy_until:
        counters["collision_ignored"]+=1;continue
    if crosses_funding(A,X):
        counters["funding_boundary_excluded"]+=1;continue
    eo=bars.get(ms(A));xo=bars.get(ms(X))
    if eo is None or xo is None or eo<=0 or xo<=0:
        counters["entry_exit_market_data_incomplete"]+=1;continue
    gross,net=long_return(eo,xo,SLIP_BPS)
    _,stress=long_return(eo,xo,STRESS_SLIP_BPS)
    fold="F1" if A.month==2 else "F2"
    trades.append({
      "cascade_id":f"fm-cascade-{idx:05d}","source_event_count":len(c["events"]),
      "first_event_time":c["first_event_time"].isoformat(),"last_event_time":c["last_event_time"].isoformat(),
      "entry_time":A.isoformat(),"exit_time":X.isoformat(),"fold":fold,"side":"LONG_SOLUSDT",
      "entry_open":eo,"exit_open":xo,"gross_return":gross,"nominal_net":net,"stress_net":stress
    })
    busy_until=X;counters["trades"]+=1

with LEDGER.open("w") as fh:
    for r in trades:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

gross=metrics(trades,"gross_return");nom=metrics(trades,"nominal_net");stress=metrics(trades,"stress_net")
f1=metrics([r for r in trades if r["fold"]=="F1"],"nominal_net")
f2=metrics([r for r in trades if r["fold"]=="F2"],"nominal_net")
boot=day_boot(trades)
days=len({r["entry_time"][:10] for r in trades})
gate={
 "n_ge_30":nom["n"]>=30,
 "distinct_utc_days_ge_8":days>=8,
 "mean_gt_0":nom["mean"] is not None and nom["mean"]>0,
 "median_gt_0":nom["median"] is not None and nom["median"]>0,
 "profit_factor_gt_1_10":nom["profit_factor"]>1.10,
 "f1_n_ge_10":f1["n"]>=10,
 "f2_n_ge_10":f2["n"]>=10,
 "f1_mean_gt_0":f1["mean"] is not None and f1["mean"]>0,
 "f2_mean_gt_0":f2["mean"] is not None and f2["mean"]>0,
 "bootstrap_lower_gt_0":boot["lower"] is not None and boot["lower"]>0
}
classification="MARGINFI_SOL_REVERSION_DEVELOPMENT_SURVIVES" if all(gate.values()) else "MARGINFI_SOL_REVERSION_DEVELOPMENT_NO_EDGE"
receipt={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "freeze":"MARGINFI_SOL_POST_CASCADE_REVERSION_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md",
 "source":{"source_run_id":36589912203,"source_classification":sr.get("classification"),
           "eligible_sol_source_events":len(eligible),"source_cascade_count":len(cascades)},
 "rule":{"cascade_link_minutes":LINK_MIN,"side":"LONG","symbol":SYMBOL,"hold_minutes":HOLD_MIN,
         "mexc_api_taker_fee_bps_per_side":FEE_BPS,"nominal_slippage_bps_per_side":SLIP_BPS,
         "nominal_approx_round_trip_cost_bps":20.0,"stress_slippage_bps_per_side":STRESS_SLIP_BPS,
         "stress_approx_round_trip_cost_bps":26.0},
 "market_data":{"authority":"Binance public USDT-M daily 1m archive","required_day_count":len(required_dates),
                "manifest_count":len(manifest),"pass_count":sum(1 for r in manifest if r["status"]=="PASS"),
                "missing_minute_count":sum(int(r.get("missing_minutes") or 0) for r in manifest),"hard_error_count":0},
 "counters":dict(counters),"distinct_utc_entry_days":days,
 "cascade_event_count_distribution":dict(sorted(Counter(str(len(c["events"])) for c in cascades).items(),key=lambda kv:int(kv[0]))),
 "gross":gross,"nominal":nom,"stress":stress,"F1":f1,"F2":f2,
 "bootstrap_day_block_95ci":boot,"gate":gate,
 "future_boundary":{"oos_holdout":"2024-04-01/2024-07-01"},
 "firewall":{"jan_2024_validation_used":False,"apr_jun_2024_opened":False,
             "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,
             "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False,
             "post_outcome_tuning":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"eligible_sol_source_events":len(eligible),
 "source_cascade_count":len(cascades),"counters":dict(counters),"distinct_utc_entry_days":days,
 "gross":gross,"nominal":nom,"stress":stress,"F1":f1,"F2":f2,"bootstrap":boot,"gate":gate},indent=2,sort_keys=True))
