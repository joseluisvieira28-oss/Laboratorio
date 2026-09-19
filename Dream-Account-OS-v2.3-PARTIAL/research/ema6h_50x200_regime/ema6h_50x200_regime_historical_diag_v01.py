from __future__ import annotations

import argparse,csv,json
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean,median

STEP_DAY=86_400_000
SMA_N=200
SLOPE_LAG=20

def pf(vals):
    pos=sum(x for x in vals if x>0);neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else None

def metrics(rows):
    vals=[float(x["base_net_bps"]) for x in rows]
    stress=[float(x["stress_net_bps"]) for x in rows]
    pos=[v for v in vals if v>0]
    by_symbol=Counter(x["symbol"] for x in rows)
    return {
        "n":len(vals),
        "base_mean_bps":mean(vals) if vals else None,
        "base_median_bps":median(vals) if vals else None,
        "base_pf":pf(vals) if vals else None,
        "stress_mean_bps":mean(stress) if stress else None,
        "stress_pf":pf(stress) if stress else None,
        "positive_fraction":sum(v>0 for v in vals)/len(vals) if vals else None,
        "largest_positive_event_share":max(pos)/sum(pos) if pos and sum(pos)>0 else None,
        "symbol_counts":dict(sorted(by_symbol.items()))
    }

def load_daily(path:Path):
    out=[]
    with path.open("r",encoding="utf-8",newline="") as f:
        r=csv.DictReader(f)
        for x in r:
            out.append({
                "open_time":int(x["open_time_ms"]),
                "close_time":int(x["close_time_ms"]),
                "close":float(x["close"])
            })
    for a,b in zip(out,out[1:]):
        if b["open_time"]-a["open_time"]!=STEP_DAY:raise ValueError("daily gap")
    return out

def regime(daily,signal_close:int):
    hist=[x for x in daily if x["close_time"]<signal_close]
    if len(hist)<SMA_N+SLOPE_LAG:
        return {"state":"MISSING","reason":"insufficient_daily_history"}
    tail=hist[-(SMA_N+SLOPE_LAG):]
    sma_now=mean(x["close"] for x in tail[-SMA_N:])
    sma_old=mean(x["close"] for x in tail[:SMA_N])
    close=tail[-1]["close"]
    if close>sma_now and sma_now>sma_old:state="BULL_TREND"
    elif close<sma_now and sma_now<sma_old:state="BEAR_TREND"
    else:state="TRANSITION_CHOP"
    return {"state":state,"btc_close":close,"sma200":sma_now,"sma200_20d_ago":sma_old,"daily_close_time":tail[-1]["close_time"]}

def bucket(state,direction):
    if state=="BULL_TREND":
        return "TREND_ALIGNED" if direction==1 else "COUNTER_REGIME"
    if state=="BEAR_TREND":
        return "TREND_ALIGNED" if direction==-1 else "COUNTER_REGIME"
    if state=="TRANSITION_CHOP":return "TRANSITION_CHOP"
    return "MISSING"

def discovery_rows(path:Path):
    out=[]
    with path.open("r",encoding="utf-8",newline="") as f:
        r=csv.DictReader(f)
        for x in r:
            if x["cell"]!="6H:EMA50x200":continue
            out.append({"block":"BINANCE_2021_2022","symbol":x["symbol"],"direction":int(x["direction"]),
                        "signal_close_ms":int(x["signal_close_time"]),"base_net_bps":float(x["h6_net_bps"]),
                        "stress_net_bps":float(x["h6_stress_bps"])})
    return out

def mexc_rows(path:Path):
    out=[]
    with path.open("r",encoding="utf-8",newline="") as f:
        r=csv.DictReader(f)
        for x in r:
            if x["cell"]!="6H:EMA50x200":continue
            out.append({"block":"MEXC_2023_2024","symbol":x["symbol"],"direction":int(x["direction"]),
                        "signal_close_ms":int(x["entry_open_time"])-1,"base_net_bps":float(x["base_net_bps"]),
                        "stress_net_bps":float(x["stress_net_bps"])})
    return out

def oos_rows(path:Path):
    out=[]
    with path.open("r",encoding="utf-8",newline="") as f:
        r=csv.DictReader(f)
        for x in r:
            out.append({"block":"BINANCE_2025_AUG2026","symbol":x["symbol"],"direction":int(x["direction"]),
                        "signal_close_ms":int(x["entry_open_time"])-1,"base_net_bps":float(x["base_net_bps"]),
                        "stress_net_bps":float(x["stress_net_bps"])})
    return out

def grouped_metrics(rows,key):
    g=defaultdict(list)
    for r in rows:g[r[key]].append(r)
    return {k:metrics(v) for k,v in sorted(g.items())}

def run(args):
    daily=load_daily(args.daily)
    rows=discovery_rows(args.discovery)+mexc_rows(args.mexc)+oos_rows(args.oos)
    if len(rows)!=189:raise ValueError(f"expected 189 immutable events, got {len(rows)}")
    for r in rows:
        rg=regime(daily,r["signal_close_ms"])
        r["regime_state"]=rg["state"]
        r["bucket"]=bucket(rg["state"],r["direction"])
        r["regime_btc_close"]=rg.get("btc_close")
        r["regime_sma200"]=rg.get("sma200")
        r["regime_sma200_20d_ago"]=rg.get("sma200_20d_ago")
        r["regime_daily_close_time"]=rg.get("daily_close_time")
    pooled_bucket=grouped_metrics(rows,"bucket")
    pooled_regime=grouped_metrics(rows,"regime_state")
    by_block={}
    for b in ("BINANCE_2021_2022","MEXC_2023_2024","BINANCE_2025_AUG2026"):
        xs=[r for r in rows if r["block"]==b]
        by_block[b]={"all":metrics(xs),"by_bucket":grouped_metrics(xs,"bucket"),"by_regime":grouped_metrics(xs,"regime_state")}
    matrix=defaultdict(list)
    for r in rows:
        matrix[f'{r["regime_state"]}:{"BULL_CROSS" if r["direction"]==1 else "BEAR_CROSS"}'].append(r)
    direction_matrix={k:metrics(v) for k,v in sorted(matrix.items())}
    aligned=pooled_bucket.get("TREND_ALIGNED",{})
    trans=pooled_bucket.get("TRANSITION_CHOP",{})
    counter=pooled_bucket.get("COUNTER_REGIME",{})
    positive_blocks=0
    for b,d in by_block.items():
        m=d["by_bucket"].get("TREND_ALIGNED",{}).get("base_mean_bps")
        if m is not None and m>0:positive_blocks+=1
    explanatory={
        "trend_aligned_base_positive":aligned.get("base_mean_bps") is not None and aligned.get("base_mean_bps")>0,
        "trend_aligned_pf_gt_1":aligned.get("base_pf") is not None and aligned.get("base_pf")>1,
        "trend_aligned_mean_gt_transition":aligned.get("base_mean_bps") is not None and trans.get("base_mean_bps") is not None and aligned["base_mean_bps"]>trans["base_mean_bps"],
        "trend_aligned_mean_gt_counter":aligned.get("base_mean_bps") is not None and counter.get("base_mean_bps") is not None and aligned["base_mean_bps"]>counter["base_mean_bps"],
        "trend_aligned_positive_in_at_least_2_of_3_blocks":positive_blocks>=2,
        "positive_blocks":positive_blocks
    }
    result={
        "experiment_id":"EMA6H-50X200-REGIME-DEPENDENCY-001",
        "status":"HISTORICAL_DIAGNOSTIC_COMPLETE",
        "promotion_authority":False,
        "event_count":len(rows),
        "regime_definition":{"anchor":"BTCUSDT Binance Spot 1D","sma_days":200,"slope_lag_days":20},
        "pooled_by_bucket":pooled_bucket,
        "pooled_by_regime":pooled_regime,
        "by_block":by_block,
        "direction_x_regime":direction_matrix,
        "explanatory_pattern":explanatory,
        "interpretation_boundary":"This post-outcome diagnostic may generate/explain a regime hypothesis but cannot promote or retroactively filter historical candidate results."
    }
    args.outdir.mkdir(parents=True,exist_ok=True)
    (args.outdir/"EMA6H_50X200_REGIME_DEPENDENCY_001_HISTORICAL_DIAGNOSTIC_V0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    fields=sorted({k for r in rows for k in r})
    with (args.outdir/"EMA6H_50X200_REGIME_DEPENDENCY_001_TAGGED_EVENTS_V0.1.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(sorted(rows,key=lambda x:(x["signal_close_ms"],x["block"],x["symbol"])))
    print(json.dumps({"event_count":len(rows),"pooled_by_bucket":pooled_bucket,"explanatory_pattern":explanatory},indent=2,sort_keys=True))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--daily",type=Path,required=True)
    ap.add_argument("--discovery",type=Path,required=True)
    ap.add_argument("--mexc",type=Path,required=True)
    ap.add_argument("--oos",type=Path,required=True)
    ap.add_argument("--outdir",type=Path,required=True)
    run(ap.parse_args())
if __name__=="__main__":main()
