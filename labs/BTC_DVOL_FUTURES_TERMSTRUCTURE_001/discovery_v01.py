#!/usr/bin/env python3
import hashlib, json, math, random, statistics, sys, time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

ROOT=Path("labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001")
AUTH=json.loads((ROOT/"DISCOVERY_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/btc_dvol_futures_discovery_v01")
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://history.deribit.com/api/v2"
S=requests.Session()
S.headers.update({"User-Agent":"SRC-Crypto-Lab-DVOL-Discovery/0.1","Accept":"application/json"})
LOWER_MS=int(datetime(2023,3,27,tzinfo=timezone.utc).timestamp()*1000)
PROTECTED_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)

def sha(b): return hashlib.sha256(b).hexdigest()
def dt(ms): return datetime.fromtimestamp(int(ms)/1000,tz=timezone.utc)

def request(path,params,allow_miss=False):
    last=None
    for attempt,wait in enumerate((1,2,4)):
        try:
            r=S.get(BASE+path,params=params,timeout=40); raw=r.content; digest=sha(raw)
            if r.status_code==429 or 500<=r.status_code<600:
                last=RuntimeError(f"HTTP {r.status_code} {path} sha256={digest}")
                if attempt<2: time.sleep(wait); continue
                raise last
            obj=r.json()
            err=obj.get("error") if isinstance(obj,dict) else None
            if err:
                msg=str(err.get("message","")).lower() if isinstance(err,dict) else str(err).lower()
                code=err.get("code") if isinstance(err,dict) else None
                data=err.get("data") if isinstance(err,dict) else None
                wrong=(code==-32602 and isinstance(data,dict) and str(data.get("param","")).lower()=="instrument_name" and str(data.get("reason","")).lower()=="wrong format")
                miss=allow_miss and (code in (11050,10004) or ("instrument" in msg and ("not found" in msg or "invalid" in msg)) or wrong)
                if miss: return None,{"endpoint":path,"sha256":digest,"candidate_miss":True}
                raise RuntimeError(f"API error {path} sha256={digest} error={err}")
            if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code} {path} sha256={digest}")
            return obj,{"endpoint":path,"sha256":digest,"bytes":len(raw)}
        except requests.RequestException as e:
            last=e
            if attempt<2: time.sleep(wait); continue
            raise
    raise last or RuntimeError("unreachable")

def wednesdays(a,b):
    d=date.fromisoformat(a); e=date.fromisoformat(b)
    while d<=e:
        yield d; d+=timedelta(days=7)

def iname(d): return "BTCDVOL_USDC-"+d.strftime("%d%b%y").upper()

def discover():
    contracts=[]; receipts=[]
    for d in wednesdays(AUTH["source"]["candidate_start"],AUTH["source"]["candidate_end"]):
        name=iname(d)
        obj,rc=request("/public/get_instrument",{"instrument_name":name},True)
        rc["candidate"]=name; receipts.append(rc)
        if obj is None: continue
        rec=(obj or {}).get("result") or {}
        c=rec.get("creation_timestamp"); e=rec.get("expiration_timestamp")
        valid=(rec.get("instrument_name")==name and rec.get("kind")=="future" and rec.get("price_index")=="btcdvol_usdc" and isinstance(c,(int,float)) and isinstance(e,(int,float)) and int(c)<PROTECTED_MS and int(e)>=LOWER_MS and int(e)<PROTECTED_MS)
        if not valid: raise RuntimeError(f"Exact metadata integrity failure {name}")
        contracts.append({"instrument_name":name,"creation_timestamp":int(c),"expiration_timestamp":int(e)})
    return contracts,receipts

def trade_slice(name,a,b):
    if a>=PROTECTED_MS or b>=PROTECTED_MS: raise RuntimeError("Protected-period request blocked")
    obj,rc=request("/public/get_last_trades_by_instrument_and_time",{"instrument_name":name,"start_timestamp":a,"end_timestamp":b,"count":1000,"sorting":"asc"})
    rows=((obj or {}).get("result") or {}).get("trades") or []
    rc.update({"instrument_name":name,"start_ms":a,"end_ms":b,"count":len(rows)})
    if len(rows)==1000:
        if b-a<=1000: raise RuntimeError(f"Unresolved overflow {name} {a}-{b}")
        m=(a+b)//2
        l,lr=trade_slice(name,a,m); r,rr=trade_slice(name,m+1,b)
        return l+r,[rc]+lr+rr
    return rows,[rc]

def acquire(meta):
    name=meta["instrument_name"]; start=max(meta["creation_timestamp"],LOWER_MS); end=min(meta["expiration_timestamp"]-1,PROTECTED_MS-1)
    step=24*60*60*1000; cur=start; rows=[]; receipts=[]
    while cur<=end:
        e=min(cur+step-1,end); x,rr=trade_slice(name,cur,e); rows.extend(x); receipts.extend(rr); cur=e+1
        time.sleep(0.005)
    ded={}
    for i,x in enumerate(rows):
        tid=str(x.get("trade_id",f"MISSING-{i}"))
        ts=x.get("timestamp")
        if not isinstance(ts,(int,float)) or int(ts)<start or int(ts)>end or int(ts)>=PROTECTED_MS:
            raise RuntimeError(f"Out-of-bounds trade {name} {ts}")
        ded[tid]=x
    ordinary=[]
    for x in ded.values():
        if x.get("block_trade_id") is not None or x.get("combo_id") is not None: continue
        try:
            p=float(x["price"]); idx=float(x["index_price"]); ts=int(x["timestamp"])
        except Exception: raise RuntimeError(f"Missing discovery field in {name}")
        if not (math.isfinite(p) and math.isfinite(idx) and p>0 and idx>0): raise RuntimeError(f"Invalid discovery value in {name}")
        ordinary.append((ts,p,idx))
    ordinary.sort()
    return ordinary,receipts

def daily_anchors(rows,expiry_ms):
    byday={}
    for ts,p,idx in rows:
        if ts>=expiry_ms: continue
        z=dt(ts)
        if z.hour<8: continue
        day=z.date().isoformat()
        if day not in byday: byday[day]=(ts,p,idx)
    return [byday[k] for k in sorted(byday)]

def quarter(ms):
    z=dt(ms); return f"{z.year}-Q{((z.month-1)//3)+1}"

def pctile(xs,p):
    ys=sorted(xs)
    if not ys:return None
    pos=(len(ys)-1)*p; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi:return ys[lo]
    w=pos-lo; return ys[lo]*(1-w)+ys[hi]*w

def bootstrap(means,reps,seed):
    rng=random.Random(seed); n=len(means); vals=[]
    for _ in range(reps):
        vals.append(sum(means[rng.randrange(n)] for _ in range(n))/n)
    return [pctile(vals,0.025),pctile(vals,0.975)]

result={"lab_id":AUTH["lab_id"],"discovery_id":AUTH["discovery_id"],"classification":None,
"access_2025":False,"access_2026":False,"strategy_pnl_opened":False,"strategy_returns_opened":False,
"transaction_costs_opened":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
try:
    contracts,meta_receipts=discover()
    summaries=[]; source_receipts=[]; all_scores=[]
    for i,m in enumerate(contracts,1):
        rows,rr=acquire(m); source_receipts.extend(rr)
        anchors=daily_anchors(rows,m["expiration_timestamp"])
        scores=[]
        for a,b in zip(anchors,anchors[1:]):
            t0,p0,i0=a; t1,p1,i1=b
            gap=(dt(t1).date()-dt(t0).date()).days
            if gap<=0: continue
            basis0=p0-i0; basis1=p1-i1
            sgn=1.0 if basis0>0 else (-1.0 if basis0<0 else 0.0)
            score=sgn*(basis0-basis1)/gap
            if math.isfinite(score): scores.append(score); all_scores.append(score)
        if scores:
            summaries.append({"instrument_name":m["instrument_name"],"expiration_quarter":quarter(m["expiration_timestamp"]),
              "pair_n":len(scores),"mean_signed_convergence_per_day":sum(scores)/len(scores),
              "median_signed_convergence_per_day":statistics.median(scores),
              "hit_rate":sum(1 for x in scores if x>0)/len(scores)})
        print(f"DISCOVERY_PROGRESS {i}/{len(contracts)} {m['instrument_name']}",flush=True)
    means=[x["mean_signed_convergence_per_day"] for x in summaries]
    quarters=defaultdict(list)
    for x in summaries: quarters[x["expiration_quarter"]].append(x["mean_signed_convergence_per_day"])
    qmeans={q:sum(v)/len(v) for q,v in sorted(quarters.items())}
    sg=AUTH["sample_gates"]; st=AUTH["statistical_gates"]
    sample_checks={
      "contracts_with_pairs_ge_min":len(summaries)>=sg["minimum_confirmed_contracts_with_pairs"],
      "total_pairs_ge_min":len(all_scores)>=sg["minimum_total_adjacent_pairs"],
      "quarters_ge_min":len(qmeans)>=sg["minimum_distinct_expiration_quarters"]
    }
    if means:
        ci=bootstrap(means,AUTH["bootstrap"]["replications"],AUTH["bootstrap"]["seed"])
        metrics={
          "contracts_with_pairs":len(summaries),"total_adjacent_pairs":len(all_scores),
          "mean_contract_convergence_per_day":sum(means)/len(means),
          "median_contract_convergence_per_day":statistics.median(means),
          "positive_contract_share":sum(1 for x in means if x>0)/len(means),
          "pooled_pair_hit_rate":sum(1 for x in all_scores if x>0)/len(all_scores),
          "expiration_quarter_means":qmeans,
          "nonnegative_expiration_quarters":sum(1 for x in qmeans.values() if x>=0),
          "cluster_bootstrap_95_ci":ci
        }
    else:
        metrics={"contracts_with_pairs":0,"total_adjacent_pairs":0}
        ci=[None,None]
    stat_checks={
      "mean_gt_zero":bool(means) and metrics["mean_contract_convergence_per_day"]>st["mean_contract_convergence_gt"],
      "median_gt_zero":bool(means) and metrics["median_contract_convergence_per_day"]>st["median_contract_convergence_gt"],
      "positive_contract_share_gte":bool(means) and metrics["positive_contract_share"]>=st["positive_contract_share_gte"],
      "nonnegative_quarters_gte":bool(means) and metrics["nonnegative_expiration_quarters"]>=st["nonnegative_expiration_quarters_gte"],
      "bootstrap_lower_gt_zero":ci[0] is not None and ci[0]>st["cluster_bootstrap_lower_95_gt"]
    }
    if not all(sample_checks.values()): cls=AUTH["classifications"]["sample_insufficient"]
    elif all(stat_checks.values()): cls=AUTH["classifications"]["pass"]
    else: cls=AUTH["classifications"]["no_signal"]
    result.update({"classification":cls,"confirmed_contracts":len(contracts),"sample_checks":sample_checks,
      "statistical_checks":stat_checks,"metrics":metrics,"contract_summaries":summaries,
      "source_request_count":len(meta_receipts)+len(source_receipts),
      "source_receipt_sha256":sha(json.dumps(meta_receipts+source_receipts,sort_keys=True).encode())})
except Exception as e:
    txt=repr(e)
    result["classification"]=AUTH["classifications"]["provenance_failure"] if "Protected" in txt else AUTH["classifications"]["technical_failure"]
    result["error"]=txt
p=OUT/"discovery_result.json"; p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
manifest={"authority_sha256":sha((ROOT/"DISCOVERY_AUTHORITY_V0.1.json").read_bytes()),"result_sha256":sha(p.read_bytes())}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="contract_summaries"},indent=2,sort_keys=True))
sys.exit(0 if result["classification"] not in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 2)
