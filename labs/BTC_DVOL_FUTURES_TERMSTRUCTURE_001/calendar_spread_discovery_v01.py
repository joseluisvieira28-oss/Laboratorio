#!/usr/bin/env python3
import hashlib,json,math,random,statistics,sys,time
from collections import defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

ROOT=Path("labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001")
AUTH=json.loads((ROOT/"CALENDAR_SPREAD_DISCOVERY_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/btc_dvol_calendar_spread_discovery_v01");OUT.mkdir(parents=True,exist_ok=True)
BASE="https://history.deribit.com/api/v2"
S=requests.Session();S.headers.update({"User-Agent":"SRC-Crypto-Lab-DVOL-CalendarDiscovery/0.1","Accept":"application/json"})
LOWER_MS=int(datetime(2023,3,27,tzinfo=timezone.utc).timestamp()*1000)
PROTECTED_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)

def sha(b):return hashlib.sha256(b).hexdigest()
def zdt(ms):return datetime.fromtimestamp(int(ms)/1000,tz=timezone.utc)

def request(path,params,allow_miss=False):
    last=None
    for attempt,wait in enumerate((1,2,4)):
        try:
            r=S.get(BASE+path,params=params,timeout=40);raw=r.content;dig=sha(raw)
            if r.status_code==429 or 500<=r.status_code<600:
                last=RuntimeError(f"HTTP {r.status_code} {path} sha256={dig}")
                if attempt<2:time.sleep(wait);continue
                raise last
            obj=r.json();err=obj.get("error") if isinstance(obj,dict) else None
            if err:
                msg=str(err.get("message","")).lower() if isinstance(err,dict) else str(err).lower()
                code=err.get("code") if isinstance(err,dict) else None
                data=err.get("data") if isinstance(err,dict) else None
                wrong=(code==-32602 and isinstance(data,dict) and str(data.get("param","")).lower()=="instrument_name" and str(data.get("reason","")).lower()=="wrong format")
                miss=allow_miss and (code in (11050,10004) or ("instrument" in msg and ("not found" in msg or "invalid" in msg)) or wrong)
                if miss:return None,{"endpoint":path,"sha256":dig,"candidate_miss":True}
                raise RuntimeError(f"API error {path} sha256={dig} error={err}")
            if r.status_code!=200:raise RuntimeError(f"HTTP {r.status_code} {path} sha256={dig}")
            return obj,{"endpoint":path,"sha256":dig,"bytes":len(raw)}
        except requests.RequestException as e:
            last=e
            if attempt<2:time.sleep(wait);continue
            raise
    raise last or RuntimeError("unreachable")

def wednesdays(a,b):
    d=date.fromisoformat(a);e=date.fromisoformat(b)
    while d<=e:yield d;d+=timedelta(days=7)
def iname(d):return "BTCDVOL_USDC-"+d.strftime("%d%b%y").upper()

def discover():
    out=[];receipts=[]
    for d in wednesdays(AUTH["source"]["candidate_start"],AUTH["source"]["candidate_end"]):
        name=iname(d);obj,rc=request("/public/get_instrument",{"instrument_name":name},True);rc["candidate"]=name;receipts.append(rc)
        if obj is None:continue
        rec=(obj or {}).get("result") or {};c=rec.get("creation_timestamp");e=rec.get("expiration_timestamp")
        valid=(rec.get("instrument_name")==name and rec.get("kind")=="future" and rec.get("price_index")=="btcdvol_usdc" and isinstance(c,(int,float)) and isinstance(e,(int,float)) and int(c)<PROTECTED_MS and int(e)>=LOWER_MS and int(e)<PROTECTED_MS)
        if not valid:raise RuntimeError(f"Metadata integrity failure {name}")
        out.append({"instrument_name":name,"creation_timestamp":int(c),"expiration_timestamp":int(e)})
    return sorted(out,key=lambda x:x["expiration_timestamp"]),receipts

def slice_trades(name,a,b):
    if a>=PROTECTED_MS or b>=PROTECTED_MS:raise RuntimeError("Protected-period request blocked")
    obj,rc=request("/public/get_last_trades_by_instrument_and_time",{"instrument_name":name,"start_timestamp":a,"end_timestamp":b,"count":1000,"sorting":"asc"})
    rows=((obj or {}).get("result") or {}).get("trades") or [];rc.update({"instrument_name":name,"start_ms":a,"end_ms":b,"count":len(rows)})
    if len(rows)==1000:
        if b-a<=1000:raise RuntimeError(f"Unresolved overflow {name}")
        m=(a+b)//2;l,lr=slice_trades(name,a,m);r,rr=slice_trades(name,m+1,b);return l+r,[rc]+lr+rr
    return rows,[rc]

def acquire(name,a,b):
    cur=a;step=86400000;rows=[];rcs=[]
    while cur<=b:
        e=min(cur+step-1,b);x,rr=slice_trades(name,cur,e);rows.extend(x);rcs.extend(rr);cur=e+1;time.sleep(0.005)
    ded={}
    for i,x in enumerate(rows):
        ts=x.get("timestamp")
        if not isinstance(ts,(int,float)) or int(ts)<a or int(ts)>b or int(ts)>=PROTECTED_MS:raise RuntimeError(f"Out-of-bounds {name}")
        ded[str(x.get("trade_id",f"MISSING-{i}"))]=x
    out=[]
    for x in ded.values():
        if any(x.get(k) is not None for k in ("block_trade_id","block_rfq_quote_id","combo_id","combo_trade_id")):continue
        try:ts=int(x["timestamp"]);p=float(x["price"]);idx=float(x["index_price"])
        except Exception:raise RuntimeError(f"Missing field {name}")
        if not(math.isfinite(p) and math.isfinite(idx) and p>0 and idx>0):raise RuntimeError(f"Invalid value {name}")
        out.append((ts,p,idx))
    out.sort();return out,rcs

def anchors(rows):
    by={}
    for ts,p,idx in rows:
        z=zdt(ts)
        if z.hour<8:continue
        k=z.date().isoformat()
        if k not in by:by[k]=(ts,p,idx)
    return by

def qtr(ms):
    z=zdt(ms);return f"{z.year}-Q{((z.month-1)//3)+1}"

def pctile(xs,p):
    ys=sorted(xs)
    if not ys:return None
    v=(len(ys)-1)*p;lo=int(math.floor(v));hi=int(math.ceil(v))
    if lo==hi:return ys[lo]
    w=v-lo;return ys[lo]*(1-w)+ys[hi]*w

def bootstrap(means,reps,seed):
    rng=random.Random(seed);n=len(means);vals=[]
    for _ in range(reps):vals.append(sum(means[rng.randrange(n)] for _ in range(n))/n)
    return [pctile(vals,0.025),pctile(vals,0.975)]

result={"lab_id":AUTH["lab_id"],"discovery_id":AUTH["discovery_id"],"classification":None,"access_2025":False,"access_2026":False,"transaction_costs_opened":False,"strategy_pnl_opened":False,"strategy_returns_opened":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
try:
    contracts,meta_rc=discover();source_rc=[];summ=[];all_scores=[];zero=0
    for i,(near,far) in enumerate(zip(contracts,contracts[1:]),1):
        start=max(near["creation_timestamp"],far["creation_timestamp"],LOWER_MS);end=min(near["expiration_timestamp"],far["expiration_timestamp"],PROTECTED_MS)-1
        if end<start:continue
        nr,nrc=acquire(near["instrument_name"],start,end);fr,frc=acquire(far["instrument_name"],start,end);source_rc.extend(nrc+frc)
        na=anchors(nr);fa=anchors(fr);days=sorted(set(na)&set(fa));scores=[]
        for d0,d1 in zip(days,days[1:]):
            n0=na[d0];f0=fa[d0];n1=na[d1];f1=fa[d1]
            basis=n0[1]-n0[2]
            if basis==0:zero+=1;continue
            sign=-1.0 if basis>0 else 1.0
            gap=(date.fromisoformat(d1)-date.fromisoformat(d0)).days
            if gap<=0:continue
            score=sign*((n1[1]-n0[1])-(f1[1]-f0[1]))/gap
            if math.isfinite(score):scores.append(score);all_scores.append(score)
        if scores:
            summ.append({"near":near["instrument_name"],"far":far["instrument_name"],"near_expiration_quarter":qtr(near["expiration_timestamp"]),
              "score_n":len(scores),"mean_hedged_score_per_day":sum(scores)/len(scores),"median_hedged_score_per_day":statistics.median(scores),
              "hit_rate":sum(1 for x in scores if x>0)/len(scores)})
        print(f"CAL_DISCOVERY_PROGRESS {i}/{len(contracts)-1} {near['instrument_name']}->{far['instrument_name']}",flush=True)
    means=[x["mean_hedged_score_per_day"] for x in summ];quarters=defaultdict(list)
    for x in summ:quarters[x["near_expiration_quarter"]].append(x["mean_hedged_score_per_day"])
    qmeans={k:sum(v)/len(v) for k,v in sorted(quarters.items())};ci=bootstrap(means,AUTH["bootstrap"]["replications"],AUTH["bootstrap"]["seed"]) if means else [None,None]
    sg=AUTH["sample_gates"];st=AUTH["statistical_gates"]
    sample_checks={"pairs_ge_min":len(summ)>=sg["minimum_pair_clusters_with_scores"],"scores_ge_min":len(all_scores)>=sg["minimum_total_adjacent_common_day_scores"],"quarters_ge_min":len(qmeans)>=sg["minimum_distinct_near_expiration_quarters"]}
    metrics={"pair_clusters_with_scores":len(summ),"total_scores":len(all_scores),"mean_pair_score_per_day":sum(means)/len(means) if means else None,
      "median_pair_score_per_day":statistics.median(means) if means else None,"positive_pair_share":sum(1 for x in means if x>0)/len(means) if means else 0.0,
      "pooled_hit_rate":sum(1 for x in all_scores if x>0)/len(all_scores) if all_scores else 0.0,"near_expiration_quarter_means":qmeans,
      "nonnegative_quarters":sum(1 for x in qmeans.values() if x>=0),"cluster_bootstrap_95_ci":ci,"zero_basis_exclusions":zero}
    stat_checks={"mean_gt_zero":metrics["mean_pair_score_per_day"] is not None and metrics["mean_pair_score_per_day"]>st["mean_pair_score_gt"],
      "median_gt_zero":metrics["median_pair_score_per_day"] is not None and metrics["median_pair_score_per_day"]>st["median_pair_score_gt"],
      "positive_pair_share_gte":metrics["positive_pair_share"]>=st["positive_pair_share_gte"],
      "nonnegative_quarters_gte":metrics["nonnegative_quarters"]>=st["nonnegative_near_expiration_quarters_gte"],
      "bootstrap_lower_gt_zero":ci[0] is not None and ci[0]>st["cluster_bootstrap_lower_95_gt"]}
    if not all(sample_checks.values()):cls=AUTH["classifications"]["insufficient"]
    elif all(stat_checks.values()):cls=AUTH["classifications"]["pass"]
    else:cls=AUTH["classifications"]["no_signal"]
    result.update({"classification":cls,"sample_checks":sample_checks,"statistical_checks":stat_checks,"metrics":metrics,"pair_summaries":summ,
      "source_request_count":len(meta_rc)+len(source_rc),"source_receipt_sha256":sha(json.dumps(meta_rc+source_rc,sort_keys=True).encode())})
except Exception as e:
    txt=repr(e);result["classification"]=AUTH["classifications"]["provenance_failure"] if "Protected" in txt else AUTH["classifications"]["technical_failure"];result["error"]=txt
p=OUT/"calendar_spread_discovery_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
(OUT/"manifest.json").write_text(json.dumps({"authority_sha256":sha((ROOT/"CALENDAR_SPREAD_DISCOVERY_AUTHORITY_V0.1.json").read_bytes()),"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="pair_summaries"},indent=2,sort_keys=True))
sys.exit(0 if result["classification"] not in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 2)
