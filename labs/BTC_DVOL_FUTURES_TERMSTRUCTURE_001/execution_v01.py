#!/usr/bin/env python3
import hashlib,json,math,random,statistics,sys,time
from collections import defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

ROOT=Path("labs/BTC_DVOL_FUTURES_TERMSTRUCTURE_001")
AUTH=json.loads((ROOT/"EXECUTION_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/btc_dvol_futures_execution_v01"); OUT.mkdir(parents=True,exist_ok=True)
BASE="https://history.deribit.com/api/v2"
S=requests.Session(); S.headers.update({"User-Agent":"SRC-Crypto-Lab-DVOL-Execution/0.1","Accept":"application/json"})
LOWER_MS=int(datetime(2023,3,27,tzinfo=timezone.utc).timestamp()*1000)
PROTECTED_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)

def sha(b): return hashlib.sha256(b).hexdigest()
def dt(ms): return datetime.fromtimestamp(int(ms)/1000,tz=timezone.utc)

def request(path,params,allow_miss=False):
    last=None
    for attempt,wait in enumerate((1,2,4)):
        try:
            r=S.get(BASE+path,params=params,timeout=40); raw=r.content; dig=sha(raw)
            if r.status_code==429 or 500<=r.status_code<600:
                last=RuntimeError(f"HTTP {r.status_code} {path} sha256={dig}")
                if attempt<2: time.sleep(wait); continue
                raise last
            obj=r.json(); err=obj.get("error") if isinstance(obj,dict) else None
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
        if not valid:raise RuntimeError(f"Exact metadata integrity failure {name}")
        out.append({"instrument_name":name,"creation_timestamp":int(c),"expiration_timestamp":int(e)})
    return out,receipts

def trade_slice(name,a,b):
    if a>=PROTECTED_MS or b>=PROTECTED_MS:raise RuntimeError("Protected-period request blocked")
    obj,rc=request("/public/get_last_trades_by_instrument_and_time",{"instrument_name":name,"start_timestamp":a,"end_timestamp":b,"count":1000,"sorting":"asc"})
    rows=((obj or {}).get("result") or {}).get("trades") or [];rc.update({"instrument_name":name,"start_ms":a,"end_ms":b,"count":len(rows)})
    if len(rows)==1000:
        if b-a<=1000:raise RuntimeError(f"Unresolved overflow {name}")
        m=(a+b)//2;l,lr=trade_slice(name,a,m);r,rr=trade_slice(name,m+1,b);return l+r,[rc]+lr+rr
    return rows,[rc]

def acquire(meta):
    name=meta["instrument_name"];start=max(meta["creation_timestamp"],LOWER_MS);end=min(meta["expiration_timestamp"]-1,PROTECTED_MS-1)
    cur=start;step=86400000;rows=[];receipts=[]
    while cur<=end:
        e=min(cur+step-1,end);x,rr=trade_slice(name,cur,e);rows.extend(x);receipts.extend(rr);cur=e+1;time.sleep(0.005)
    ded={}
    for i,x in enumerate(rows):
        ts=x.get("timestamp")
        if not isinstance(ts,(int,float)) or int(ts)<start or int(ts)>end or int(ts)>=PROTECTED_MS:raise RuntimeError(f"Out-of-bounds trade {name}")
        ded[str(x.get("trade_id",f"MISSING-{i}"))]=x
    ordinary=[]
    for x in ded.values():
        if any(x.get(k) is not None for k in ("block_trade_id","block_rfq_quote_id","combo_id","combo_trade_id")):continue
        try:
            ts=int(x["timestamp"]);p=float(x["price"]);idx=float(x["index_price"]);direction=str(x["direction"]).lower()
        except Exception:raise RuntimeError(f"Missing execution field {name}")
        if direction not in ("buy","sell") or not(math.isfinite(p) and math.isfinite(idx) and p>0 and idx>0):raise RuntimeError(f"Invalid execution row {name}")
        ordinary.append({"timestamp":ts,"price":p,"index_price":idx,"direction":direction})
    ordinary.sort(key=lambda x:x["timestamp"]);return ordinary,receipts

def daily_signals(rows,expiry):
    by={}
    for x in rows:
        if x["timestamp"]>=expiry:continue
        z=dt(x["timestamp"])
        if z.hour<8:continue
        k=z.date().isoformat()
        if k not in by:by[k]=x
    return [by[k] for k in sorted(by)]

def first_fill(rows,start_ts,direction,minutes):
    end=start_ts+minutes*60*1000
    for x in rows:
        if x["timestamp"]<=start_ts:continue
        if x["timestamp"]>end:break
        if x["direction"]==direction:return x
    return None

def pf(xs):
    pos=sum(x for x in xs if x>0);neg=-sum(x for x in xs if x<0)
    return pos/neg if neg>0 else (1e9 if pos>0 else 0.0)

def pctile(xs,p):
    ys=sorted(xs)
    if not ys:return None
    q=(len(ys)-1)*p;lo=int(math.floor(q));hi=int(math.ceil(q))
    if lo==hi:return ys[lo]
    w=q-lo;return ys[lo]*(1-w)+ys[hi]*w

def bootstrap(means,reps,seed):
    rng=random.Random(seed);n=len(means);vals=[]
    for _ in range(reps):vals.append(sum(means[rng.randrange(n)] for _ in range(n))/n)
    return [pctile(vals,0.025),pctile(vals,0.975)]

def quarter(ms):
    z=dt(ms);return f"{z.year}-Q{((z.month-1)//3)+1}"

result={"lab_id":AUTH["lab_id"],"execution_mve_id":AUTH["execution_mve_id"],"classification":None,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
try:
    contracts,meta_rc=discover();source_rc=[];episodes=[];ex=defaultdict(int)
    q=float(AUTH["position"]["quantity_btcdvol"]);rate=float(AUTH["fixed_cost_model"]["base_taker_rate_each_side"])
    tick=float(AUTH["fixed_cost_model"]["stress"]["tick_size_usdc"]);fm=float(AUTH["fixed_cost_model"]["stress"]["fee_multiplier"])
    win=int(AUTH["fill_rule"]["fill_window_minutes"])
    for i,m in enumerate(contracts,1):
        rows,rr=acquire(m);source_rc.extend(rr);signals=daily_signals(rows,m["expiration_timestamp"])
        for k in range(0,len(signals)-1,2):
            s0,s1=signals[k],signals[k+1];basis=s0["price"]-s0["index_price"]
            if basis==0:ex["zero_basis"]+=1;continue
            edir="sell" if basis>0 else "buy";xdir="buy" if edir=="sell" else "sell"
            entry=first_fill(rows,s0["timestamp"],edir,win)
            if entry is None:ex["no_entry_direction_fill"]+=1;continue
            exitf=first_fill(rows,s1["timestamp"],xdir,win)
            if exitf is None:ex["no_exit_direction_fill"]+=1;continue
            if exitf["timestamp"]<=entry["timestamp"]:ex["nonpositive_hold"]+=1;continue
            sign=1.0 if edir=="buy" else -1.0
            gross=sign*q*(exitf["price"]-entry["price"])
            fees=rate*q*(entry["price"]+exitf["price"])
            base=gross-fees
            if edir=="buy":
                ein=entry["price"]+tick;eout=max(0.0,exitf["price"]-tick)
            else:
                ein=max(0.0,entry["price"]-tick);eout=exitf["price"]+tick
            gross_s=sign*q*(eout-ein);fees_s=rate*fm*q*(ein+eout);stress=gross_s-fees_s
            episodes.append({"instrument_name":m["instrument_name"],"expiration_quarter":quarter(m["expiration_timestamp"]),
              "signal_date":dt(s0["timestamp"]).date().isoformat(),"exit_anchor_date":dt(s1["timestamp"]).date().isoformat(),
              "direction":edir,"hold_calendar_days":(dt(s1["timestamp"]).date()-dt(s0["timestamp"]).date()).days,
              "base_net_usdc":base,"stress_net_usdc":stress})
        print(f"EXECUTION_PROGRESS {i}/{len(contracts)} {m['instrument_name']}",flush=True)
    by=defaultdict(list);bys=defaultdict(list);quarters=defaultdict(list)
    for e in episodes:by[e["instrument_name"]].append(e["base_net_usdc"]);bys[e["instrument_name"]].append(e["stress_net_usdc"])
    summaries=[]
    expq={m["instrument_name"]:quarter(m["expiration_timestamp"]) for m in contracts}
    for n,v in sorted(by.items()):
        summaries.append({"instrument_name":n,"expiration_quarter":expq[n],"n":len(v),"base_total_usdc":sum(v),"base_mean_usdc":sum(v)/len(v),
          "stress_total_usdc":sum(bys[n]),"stress_mean_usdc":sum(bys[n])/len(bys[n])})
        quarters[expq[n]].append(sum(v)/len(v))
    base=[e["base_net_usdc"] for e in episodes];stress=[e["stress_net_usdc"] for e in episodes]
    means=[x["base_mean_usdc"] for x in summaries];smeans=[x["stress_mean_usdc"] for x in summaries]
    qmeans={k:sum(v)/len(v) for k,v in sorted(quarters.items())}
    pos_totals=[x["base_total_usdc"] for x in summaries if x["base_total_usdc"]>0]
    concentration=max(pos_totals)/sum(pos_totals) if pos_totals else 1.0
    ci=bootstrap(means,AUTH["bootstrap"]["replications"],AUTH["bootstrap"]["seed"]) if means else [None,None]
    sg=AUTH["sample_gates"];eg=AUTH["economic_gates"]
    sample_checks={"episodes_ge_min":len(base)>=sg["minimum_executable_episodes"],"contracts_ge_min":len(summaries)>=sg["minimum_contracts_with_executable_episodes"],"quarters_ge_min":len(qmeans)>=sg["minimum_expiration_quarters"]}
    metrics={"executable_episodes":len(base),"contracts_with_episodes":len(summaries),"expiration_quarters":len(qmeans),
      "mean_contract_base_net_usdc":sum(means)/len(means) if means else None,"median_contract_base_net_usdc":statistics.median(means) if means else None,
      "base_profit_factor":pf(base),"cluster_bootstrap_base_95_ci":ci,"positive_contract_share":sum(1 for x in means if x>0)/len(means) if means else 0.0,
      "nonnegative_quarters":sum(1 for x in qmeans.values() if x>=0),"quarter_means_usdc":qmeans,
      "mean_contract_stress_net_usdc":sum(smeans)/len(smeans) if smeans else None,"stress_profit_factor":pf(stress),
      "max_positive_contract_contribution_share":concentration,"mean_hold_calendar_days":sum(e["hold_calendar_days"] for e in episodes)/len(episodes) if episodes else None,
      "exclusions":dict(ex)}
    econ_checks={
      "mean_contract_base_net_gt":metrics["mean_contract_base_net_usdc"] is not None and metrics["mean_contract_base_net_usdc"]>eg["mean_contract_base_net_gt"],
      "base_pf_gt":metrics["base_profit_factor"]>eg["base_profit_factor_gt"],
      "bootstrap_lower_gt":ci[0] is not None and ci[0]>eg["cluster_bootstrap_base_lower_95_gt"],
      "positive_contract_share_gte":metrics["positive_contract_share"]>=eg["positive_contract_share_gte"],
      "nonnegative_quarters_gte":metrics["nonnegative_quarters"]>=eg["nonnegative_quarters_gte"],
      "mean_contract_stress_net_gt":metrics["mean_contract_stress_net_usdc"] is not None and metrics["mean_contract_stress_net_usdc"]>eg["mean_contract_stress_net_gt"],
      "stress_pf_gt":metrics["stress_profit_factor"]>eg["stress_profit_factor_gt"],
      "concentration_lte":metrics["max_positive_contract_contribution_share"]<=eg["max_positive_contract_contribution_share_lte"]
    }
    if not all(sample_checks.values()):cls=AUTH["classifications"]["insufficient"]
    elif all(econ_checks.values()):cls=AUTH["classifications"]["pass"]
    else:cls=AUTH["classifications"]["no_edge"]
    result.update({"classification":cls,"sample_checks":sample_checks,"economic_checks":econ_checks,"metrics":metrics,"contract_summaries":summaries,
      "source_request_count":len(meta_rc)+len(source_rc),"source_receipt_sha256":sha(json.dumps(meta_rc+source_rc,sort_keys=True).encode())})
except Exception as e:
    txt=repr(e);result["classification"]=AUTH["classifications"]["provenance_failure"] if "Protected" in txt else AUTH["classifications"]["technical_failure"];result["error"]=txt
p=OUT/"execution_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
(OUT/"manifest.json").write_text(json.dumps({"authority_sha256":sha((ROOT/"EXECUTION_AUTHORITY_V0.1.json").read_bytes()),"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="contract_summaries"},indent=2,sort_keys=True))
sys.exit(0 if result["classification"] not in (AUTH["classifications"]["technical_failure"],AUTH["classifications"]["provenance_failure"]) else 2)
