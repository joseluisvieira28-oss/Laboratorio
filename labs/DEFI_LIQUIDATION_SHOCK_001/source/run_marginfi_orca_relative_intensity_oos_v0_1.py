#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,statistics,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

SYMBOL="SOLUSDT"
START=dt.datetime(2024,10,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
FOLD_CUT=dt.datetime(2024,12,1,tzinfo=dt.timezone.utc)
FEE_BPS=8.0
SLIP_BPS=2.0
STRESS_SLIP_BPS=5.0
BOOT_N=20000
BOOT_SEED=26100104

ap=argparse.ArgumentParser()
ap.add_argument("--selection-root",required=True)
ap.add_argument("--workers",type=int,default=8)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V01_RECEIPT.json"
LEDGER=OUT/"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V01_LEDGER.ndjson"
MANIFEST=OUT/"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V01_MARKET_DATA_MANIFEST.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def ms(t):return int(t.timestamp()*1000)

def blocked(stage,detail,**extra):
    rec={"schema_version":"0.1","classification":"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_SOURCE_BLOCKED",
         "stage":stage,"detail":str(detail)[:1600],
         "firewall":{"oct_dec_market_outcomes_opened":True,"market_2025_opened":False,"market_2026_opened":False,
                     "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False,
                     "post_outcome_tuning":False},**extra}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

def http_bytes(url,retries=8):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-orca-relative-intensity-oos-v01/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            last={"http":int(e.code)}
            if e.code in (429,500,502,503,504):
                time.sleep(min(30,2**i));continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]}
            time.sleep(min(30,2**i))
    return None,last

def acquire_day(day):
    ds=day.isoformat()
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    ss,sb=http_bytes(base+".CHECKSUM");zs,zb=http_bytes(base)
    rec={"date":ds,"checksum_http":ss,"zip_http":zs,"status":None}
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
        z=zipfile.ZipFile(io.BytesIO(zb));names=[n for n in z.namelist() if not n.endswith("/")]
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
                op=float(row[1])
                if op<=0:
                    rec["status"]="NONPOSITIVE_OPEN";return rec,{}
                bars[t]=op
        if dup or nonmono:
            rec.update({"status":"ARCHIVE_STRUCTURE_CONFLICT","duplicate_count":dup,"non_monotonic_count":nonmono});return rec,{}
        rec.update({"status":"PASS","bars":len(bars),"missing_minutes":1440-len(bars),
                    "duplicate_count":0,"non_monotonic_count":0})
        return rec,bars
    except Exception as e:
        rec.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:240]})
        return rec,{}

def crosses_funding(a,b):
    d=a.date()-dt.timedelta(days=1)
    while d<=b.date():
        for h in (0,8,16):
            f=dt.datetime(d.year,d.month,d.day,h,tzinfo=dt.timezone.utc)
            if a<=f<=b:return True
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

prec=find_one(args.selection_root,"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V01_PREOUTCOME_RECEIPT.json")
prows=find_one(args.selection_root,"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V01_PREOUTCOME_ROWS.ndjson")
if prec is None or prows is None:blocked("selection_authority","selection artifact missing or duplicate")
pr=json.loads(prec.read_text())
if pr.get("classification")!="MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_PREOUTCOME_READY":
    blocked("selection_authority",pr.get("classification"))
fw=pr.get("firewall") or {}
if fw.get("ohlc_read") is not False or fw.get("returns_read") is not False or fw.get("pnl_read") is not False:
    blocked("selection_firewall",fw)

rows=[json.loads(x) for x in prows.read_text().splitlines() if x.strip()]
selected=[r for r in rows if r.get("selected") is True]
if len(selected)!=int(pr.get("selected_count",-1)) or len(selected)<25:
    blocked("selection_count",f"{len(selected)} vs {pr.get('selected_count')}")

required_dates=set()
for r in selected:
    A=parse_iso(r["decision_time"]);X=A+dt.timedelta(minutes=1)
    if crosses_funding(A,X):blocked("funding_recheck",r.get("cascade_id"))
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
if hard:blocked("market_data",f"{len(hard)} archive hard errors",hard_errors=hard)

trades=[]
for r in selected:
    A=parse_iso(r["decision_time"]);X=A+dt.timedelta(minutes=1)
    if not(START<=A<END) or X>END:blocked("boundary",r.get("cascade_id"))
    eo=bars.get(ms(A));xo=bars.get(ms(X))
    if eo is None or xo is None:blocked("market_data_required_minutes",r.get("cascade_id"))
    gross,net=long_return(eo,xo,SLIP_BPS);_,stress=long_return(eo,xo,STRESS_SLIP_BPS)
    fold="F1" if A<FOLD_CUT else "F2"
    trades.append({
      "cascade_id":r.get("cascade_id"),"entry_time":A.isoformat(),"exit_time":X.isoformat(),"fold":fold,
      "side":"LONG_SOLUSDT","flow_turnover_intensity":r.get("flow_turnover_intensity"),
      "rolling_threshold":r.get("rolling_threshold"),"source_event_count":r.get("source_event_count"),
      "cascade_sold_sol":r.get("cascade_sold_sol"),"entry_open":eo,"exit_open":xo,
      "gross_return":gross,"nominal_net":net,"stress_net":stress
    })

with LEDGER.open("w") as fh:
    for r in trades:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

gross=metrics(trades,"gross_return");nom=metrics(trades,"nominal_net");stress=metrics(trades,"stress_net")
f1=metrics([r for r in trades if r["fold"]=="F1"],"nominal_net")
f2=metrics([r for r in trades if r["fold"]=="F2"],"nominal_net")
boot=day_boot(trades);days=len({r["entry_time"][:10] for r in trades})
gate={
 "n_ge_25":nom["n"]>=25,
 "distinct_utc_days_ge_8":days>=8,
 "mean_gt_0":nom["mean"] is not None and nom["mean"]>0,
 "median_gt_0":nom["median"] is not None and nom["median"]>0,
 "profit_factor_gt_1_10":nom["profit_factor"]>1.10,
 "f1_n_ge_15":f1["n"]>=15,
 "f2_n_ge_8":f2["n"]>=8,
 "f1_mean_gt_0":f1["mean"] is not None and f1["mean"]>0,
 "f2_mean_gt_0":f2["mean"] is not None and f2["mean"]>0,
 "bootstrap_lower_gt_0":boot["lower"] is not None and boot["lower"]>0
}
classification="MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_SURVIVES" if all(gate.values()) else "MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_NO_EDGE"
receipt={
 "schema_version":"0.1","lab_id":"DLS-MARGINFI-ORCA-RELATIVE-INTENSITY-OOS-001",
 "classification":classification,
 "freeze":"MARGINFI_ORCA_RELATIVE_INTENSITY_OOS_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "selection":{"run_id":36815529203,"artifact_id":11141660030,
              "digest":"sha256:b5a151079b7da61a457ba5d9634bf7abe0fe2befb628649b36b97648d1da64dc",
              "selected_count":len(selected)},
 "rule":{"rolling_lookback_cascades":30,"rolling_percentile":0.75,"side":"LONG","hold_minutes":1,
         "mexc_api_taker_fee_bps_per_side":FEE_BPS,"nominal_slippage_bps_per_side":SLIP_BPS,
         "nominal_approx_round_trip_cost_bps":20.0,"stress_slippage_bps_per_side":STRESS_SLIP_BPS,
         "stress_approx_round_trip_cost_bps":26.0},
 "market_data":{"authority":"Binance public USDT-M daily 1m archive","required_day_count":len(required_dates),
                "pass_count":sum(1 for r in manifest if r["status"]=="PASS"),
                "missing_minute_count":sum(int(r.get("missing_minutes") or 0) for r in manifest),
                "hard_error_count":0},
 "distinct_utc_entry_days":days,"gross":gross,"nominal":nom,"stress":stress,
 "F1":f1,"F2":f2,"bootstrap_day_block_95ci":boot,"gate":gate,
 "firewall":{"oct_dec_market_outcomes_opened":True,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False,
             "post_outcome_tuning":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
