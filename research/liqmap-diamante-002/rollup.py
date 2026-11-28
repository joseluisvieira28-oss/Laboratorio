#!/usr/bin/env python3
"""LIQMAP002 forward audit: every scheduled day counts, including blocked/missing days.
This code cannot approve live capital, even if model wins (no actual fills).
"""
import collections
import datetime as dt
import json
import math
import pathlib
import random
import statistics

HERE=pathlib.Path(__file__).resolve().parent
OBS=HERE/"observations"
SET=HERE/"settlements"
FIRST=dt.date(2026,11,27)
LAST=dt.date(2027,1,26)
CHECK=dt.date(2027,1,28)

def wilson(w,n):
    if n==0:return {"low":None,"high":None}
    z=1.959963984540054
    p=w/n;den=1+z*z/n
    cen=(p+z*z/(2*n))/den
    delta=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return {"low":cen-delta,"high":cen+delta}

def bootstrap_by_week(pairs,seed=2002):
    """Mean paired excess in bps with weekly resampling, 2000 replicates."""
    groups=collections.defaultdict(list)
    for day,delta in pairs:
        iso=dt.date.fromisoformat(day).isocalendar()
        groups[(iso.year,iso.week)].append(delta)
    blocks=list(groups.values())
    if len(blocks)<4:return {"low":None,"high":None,"num_weeks":len(blocks)}
    rng=random.Random(seed);samples=[]
    for _ in range(2000):
        drawn=[blocks[rng.randrange(len(blocks))] for _ in blocks]
        vals=[v for b in drawn for v in b]
        samples.append(statistics.mean(vals))
    samples.sort()
    return {"low":samples[49],"high":samples[1950],"num_weeks":len(blocks)}

def evaluate(today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    expected=[FIRST+dt.timedelta(days=i) for i in range((LAST-FIRST).days+1)]
    observations={}
    settlement={}
    for day in expected:
        k=str(day)
        p=OBS/(k+".json")
        q=SET/(k+".json")
        if p.exists():observations[k]=json.loads(p.read_text())
        if q.exists():settlement[k]=json.loads(q.read_text())
    counts=collections.Counter(v.get("status","UNKNOWN") for v in observations.values())
    scounts=collections.Counter(v.get("status","UNKNOWN") for v in settlement.values())
    scored=[]
    for day,r in settlement.items():
        if r.get("status")!="MATURED_OUTCOME" or r.get("model_result") is None:continue
        scored.append((day,r))
    decided=[(day,r) for day,r in scored if r["model_result"] in ("TARGET_FIRST","MIRROR_FIRST")]
    wins=sum(r["model_result"]=="TARGET_FIRST" for _,r in decided)
    paired=[(day,r) for day,r in decided if r["momentum_result"] in ("TARGET_FIRST","MIRROR_FIRST")]
    paired_map=sum(r["model_result"]=="TARGET_FIRST" for _,r in paired)
    paired_mom=sum(r["momentum_result"]=="TARGET_FIRST" for _,r in paired)
    denom=len(paired)
    advantage=(paired_map-paired_mom)/denom if denom else None
    allcost=[]
    pairdiff=[]
    months=collections.defaultdict(list)
    for day,r in scored:
        v=r["simulated_fee_stress"]["80"]
        mapnet=v["map"]["net_bps"]
        momnet=v["mom24"]["net_bps"]
        allcost.append(mapnet)
        pairdiff.append((day,mapnet-momnet))
        months[day[:7]].append(mapnet-momnet)
    ci=bootstrap_by_week(pairdiff)
    month_positive=sum(statistics.mean(v)>0 for v in months.values())
    gates={
        "at_least_50_decided":len(decided)>=50,
        "wilson_lower_over_half":wilson(wins,len(decided))["low"] is not None and wilson(wins,len(decided))["low"]>.5,
        "paired_advantage_over_5pp":advantage is not None and advantage>.05,
        "mean_80bps_net_positive":bool(allcost) and statistics.mean(allcost)>0,
        "weekly_bootstrap_lower_excess_positive":ci["low"] is not None and ci["low"]>0,
        "two_months_positive_excess":month_positive>=2}
    no_missing=all(str(d) in observations for d in expected)
    final_ready=today>=CHECK and no_missing and all(
        str(d) in settlement for d in expected if observations[str(d)].get("status")=="FUTURE_PENDING_OUTCOME")
    if not final_ready:
        scientific="FORWARD_PENDING_OR_CENSORED"
    elif len(decided)<50:
        scientific="INCONCLUSIVE_INSUFFICIENT_EVENTS"
    else:
        scientific="SHADOW_CANDIDATE_ONLY" if all(gates.values()) else "ECONOMIC_HYPOTHESIS_NO_GO"
    return {"experiment":"LIQMAP-DIAMANTE-002","as_of_date":str(today),
       "hypothesis":"BTC partial real-position liquidation map vs equidistant mirror and 24h price momentum",
       "not_Neuron_and_not_full_position_book":True,
       "expected_days":len(expected),"observed_days":len(observations),
       "missing_dates":[str(d) for d in expected if d<=today and str(d) not in observations],
       "source_states":dict(counts),"settlement_states":dict(scounts),
       "matured_model_signals":len(scored),"resolved_first_touch":len(decided),
       "target_first":wins,"mirror_first":len(decided)-wins,
       "ambiguous":sum(r["model_result"]=="AMBIGUOUS" for _,r in scored),
       "neither":sum(r["model_result"]=="NEITHER" for _,r in scored),
       "accuracy":wins/len(decided) if decided else None,
       "wilson95":wilson(wins,len(decided)),
       "paired_resolved":denom,"paired_map_wins":paired_map,"paired_mom_wins":paired_mom,
       "paired_excess_hit_fraction":advantage,
       "mean_80bps_net_per_matured_signal":statistics.mean(allcost) if allcost else None,
       "mean_paired_excess_bps":statistics.mean(x for _,x in pairdiff) if pairdiff else None,
       "weekly_block_bootstrap_95_bps":ci,"positive_monthly_blocks":month_positive,
       "candidate_gates":gates,
       "scientific_status":scientific,"live_trading_verdict":"NO_GO",
       "trades_executed":0,"finalization_eligible":final_ready}

def main():
    r=evaluate()
    (HERE/"rollup_summary.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("LIQMAP002_ROLLUP",r["scientific_status"],"observations",r["observed_days"],
       "matured",r["matured_model_signals"],"resolved",r["resolved_first_touch"],
       "missing",r["missing_dates"][:5],flush=True)

if __name__=="__main__":main()
