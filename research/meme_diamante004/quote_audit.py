#!/usr/bin/env python3
"""004: read-only, noncommercial historical feasibility, NEVER an execution predictor."""
import collections
import datetime as dt
import gzip
import hashlib
import json
import math
import pathlib
import statistics
import sys

CONF = dict(age_min=120,age_max=2400,min_real_sol=2.,lookback=120,
            min_buy_wallets=5,min_buy_flow=1.,min_buy_frac=.60,max_wallet_frac=.45,
            delay=30,max_entry_delay=180,horizon=300,max_exit_lateness=120,
            size_sol=.05,fee_each=.017,priority_total=.0001)

def parse(obj):
    out=[];bad=0;ambig=0
    for i,e in enumerate(obj.get("events") or []):
        try:
            vals=[float(e[k]) for k in ("v_sol_post","v_tok_post","real_sol_post","real_tok_post","sol_amount")]
            vsol,vtok,real_sol,real_tok,sol=vals
            when=int(e["block_time"])
            slot=int(e["slot"])
            tx_index=int(e["tx_index"])
            who=e["user"]; buy=e["is_buy"]
            if not (vsol>0 and vtok>0 and real_sol>=0 and real_tok>=0 and sol>0 and
                    isinstance(who,str) and bool(who) and isinstance(buy,bool) and
                    when>0 and all(math.isfinite(v) for v in vals)):
                raise ValueError("invalid")
            out.append(dict(order=(slot,tx_index,int(e.get("ordinal",i))),ts=when,
                vs=vsol/1e9,vt=vtok,rs=real_sol/1e9,rt=real_tok,
                flow=sol/1e9,who=who,buy=buy))
        except (KeyError,ValueError,TypeError,OverflowError):
            bad+=1
    out.sort(key=lambda x:x["order"])
    for a,b in zip(out,out[1:]):
        if a["order"][:2]==b["order"][:2]:ambig+=1
    return out,bad,ambig

def choose(rows,filtered):
    if not rows:return None
    start=rows[0]["ts"]
    for i,r in enumerate(rows):
        age=r["ts"]-start
        if age>CONF["age_max"]:break
        if age<CONF["age_min"] or r["rs"]<CONF["min_real_sol"]:continue
        if filtered:
            wallets=collections.defaultdict(float);buy=sell=0.
            for h in rows[:i+1]:
                if r["ts"]-CONF["lookback"]<=h["ts"]<=r["ts"]:
                    if h["buy"]:
                        buy+=h["flow"];wallets[h["who"]]+=h["flow"]
                    else:sell+=h["flow"]
            if (buy<CONF["min_buy_flow"] or buy+sell<=0
                or len(wallets)<CONF["min_buy_wallets"]
                or buy/(buy+sell)<CONF["min_buy_frac"]
                or max(wallets.values(),default=0)/buy>CONF["max_wallet_frac"]):
                continue
        return i
    return None

def quote_buy(state,budget,fee):
    # Constant product virtual reserve approximation, NOT canonical on-chain exact integer quote.
    net=budget/(1+fee)
    quantity=net*state["vt"]/(state["vs"]+net)
    if quantity<=0 or quantity>=state["rt"] or state["rs"]<=0:return None
    return quantity

def quote_sell(state,quantity,fee):
    gross=state["vs"]*quantity/(state["vt"]+quantity)
    if gross>state["rs"] or gross<=0:return None
    return gross*(1-fee)

def settle(rows,idx,fee=.017,slip=.02):
    if idx is None:return dict(status="NO_SIGNAL")
    signal=rows[idx]
    entry=next((r for r in rows[idx+1:] if
        signal["ts"]+CONF["delay"]<=r["ts"]<=signal["ts"]+CONF["max_entry_delay"]
        and r["rs"]>=CONF["min_real_sol"]),None)
    if entry is None:return dict(status="NO_OBSERVED_ENTRY")
    end=entry["ts"]+CONF["horizon"]
    exit_=next((r for r in rows if end<=r["ts"]<=end+CONF["max_exit_lateness"]
                and r["order"]>entry["order"]),None)
    if exit_ is None:return dict(status="NO_OBSERVED_EXIT")
    quantity=quote_buy(entry,CONF["size_sol"],fee)
    if quantity is None:return dict(status="ENTRY_RESERVE_BLOCKED")
    # Adversarial spread stress; applying slippage on token amount in AND SOL amount out.
    out=quote_sell(exit_,quantity*(1-slip),fee)
    if out is None:return dict(status="EXIT_RESERVE_BLOCKED")
    out=out*(1-slip)
    ret=(out-CONF["size_sol"]-CONF["priority_total"])/CONF["size_sol"]
    return dict(status="HYPOTHETICAL_CURVE_QUOTE",net_pct=round(100*ret,5),
        gross_token_price_ratio=round((exit_["vs"]/exit_["vt"])/(entry["vs"]/entry["vt"]),5),
        entry_sol_reserve=round(entry["rs"],4),exit_sol_reserve=round(exit_["rs"],4),
        entry_at=entry["ts"],exit_at=exit_["ts"])

def aggregate(source):
    counter=collections.Counter();status=collections.Counter();results=collections.defaultdict(list)
    samples=collections.defaultdict(list);days=set()
    sig_day=collections.defaultdict(set)
    with gzip.open(source,"rt",encoding="utf-8") as f:
        for line in f:
            if not line.strip():continue
            obj=json.loads(line);counter["objects"]+=1
            status[str(obj.get("status"))]+=1
            rows,bad,ambig=parse(obj)
            counter["invalid_events"]+=bad
            counter["parseable_events"]+=len(rows)
            counter["ambiguous_order_events"]+=ambig
            if not rows:counter["empty"]+=1;continue
            span=max(r["ts"] for r in rows)-min(r["ts"] for r in rows)
            if span>=300:counter["span_5m"]+=1
            if span>=600:counter["span_10m"]+=1
            if span>=900:counter["span_15m"]+=1
            day=dt.datetime.fromtimestamp(rows[0]["ts"],dt.timezone.utc).strftime("%Y-%m-%d")
            days.add(day)
            if ambig:
                counter["exclude_ambiguous_mints"]+=1
                continue
            if str(obj.get("status"))!="ok":
                counter["exclude_source_not_ok"]+=1
                continue
            for name,filtered in [("reserve",False),("wallet_flow",True)]:
                idx=choose(rows,filtered)
                if idx is None:continue
                counter[name+"_signal"]+=1
                sig_day[name].add(day)
                for slip in [0.,.02,.05]:
                    out=settle(rows,idx,slip=slip)
                    if slip==.02:counter[name+"_"+out["status"]]+=1
                    if out["status"]=="HYPOTHETICAL_CURVE_QUOTE":
                        results[(name,slip)].append(out["net_pct"])
    report={"file":str(source.name),"sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "counts":dict(counter),"source_statuses":dict(status),
            "distinct_days":len(days),"signal_days":{k:len(v) for k,v in sig_day.items()},
            "params":CONF,"outcomes":{},"caveat":"Historical selected cohort; virtual reserve indicative states; 0 proven fills. Censored exits explicitly retained."}
    for name in ("reserve","wallet_flow"):
        nr=counter[name+"_signal"]
        for slip in (0.,.02,.05):
            vals=results[(name,slip)]
            # Adversarial unobserved outcomes are assumed -100%, NOT considered proved.
            report["outcomes"][name+"_slippage_"+str(slip)]=dict(
                signals=nr,quote_outcomes=len(vals),
                mean_observed_pct=round(statistics.mean(vals),4) if vals else None,
                win_frac_observed=round(sum(x>0 for x in vals)/len(vals),4) if vals else None,
                adversarial_mean_missing_at_minus_100pct=round((sum(vals)-100*(nr-len(vals)))/nr,4) if nr else None)
    return report

if __name__=="__main__":
    paths=[pathlib.Path(x) for x in sys.argv[1:]]
    if not paths:raise SystemExit("Usage: quote_audit.py [gz data files]")
    reports=[aggregate(p) for p in paths]
    for r in reports:print("MEME004_RESULT="+json.dumps(r,sort_keys=True))
    pathlib.Path("meme004_results.json").write_text(json.dumps(reports,indent=2)+"\n",encoding="utf-8")
