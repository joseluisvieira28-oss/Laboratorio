#!/usr/bin/env python3
"""Exploratory real historical trade-print replay. No orders, no network, NO profit claims."""
import sys,gzip,json,hashlib,collections,math
from pathlib import Path

P=dict(min_age_s=180,max_age_s=3600,drawdown=.28,bounce=.12,max_of_peak=.95,
       window_s=300,min_buyers=8,min_wallet_buy_sol=.1,min_buy_sol=2.,
       min_buy_share=.65,max_wallet_share=.35,min_real_sol=5.,
       entry_delay_s=30,entry_deadline_s=120,stop=.25,take=.30,hold_s=1800)

def normalize(obj):
    out=[];reject=0;same_order=0
    for i,e in enumerate(obj.get("events") or []):
        try:
            vsol=float(e["v_sol_post"]);vtok=float(e["v_tok_post"])
            sol=int(e["sol_amount"]);tok=int(e["token_amount"])
            real=float(e["real_sol_post"]);ts=int(e["block_time"])
            slot=int(e["slot"]);txidx=int(e["tx_index"])
            wallet=e["user"];isbuy=e["is_buy"]
            if not (vsol>0 and vtok>0 and sol>0 and tok>0 and real>=0 and ts>0 and
                    math.isfinite(vsol) and math.isfinite(vtok) and math.isfinite(real) and
                    isinstance(wallet,str) and bool(wallet) and isinstance(isbuy,bool)):
                raise ValueError("invalid values")
            out.append(dict(order=(slot,txidx,int(e.get("ordinal",i))),t=ts,
                            price=vsol/vtok,sol=sol/1e9,real=real/1e9,
                            wallet=wallet,buy=isbuy))
        except (KeyError,ValueError,TypeError,OverflowError):
            reject+=1
    out.sort(key=lambda x:x["order"])
    for prev,cur in zip(out,out[1:]):
        if prev["order"][:2]==cur["order"][:2]:same_order+=1
    return out,reject,same_order

def find(rows,filtered):
    if len(rows)<12:return None
    p=P;start=rows[0]["t"];peak=rows[0]["price"];trough=peak;drawn=False
    for i,r in enumerate(rows):
        age=r["t"]-start;px=r["price"]
        if age>p["max_age_s"]:break
        if not drawn:
            peak=max(peak,px)
            if age>=p["min_age_s"] and px<=peak*(1-p["drawdown"]):
                drawn=True;trough=px
            continue
        trough=min(trough,px)
        if not (px>=trough*(1+p["bounce"]) and px<=peak*p["max_of_peak"]):continue
        if r["real"]<p["min_real_sol"]:continue
        if filtered:
            wallets=collections.defaultdict(float);buy=sell=0.
            for h in rows[:i+1]:
                if r["t"]-p["window_s"]<=h["t"]<=r["t"]:
                    if h["buy"]:
                        wallets[h["wallet"]]+=h["sol"];buy+=h["sol"]
                    else:sell+=h["sol"]
            if (buy<p["min_buy_sol"] or buy+sell<=0 or
                sum(v>=p["min_wallet_buy_sol"] for v in wallets.values())<p["min_buyers"] or
                buy/(buy+sell)<p["min_buy_share"] or
                max(wallets.values(),default=0)/buy>p["max_wallet_share"]):continue
        return dict(i=i,t=r["t"],price=px,age=age,reserve=r["real"])
    return None

def exit_proxy(rows,sig,slip):
    if sig is None:return dict(status="NO_SIGNAL")
    p=P;later=rows[sig["i"]+1:]
    entry=next((r for r in later if sig["t"]+p["entry_delay_s"]<=r["t"]<=sig["t"]+p["entry_deadline_s"]
                and r["real"]>=p["min_real_sol"]),None)
    if entry is None:return dict(status="ENTRY_UNOBSERVED")
    ex=None;reason=""
    for r in later:
        if r["order"]<=entry["order"]:continue
        if r["price"]<=entry["price"]*(1-p["stop"]):ex=r;reason="STOP";break
        if r["price"]>=entry["price"]*(1+p["take"]):ex=r;reason="TAKE";break
        if r["t"]>=entry["t"]+p["hold_s"]:ex=r;reason="TIME";break
    if ex is None:return dict(status="EXIT_UNOBSERVED")
    if ex["real"]<p["min_real_sol"]:return dict(status="EXIT_RESERVE_BLOCKED")
    gross=ex["price"]/entry["price"]
    # 1.7% fee per side is NOV 2026 illustrative stress, not historical May/Jun 2026 verified schedule.
    net=gross*(1-.017)**2*(1-slip)/(1+slip)-1-.001
    return dict(status="PRINT_PROXY",reason=reason,gross_pct=100*(gross-1),
                net_pct=100*net)

def stats(a):
    if not a:return dict(n=0,mean=None,median=None,positive_fraction=None)
    a=sorted(a)
    return dict(n=len(a),mean=round(sum(a)/len(a),4),
                median=round(a[len(a)//2],4),
                positive_fraction=round(sum(z>0 for z in a)/len(a),4))

def evaluate(path):
    counts=collections.Counter();vals=collections.defaultdict(list)
    statuses=collections.Counter();first=9999999999;last=0
    rejected=ambiguous=events_count=0
    with gzip.open(path,"rt",encoding="utf-8") as f:
        for raw in f:
            if not raw.strip():continue
            obj=json.loads(raw);counts["objects"]+=1
            statuses[str(obj.get("status"))]+=1
            rows,bad,amb=normalize(obj)
            rejected+=bad;ambiguous+=amb;events_count+=len(rows)
            if not rows:
                counts["empty"]+=1;continue
            first=min(first,rows[0]["t"]);last=max(last,rows[-1]["t"])
            for name,filter_wallet in (("momentum",False),("wallet",True)):
                sig=find(rows,filter_wallet)
                if sig:counts[name+"_signals"]+=1
                for slip in (.005,.02,.05,.10):
                    out=exit_proxy(rows,sig,slip)
                    if slip==.02:counts[name+"_"+out["status"]]+=1
                    if out["status"]=="PRINT_PROXY":
                        vals[name+"_slip_"+str(slip)].append(out["net_pct"])
    report=dict(source=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                source_statuses=dict(statuses),objects=counts["objects"],
                events=events_count,invalid_events=rejected,same_slot_txindex=ambiguous,
                earliest_block_time=first,latest_block_time=last,
                signals_wallet_filtered=counts["wallet_signals"],
                signals_momentum=counts["momentum_signals"],
                statuses={k:v for k,v in counts.items() if "_" in k},
                sensitivity={k:stats(v) for k,v in vals.items()},
                protocol="Historical exploration; USD rules unavailable; 5 SOL reserve threshold is NOT $20k depth",
                scientific_gate="INCONCLUSIVE: selected retrospective sample and trade availability timestamps unverified",
                economic_gate="NO-GO: only future observed prints, not executable quotes; censoring and fee-model gaps")
    print("REAL_REPLAY_RESULT="+json.dumps(report,sort_keys=True))
    return report

if __name__=="__main__":
    res=[evaluate(Path(x)) for x in sys.argv[1:]]
    Path("meme003-results.json").write_text(json.dumps(res,indent=2)+"\n",encoding="utf-8")
