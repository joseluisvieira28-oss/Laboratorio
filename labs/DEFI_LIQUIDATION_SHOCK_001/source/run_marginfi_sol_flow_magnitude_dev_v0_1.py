#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,statistics,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

LAB="DLS-MARGINFI-SOL-FLOW-MAGNITUDE-REVERSION-001"
SOL="So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2024,4,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2024,7,1,tzinfo=dt.timezone.utc)
LINK_MIN=5
HOLD_MIN=15
FEE_BPS=8.0
SLIP_BPS=2.0
STRESS_SLIP_BPS=5.0
BOOT_N=20000
BOOT_SEED=26093075

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--calibration-root",required=True)
ap.add_argument("--workers",type=int,default=12)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_FLOW_MAGNITUDE_V01_DEVELOPMENT_RECEIPT.json"
LEDGER=OUT/"MARGINFI_SOL_FLOW_MAGNITUDE_V01_DEVELOPMENT_LEDGER.ndjson"
CASCADES=OUT/"MARGINFI_SOL_FLOW_MAGNITUDE_V01_SOURCE_CASCADES.ndjson"
MANIFEST=OUT/"MARGINFI_SOL_FLOW_MAGNITUDE_V01_MARKET_DATA_MANIFEST.ndjson"

def find_one(root,name):
    h=sorted(Path(root).rglob(name));return h[0] if len(h)==1 else None
def parse(s):return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)
def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(x):return x["signature"]+"|"+addrkey(x["instructionAddress"])
def entry_minute(t):return t.replace(second=0,microsecond=0)+dt.timedelta(minutes=1)
def ms(t):return int(t.timestamp()*1000)

def fail(stage,errors,**extra):
    o={"schema_version":"0.1","lab_id":LAB,"classification":"MARGINFI_SOL_FLOW_MAGNITUDE_DEVELOPMENT_SOURCE_BLOCKED",
       "stage":stage,"errors":errors if isinstance(errors,list) else [str(errors)],
       "firewall":{"jul_sep_oos_opened":False,"oct_dec_holdout_opened":False,
                   "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,
                   "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False},
       **extra}
    RECEIPT.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n");print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(2)

def http_bytes(url,retries=7):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-marginfi-flow-mag-v01/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504):
                last={"http":e.code};time.sleep(min(20,2**i));continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:240]};time.sleep(min(20,2**i))
    return None,last

def acquire_day(day):
    ds=day.isoformat()
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    ss,sb=http_bytes(base+".CHECKSUM");zs,zb=http_bytes(base)
    rec={"date":ds,"checksum_http":ss,"zip_http":zs,"status":None,"bars":0}
    if ss!=200 or zs!=200 or not isinstance(sb,(bytes,bytearray)) or not isinstance(zb,(bytes,bytearray)):
        rec["status"]="TRANSPORT_FAIL";return rec,{}
    m=re.search(r"([0-9a-fA-F]{64})",sb.decode("utf-8","replace"))
    if not m:rec["status"]="CHECKSUM_FORMAT_INVALID";return rec,{}
    exp=m.group(1).lower();obs=hashlib.sha256(zb).hexdigest()
    rec["expected_sha256"]=exp;rec["observed_sha256"]=obs
    if exp!=obs:rec["status"]="CHECKSUM_MISMATCH";return rec,{}
    try:
        z=zipfile.ZipFile(io.BytesIO(zb));names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:rec["status"]="ZIP_MEMBER_COUNT_INVALID";return rec,{}
        day0=dt.datetime.combine(day,dt.time(0),tzinfo=dt.timezone.utc);lo=ms(day0);hi=lo+86400000
        bars={};prev=None;dup=0;nonmono=0
        with z.open(names[0]) as fh:
            rdr=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
            for row in rdr:
                if not row or str(row[0]).strip().lower()=="open_time":continue
                t=int(row[0])
                if t>10**14:t//=1000
                if t%60000!=0 or not(lo<=t<hi):rec["status"]="TIMESTAMP_INTEGRITY_FAIL";return rec,{}
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
        rec.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:240]});return rec,{}

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
    ee=entry_open*(1+slip);xe=exit_open*(1-slip);ratio=xe/ee
    gross=exit_open/entry_open-1.0
    net=(ratio-1.0)-fee*(1.0+ratio)
    return gross,net

def metrics(rows,key):
    v=[r[key] for r in rows];pos=sum(x for x in v if x>0);neg=sum(x for x in v if x<0)
    pf=(pos/abs(neg)) if neg<0 else (float("inf") if pos>0 else 0.0)
    return {"n":len(v),"mean":sum(v)/len(v) if v else None,"median":statistics.median(v) if v else None,
            "win_rate":sum(1 for x in v if x>0)/len(v) if v else None,"profit_factor":pf,
            "cumulative_simple_return":sum(v)}

def boot(rows):
    by=defaultdict(list)
    for r in rows:by[r["entry_time"][:10]].append(r["nominal_net"])
    days=sorted(by)
    if len(days)<2:return {"replicates":0,"day_count":len(days),"lower":None,"upper":None}
    rng=random.Random(BOOT_SEED);vals=[]
    for _ in range(BOOT_N):
        sample=[]
        for __ in range(len(days)):sample.extend(by[days[rng.randrange(len(days))]])
        vals.append(sum(sample)/len(sample))
    vals.sort()
    def q(p):
        i=(len(vals)-1)*p;lo=int(math.floor(i));hi=int(math.ceil(i))
        if lo==hi:return vals[lo]
        return vals[lo]+(vals[hi]-vals[lo])*(i-lo)
    return {"replicates":BOOT_N,"day_count":len(days),"seed":BOOT_SEED,"lower":q(.025),"upper":q(.975)}

srec=find_one(args.source_root,"MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json")
srows=find_one(args.source_root,"MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_ROWS_V0.2.ndjson")
qrec=find_one(args.calibration_root,"MARGINFI_SOL_FLOW_MAGNITUDE_Q75_CALIBRATION_RECEIPT_V0.1.json")
if srec is None or srows is None or qrec is None:fail("authority","source_or_q75_artifact_missing_or_duplicate")
sr=json.loads(srec.read_text());qr=json.loads(qrec.read_text())
if sr.get("classification")!="MARGINFI_SOL_APRJUN_SIGNED_FLOW_SOURCE_PASS":fail("authority","aprjun_source_not_pass",source_classification=sr.get("classification"))
if qr.get("classification")!="MARGINFI_SOL_FLOW_MAGNITUDE_Q75_CALIBRATION_PASS":fail("authority","q75_not_pass",q75_classification=qr.get("classification"))
thr=int(qr["threshold_lamports"])
if thr!=177172524:fail("authority","frozen_q75_numeric_mismatch",observed_threshold_lamports=thr)

rows=[json.loads(x) for x in srows.read_text().splitlines() if x.strip()]
eligible=[]
for r in rows:
    if r.get("classification")!="DIRECTION_PROVEN" or r.get("route_semantic")!="COLLATERAL_TO_LIABILITY_MULTI_HOP_PROVEN":continue
    if r.get("asset_label")!="SIGNED_SELL_PRESSURE_PROVEN" or r.get("asset_mint")!=SOL or r.get("route_input_mint")!=SOL:continue
    evs=r.get("decoded_swap_events") or []
    if not evs or evs[0].get("inputMint")!=SOL or not isinstance(evs[0].get("inputAmount"),int) or evs[0]["inputAmount"]<=0:
        fail("source_amount","invalid_realized_sol_input",identity=ident(r))
    eligible.append({**r,"t":parse(r["timestamp"]),"realized_lamports":int(evs[0]["inputAmount"])})
eligible.sort(key=lambda r:(r["t"],r["signature"],addrkey(r["instructionAddress"])))

casc=[]
for e in eligible:
    if not casc or e["t"]>casc[-1]["last"]+dt.timedelta(minutes=LINK_MIN):
        casc.append({"first":e["t"],"last":e["t"],"events":[e]})
    else:
        casc[-1]["events"].append(e);casc[-1]["last"]=e["t"]

casrows=[];selected=[]
for i,c in enumerate(casc,1):
    lam=sum(x["realized_lamports"] for x in c["events"])
    x={"cascade_id":f"aj-mag-{i:05d}","first_event_time":c["first"].isoformat(),"last_event_time":c["last"].isoformat(),
       "source_event_count":len(c["events"]),"realized_lamports":lam,"realized_sol":lam/1e9,
       "selected_q75":lam>=thr,"member_identities":[ident(e) for e in c["events"]]}
    casrows.append(x)
    if lam>=thr:selected.append((c,x))
with CASCADES.open("w") as fh:
    for x in casrows:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")

# Market data opens only after both source and Q75 authority passed above.
required=set()
for c,x in selected:
    A=entry_minute(c["last"]);X=A+dt.timedelta(minutes=HOLD_MIN)
    if START<=A<END and X<=END:required.add(A.date());required.add(X.date())
bars={};manifest=[];hard=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in sorted(required)}
    for fut in as_completed(futs):
        rec,b=fut.result();manifest.append(rec)
        if rec["status"]!="PASS":hard.append(rec)
        else:bars.update(b)
manifest.sort(key=lambda x:x["date"])
with MANIFEST.open("w") as fh:
    for x in manifest:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")
if hard:fail("market_data",["market_data_integrity_failure"],hard_errors=hard[:100],selected_cascade_count=len(selected))

trades=[];cnt=defaultdict(int);busy=None
for c,x in selected:
    A=entry_minute(c["last"]);X=A+dt.timedelta(minutes=HOLD_MIN)
    if not(START<=A<END) or X>END:cnt["boundary_excluded"]+=1;continue
    if busy is not None and A<busy:cnt["collision_ignored"]+=1;continue
    if crosses_funding(A,X):cnt["funding_boundary_excluded"]+=1;continue
    eo=bars.get(ms(A));xo=bars.get(ms(X))
    if eo is None or xo is None or eo<=0 or xo<=0:cnt["entry_exit_market_data_incomplete"]+=1;continue
    gross,net=long_return(eo,xo,SLIP_BPS);_,stress=long_return(eo,xo,STRESS_SLIP_BPS)
    fold={4:"APR",5:"MAY",6:"JUN"}[A.month]
    trades.append({"cascade_id":x["cascade_id"],"realized_sol":x["realized_sol"],"source_event_count":x["source_event_count"],
                   "entry_time":A.isoformat(),"exit_time":X.isoformat(),"fold":fold,"side":"LONG_SOLUSDT",
                   "entry_open":eo,"exit_open":xo,"gross_return":gross,"nominal_net":net,"stress_net":stress})
    busy=X;cnt["trades"]+=1
with LEDGER.open("w") as fh:
    for x in trades:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")

gross=metrics(trades,"gross_return");nom=metrics(trades,"nominal_net");stress=metrics(trades,"stress_net")
aprm=metrics([x for x in trades if x["fold"]=="APR"],"nominal_net")
maym=metrics([x for x in trades if x["fold"]=="MAY"],"nominal_net")
junm=metrics([x for x in trades if x["fold"]=="JUN"],"nominal_net")
bt=boot(trades);days=len({x["entry_time"][:10] for x in trades})
gate={
 "n_ge_20":nom["n"]>=20,"distinct_utc_days_ge_10":days>=10,
 "mean_gt_0":nom["mean"] is not None and nom["mean"]>0,
 "median_gt_0":nom["median"] is not None and nom["median"]>0,
 "profit_factor_gt_1_10":nom["profit_factor"]>1.10,
 "apr_n_ge_5":aprm["n"]>=5,"may_n_ge_5":maym["n"]>=5,"jun_n_ge_5":junm["n"]>=5,
 "apr_mean_gt_0":aprm["mean"] is not None and aprm["mean"]>0,
 "may_mean_gt_0":maym["mean"] is not None and maym["mean"]>0,
 "jun_mean_gt_0":junm["mean"] is not None and junm["mean"]>0,
 "bootstrap_lower_gt_0":bt["lower"] is not None and bt["lower"]>0
}
classification="MARGINFI_SOL_FLOW_MAGNITUDE_DEVELOPMENT_SURVIVES" if all(gate.values()) else "MARGINFI_SOL_FLOW_MAGNITUDE_DEVELOPMENT_NO_EDGE"
receipt={"schema_version":"0.1","lab_id":LAB,"classification":classification,
 "freeze":"MARGINFI_SOL_FLOW_MAGNITUDE_REVERSION_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "source":{"classification":sr.get("classification"),"eligible_event_count":len(eligible),"cascade_count":len(casc),
           "selected_q75_cascade_count":len(selected)},
 "q75":{"calibration_run_id":36713252128,"threshold_lamports":thr,"threshold_sol":thr/1e9,
        "method":qr.get("method"),"calibration_cascade_count":qr.get("cascade_count")},
 "rule":{"cascade_link_minutes":LINK_MIN,"side":"LONG","symbol":SYMBOL,"hold_minutes":HOLD_MIN,
         "mexc_api_taker_fee_bps_per_side":FEE_BPS,"nominal_slippage_bps_per_side":SLIP_BPS,
         "nominal_approx_round_trip_cost_bps":20.0,"stress_slippage_bps_per_side":STRESS_SLIP_BPS,
         "stress_approx_round_trip_cost_bps":26.0},
 "market_data":{"required_day_count":len(required),"manifest_count":len(manifest),
                "pass_count":sum(1 for x in manifest if x["status"]=="PASS"),
                "missing_minute_count":sum(int(x.get("missing_minutes") or 0) for x in manifest),"hard_error_count":0},
 "counters":dict(cnt),"distinct_utc_entry_days":days,"gross":gross,"nominal":nom,"stress":stress,
 "APR":aprm,"MAY":maym,"JUN":junm,"bootstrap_day_block_95ci":bt,"gate":gate,
 "future_boundaries":{"oos":"2024-07-01/2024-10-01","holdout":"2024-10-01/2025-01-01"},
 "firewall":{"jul_sep_oos_opened":False,"oct_dec_holdout_opened":False,"market_2025_opened":False,
             "market_2026_opened":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False,"post_outcome_tuning":False}}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"eligible_event_count":len(eligible),"cascade_count":len(casc),
 "selected_q75_cascade_count":len(selected),"threshold_sol":thr/1e9,"counters":dict(cnt),
 "distinct_utc_entry_days":days,"gross":gross,"nominal":nom,"stress":stress,"APR":aprm,"MAY":maym,"JUN":junm,
 "bootstrap":bt,"gate":gate},indent=2,sort_keys=True))
