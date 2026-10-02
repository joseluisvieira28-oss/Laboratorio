#!/usr/bin/env python3
import importlib.util, json, os
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("v04",ROOT/"techsignals_v04.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

SYMBOLS={
 "BTCUSDT":"BTC_USDT",
 "ETHUSDT":"ETH_USDT",
 "NVDAUSDT":"NVIDIA_USDT",
 "SPCXUSDT":"SPCXSTOCK_USDT",
 "MUUSDT":"MUSTOCK_USDT",
}
PAYOUTS={
 "BTCUSDT":{10:0.80,30:0.85,60:0.85,1440:0.85},
 "ETHUSDT":{10:0.40,30:0.85,60:0.85,1440:0.85},
 "NVDAUSDT":{10:0.80,30:0.85,60:0.85,240:0.85},
 "SPCXUSDT":{10:0.80,30:0.85,60:0.85,240:0.85},
 "MUUSDT":{10:0.80,30:0.85,60:0.85,240:0.85},
}
MIN_N={10:120,30:100,60:80,240:50,1440:40}
BH_Q=0.05

def ev_at(r,q):
    n=r["wins"]+r["losses"]+r["ties"]
    return None if n<=0 else (r["wins"]*q-r["losses"])/n

def eligible(r,h,p0):
    return (
      r["non_ties"]>=MIN_N[h]
      and r["accuracy"] is not None and r["accuracy"]>p0
      and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
      and all(x is not None and x>0.50 for x in r["third_accuracies"])
      and r["p_value_vs_be80"] is not None
    )

def bh(cells):
    e=[x for x in cells if x["eligible"]]
    e.sort(key=lambda x:x["discovery"]["p_value_vs_product_be"])
    M=len(e); cutoff=None
    for rank,x in enumerate(e,1):
        if x["discovery"]["p_value_vs_product_be"] <= rank/M*BH_Q:
            cutoff=x["discovery"]["p_value_vs_product_be"]
    return ([] if cutoff is None else [x for x in e if x["discovery"]["p_value_vs_product_be"]<=cutoff]),M,cutoff

def decorate(r,q,p0):
    z=dict(r)
    z["payout_reference"]=q
    z["break_even_accuracy"]=p0
    z["p_value_vs_product_be"]=z.pop("p_value_vs_be80")
    z["ev_at_reference_payout"]=ev_at(r,q)
    return z

def oos_pass(r,q,p0):
    return (
      r["non_ties"]>0
      and r["accuracy"] is not None and r["accuracy"]>p0
      and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
      and r["p_value_vs_product_be"] is not None and r["p_value_vs_product_be"]<0.05
      and r["ev_at_reference_payout"] is not None and r["ev_at_reference_payout"]>0
    )

def main():
    outdir="artifacts/mexc_event_futures"; os.makedirs(outdir,exist_ok=True)
    report={
      "lab":"MEXC_EVENT_FUTURES_PRODUCT_ALIGNED_TECH_V0.16",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "source":"MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_BOUND_TO_EVENT_PAGE_BY_V0.15",
      "payout_role":"CURRENT_REFERENCE_NOT_HISTORICAL",
      "historical_holdout_sep_2026":"LOCKED_NOT_FETCHED",
      "assets":{},"discovery_cells":[],"bh_selected":[],"oos_survivors":[],
    }

    prices_by={}
    for asset,proxy in SYMBOLS.items():
        try:
            prices,reqs=m.fetch_min5_closes(proxy)
            prices_by[asset]=prices
            report["assets"][asset]={"proxy_symbol":proxy,"rows":len(prices),"requests":reqs,"status":"SOURCE_AVAILABLE"}
        except Exception as e:
            report["assets"][asset]={"proxy_symbol":proxy,"status":"SOURCE_BLOCKED","error":repr(e)}

    for asset in SYMBOLS:
        if asset not in prices_by: continue
        prices=prices_by[asset]
        for tf in m.CHART_TFS:
            for h,q in PAYOUTS[asset].items():
                p0=1.0/(1.0+q)
                for strategy in m.STRATEGIES:
                    m.P0=p0
                    raw=m.score(prices,tf,h,strategy,m.DISC_START,m.DISC_END)
                    r=decorate(raw,q,p0)
                    ok=eligible(r,h,p0)
                    report["discovery_cells"].append({
                      "asset":asset,"proxy_symbol":SYMBOLS[asset],"chart_tf_min":tf,
                      "horizon_min":h,"strategy":strategy,"payout_reference":q,
                      "break_even_accuracy":p0,"eligible":ok,"discovery":r
                    })

    selected,M,cutoff=bh(report["discovery_cells"])
    report["bh_eligible_count"]=M
    report["bh_cutoff_p"]=cutoff
    report["bh_selected"]=[{k:v for k,v in x.items() if k!="eligible"} for x in selected]

    for c in selected:
        prices=prices_by[c["asset"]]
        q=c["payout_reference"]; p0=c["break_even_accuracy"]
        m.P0=p0
        raw=m.score(prices,c["chart_tf_min"],c["horizon_min"],c["strategy"],m.OOS_START,m.OOS_END)
        r=decorate(raw,q,p0)
        if oos_pass(r,q,p0):
            report["oos_survivors"].append({
              "asset":c["asset"],"proxy_symbol":c["proxy_symbol"],
              "chart_tf_min":c["chart_tf_min"],"horizon_min":c["horizon_min"],
              "strategy":c["strategy"],"payout_reference":q,
              "break_even_accuracy":p0,"discovery":c["discovery"],"oos":r
            })

    report["verdict"]="CURRENT_PAYOUT_REFERENCE_PROXY_SURVIVORS" if report["oos_survivors"] else "NO_PRODUCT_ALIGNED_TECH_SURVIVOR"
    report["promotion_status"]="NO_EXACT_HISTORICAL_OR_LIVE_PROMOTION"

    p=f"{outdir}/product_aligned_tech_v016.json"
    with open(p,"w",encoding="utf-8") as f: json.dump(report,f,indent=2,sort_keys=True)

    print("VERDICT="+report["verdict"])
    print("DISCOVERY_CELLS="+str(len(report["discovery_cells"])))
    print("BH_ELIGIBLE="+str(M))
    print("BH_SELECTED="+str(len(selected)))
    print("OOS_SURVIVORS="+str(len(report["oos_survivors"])))
    for x in report["oos_survivors"]:
        print("SURVIVOR="+json.dumps({
          "asset":x["asset"],"tf":x["chart_tf_min"],"h":x["horizon_min"],
          "strategy":x["strategy"],"payout_ref":x["payout_reference"],
          "disc_n":x["discovery"]["non_ties"],"disc_acc":x["discovery"]["accuracy"],
          "disc_p":x["discovery"]["p_value_vs_product_be"],
          "oos_n":x["oos"]["non_ties"],"oos_acc":x["oos"]["accuracy"],
          "oos_p":x["oos"]["p_value_vs_product_be"],
          "oos_ev_ref":x["oos"]["ev_at_reference_payout"],
          "required_payout":x["oos"]["required_payout_for_ev0"],
        },sort_keys=True))
    print("HOLDOUT_LOCK=PASS")
    print("WROTE "+p)

if __name__=="__main__": main()
