#!/usr/bin/env python3
"""Causal research proxy, not a vendor liquidation heatmap or executable bot."""
import json
import math
import pathlib
import random
import statistics

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"results"
LEVERAGES=(10,25,50)
TIER_WEIGHTS=(.5,.3,.2)
HALF_LIVES=(72.,36.,12.)
BIN=.0025
D_MIN=.005
D_MAX=.05
TAU=.03
H=6
WARMUP=120
BPS=(10,35,80)
SLIP_BPS=5

def update_levels(levels,bar,previous_oi):
    """Close candle, decay and clear known past levels; then seed assumed OI."""
    cleaned=[]
    for obj in levels:
        age=obj["age"]+1
        if age>120 or bar["l"]<=obj["price"]<=bar["h"]:
            continue
        mass=obj["mass"]*math.exp(-math.log(2)/obj["half_life"])
        if mass>1e-10:cleaned.append({**obj,"age":age,"mass":mass})
    oi_delta=max(0.,bar["oi"]-previous_oi)
    if previous_oi>0 and oi_delta>0:
        for lev,weight,half in zip(LEVERAGES,TIER_WEIGHTS,HALF_LIVES):
            for sign in (-1,1):
                price=bar["c"]*(1+sign/lev)
                mass=oi_delta*bar["c"]*weight*.5
                if price>0:
                    cleaned.append({"age":0,"half_life":half,"price":price,
                                    "mass":mass,"side":"UP" if sign==1 else "DOWN"})
    return cleaned

def strongest_band(levels,last_price):
    """Choose a single side from levels already known at close t."""
    if not levels or last_price<=0: return None
    bins={}
    for item in levels:
        dist=math.log(item["price"]/last_price)
        if not D_MIN<=abs(dist)<=D_MAX:continue
        key=math.floor(math.log(item["price"])/BIN)
        center=math.exp((key+.5)*BIN)
        cdist=math.log(center/last_price)
        if not D_MIN<=abs(cdist)<=D_MAX:continue
        bins[key]=bins.get(key,0.)+item["mass"]*math.exp(-abs(cdist)/TAU)
    if not bins:return None
    key=max(sorted(bins),key=lambda b:bins[b])
    target=math.exp((key+.5)*BIN)
    direction=1 if target>last_price else -1
    distance=abs(math.log(target/last_price))
    return {"dir":direction,"target":target,"opposite":last_price*math.exp(-direction*distance),
            "distance_log":distance,"strength_est":bins[key],
            "side":"ABOVE" if direction==1 else "BELOW"}

def labels(bars,t,chosen,dir_sign):
    """Outcome only; future bars t+1..t+6 never passed to signal selection."""
    a=chosen["target"] if dir_sign==chosen["dir"] else chosen["opposite"]
    b=chosen["opposite"] if dir_sign==chosen["dir"] else chosen["target"]
    for j in range(t+1,t+1+H):
        row=bars[j]
        if dir_sign==1:
            hit_target=row["h"]>=a
            hit_stop=row["l"]<=b
        else:
            hit_target=row["l"]<=a
            hit_stop=row["h"]>=b
        if hit_target and hit_stop:return "AMBIGUOUS",j
        if hit_target:return "TARGET_FIRST",j
        if hit_stop:return "OPPOSITE_FIRST",j
    return "NEITHER",t+H

def pseudo_trade(bars,t,chosen,dir_sign,fee_bps,slippage_bps=SLIP_BPS):
    """Futures-style hypothetical directional PnL. No margin/funding/fill proof."""
    result,exiti=labels(bars,t,chosen,dir_sign)
    entry=bars[t+1]["o"]
    target=chosen["target"] if dir_sign==chosen["dir"] else chosen["opposite"]
    stop=chosen["opposite"] if dir_sign==chosen["dir"] else chosen["target"]
    if result=="TARGET_FIRST":exit_price=target
    elif result in ("OPPOSITE_FIRST","AMBIGUOUS"):exit_price=stop
    else:exit_price=bars[exiti]["c"]
    raw=dir_sign*(exit_price/entry-1)
    gap=entry>=target if dir_sign==1 else entry<=target
    gap|=entry<=stop if dir_sign==1 else entry>=stop
    if result=="AMBIGUOUS":raw=min(raw,-abs(stop/entry-1))
    if gap:raw=min(raw,0.)
    net=raw-2*(fee_bps+slippage_bps)/10000.
    return {"outcome":result,"entry":entry,"exit":exit_price,"gap_uncertain":gap,
            "gross_bps":10000*raw,"net_bps":10000*net}

def wilson(wins,n,z=1.959963984540054):
    if not n:return [None,None]
    ph=wins/n
    den=1+z*z/n
    c=(ph+z*z/(2*n))/den
    h=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    return [round(c-h,6),round(c+h,6)]

def boot_diff(xs,seed=6001):
    if len(xs)<8:return {"low_bps":None,"high_bps":None,"block_size":4}
    rng=random.Random(seed)
    n=len(xs);block=4;vals=[]
    for _ in range(2000):
        y=[]
        while len(y)<n:
            begin=rng.randint(0,n-block)
            y.extend(xs[begin:begin+block])
        vals.append(statistics.mean(y[:n]))
    vals.sort()
    return {"low_bps":round(vals[49],5),"high_bps":round(vals[1950],5),"block_size":4}

def evaluate(bars,market):
    if len(bars)!=576:raise ValueError("SOURCE_BLOCKED wrong bar count")
    levels=[];records=[]
    for i,row in enumerate(bars):
        if i:
            levels=update_levels(levels,row,bars[i-1]["oi"])
        if i<WARMUP or i%H or i+H>=len(bars):continue
        pool=strongest_band(levels,row["c"])
        if pool is None:
            records.append({"i":i,"utc_ms":row["t"],"status":"NO_SIGNAL"})
            continue
        mom=1 if row["c"]>bars[i-6]["c"] else -1
        rec={"i":i,"utc_ms":row["t"],"status":"PROXY_SIGNAL",
             "signal_candle_close_assumed_utc_ms":row["t"]+3600000,
             "choice":"UP" if pool["dir"]==1 else "DOWN",
             "momentum":"UP" if mom==1 else "DOWN",
             "target":round(pool["target"],8),
             "opposite":round(pool["opposite"],8),
             "dist_pct":100*(math.exp(pool["distance_log"])-1),
             "estimated_strength_units_not_actual_liquidations":pool["strength_est"]}
        rec["outcome_proxy"],_=labels(bars,i,pool,pool["dir"])
        rec["outcome_momentum"],_=labels(bars,i,pool,mom)
        rec["simulated_net_bps"]={}
        for fee in BPS:
            rec["simulated_net_bps"][str(fee)]={
                "proxy":round(pseudo_trade(bars,i,pool,pool["dir"],fee)["net_bps"],6),
                "momentum":round(pseudo_trade(bars,i,pool,mom,fee)["net_bps"],6)}
        records.append(rec)
    active=[r for r in records if r["status"]=="PROXY_SIGNAL"]
    decided=[r for r in active if r["outcome_proxy"] in ("TARGET_FIRST","OPPOSITE_FIRST")]
    wins=sum(r["outcome_proxy"]=="TARGET_FIRST" for r in decided)
    mom_decided=[r for r in active if r["outcome_momentum"] in ("TARGET_FIRST","OPPOSITE_FIRST")]
    momwins=sum(r["outcome_momentum"]=="TARGET_FIRST" for r in mom_decided)
    overlap=[r for r in active if (r["outcome_proxy"] in ("TARGET_FIRST","OPPOSITE_FIRST") and
             r["outcome_momentum"] in ("TARGET_FIRST","OPPOSITE_FIRST"))]
    avg={};boot={}
    for fee in BPS:
        pairs=[r["simulated_net_bps"][str(fee)] for r in active]
        avg[str(fee)]={"proxy_mean_bps_per_signal":round(statistics.mean(v["proxy"] for v in pairs),6) if pairs else None,
          "momentum_mean_bps_same_opportunities":round(statistics.mean(v["momentum"] for v in pairs),6) if pairs else None,
          "proxy_wins_above_zero":sum(v["proxy"]>0 for v in pairs),
          "proxy_sum_bps_not_compounded":round(sum(v["proxy"] for v in pairs),5)}
        if fee==80:boot[str(fee)]=boot_diff([x["proxy"]-x["momentum"] for x in pairs])
    pwin=wins/len(decided) if decided else None
    mwin=momwins/len(mom_decided) if mom_decided else None
    paired_adv=(sum(r["outcome_proxy"]=="TARGET_FIRST" for r in overlap)
                -sum(r["outcome_momentum"]=="TARGET_FIRST" for r in overlap))/len(overlap) if overlap else None
    gates={"min_50_resolved":len(decided)>=50,
          "wilson_low_gt_half":wilson(wins,len(decided))[0] is not None and wilson(wins,len(decided))[0]>.5,
          "paired_plus_5pp":paired_adv is not None and paired_adv>.05,
          "eighty_bps_mean_positive":avg["80"]["proxy_mean_bps_per_signal"] is not None and avg["80"]["proxy_mean_bps_per_signal"]>0,
          "another_period_venue_confirmed":False}
    return {"symbol":market,"total_decision_windows":len(records),
       "no_signal":len(records)-len(active),"signals":len(active),
       "resolved":len(decided),"wins_target_first":wins,
       "loss_opposite_first":len(decided)-wins,
       "neither":sum(r["outcome_proxy"]=="NEITHER" for r in active),
       "ambiguous":sum(r["outcome_proxy"]=="AMBIGUOUS" for r in active),
       "hit_rate":pwin,"wilson95":wilson(wins,len(decided)),
       "momentum_resolved":len(mom_decided),"momentum_hits":momwins,
       "momentum_rate":mwin,
       "paired_resolved":len(overlap),"paired_hit_rate_adv_pp":100*paired_adv if paired_adv is not None else None,
       "fee_scenarios":avg,"paired_bootstrap":boot,"gates":gates,
       "research_candidate":all(gates.values()),"events":records}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=json.loads((OUT/"sources.json").read_text())
    result={"study":"LIQMAP-DIAMANTE-001","source":"Bybit hourly OHLC and OI",
      "hypothesis":"Open-interest liquidation proxy; NOT Neuron or actual liquidation levels",
      "history_not_prospective":True,"trades":0,"fee_scenarios_bps":list(BPS),
      "status_by_symbol":source["status"],"markets":{}}
    for symbol,bars in source["data"].items():
        result["markets"][symbol]=evaluate(bars,symbol)
        print("EVAL",symbol,"resolved",result["markets"][symbol]["resolved"],
             "hit_rate",result["markets"][symbol]["hit_rate"],
             "cost80",result["markets"][symbol]["fee_scenarios"]["80"],flush=True)
    if len(result["markets"])!=2:result["economic_verdict"]="SOURCE_BLOCKED"
    else:result["economic_verdict"]="NO_GO_LIVE; RETROSPECTIVE_PROXY_ONLY"
    (OUT/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# LIQMAP-001: Real public OHLC+OI, estimated hypothetical bands","",
      "THIS IS NOT A TEST OF NEURON ITSELF, NOR REAL LIQUIDATIONS. All results retrospective.",
      "At least 50 decided cases per symbol, good controls and net value required for candidate.",
      "No orders or trades. 80bps/side plus 5bps/side slippage is a hypothetical stress.",
      "","| Symbol | Signals | Target first | Opposite first | Neither | Ambiguous | Hit rate | Wilson low | MOM6 rate | 80bps mean net bps |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for symbol,x in result["markets"].items():
        fmt=lambda z:"N/A" if z is None else f"{z:.4f}"
        lines.append("| "+symbol+" | "+ " | ".join([
           str(x["signals"]),str(x["wins_target_first"]),str(x["loss_opposite_first"]),
           str(x["neither"]),str(x["ambiguous"]),fmt(x["hit_rate"]),
           fmt(x["wilson95"][0]),fmt(x["momentum_rate"]),
           fmt(x["fee_scenarios"]["80"]["proxy_mean_bps_per_signal"])])+" |")
    lines+=["","## Data-source gates",""]
    for symbol,st in source["status"].items():
        lines.append("- "+symbol+": "+st["status"]+", "+str(st.get("reason",st.get("n",""))))
    lines+=["","## Interpretation",
       "A manufactured synthetic pool derived from public OHLC+OI is NOT the proprietary product's historical forecast.",
       "Touch of an estimated region is not actual forced liquidation. OI may reflect opening/closing net, not leverage mix.",
       "A result here may motivate new genuine pre-timestamped snapshots; it never provides live trading GO.",
       "Price at next-hour open remains a model fill; true published OI latency unknown, and short funding/margin/fees omitted.",
       "Full event records and source response SHA256 in RESULTS/sources.json and RESULT.json."]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("DONE",result["economic_verdict"])
if __name__=="__main__":main()
