#!/usr/bin/env python3
"""Meme006 independent 30-day settlement audit; never a trading recommendation."""
import collections
import datetime as dt
import json
import pathlib
import random
import statistics
import sys

def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z","+00:00"))

def bootstrap_day_lower(rows, reps=2000):
    if not rows:return None
    by_day=collections.defaultdict(list)
    for day,value in rows:by_day[day].append(value)
    days=sorted(by_day)
    if len(days)<3:return None
    rng=random.Random(20261119)
    means=[]
    for _ in range(reps):
        sample=[v for day in rng.choices(days,k=len(days)) for v in by_day[day]]
        means.append(statistics.mean(sample))
    means.sort()
    return round(means[int(.025*(len(means)-1))],5)

def analyze(state):
    snapshots=state.get("snapshots") or []
    entries=state.get("entries") or []
    days={parse(x["started_at"]).date().isoformat() for x in snapshots}
    span= ((parse(snapshots[-1]["started_at"])-parse(snapshots[0]["started_at"])).total_seconds()/86400
           if len(snapshots)>=2 else 0)
    summaries={}
    for label in ("H_REVERSAL","H_MOMENTUM","CONTROL_UNCONDITIONAL"):
        matched=[e for e in entries if label=="CONTROL_UNCONDITIONAL" or label in e.get("policy",[])]
        for horizon in ("h4","h24"):
            values=[];pending=censored=0
            for e in matched:
                status=(e.get("settlements") or {}).get(horizon) or {}
                st=status.get("status","MISSING")
                if st=="COUNTERFACTUAL_QUOTE_ONLY":
                    values.append((parse(e["entry_at"]).date().isoformat(),float(status["net_pct"])))
                elif st=="PENDING":pending+=1
                else:censored+=1
            obs=[x for _,x in values]
            n=len(matched)
            summaries[label+"_"+horizon]=dict(
                opportunity_entries=n, quote_outcomes=len(obs),pending=pending,censored=censored,
                mean_proxy_pct=round(statistics.mean(obs),5) if obs else None,
                median_proxy_pct=round(statistics.median(obs),5) if obs else None,
                positive_quote_fraction=round(sum(x>0 for x in obs)/len(obs),5) if obs else None,
                bootstrap_95pct_lower_day_cluster=bootstrap_day_lower(values),
                adversarial_missing_minus100pct_mean=round(
                    (sum(obs)-100*(n-len(obs)))/n,5) if n else None)
    observations=sum(len(s.get("coins") or []) for s in snapshots)
    errors=collections.Counter(x.get("decision") for s in snapshots for x in s.get("coins") or [])
    fully_settled_signals=sum(
        1 for e in entries if any(x in e.get("policy",[]) for x in ("H_REVERSAL","H_MOMENTUM"))
        and (e.get("settlements") or {}).get("h4",{}).get("status")=="COUNTERFACTUAL_QUOTE_ONLY"
    )
    span_gate=span>=30 and len(days)>=30 and fully_settled_signals>=200
    # Real marketable fills absent by design. NO-GO applies regardless of proxy outcome.
    return dict(protocol=state.get("protocol"),cycles=len(snapshots),observations=observations,
      elapsed_calendar_days=round(span,3),distinct_observed_utc_days=len(days),
      frozen_cohort_size=len(state.get("cohort") or []),
      total_shadow_entries=len(entries),fully_settled_h4_policy_signals=fully_settled_signals,
      statuses=dict(errors),results=summaries,
      minimum_scientific_sample_gate_met=span_gate,
      economic_live_trading_gate="NO-GO: this study has ZERO executed marketable fills",
      note="Quoted expected/min outputs at different times are NOT actual realized P&L, and missing quotes cannot be treated as winners.")

if __name__=="__main__":
    p=pathlib.Path(sys.argv[1])
    state=json.loads(p.read_text(encoding="utf8"))
    result=analyze(state)
    print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False))
