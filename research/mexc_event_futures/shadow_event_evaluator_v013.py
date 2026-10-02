#!/usr/bin/env python3
"""
V0.13 statistical engine for finalized SHADOW Event Futures observations.

This module does not collect signals, place orders, activate families or open outcomes.
The CLI defaults to a deterministic synthetic mechanics self-test only.
"""
import argparse, hashlib, json, math, random
from collections import defaultdict

MC_SIMS=200_000
BOOT_SIMS=20_000
MC_SEED=130313
BOOT_SEED=130314
ALPHA=0.05
CORE_MIN_N=20

def break_even(q):
    q=float(q)
    if q <= 0:
        raise ValueError("payout must be positive")
    return 1.0/(1.0+q)

def resolve(direction, p0, p1, q):
    direction=str(direction).upper()
    p0=float(p0); p1=float(p1); q=float(q)
    if p1==p0:
        return "TIE",0.0
    up=p1>p0
    win=(direction=="UP" and up) or (direction=="DOWN" and not up)
    return ("WIN",q) if win else ("LOSS",-1.0)

def validate_event(r):
    req=[
        "family_id","family_version","signal_id","symbol","direction","horizon_minutes",
        "decision_ts_ms","decision_index","payout","break_even_probability",
        "expiry_target_ts_ms","expiry_ts_ms","expiry_index","outcome","unit_return",
        "payout_source_sha256","decision_index_raw_sha256","expiry_index_raw_sha256",
        "rule_hash","status"
    ]
    miss=[k for k in req if k not in r]
    if miss:
        raise ValueError(f"missing fields: {miss}")
    if r["status"]!="RESOLVED":
        raise ValueError("only RESOLVED events may enter statistics")
    if r["direction"] not in ("UP","DOWN"):
        raise ValueError("bad direction")
    if int(r["horizon_minutes"]) <= 0:
        raise ValueError("bad horizon")
    if float(r["decision_index"]) <= 0 or float(r["expiry_index"]) <= 0:
        raise ValueError("index must be positive")
    q=float(r["payout"])
    if q <= 0:
        raise ValueError("payout must be positive")
    be=break_even(q)
    if abs(float(r["break_even_probability"])-be)>1e-12:
        raise ValueError("break-even mismatch")
    out,ret=resolve(r["direction"],r["decision_index"],r["expiry_index"],q)
    if r["outcome"]!=out or abs(float(r["unit_return"])-ret)>1e-12:
        raise ValueError("outcome/unit-return mismatch")
    if int(r["expiry_ts_ms"]) < int(r["expiry_target_ts_ms"]):
        raise ValueError("expiry tick before target")
    if int(r["expiry_ts_ms"])-int(r["expiry_target_ts_ms"]) > 5000:
        raise ValueError("expiry tick exceeds frozen 5s lateness")
    for k in ("payout_source_sha256","decision_index_raw_sha256","expiry_index_raw_sha256"):
        v=str(r[k])
        if len(v)!=64 or any(c not in "0123456789abcdef" for c in v):
            raise ValueError(f"bad sha256: {k}")
    if r.get("source_integrity_ok") is not True:
        raise ValueError("source_integrity_ok must be true")
    return True

def cell_key(r):
    return (
        r["family_id"],r["family_version"],r["symbol"],int(r["horizon_minutes"]),
        r.get("direction_policy","UNSPECIFIED")
    )

def chronological_thirds(events):
    e=sorted(events,key=lambda r:(int(r["decision_ts_ms"]),r["signal_id"]))
    n=len(e)
    bounds=[0,n//3,2*n//3,n]
    # Avoid an empty first third for n>=3.
    if n>=3:
        bounds=[0,math.ceil(n/3),math.ceil(2*n/3),n]
    return [e[bounds[i]:bounds[i+1]] for i in range(3)]

def bootstrap_ci(returns, sims=BOOT_SIMS, seed=BOOT_SEED):
    if not returns:
        return (None,None)
    rng=random.Random(seed)
    n=len(returns)
    vals=[]
    for _ in range(sims):
        vals.append(sum(returns[rng.randrange(n)] for _ in range(n))/n)
    vals.sort()
    lo=vals[int(0.025*(sims-1))]
    hi=vals[int(0.975*(sims-1))]
    return lo,hi

def breakeven_null_pvalue(events, sims=MC_SIMS, seed=MC_SEED):
    obs=sum(float(r["unit_return"]) for r in events)
    rng=random.Random(seed)
    exceed=0
    params=[(float(r["payout"]),break_even(float(r["payout"]))) for r in events]
    for _ in range(sims):
        total=0.0
        for q,p in params:
            total += q if rng.random()<p else -1.0
        if total >= obs-1e-15:
            exceed+=1
    return (1+exceed)/(1+sims)

def summarize_cell(events, min_n):
    for r in events:
        validate_event(r)
    events=sorted(events,key=lambda r:(int(r["decision_ts_ms"]),r["signal_id"]))
    returns=[float(r["unit_return"]) for r in events]
    q=[float(r["payout"]) for r in events]
    wins=sum(r["outcome"]=="WIN" for r in events)
    losses=sum(r["outcome"]=="LOSS" for r in events)
    ties=sum(r["outcome"]=="TIE" for r in events)
    thirds=chronological_thirds(events)
    third_totals=[sum(float(r["unit_return"]) for r in g) for g in thirds]
    result={
        "n":len(events),"wins":wins,"losses":losses,"ties":ties,
        "win_rate_ex_ties": wins/(wins+losses) if wins+losses else None,
        "total_unit_return":sum(returns),
        "mean_unit_return":sum(returns)/len(returns) if returns else None,
        "mean_payout":sum(q)/len(q) if q else None,
        "mean_break_even_probability":sum(break_even(x) for x in q)/len(q) if q else None,
        "chronological_third_total_returns":third_totals,
        "min_n":min_n,
        "eligible_for_survival_test":len(events)>=min_n,
    }
    if len(events)>=min_n:
        lo,hi=bootstrap_ci(returns)
        result["bootstrap95_mean_return"]=[lo,hi]
        result["raw_p_value"]=breakeven_null_pvalue(events)
    else:
        result["bootstrap95_mean_return"]=[None,None]
        result["raw_p_value"]=None
    return result

def holm_adjust(pairs):
    # pairs = [(key,p)]
    m=len(pairs)
    ordered=sorted(pairs,key=lambda x:x[1])
    out={}
    running=0.0
    for rank,(key,p) in enumerate(ordered,1):
        adj=min(1.0,(m-rank+1)*p)
        running=max(running,adj)
        out[key]=running
    return out

def evaluate(events, min_n_by_family=None):
    min_n_by_family=min_n_by_family or {}
    groups=defaultdict(list)
    ids=set()
    for r in events:
        validate_event(r)
        uid=(r["family_id"],r["family_version"],r["signal_id"],r["symbol"],r["horizon_minutes"])
        if uid in ids:
            raise ValueError(f"duplicate finalized event identity: {uid}")
        ids.add(uid)
        groups[cell_key(r)].append(r)

    summaries={}
    eligible_p=[]
    for k,rows in groups.items():
        family=k[0]
        min_n=max(CORE_MIN_N,int(min_n_by_family.get(family,CORE_MIN_N)))
        s=summarize_cell(rows,min_n)
        summaries[k]=s
        if s["raw_p_value"] is not None:
            eligible_p.append((k,s["raw_p_value"]))

    adj=holm_adjust(eligible_p)
    for k,s in summaries.items():
        s["holm_adjusted_p"]=adj.get(k)
        if s["n"]<s["min_n"]:
            verdict="INSUFFICIENT_N"
        else:
            lo=s["bootstrap95_mean_return"][0]
            thirds=s["chronological_third_total_returns"]
            ok=(
                s["mean_unit_return"]>0
                and lo is not None and lo>0
                and s["holm_adjusted_p"] is not None and s["holm_adjusted_p"]<ALPHA
                and all(x>0 for x in thirds)
            )
            verdict="SURVIVES_FORWARD_SHADOW_GATE" if ok else "NO_SURVIVOR"
        s["verdict"]=verdict

    return {
        "engine":"MEXC_EVENT_FUTURES_EVENT_CONDITIONED_V0.13",
        "monte_carlo_sims":MC_SIMS,
        "bootstrap_sims":BOOT_SIMS,
        "mc_seed":MC_SEED,
        "bootstrap_seed":BOOT_SEED,
        "holm_alpha":ALPHA,
        "core_min_n_floor":CORE_MIN_N,
        "cells":[{"cell":list(k),"summary":v} for k,v in sorted(summaries.items())],
    }

def fake_sha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def synthetic_self_test():
    # Mechanics-only fixture. It is NOT research evidence and cannot be promoted.
    rows=[]
    p0=100.0
    for i in range(24):
        direction="UP"
        q=0.85
        # deterministic artificial 20 wins / 4 losses
        win=i not in {5,11,17,23}
        p1=p0+1 if win else p0-1
        outcome,ret=resolve(direction,p0,p1,q)
        dec=1_800_000_000_000+i*3_600_000
        target=dec+60*60*1000
        rows.append({
            "family_id":"SYNTHETIC-SELFTEST",
            "family_version":"0",
            "signal_id":f"synthetic-{i:03d}",
            "symbol":"BTC_USDT",
            "direction":direction,
            "direction_policy":"SYNTHETIC",
            "horizon_minutes":60,
            "decision_ts_ms":dec,
            "decision_index":p0,
            "payout":q,
            "break_even_probability":break_even(q),
            "expiry_target_ts_ms":target,
            "expiry_ts_ms":target+1000,
            "expiry_index":p1,
            "outcome":outcome,
            "unit_return":ret,
            "payout_source_sha256":fake_sha("p"+str(i)),
            "decision_index_raw_sha256":fake_sha("d"+str(i)),
            "expiry_index_raw_sha256":fake_sha("e"+str(i)),
            "rule_hash":"SYNTHETIC_ONLY",
            "status":"RESOLVED",
            "source_integrity_ok":True,
        })
    out=evaluate(rows,{"SYNTHETIC-SELFTEST":20})
    assert out["cells"]
    s=out["cells"][0]["summary"]
    assert s["n"]==24
    assert s["wins"]==20 and s["losses"]==4
    assert s["mean_unit_return"]>0
    print(json.dumps({
        "self_test":"ENGINE_SELF_TEST_PASS",
        "warning":"SYNTHETIC_FIXTURE_NOT_RESEARCH_EVIDENCE",
        "summary":s,
    },indent=2,sort_keys=True))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--jsonl")
    args=ap.parse_args()
    if args.self_test:
        synthetic_self_test()
        return
    if not args.jsonl:
        raise SystemExit("Use --self-test or supply --jsonl with finalized forward shadow events.")
    rows=[]
    with open(args.jsonl,encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    print(json.dumps(evaluate(rows),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
