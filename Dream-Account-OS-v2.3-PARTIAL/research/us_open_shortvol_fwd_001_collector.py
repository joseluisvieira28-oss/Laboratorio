#!/usr/bin/env python3
import json, math, os, random, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LAB="USOPEN-SHORTVOL-FWD-001"
BASE="https://www.deribit.com/api/v2"
NY=ZoneInfo("America/New_York")
ROOT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/usopen_shortvol_fwd_001")
LEDGER=ROOT/"ledger.json"
HOLIDAYS={"2026-11-26","2026-12-25"}

def call(method, params):
    url=f"{BASE}/{method}?{urllib.parse.urlencode(params)}"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-USOPEN-SHORTVOL-FWD-001/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        x=json.loads(r.read().decode())
    if "error" in x: raise RuntimeError(x["error"])
    return x["result"]

def fee(price, amount=0.1):
    return min(0.0003*amount,0.125*price*amount)

def pf(xs):
    pos=sum(x for x in xs if x>0); neg=-sum(x for x in xs if x<0)
    if neg==0: return None if pos==0 else "INF"
    return pos/neg

def pct(xs,p):
    ys=sorted(xs); n=len(ys)
    if not n: return None
    k=(n-1)*p; f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def boot(xs,reps=10000,seed=20261002):
    rng=random.Random(seed); n=len(xs); vals=[]
    for _ in range(reps):
        vals.append(sum(xs[rng.randrange(n)] for __ in range(n))/n)
    return [pct(vals,.025),pct(vals,.975)]

def get_book(name):
    b=call("public/get_order_book",{"instrument_name":name,"depth":5})
    return {
      "instrument_name":name,
      "timestamp":b.get("timestamp"),
      "bid":b.get("best_bid_price"),"ask":b.get("best_ask_price"),
      "bid_amount":b.get("best_bid_amount"),"ask_amount":b.get("best_ask_amount")
    }

def valid_entry_book(b):
    return all(v is not None for v in (b["bid"],b["ask"],b["bid_amount"],b["ask_amount"])) and b["bid"]>0 and b["ask"]>=b["bid"] and b["bid_amount"]>=0.1 and b["ask_amount"]>=0.1

def valid_exit_book(b):
    return valid_entry_book(b) and b["ask_amount"]>=0.1

def select_pair(now):
    idx=float(call("public/get_index_price",{"index_name":"btc_usd"})["index_price"])
    ins=call("public/get_instruments",{"currency":"BTC","kind":"option","expired":"false"})
    rows=[]
    for x in ins:
        exp=datetime.fromtimestamp(x["expiration_timestamp"]/1000,tz=timezone.utc)
        dte=(exp-now).total_seconds()/86400
        if not (7<=dte<=14): continue
        ps=x["instrument_name"].split("-")
        if len(ps)<4 or ps[-1] not in ("C","P"): continue
        try: strike=float(ps[-2])
        except: continue
        rows.append((x["expiration_timestamp"],exp,dte,strike,ps[-1],x["instrument_name"]))
    if not rows: return None
    nearest=min(x[0] for x in rows)
    pairs={}
    for x in rows:
        if x[0]!=nearest: continue
        pairs.setdefault(x[3],{})[x[4]]=x
    candidates=[]
    for strike,v in pairs.items():
        if "C" in v and "P" in v:
            candidates.append((abs(math.log(strike/idx)),strike,v["C"],v["P"]))
    if not candidates: return None
    candidates.sort(key=lambda z:(z[0],z[1]))
    _,strike,c,p=candidates[0]
    return {
      "index_price":idx,"strike":strike,"expiry":c[1].isoformat(),"dte":c[2],
      "call":get_book(c[5]),"put":get_book(p[5])
    }

def load_ledger():
    if LEDGER.exists(): return json.loads(LEDGER.read_text())
    return {"lab_id":LAB,"events":[],"classification":"FORWARD_SHADOW_COLLECTING"}

def adjudicate(ledger):
    xs=[e["base_net_btc"] for e in ledger["events"] if e.get("status")=="COMPLETE"]
    stress=[e["stress_net_btc"] for e in ledger["events"] if e.get("status")=="COMPLETE"]
    n=len(xs)
    ledger["completed_dates"]=n
    if n<30:
        ledger["classification"]="FORWARD_SHADOW_COLLECTING"
        return
    months={}
    for e in ledger["events"]:
        if e.get("status")!="COMPLETE": continue
        months.setdefault(e["date"][:7],[]).append(e["base_net_btc"])
    nonneg=sum(1 for v in months.values() if sum(v)/len(v)>=0)
    ci=boot(xs)
    pfb=pf(xs); pfs=pf(stress)
    pfbn=float("inf") if pfb=="INF" else pfb
    pfsn=float("inf") if pfs=="INF" else pfs
    pos=sum(x for x in xs if x>0)
    share=max([x for x in xs if x>0],default=0)/pos if pos>0 else None
    passed=(sum(xs)/n>0 and pfbn>=1.2 and ci[0]>0 and sum(stress)/n>0 and pfsn>1 and nonneg>=2 and share is not None and share<=0.25)
    ledger["classification"]="FORWARD_SHADOW_SHORTVOL_SURVIVES" if passed else "FORWARD_SHADOW_SHORTVOL_NO_EDGE"
    ledger["metrics"]={
      "n":n,"mean_base_net_btc":sum(xs)/n,"base_pf":pfb,"bootstrap95":ci,
      "mean_stress_net_btc":sum(stress)/n,"stress_pf":pfs,
      "nonnegative_months":nonneg,"max_single_positive_share":share,
      "worst_episode_btc":min(xs),"best_episode_btc":max(xs)
    }

def main():
    now=datetime.now(timezone.utc); local=now.astimezone(NY)
    ds=local.date().isoformat()
    ROOT.mkdir(parents=True,exist_ok=True)
    state=ROOT/f"{ds}.json"

    if local.weekday()>=5 or ds in HOLIDAYS:
        print(json.dumps({"status":"NOOP_NONTRADING_DAY","date":ds}))
        return

    mins=local.hour*60+local.minute
    phase="ENTRY" if 540<=mins<=550 else ("EXIT" if 660<=mins<=670 else os.environ.get("FORCE_PHASE",""))
    if phase not in ("ENTRY","EXIT"):
        print(json.dumps({"status":"NOOP_OUTSIDE_FROZEN_WINDOWS","local":local.isoformat()}))
        return

    if phase=="ENTRY":
        if state.exists():
            print(json.dumps({"status":"IDEMPOTENT_ENTRY_ALREADY_CAPTURED","date":ds}))
            return
        pair=select_pair(now)
        if not pair or not valid_entry_book(pair["call"]) or not valid_entry_book(pair["put"]):
            state.write_text(json.dumps({"lab_id":LAB,"date":ds,"status":"SOURCE_INELIGIBLE_ENTRY","captured_at":now.isoformat()},indent=2)+"\n")
            print(state.read_text()); return
        rec={"lab_id":LAB,"date":ds,"status":"ENTRY_CAPTURED","captured_at":now.isoformat(),"local_time":local.isoformat(),**pair}
        state.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"status":"ENTRY_CAPTURED","date":ds,"call":pair["call"]["instrument_name"],"put":pair["put"]["instrument_name"],"dte":pair["dte"]},indent=2))
        return

    if not state.exists():
        print(json.dumps({"status":"SOURCE_INELIGIBLE_NO_ENTRY","date":ds})); return
    rec=json.loads(state.read_text())
    if rec.get("status")!="ENTRY_CAPTURED":
        print(json.dumps({"status":"SOURCE_INELIGIBLE_ENTRY_STATE","date":ds})); return
    cb=get_book(rec["call"]["instrument_name"]); pb=get_book(rec["put"]["instrument_name"])
    if not valid_exit_book(cb) or not valid_exit_book(pb):
        rec["status"]="SOURCE_INELIGIBLE_EXIT"; rec["exit_captured_at"]=now.isoformat()
        state.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n"); print(state.read_text()); return

    amount=0.1
    entry_proceeds=amount*(rec["call"]["bid"]+rec["put"]["bid"])
    exit_cost=amount*(cb["ask"]+pb["ask"])
    fees=fee(rec["call"]["bid"],amount)+fee(rec["put"]["bid"],amount)+fee(cb["ask"],amount)+fee(pb["ask"],amount)
    base_net=entry_proceeds-exit_cost-fees
    extra=amount*(max(rec["call"]["ask"]-rec["call"]["bid"],cb["ask"]-cb["bid"])+max(rec["put"]["ask"]-rec["put"]["bid"],pb["ask"]-pb["bid"]))
    stress=base_net-extra

    event={
      "date":ds,"status":"COMPLETE","entry_captured_at":rec["captured_at"],"exit_captured_at":now.isoformat(),
      "call":rec["call"]["instrument_name"],"put":rec["put"]["instrument_name"],"strike":rec["strike"],"expiry":rec["expiry"],
      "entry_bid_call":rec["call"]["bid"],"entry_bid_put":rec["put"]["bid"],
      "exit_ask_call":cb["ask"],"exit_ask_put":pb["ask"],
      "base_net_btc":base_net,"stress_net_btc":stress,"fees_btc":fees,
      "live_execution":False,"orders":False
    }
    rec["status"]="COMPLETE"; rec["event"]=event
    state.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")

    ledger=load_ledger()
    ledger["events"]=[e for e in ledger["events"] if e.get("date")!=ds]+[event]
    ledger["events"]=sorted(ledger["events"],key=lambda e:e["date"])
    adjudicate(ledger)
    LEDGER.write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"COMPLETE","date":ds,"classification":ledger["classification"],"completed_dates":ledger.get("completed_dates",0)},indent=2))

if __name__=="__main__":
    main()
