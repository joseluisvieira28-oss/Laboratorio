#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,statistics,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

LAB="DLS-BASIS-DISLOCATION-001"
SOL_ID="mint:So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2021,12,8,tzinfo=dt.timezone.utc)
END=dt.datetime(2023,1,1,tzinfo=dt.timezone.utc)
DOWNLOAD_START=dt.date(2021,12,7)
DOWNLOAD_END=dt.date(2022,12,31)
PRE_MIN=60
Z_THRESHOLD=2.0
HOLD_MIN=15
SPOT_FEE_BPS=10.0
FUT_FEE_BPS=8.0
SLIP_BPS=5.0
BOOT_N=10000
BOOT_SEED=260930

ap=argparse.ArgumentParser()
ap.add_argument("--cluster-source",required=True)
ap.add_argument("--workers",type=int,default=16)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"DLS_BASIS_DISLOCATION_V01_DEVELOPMENT_RECEIPT_V0.1.json"
LEDGER=OUT/"DLS_BASIS_DISLOCATION_V01_DEVELOPMENT_LEDGER_V0.1.ndjson"
MANIFEST=OUT/"DLS_BASIS_DISLOCATION_V01_MARKET_DATA_MANIFEST_V0.1.ndjson"

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def entry_minute(t):
    t=t.astimezone(dt.timezone.utc)
    return t.replace(second=0,microsecond=0)+dt.timedelta(minutes=1)

def ms(t): return int(t.timestamp()*1000)

def daterange(a,b):
    d=a
    while d<=b:
        yield d
        d+=dt.timedelta(days=1)

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if hits else None

def http_bytes(url,retries=7):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-basis-v01/0.1"})
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

def acquire_day(kind,day):
    ds=day.isoformat()
    if kind=="spot":
        base=f"https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    else:
        base=f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    ss,sb=http_bytes(base+".CHECKSUM")
    zs,zb=http_bytes(base)
    rec={"kind":kind,"date":ds,"checksum_http":ss,"zip_http":zs,"status":None,"bars":0}
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

def long_net(entry_open,exit_open,fee_bps,slip_bps):
    slip=slip_bps/10000.0;fee=fee_bps/10000.0
    entry=entry_open*(1+slip);exitp=exit_open*(1-slip)
    ratio=exitp/entry
    return (ratio-1.0)-fee*(1.0+ratio)

def short_net(entry_open,exit_open,fee_bps,slip_bps):
    slip=slip_bps/10000.0;fee=fee_bps/10000.0
    entry=entry_open*(1-slip);exitp=exit_open*(1+slip)
    ratio=exitp/entry
    return (1.0-ratio)-fee*(1.0+ratio)

def metrics(rows):
    rs=[r["portfolio_net"] for r in rows]
    pos=sum(v for v in rs if v>0);neg=sum(v for v in rs if v<0)
    pf=(pos/abs(neg)) if neg<0 else (float("inf") if pos>0 else 0.0)
    return {
      "n":len(rs),
      "mean":sum(rs)/len(rs) if rs else None,
      "median":statistics.median(rs) if rs else None,
      "win_rate":sum(1 for v in rs if v>0)/len(rs) if rs else None,
      "profit_factor":pf,
      "cumulative_simple_return":sum(rs)
    }

def block_bootstrap(rows):
    by=defaultdict(list)
    for r in rows:by[r["entry_time"][:10]].append(r["portfolio_net"])
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

receipt_path=find_one(args.cluster_source,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
census_path=find_one(args.cluster_source,"SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson")
errors=[]
if receipt_path is None:errors.append("cluster_receipt_missing")
if census_path is None:errors.append("cluster_census_missing")
if receipt_path is not None:
    src=json.loads(receipt_path.read_text())
    if src.get("classification")!="SOURCE_SAMPLE_GATE_PASS":errors.append("cluster_source_not_pass")
else:src={}
if errors:
    RECEIPT.write_text(json.dumps({"classification":"DLS_BASIS_DEVELOPMENT_SOURCE_BLOCKED","stage":"authority","errors":errors,
      "market_2023_oos_opened":False,"market_2024_holdout_opened":False,"market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

clusters=[]
with census_path.open() as fh:
    for line in fh:
        r=json.loads(line)
        if r.get("split")!="discovery":continue
        if r.get("primary_market_identity")!=SOL_ID:continue
        t0=parse_iso(r["t0"])
        if not(START<=t0<END):continue
        x=dict(r);x["T0"]=t0;x["A"]=entry_minute(t0);clusters.append(x)
clusters.sort(key=lambda r:(r["A"],r["cluster_id"]))

spot={};fut={};manifest=[];hard=[]
tasks=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    for d in daterange(DOWNLOAD_START,DOWNLOAD_END):
        tasks.append(ex.submit(acquire_day,"spot",d))
        tasks.append(ex.submit(acquire_day,"futures",d))
    for futr in as_completed(tasks):
        rec,bars=futr.result();manifest.append(rec)
        if rec["status"]!="PASS":hard.append(rec)
        elif rec["kind"]=="spot":spot.update(bars)
        else:fut.update(bars)
manifest.sort(key=lambda x:(x["date"],x["kind"]))
with MANIFEST.open("w") as fh:
    for r in manifest:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
if hard:
    RECEIPT.write_text(json.dumps({"classification":"DLS_BASIS_DEVELOPMENT_SOURCE_BLOCKED","stage":"market_data",
      "hard_error_count":len(hard),"hard_errors":hard[:100],"canonical_cluster_count":len(clusters),
      "market_2023_oos_opened":False,"market_2024_holdout_opened":False,"market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

counters=defaultdict(int);trades=[];busy_until=None
for c in clusters:
    A=c["A"];X=A+dt.timedelta(minutes=HOLD_MIN)
    if not(START<=A<END) or X>=END:
        counters["boundary_excluded"]+=1;continue
    if busy_until is not None and A<busy_until:
        counters["collision_ignored"]+=1;continue
    if crosses_funding(A,X):
        counters["funding_boundary_excluded"]+=1;continue
    pre=[]
    ok=True
    for i in range(PRE_MIN,0,-1):
        t=ms(A-dt.timedelta(minutes=i))
        ps=spot.get(t);pf=fut.get(t)
        if ps is None or pf is None or ps<=0 or pf<=0:
            ok=False;break
        pre.append(math.log(pf/ps))
    if not ok:
        counters["pre_window_incomplete"]+=1;continue
    at=ms(A);xt=ms(X)
    psa=spot.get(at);pfa=fut.get(at);psx=spot.get(xt);pfx=fut.get(xt)
    if None in (psa,pfa,psx,pfx) or min(psa,pfa,psx,pfx)<=0:
        counters["entry_exit_incomplete"]+=1;continue
    mu=sum(pre)/len(pre)
    sigma=statistics.pstdev(pre)
    if not math.isfinite(sigma) or sigma<=0:
        counters["basis_sigma_invalid"]+=1;continue
    bA=math.log(pfa/psa);z=(bA-mu)/sigma
    if abs(z)<Z_THRESHOLD:
        counters["below_threshold"]+=1;continue
    if z>=Z_THRESHOLD:
        side="SHORT_PERP_LONG_SPOT"
        spot_net=long_net(psa,psx,SPOT_FEE_BPS,SLIP_BPS)
        fut_net=short_net(pfa,pfx,FUT_FEE_BPS,SLIP_BPS)
    else:
        side="LONG_PERP_SHORT_SPOT"
        spot_net=short_net(psa,psx,SPOT_FEE_BPS,SLIP_BPS)
        fut_net=long_net(pfa,pfx,FUT_FEE_BPS,SLIP_BPS)
    net=.5*spot_net+.5*fut_net
    fold="F1" if A<dt.datetime(2022,7,1,tzinfo=dt.timezone.utc) else "F2"
    trades.append({
      "cluster_id":c["cluster_id"],"protocol":c["protocol"],"instruction_class":c["instruction_class"],
      "t0":c["T0"].isoformat(),"entry_time":A.isoformat(),"exit_time":X.isoformat(),"fold":fold,
      "basis_z":z,"basis_at_entry":bA,"pre_basis_mean":mu,"pre_basis_sigma":sigma,"side":side,
      "spot_entry_open":psa,"spot_exit_open":psx,"futures_entry_open":pfa,"futures_exit_open":pfx,
      "spot_leg_net":spot_net,"futures_leg_net":fut_net,"portfolio_net":net
    })
    busy_until=X
    counters["trades"]+=1

with LEDGER.open("w") as fh:
    for r in trades:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
overall=metrics(trades)
f1=metrics([r for r in trades if r["fold"]=="F1"])
f2=metrics([r for r in trades if r["fold"]=="F2"])
boot=block_bootstrap(trades)
gate={
 "n_ge_100":overall["n"]>=100,
 "mean_gt_0":overall["mean"] is not None and overall["mean"]>0,
 "median_gt_0":overall["median"] is not None and overall["median"]>0,
 "profit_factor_gt_1_05":overall["profit_factor"]>1.05,
 "f1_n_ge_30":f1["n"]>=30,
 "f2_n_ge_30":f2["n"]>=30,
 "f1_mean_gt_0":f1["mean"] is not None and f1["mean"]>0,
 "f2_mean_gt_0":f2["mean"] is not None and f2["mean"]>0,
 "bootstrap_lower_gt_0":boot["lower"] is not None and boot["lower"]>0
}
classification="DLS_BASIS_DEVELOPMENT_SURVIVES" if all(gate.values()) else "DLS_BASIS_DEVELOPMENT_NO_EDGE"
receipt={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "freeze":"DLS_BASIS_DISLOCATION_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md",
 "source":{"run_id":36465385517,"artifact_id":10988887983,"classification":src.get("classification"),
           "canonical_cluster_count":len(clusters),"primary_market_identity":SOL_ID},
 "rule":{"pre_minutes":PRE_MIN,"z_threshold":Z_THRESHOLD,"hold_minutes":HOLD_MIN,
         "spot_fee_bps_per_side":SPOT_FEE_BPS,"futures_fee_bps_per_side":FUT_FEE_BPS,
         "slippage_bps_per_side_each_leg":SLIP_BPS,"nominal_portfolio_round_trip_cost_bps":28.0},
 "market_data":{"manifest_count":len(manifest),"pass_count":sum(1 for r in manifest if r["status"]=="PASS"),
                "missing_minute_count":sum(int(r.get("missing_minutes") or 0) for r in manifest),"hard_error_count":0},
 "counters":dict(counters),"overall":overall,"F1":f1,"F2":f2,"bootstrap_day_block_95ci":boot,"gate":gate,
 "future_boundaries":{"oos_2023":"2023-01-01/2023-12-31","holdout_2024":"2024-01-01/2024-12-31"},
 "firewall":{"signed_flow_used":False,"market_2023_oos_opened":False,"market_2024_holdout_opened":False,
   "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,"wallets":False,
   "exchange_mutation":False,"merge_main":False,"post_outcome_tuning":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"canonical_clusters":len(clusters),"counters":dict(counters),
 "overall":overall,"F1":f1,"F2":f2,"bootstrap":boot,"gate":gate},indent=2,sort_keys=True))
