#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,statistics,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001-V0.2"
SOL_ID="mint:So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2021,12,8,tzinfo=dt.timezone.utc)
END=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
DOWNLOAD_START=dt.date(2021,12,7)
DOWNLOAD_END=dt.date(2024,12,31)
K_VALUES=[0.25,0.50,0.75,1.00,1.50]
W_VALUES=[5,15,30]
H_VALUES=[5,15,30,60]
SLIP_SCENARIOS_BPS=[2.0,5.0,10.0]
PRIMARY_SLIP_BPS=5.0
TAKER_FEE_BPS=8.0

ap=argparse.ArgumentParser()
ap.add_argument("--source-gate",required=True)
ap.add_argument("--sample-gate",required=True)
ap.add_argument("--workers",type=int,default=16)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()

OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
ACQ=OUT/"V02_DEVELOPMENT_MARKET_DATA_ACQUISITION_RECEIPT_V0.1.json"
GRID=OUT/"V02_EXECUTABLE_VOLATILITY_GRID_V0.1.json"
SEL=OUT/"V02_EXECUTABLE_VOLATILITY_SELECTION_RECEIPT_V0.1.json"
MANIFEST=OUT/"V02_DEVELOPMENT_ARCHIVE_MANIFEST_V0.1.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits:return None,None
    return json.loads(hits[0].read_text()),str(hits[0])

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def ceil_minute(x):
    x=x.astimezone(dt.timezone.utc)
    if x.second==0 and x.microsecond==0:return x.replace(second=0,microsecond=0)
    return x.replace(second=0,microsecond=0)+dt.timedelta(minutes=1)

def ms(x):return int(x.timestamp()*1000)

def daterange(a,b):
    d=a
    while d<=b:
        yield d;d+=dt.timedelta(days=1)

def http_bytes(url,retries=7,allow_404=False):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-v02-development/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code==404:return 404,None
            last={"http":e.code}
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
    ss,sb=http_bytes(base+".CHECKSUM",allow_404=True)
    zs,zb=http_bytes(base,allow_404=True)
    rec={"date":ds,"zip_http":zs,"checksum_http":ss,"status":None,"bars":0}
    if ss==404 or zs==404:
        rec["status"]="MISSING_ARCHIVE";return rec,{}
    if ss!=200 or zs!=200 or not isinstance(sb,(bytes,bytearray)) or not isinstance(zb,(bytes,bytearray)):
        rec["status"]="TRANSPORT_EXHAUSTED";return rec,{}
    txt=sb.decode("utf-8","replace")
    import re
    m=re.search(r"([0-9a-fA-F]{64})",txt)
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
        start=ms(dt.datetime.combine(day,dt.time(0),tzinfo=dt.timezone.utc));end=start+86400000
        out={};prev=None;dup=0;nonmono=0
        with z.open(names[0]) as fh:
            rdr=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
            for row in rdr:
                if not row:continue
                t=int(row[0])
                if t>10**14:t//=1000
                if t%60000!=0 or not(start<=t<end):
                    rec["status"]="TIMESTAMP_INTEGRITY_FAIL";return rec,{}
                if prev is not None and t<=prev:
                    if t==prev:dup+=1
                    else:nonmono+=1
                prev=t
                if t in out:dup+=1
                out[t]=(float(row[1]),float(row[2]),float(row[3]),float(row[4]))
        if dup or nonmono:
            rec.update({"status":"ARCHIVE_STRUCTURE_CONFLICT","duplicate_count":dup,"non_monotonic_count":nonmono});return rec,{}
        rec.update({"status":"PASS","bars":len(out),"missing_minutes":1440-len(out),"duplicate_count":0,"non_monotonic_count":0})
        return rec,out
    except Exception as e:
        rec.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:200]});return rec,{}

def fold_name(a):
    if START<=a<dt.datetime(2023,1,1,tzinfo=dt.timezone.utc):return "F1_2021_12_TO_2022"
    if dt.datetime(2023,1,1,tzinfo=dt.timezone.utc)<=a<dt.datetime(2024,1,1,tzinfo=dt.timezone.utc):return "F2_2023"
    if dt.datetime(2024,1,1,tzinfo=dt.timezone.utc)<=a<END:return "F3_2024"
    return None

def crosses_funding(start,end):
    d=start.date()-dt.timedelta(days=1)
    while d<=end.date():
        for h in (0,8,16):
            b=dt.datetime(d.year,d.month,d.day,h,tzinfo=dt.timezone.utc)
            if start<=b<=end:return True
        d+=dt.timedelta(days=1)
    return False

def net_return(side,entry,exitp,fee):
    ratio=exitp/entry
    gross=(ratio-1.0) if side=="LONG" else (1.0-ratio)
    return gross-(fee+fee*ratio)

def calc_metrics(trades):
    rs=[x["net"] for x in trades]
    pos=sum(r for r in rs if r>0);neg=sum(r for r in rs if r<0)
    pf=(pos/abs(neg)) if neg<0 else (float("inf") if pos>0 else 0.0)
    cum=0.0;peak=0.0;mdd=0.0
    for r in rs:
        cum+=r;peak=max(peak,cum);mdd=max(mdd,peak-cum)
    return {
      "n":len(rs),"mean":(sum(rs)/len(rs) if rs else None),
      "median":(statistics.median(rs) if rs else None),
      "win_rate":(sum(1 for r in rs if r>0)/len(rs) if rs else None),
      "profit_factor":pf,"cumulative_simple_return":sum(rs),"max_drawdown_simple":mdd
    }

source,_=find_one(args.source_gate,"V02_EXECUTION_SOURCE_FEASIBILITY_RECEIPT_V0.1.json")
sample,_=find_one(args.sample_gate,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
census_hits=sorted(Path(args.sample_gate).rglob("SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"))
pre_errors=[]
if not source or source.get("classification")!="V02_EXECUTION_SOURCE_PASS":
    pre_errors.append({"reason":"v02_source_gate_not_pass","classification":(source or {}).get("classification")})
if not sample or sample.get("classification")!="SOURCE_SAMPLE_GATE_PASS":
    pre_errors.append({"reason":"v01_sample_gate_not_pass","classification":(sample or {}).get("classification")})
if not census_hits:pre_errors.append({"reason":"canonical_cluster_census_missing"})
if pre_errors:
    ACQ.write_text(json.dumps({"classification":"V02_DEVELOPMENT_SOURCE_BLOCKED","stage":"pre_acquisition","errors":pre_errors,"market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

clusters=[]
with census_hits[0].open() as fh:
    for line in fh:
        r=json.loads(line)
        if r.get("primary_market_identity")!=SOL_ID:continue
        t0=parse_iso(r["t0"]);a=ceil_minute(t0)
        if START<=a<END:
            x=dict(r);x["A"]=a;x["fold"]=fold_name(a);clusters.append(x)
clusters.sort(key=lambda x:(x["A"],x["cluster_id"]))

bars={};manifest=[];hard=[]
days=list(daterange(DOWNLOAD_START,DOWNLOAD_END))
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in days}
    for fut in as_completed(futs):
        rec,bd=fut.result();manifest.append(rec)
        if rec["status"]=="PASS":bars.update(bd)
        elif rec["status"] not in ("MISSING_ARCHIVE",):
            hard.append(rec)
manifest.sort(key=lambda x:x["date"])
with MANIFEST.open("w") as fh:
    for r in manifest:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
if hard:
    acq={"classification":"V02_DEVELOPMENT_SOURCE_BLOCKED","stage":"archive_integrity","hard_error_count":len(hard),"hard_errors":hard[:100],"market_2025_opened":False,"market_2026_opened":False}
    ACQ.write_text(json.dumps(acq,indent=2,sort_keys=True)+"\n");raise SystemExit(2)

features=[]
feat_counts=defaultdict(int)
for c in clusters:
    A=c["A"];am=ms(A)
    prev_times=[am-i*60000 for i in range(61,0,-1)]
    if any(t not in bars for t in prev_times) or am not in bars:
        feat_counts["insufficient_pre_event_vol"]+=1;continue
    closes=[bars[t][3] for t in prev_times]
    if any(x<=0 for x in closes):
        feat_counts["invalid_pre_event_price"]+=1;continue
    rets=[math.log(closes[i]/closes[i-1]) for i in range(1,len(closes))]
    sigma=math.sqrt(sum(r*r for r in rets)/len(rets))
    if not math.isfinite(sigma) or sigma<=0:
        feat_counts["zero_or_invalid_sigma"]+=1;continue
    features.append({
      "cluster_id":c["cluster_id"],"protocol":c["protocol"],"instruction_class":c["instruction_class"],
      "A":A,"fold":c["fold"],"p0":bars[am][0],"sigma60":sigma
    })

acq={
 "schema_version":"0.1","lab_id":LAB,"classification":"V02_DEVELOPMENT_MARKET_DATA_ACQUISITION_PASS",
 "source_gate_classification":source.get("classification"),"canonical_cluster_count":len(clusters),
 "feature_ready_count":len(features),"feature_exclusions":dict(feat_counts),
 "archive_day_count":len(manifest),"archive_pass_count":sum(1 for x in manifest if x["status"]=="PASS"),
 "archive_missing_count":sum(1 for x in manifest if x["status"]=="MISSING_ARCHIVE"),
 "archive_missing_minute_count":sum(int(x.get("missing_minutes") or 0) for x in manifest),
 "hard_error_count":0,
 "development_window":"2021-12-08/2024-12-31",
 "market_2025_opened":False,"market_2026_opened":False,
 "live_trading":False,"orders":False,"exchange_mutation":False
}
ACQ.write_text(json.dumps(acq,indent=2,sort_keys=True)+"\n")

results=[]
fee=TAKER_FEE_BPS/10000.0
for k in K_VALUES:
  for W in W_VALUES:
    for H in H_VALUES:
      for slip_bps in SLIP_SCENARIOS_BPS:
        slip=slip_bps/10000.0;busy_until=None;trades=[]
        counts=defaultdict(int)
        for f in features:
            A=f["A"]
            counts["eligible_source"]+=1
            if busy_until is not None and A<busy_until:
                counts["collision_ignore"]+=1;continue
            upper=f["p0"]*math.exp(k*f["sigma60"]);lower=f["p0"]*math.exp(-k*f["sigma60"])
            trig=None;amb=False
            for i in range(W):
                t=A+dt.timedelta(minutes=i);row=bars.get(ms(t))
                if row is None:continue
                hi=row[1];lo=row[2]
                up=hi>=upper;dn=lo<=lower
                if up or dn:
                    trig=t;amb=(up and dn);side=("AMB" if amb else ("LONG" if up else "SHORT"));break
            if trig is None:
                counts["no_breakout"]+=1;continue
            exit_t=trig+dt.timedelta(minutes=H)
            if exit_t>=END:
                counts["split_boundary"]+=1;continue
            if crosses_funding(trig,exit_t):
                counts["funding_boundary"]+=1;continue
            erow=bars.get(ms(exit_t))
            if erow is None:
                counts["missing_exit"]+=1;continue
            xopen=erow[0]
            long_entry=upper*(1+slip);long_exit=xopen*(1-slip)
            short_entry=lower*(1-slip);short_exit=xopen*(1+slip)
            long_net=net_return("LONG",long_entry,long_exit,fee)
            short_net=net_return("SHORT",short_entry,short_exit,fee)
            if side=="LONG":net=long_net;chosen="LONG"
            elif side=="SHORT":net=short_net;chosen="SHORT"
            else:
                net=min(long_net,short_net);chosen=("LONG" if long_net<=short_net else "SHORT")
                counts["ambiguous"]+=1
            trades.append({"cluster_id":f["cluster_id"],"protocol":f["protocol"],"fold":f["fold"],"entry_time":trig.isoformat(),"exit_time":exit_t.isoformat(),"side":chosen,"ambiguous":amb,"net":net})
            busy_until=exit_t
        met=calc_metrics(trades)
        fold_metrics={fn:calc_metrics([t for t in trades if t["fold"]==fn]) for fn in ("F1_2021_12_TO_2022","F2_2023","F3_2024")}
        proto_metrics={p:calc_metrics([t for t in trades if t["protocol"]==p]) for p in sorted(set(t["protocol"] for t in trades))}
        positive_by_proto={p:sum(max(0.0,t["net"]) for t in trades if t["protocol"]==p) for p in proto_metrics}
        total_pos=sum(positive_by_proto.values())
        max_pos_share=(max(positive_by_proto.values())/total_pos if total_pos>0 and positive_by_proto else 1.0)
        amb_rate=(counts["ambiguous"]/len(trades) if trades else 0.0)
        rec={
          "k":k,"W":W,"H":H,"slippage_bps_per_side":slip_bps,
          "taker_fee_bps_per_side":TAKER_FEE_BPS,
          "round_trip_nominal_cost_bps":2*(TAKER_FEE_BPS+slip_bps),
          "counts":dict(counts),"metrics":met,"fold_metrics":fold_metrics,"protocol_metrics":proto_metrics,
          "positive_pnl_by_protocol":positive_by_proto,"max_positive_pnl_protocol_share":max_pos_share,
          "ambiguous_trade_rate":amb_rate
        }
        results.append(rec)

primary=[r for r in results if r["slippage_bps_per_side"]==PRIMARY_SLIP_BPS]
eligible=[]
for r in primary:
    folds=r["fold_metrics"];m=r["metrics"]
    fold_means=[folds[x]["mean"] for x in ("F1_2021_12_TO_2022","F2_2023","F3_2024")]
    ok=(m["n"]>=500 and m["mean"] is not None and m["mean"]>0 and
        all(x is not None and x>0 for x in fold_means) and
        m["profit_factor"]>1.05 and
        r["max_positive_pnl_protocol_share"]<=0.80 and
        r["ambiguous_trade_rate"]<=0.10)
    r["eligible_to_freeze_for_2025"]=ok
    r["min_fold_mean"]=min(fold_means) if all(x is not None for x in fold_means) else None
    if ok:eligible.append(r)

eligible.sort(key=lambda r:(-r["min_fold_mean"],-r["metrics"]["mean"],r["k"],r["W"],r["H"]))
selected=eligible[0] if eligible else None
classification="V02_DEVELOPMENT_EXECUTABLE_CANDIDATE_FOUND" if selected else "V02_DEVELOPMENT_NO_EXECUTABLE_EDGE"

GRID.write_text(json.dumps({
 "schema_version":"0.1","lab_id":LAB,"classification":"V02_DEVELOPMENT_GRID_COMPLETE",
 "configuration_count":len(results),"primary_configuration_count":len(primary),"results":results,
 "market_2025_opened":False,"market_2026_opened":False
},indent=2,sort_keys=True)+"\n")

selection={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "eligible_configuration_count":len(eligible),
 "selected":selected,
 "selection_rule":"highest minimum fold net mean, then overall net mean, then lower k, shorter W, shorter H",
 "primary_cost":{"taker_fee_bps_per_side":TAKER_FEE_BPS,"slippage_bps_per_side":PRIMARY_SLIP_BPS},
 "development_source_gate":source.get("classification"),
 "market_2025_opened":False,"market_2026_opened":False,
 "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False
}
SEL.write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":classification,"eligible_configuration_count":len(eligible),
 "selected":None if not selected else {
   "k":selected["k"],"W":selected["W"],"H":selected["H"],
   "trades":selected["metrics"]["n"],"mean_net":selected["metrics"]["mean"],
   "profit_factor":selected["metrics"]["profit_factor"],"min_fold_mean":selected["min_fold_mean"],
   "ambiguous_rate":selected["ambiguous_trade_rate"],"max_protocol_positive_pnl_share":selected["max_positive_pnl_protocol_share"]
 },
 "feature_ready_count":len(features),"canonical_cluster_count":len(clusters)
},indent=2))
