#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,re,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
SOL_MINT="mint:So11111111111111111111111111111111111111112"
SYMBOL="SOLUSDT"
START=dt.datetime(2021,12,8,tzinfo=dt.timezone.utc)
END=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)
K_GRID=[0.25,0.50,0.75,1.00,1.50]
W_GRID=[5,15,30]
H_GRID=[5,15,30,60]
SLIPPAGE={"20bps":0.0002,"26bps":0.0005,"36bps":0.0010}
TAKER_FEE_SIDE=0.0008
EXPECTED_SOURCE_CLUSTERS=15603

ap=argparse.ArgumentParser()
ap.add_argument("--source-gate",required=True)
ap.add_argument("--sample-gate",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
ap.add_argument("--workers",type=int,default=16)
args=ap.parse_args()

OUT=Path(args.outdir); OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"DLS_V0_2_DEVELOPMENT_RESULT_RECEIPT_V0.1.json"
MANIFEST=OUT/"DLS_V0_2_FUTURES_ARCHIVE_MANIFEST_V0.1.ndjson"
TRADES=OUT/"DLS_V0_2_SELECTED_CONFIG_TRADES_V0.1.ndjson"

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
        yield d
        d+=dt.timedelta(days=1)

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as fh:
        for block in iter(lambda:fh.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def http_bytes(url,retries=6,allow_404=False):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-v02-exec/0.1"})
            with urllib.request.urlopen(q,timeout=60) as r:return int(r.status),r.read()
        except urllib.error.HTTPError as e:
            if allow_404 and e.code==404:return 404,None
            last={"http":e.code}
            if e.code in (429,500,502,503,504):
                time.sleep(min(20,2**i));continue
            return int(e.code),None
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:220]}
            time.sleep(min(20,2**i))
    return None,last

source_gate,_=find_one(args.source_gate,"DLS_V0_2_FUTURES_SOURCE_GATE_RECEIPT_V0.1.json")
sample_receipt,_=find_one(args.sample_gate,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
census_hits=sorted(Path(args.sample_gate).rglob("SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson"))
pre_errors=[]
if not source_gate or source_gate.get("classification")!="DLS_V0_2_FUTURES_SOURCE_PASS":
    pre_errors.append({"reason":"futures_source_gate_not_pass","classification":(source_gate or {}).get("classification")})
if not sample_receipt or sample_receipt.get("classification")!="SOURCE_SAMPLE_GATE_PASS":
    pre_errors.append({"reason":"sample_gate_not_pass","classification":(sample_receipt or {}).get("classification")})
if not census_hits:pre_errors.append({"reason":"cluster_census_missing"})
if census_hits:
    obs=file_sha256(census_hits[0]); exp=((sample_receipt or {}).get("cluster_census") or {}).get("sha256")
    if not exp or obs!=exp:pre_errors.append({"reason":"cluster_census_sha256_mismatch","observed":obs,"expected":exp})
if pre_errors:
    r={"schema_version":"0.1","lab_id":LAB,"classification":"DLS_V0_2_DEVELOPMENT_SOURCE_BLOCKED",
       "stage":"pre_acquisition","error_count":len(pre_errors),"errors":pre_errors,
       "futures_prices_opened":False,"protected_2025_opened":False,"protected_2026_opened":False}
    RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,indent=2));raise SystemExit(2)

clusters=[]
with census_hits[0].open() as fh:
    for line in fh:
        r=json.loads(line)
        if r.get("primary_market_identity")!=SOL_MINT:continue
        t0=parse_iso(r["t0"])
        if not (START<=t0<END):continue
        x=dict(r);x["_t0"]=t0;x["_A"]=ceil_minute(t0)
        clusters.append(x)
clusters.sort(key=lambda x:(x["_A"],x["cluster_id"]))
if len(clusters)!=EXPECTED_SOURCE_CLUSTERS:
    r={"schema_version":"0.1","lab_id":LAB,"classification":"DLS_V0_2_DEVELOPMENT_SOURCE_BLOCKED",
       "stage":"population_binding","observed_source_clusters":len(clusters),"expected":EXPECTED_SOURCE_CLUSTERS,
       "futures_prices_opened":False,"protected_2025_opened":False,"protected_2026_opened":False}
    RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,indent=2));raise SystemExit(2)

bars={}
manifest=[]
hard_errors=[]

def acquire_day(day):
    ds=day.isoformat()
    base=f"https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    ss,sb=http_bytes(base+".CHECKSUM",allow_404=True)
    zs,zb=http_bytes(base,allow_404=True)
    row={"symbol":SYMBOL,"date":ds,"zip_http":zs,"checksum_http":ss,"status":None}
    if ss!=200 or zs!=200 or not isinstance(sb,(bytes,bytearray)) or not isinstance(zb,(bytes,bytearray)):
        row["status"]="MISSING_OR_TRANSPORT";return row,{}
    m=re.search(rb"([0-9a-fA-F]{64})",sb)
    if not m:
        row["status"]="CHECKSUM_FORMAT_INVALID";return row,{}
    exp=m.group(1).decode().lower();obs=hashlib.sha256(zb).hexdigest()
    row["expected_sha256"]=exp;row["observed_sha256"]=obs
    if exp!=obs:
        row["status"]="CHECKSUM_MISMATCH";return row,{}
    try:
        z=zipfile.ZipFile(io.BytesIO(zb))
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=1:
            row["status"]="ZIP_MEMBER_COUNT_INVALID";return row,{}
        start=ms(dt.datetime.combine(day,dt.time(0),tzinfo=dt.timezone.utc));end=start+86400000
        out={};prev=None;dup=0;nonmono=0
        with z.open(names[0]) as fh:
            reader=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
            for rec in reader:
                if not rec:continue
                t=int(rec[0])
                if t>10**14:t//=1000
                if t%60000!=0:
                    row["status"]="TIMESTAMP_NOT_MINUTE_ALIGNED";row["timestamp"]=t;return row,{}
                if not(start<=t<end):
                    row["status"]="OUT_OF_DAY_TIMESTAMP";row["timestamp"]=t;return row,{}
                if prev is not None and t<=prev:
                    if t==prev:dup+=1
                    else:nonmono+=1
                prev=t
                if t in out:dup+=1
                out[t]=(Decimal(rec[1]),Decimal(rec[2]),Decimal(rec[3]),Decimal(rec[4]))
        row.update({"status":"PASS","bar_count":len(out),"missing_minutes":1440-len(out),
                    "duplicate_count":dup,"non_monotonic_count":nonmono})
        if len(out)!=1440 or dup or nonmono:row["status"]="ARCHIVE_STRUCTURE_CONFLICT"
        return row,out
    except Exception as e:
        row.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:220]});return row,{}

# Include previous day for 60 pre-event returns at development start.
days=list(daterange(dt.date(2021,12,7),dt.date(2024,12,31)))
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in days}
    for fut in as_completed(futs):
        row,bd=fut.result();manifest.append(row)
        if row["status"]=="PASS":bars.update(bd)
        else:hard_errors.append({"reason":row["status"],"date":row["date"]})
manifest.sort(key=lambda x:x["date"])
with MANIFEST.open("w") as fh:
    for r in manifest:fh.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")

if hard_errors:
    r={"schema_version":"0.1","lab_id":LAB,"classification":"DLS_V0_2_DEVELOPMENT_SOURCE_BLOCKED",
       "stage":"futures_archive_acquisition","source_cluster_count":len(clusters),
       "archive_day_count":len(manifest),"hard_error_count":len(hard_errors),"hard_errors":hard_errors[:100],
       "protected_2025_opened":False,"protected_2026_opened":False}
    RECEIPT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":r["classification"],"hard_error_count":len(hard_errors)},indent=2));raise SystemExit(2)

def ohlc(t):
    return bars.get(ms(t))

def sigma60(A):
    opens=[]
    for j in range(61):
        b=ohlc(A-dt.timedelta(minutes=61-j))
        if b is None:return None
        opens.append(float(b[0]))
    rs=[math.log(opens[i]/opens[i-1]) for i in range(1,len(opens))]
    return math.sqrt(sum(x*x for x in rs)/60.0)

def fold_of(A):
    if A.year<=2022:return "2021_12_08_to_2022_12_31"
    if A.year==2023:return "2023"
    if A.year==2024:return "2024"
    return None

def trade_return(side,raw_fill,raw_exit,slip):
    rf=float(raw_fill);rx=float(raw_exit)
    if side=="LONG":
        entry=rf*(1+slip);exitp=rx*(1-slip);gross=exitp/entry-1
    else:
        entry=rf*(1-slip);exitp=rx*(1+slip);gross=(entry-exitp)/entry
    return gross-2*TAKER_FEE_SIDE

def simulate(k,W,H):
    state={"source_cascades":len(clusters),"collision_ignored":0,"pre_event_missing":0,
           "no_breakout":0,"exit_missing_or_boundary":0,"trades":0,"ambiguous":0}
    raw=[]
    open_until=None
    for c in clusters:
        A=c["_A"]
        if open_until is not None and A<open_until:
            state["collision_ignored"]+=1;continue
        sig=sigma60(A)
        ref=ohlc(A)
        if sig is None or ref is None:
            state["pre_event_missing"]+=1;continue
        pA=float(ref[0]);upper=pA*math.exp(k*sig);lower=pA*math.exp(-k*sig)
        fill=None
        for j in range(W):
            T=A+dt.timedelta(minutes=j)
            b=ohlc(T)
            if b is None:continue
            hi=float(b[1]);lo=float(b[2])
            up=hi>=upper;dn=lo<=lower
            if up or dn:
                fill=(T,up,dn);break
        if fill is None:
            state["no_breakout"]+=1;continue
        F,up,dn=fill
        X=F+dt.timedelta(minutes=H)
        if X>=END:
            state["exit_missing_or_boundary"]+=1;continue
        xb=ohlc(X)
        if xb is None:
            state["exit_missing_or_boundary"]+=1;continue
        raw.append({"cluster_id":c["cluster_id"],"protocol":c["protocol"],"class":c["instruction_class"],
                    "event_t0":c["t0"],"A":A.strftime("%Y-%m-%dT%H:%M:00Z"),
                    "fill_time":F.strftime("%Y-%m-%dT%H:%M:00Z"),"exit_time":X.strftime("%Y-%m-%dT%H:%M:00Z"),
                    "fold":fold_of(A),"upper":upper,"lower":lower,"exit_open":float(xb[0]),
                    "up":up,"down":dn,"ambiguous":bool(up and dn)})
        state["trades"]+=1
        if up and dn:state["ambiguous"]+=1
        open_until=X
    return state,raw

def metrics_for(raw,slip):
    vals=[];by_fold=defaultdict(list);by_protocol=defaultdict(list);trade_rows=[]
    for x in raw:
        if x["ambiguous"]:
            lr=trade_return("LONG",x["upper"],x["exit_open"],slip)
            sr=trade_return("SHORT",x["lower"],x["exit_open"],slip)
            ret=min(lr,sr);side="AMBIGUOUS_WORST"
        elif x["up"]:
            ret=trade_return("LONG",x["upper"],x["exit_open"],slip);side="LONG"
        else:
            ret=trade_return("SHORT",x["lower"],x["exit_open"],slip);side="SHORT"
        vals.append(ret);by_fold[x["fold"]].append(ret);by_protocol[x["protocol"]].append(ret)
        y=dict(x);y.update({"side":side,"net_return":ret});trade_rows.append(y)
    n=len(vals)
    if not n:return {"trade_count":0},trade_rows
    pos=sum(v for v in vals if v>0);neg=-sum(v for v in vals if v<0)
    pf_inf=(neg==0 and pos>0);pf=(None if pf_inf else (pos/neg if neg>0 else 0.0))
    csum=0.0;peak=0.0;mdd=0.0
    for v in vals:
        csum+=v;peak=max(peak,csum);mdd=max(mdd,peak-csum)
    protocol_positive={p:sum(max(v,0.0) for v in vs) for p,vs in by_protocol.items()}
    total_positive=sum(protocol_positive.values())
    conc=(max(protocol_positive.values())/total_positive) if total_positive>0 and protocol_positive else 1.0
    return {
      "trade_count":n,"mean_net_return":sum(vals)/n,"median_net_return":sorted(vals)[n//2] if n%2 else (sorted(vals)[n//2-1]+sorted(vals)[n//2])/2,
      "win_rate":sum(1 for v in vals if v>0)/n,"profit_factor":pf,"profit_factor_infinite":pf_inf,
      "cumulative_simple_net_return":csum,"max_drawdown":mdd,
      "folds":{k:{"n":len(vs),"mean_net_return":sum(vs)/len(vs)} for k,vs in sorted(by_fold.items())},
      "protocol_positive_pnl":protocol_positive,"max_positive_pnl_protocol_concentration":conc
    },trade_rows

results=[]
raw_cache={}
for k in K_GRID:
    for W in W_GRID:
        for H in H_GRID:
            key=f"k={k}|W={W}|H={H}"
            state,raw=simulate(k,W,H);raw_cache[key]=(state,raw)
            for label,slip in SLIPPAGE.items():
                met,_=metrics_for(raw,slip)
                activation=state["trades"]+state["no_breakout"]
                row={"k":k,"W":W,"H":H,"cost_scenario":label,"slippage_per_side":slip,
                     "state":state,"no_trade_rate":state["no_breakout"]/activation if activation else None,
                     "ambiguous_first_bar_rate":state["ambiguous"]/state["trades"] if state["trades"] else None,
                     "metrics":met}
                results.append(row)

primary=[r for r in results if r["cost_scenario"]=="26bps"]
eligible=[]
for r in primary:
    m=r["metrics"];folds=m.get("folds") or {}
    checks={
      "trades_ge_500":m.get("trade_count",0)>=500,
      "overall_mean_positive":(m.get("mean_net_return") or -999)>0,
      "all_three_folds_positive":all((folds.get(f) or {}).get("mean_net_return", -999)>0 for f in ["2021_12_08_to_2022_12_31","2023","2024"]),
      "profit_factor_gt_1_05":bool(m.get("profit_factor_infinite")) or ((m.get("profit_factor") or 0)>1.05),
      "positive_pnl_concentration_le_80pct":(m.get("max_positive_pnl_protocol_concentration") or 1)<=0.80,
      "ambiguous_rate_le_10pct":(r.get("ambiguous_first_bar_rate") or 0)<=0.10
    }
    r["eligibility_checks"]=checks;r["eligible_to_freeze_for_2025"]=all(checks.values())
    if r["eligible_to_freeze_for_2025"]:
        fold_means=[folds[f]["mean_net_return"] for f in ["2021_12_08_to_2022_12_31","2023","2024"]]
        r["_min_fold_mean"]=min(fold_means);eligible.append(r)

selected=None
if eligible:
    selected=sorted(eligible,key=lambda r:(-r["_min_fold_mean"],-r["metrics"]["mean_net_return"],r["k"],r["W"],r["H"]))[0]
    selected={k:v for k,v in selected.items() if not k.startswith("_")}
classification="DLS_V0_2_DEVELOPMENT_CANDIDATE_READY" if selected else "DLS_V0_2_DEVELOPMENT_NO_EXECUTABLE_EDGE"

selected_trades=[]
if selected:
    key=f"k={selected['k']}|W={selected['W']}|H={selected['H']}"
    _,raw=raw_cache[key]
    _,selected_trades=metrics_for(raw,SLIPPAGE["26bps"])
with TRADES.open("w") as fh:
    for t in selected_trades:fh.write(json.dumps(t,sort_keys=True,separators=(",",":"))+"\n")

receipt={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "source_gate_classification":source_gate.get("classification"),
 "source_cluster_count":len(clusters),"archive_day_count":len(manifest),
 "grid":{"k":K_GRID,"W":W_GRID,"H":H_GRID,"configuration_count":60,"cost_scenarios":SLIPPAGE},
 "primary_cost_scenario":"26bps","taker_fee_per_side":TAKER_FEE_SIDE,
 "result_count":len(results),"eligible_configuration_count":len(eligible),
 "selected_configuration":selected,
 "results":results,
 "development_period":{"start":"2021-12-08T00:00:00Z","end_exclusive":"2025-01-01T00:00:00Z",
                       "folds":["2021_12_08_to_2022_12_31","2023","2024"]},
 "protected_2025_opened":False,"protected_2026_opened":False,
 "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
 "post_outcome_parameter_expansion":False
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"source_clusters":len(clusters),
                  "eligible_configuration_count":len(eligible),
                  "selected":selected},indent=2))
