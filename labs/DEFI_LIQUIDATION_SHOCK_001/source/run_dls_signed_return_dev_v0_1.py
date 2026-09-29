#!/usr/bin/env python3
import argparse,csv,datetime as dt,hashlib,io,json,math,random,re,statistics,time,urllib.error,urllib.request,zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001-SIGNED-RETURN-V0.1"
SYMBOL="SOLUSDT"
MARKET_INDEX=0
START=dt.datetime(2023,1,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2023,2,1,tzinfo=dt.timezone.utc)
HORIZON_MIN=5
TAKER_FEE_BPS=8.0
SLIP_SCENARIOS_BPS=[2.0,5.0,10.0]
PRIMARY_SLIP_BPS=5.0
MIN_TRADES=30
BOOTSTRAP_N=10000
BOOTSTRAP_SEED=260929
EXPECTED_POPULATION=3179
EXPECTED_CLASSIFICATION="DRIFT_LIQUIDATE_PERP_SIGNED_FLOW_AUTHORIZED"

ap=argparse.ArgumentParser()
ap.add_argument("--signed-source",required=True)
ap.add_argument("--execution-source-gate",required=True)
ap.add_argument("--workers",type=int,default=8)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"DLS_SIGNED_RETURN_V01_DEVELOPMENT_RECEIPT_V0.1.json"
MANIFEST=OUT/"DLS_SIGNED_RETURN_V01_MARKET_DATA_MANIFEST_V0.1.ndjson"
LEDGER=OUT/"DLS_SIGNED_RETURN_V01_DEVELOPMENT_TRADE_LEDGER_V0.1.ndjson"

def parse_iso(s):
    return dt.datetime.fromisoformat(str(s).replace("Z","+00:00")).astimezone(dt.timezone.utc)

def floor_minute(x):
    return x.astimezone(dt.timezone.utc).replace(second=0,microsecond=0)

def ms(x): return int(x.timestamp()*1000)

def find_json(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits:return None,None
    return json.loads(hits[0].read_text()),str(hits[0])

def http_bytes(url,retries=7):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-signed-return-v01/0.1"})
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
        lo=ms(day0);hi=lo+86400000;bars={};prev=None;dup=0;nonmono=0
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
                bars[t]=(float(row[1]),float(row[2]),float(row[3]),float(row[4]))
        if dup or nonmono:
            rec.update({"status":"ARCHIVE_STRUCTURE_CONFLICT","duplicate_count":dup,"non_monotonic_count":nonmono});return rec,{}
        rec.update({"status":"PASS","bars":len(bars),"missing_minutes":1440-len(bars),"duplicate_count":0,"non_monotonic_count":0})
        return rec,bars
    except Exception as e:
        rec.update({"status":"ARCHIVE_PARSE_FAILURE","error":type(e).__name__,"detail":str(e)[:200]});return rec,{}

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

def metrics(rows,key="net"):
    rs=[float(x[key]) for x in rows]
    pos=sum(x for x in rs if x>0);neg=sum(x for x in rs if x<0)
    pf=(pos/abs(neg)) if neg<0 else (float("inf") if pos>0 else 0.0)
    return {
      "n":len(rs),
      "mean":(sum(rs)/len(rs) if rs else None),
      "median":(statistics.median(rs) if rs else None),
      "win_rate":(sum(1 for x in rs if x>0)/len(rs) if rs else None),
      "profit_factor":pf,
      "cumulative_simple_return":sum(rs)
    }

def day_block_bootstrap(rows,n=BOOTSTRAP_N,seed=BOOTSTRAP_SEED):
    by=defaultdict(list)
    for r in rows:by[r["entry_time"][:10]].append(float(r["net"]))
    days=sorted(by)
    if len(days)<2:return {"replicates":0,"day_count":len(days),"lower":None,"upper":None}
    rng=random.Random(seed);vals=[]
    for _ in range(n):
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
    return {"replicates":n,"day_count":len(days),"seed":seed,"lower":q(0.025),"upper":q(0.975)}

signed,path=find_json(args.signed_source,"DRIFT_JAN2023_REALIZED_SIGNED_FLOW_POPULATION_RECEIPT_V0.1.json")
gate,gpath=find_json(args.execution_source_gate,"V02_EXECUTION_SOURCE_FEASIBILITY_RECEIPT_V0.1.json")
errors=[]
if not signed:errors.append("signed_source_receipt_missing")
if not gate:errors.append("execution_source_gate_missing")
if signed:
    if signed.get("classification")!=EXPECTED_CLASSIFICATION:errors.append("signed_source_classification_not_authorized")
    if int(signed.get("population_candidate_count",-1))!=EXPECTED_POPULATION:errors.append("signed_source_population_count_mismatch")
    fam=signed.get("family") or {}
    if fam.get("protocol")!="Drift" and fam.get("protocol")!="DRIFT":errors.append("signed_source_protocol_mismatch")
if gate and gate.get("classification")!="V02_EXECUTION_SOURCE_PASS":errors.append("execution_source_gate_not_pass")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"SIGNED_RETURN_DEVELOPMENT_SOURCE_BLOCKED","stage":"authority","errors":errors,
      "oos_outcomes_opened":False,"holdout_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

rows=signed.get("results") or []
minute_sum=defaultdict(int);incomplete=set();counts=defaultdict(int)
for r in rows:
    if int(r.get("canonical_market_index",-999))!=MARKET_INDEX:continue
    t=parse_iso(r["timestamp"])
    if not(START<=t<END):continue
    m=floor_minute(t)
    counts["market0_candidates"]+=1
    status=r.get("status");lab=r.get("direction_label")
    if status=="SOURCE_EVIDENCE_INCOMPLETE":
        incomplete.add(m);counts["source_incomplete_rows"]+=1;continue
    if status=="PROVEN_NOT_REALIZED":
        counts["proven_not_realized_rows"]+=1;continue
    if status!="PROVEN_REALIZED":
        counts["unexpected_status_rows"]+=1;continue
    amt=int(r.get("signed_base_asset_amount") or 0)
    if lab=="SIGNED_BUY_PRESSURE_PROVEN":
        if amt<=0:
            errors.append("buy_label_nonpositive_signed_amount");continue
        minute_sum[m]+=abs(amt);counts["proven_buy_rows"]+=1
    elif lab=="SIGNED_SELL_PRESSURE_PROVEN":
        if amt>=0:
            errors.append("sell_label_nonnegative_signed_amount");continue
        minute_sum[m]-=abs(amt);counts["proven_sell_rows"]+=1
    else:
        errors.append("realized_row_without_proven_direction")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"SIGNED_RETURN_DEVELOPMENT_SOURCE_BLOCKED","stage":"source_semantics","errors":sorted(set(errors)),
      "source_counts":dict(counts),"oos_outcomes_opened":False,"holdout_outcomes_opened":False,
      "market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

signals=[]
for m,s in sorted(minute_sum.items()):
    if m in incomplete:
        counts["minutes_excluded_source_incomplete"]+=1;continue
    if s==0:
        counts["zero_net_minutes"]+=1;continue
    signals.append({"signal_minute":m,"entry_time":m+dt.timedelta(minutes=1),"side":"LONG" if s>0 else "SHORT","net_signed_base":s})
counts["signal_minutes"]=len(signals)
counts["long_signal_minutes"]=sum(1 for x in signals if x["side"]=="LONG")
counts["short_signal_minutes"]=sum(1 for x in signals if x["side"]=="SHORT")

days=[]
d=START.date()
while d<=dt.date(2023,1,31):
    days.append(d);d+=dt.timedelta(days=1)
bars={};manifest=[];hard=[]
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs={ex.submit(acquire_day,d):d for d in days}
    for fut in as_completed(futs):
        rec,bd=fut.result();manifest.append(rec)
        if rec["status"]=="PASS":bars.update(bd)
        else:hard.append(rec)
manifest.sort(key=lambda x:x["date"])
with MANIFEST.open("w") as fh:
    for r in manifest:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
if hard:
    RECEIPT.write_text(json.dumps({"classification":"SIGNED_RETURN_DEVELOPMENT_SOURCE_BLOCKED","stage":"market_data",
      "hard_error_count":len(hard),"hard_errors":hard,"source_counts":dict(counts),
      "oos_outcomes_opened":False,"holdout_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False},indent=2)+"\n")
    raise SystemExit(2)

base_trades=[];busy_until=None
trade_counts=defaultdict(int)
for s in signals:
    M=s["signal_minute"];A=s["entry_time"];X=A+dt.timedelta(minutes=HORIZON_MIN)
    if busy_until is not None and M<busy_until:
        trade_counts["ignored_while_position_open"]+=1;continue
    if crosses_funding(A,X):
        trade_counts["funding_boundary_excluded"]+=1;continue
    er=bars.get(ms(A));xr=bars.get(ms(X))
    if er is None or xr is None:
        trade_counts["missing_entry_or_exit_bar"]+=1;continue
    p0=er[0];px=xr[0]
    if p0<=0 or px<=0:
        trade_counts["invalid_price"]+=1;continue
    base_trades.append({
      "signal_minute":M.isoformat(),"entry_time":A.isoformat(),"exit_time":X.isoformat(),
      "side":s["side"],"net_signed_base":s["net_signed_base"],"entry_open":p0,"exit_open":px
    })
    busy_until=X
trade_counts["analyzable_trades"]=len(base_trades)

fee=TAKER_FEE_BPS/10000.0
scenarios={}
ledgers={}
for slip_bps in SLIP_SCENARIOS_BPS:
    slip=slip_bps/10000.0;tr=[]
    for b in base_trades:
        if b["side"]=="LONG":
            entry=b["entry_open"]*(1+slip);exitp=b["exit_open"]*(1-slip)
        else:
            entry=b["entry_open"]*(1-slip);exitp=b["exit_open"]*(1+slip)
        x=dict(b);x["slippage_bps_per_side"]=slip_bps;x["taker_fee_bps_per_side"]=TAKER_FEE_BPS
        x["net"]=net_return(b["side"],entry,exitp,fee);tr.append(x)
    scenarios[str(slip_bps)]=metrics(tr)
    ledgers[str(slip_bps)]=tr

primary=ledgers[str(PRIMARY_SLIP_BPS)]
pm=metrics(primary);boot=day_block_bootstrap(primary)
gate_bits={
 "n_ge_30":pm["n"]>=MIN_TRADES,
 "mean_net_gt_0":pm["mean"] is not None and pm["mean"]>0,
 "profit_factor_gt_1_05":pm["profit_factor"]>1.05,
 "bootstrap_lower_gt_0":boot["lower"] is not None and boot["lower"]>0
}
classification="SIGNED_RETURN_DEVELOPMENT_SURVIVES" if all(gate_bits.values()) else "SIGNED_RETURN_DEVELOPMENT_NO_EDGE"

with LEDGER.open("w") as fh:
    for x in primary:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")

receipt={
 "schema_version":"0.1","lab_id":LAB,"classification":classification,
 "freeze":"DLS_SIGNED_RETURN_V0_1_DEVELOPMENT_FREEZE_2026-09-29.md",
 "source_authority":{"signed_source_run_id":36525438771,"signed_source_artifact_id":11014134904,
   "signed_source_classification":signed.get("classification"),"execution_source_gate_classification":gate.get("classification"),
   "market_index":MARKET_INDEX,"market_identity":"Drift SOL-PERP","venue_symbol":"Binance USDT-M SOLUSDT"},
 "window":{"development_start":START.isoformat(),"development_end":END.isoformat(),"primary_horizon_minutes":HORIZON_MIN},
 "source_counts":dict(counts),"trade_counts":dict(trade_counts),
 "primary_cost":{"taker_fee_bps_per_side":TAKER_FEE_BPS,"slippage_bps_per_side":PRIMARY_SLIP_BPS,
   "nominal_round_trip_bps":2*(TAKER_FEE_BPS+PRIMARY_SLIP_BPS)},
 "primary_metrics":pm,"bootstrap_day_block_95ci":boot,"gate":gate_bits,
 "cost_sensitivity_metrics":scenarios,
 "market_data":{"archive_day_count":len(manifest),"archive_pass_count":sum(1 for x in manifest if x["status"]=="PASS"),
   "archive_missing_minute_count":sum(int(x.get("missing_minutes") or 0) for x in manifest),"hard_error_count":0},
 "future_boundaries":{"oos":"2023-02-01/2023-03-31","holdout":"2024-01-01/2024-12-31"},
 "firewall":{"oos_outcomes_opened":False,"holdout_outcomes_opened":False,"market_2025_opened":False,
   "market_2026_opened":False,"live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
   "merge_main":False,"post_outcome_tuning":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"source_counts":dict(counts),"trade_counts":dict(trade_counts),
 "primary_metrics":pm,"bootstrap":boot,"gate":gate_bits,"sensitivity":scenarios},indent=2,sort_keys=True))
if classification=="SIGNED_RETURN_DEVELOPMENT_SOURCE_BLOCKED":raise SystemExit(2)
