#!/usr/bin/env python3
import json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_SESSION_SHOCK_NEWASSETS_RULE_V1.5.json").read_text())
B=json.loads((HERE/"MEXC_SESSION_SHOCK_NEWASSETS_SOURCE_BINDING_V1.5.json").read_text())
IN=Path("artifacts/mexc_global_assets/session_shock_newassets_v15/assets")
OUT=Path("artifacts/mexc_global_assets/session_shock_newassets_v15")
def mean(x):return sum(x)/len(x) if x else None
def binom(w,n):return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def main():
    rec=[json.loads(p.read_text()) for p in IN.glob("*.json")]
    exp={x["target"] for x in B["candidates"]}
    if {x["target"] for x in rec}!=exp:raise SystemExit("FAIL_CLOSED_RECEIPT_SET")
    byts={}
    for x in rec:
        for e in x["events"]:byts.setdefault(int(e["timestamp"]),[]).append(e)
    clusters=[];next_allowed=-1
    for t in sorted(byts):
        if t<next_allowed:continue
        ev=byts[t];g=mean([x["gross_bps"] for x in ev])
        clusters.append({"timestamp":t,"date":ev[0]["date"],"asset_count":len(ev),"gross_bps":g,"assets":[x["target"] for x in ev]})
        next_allowed=t+R["cluster_global_cooldown_min"]*60
    vals=[x["gross_bps"] for x in clusters];n=len(vals);w=sum(x>0 for x in vals);k=n//2
    halves=[mean(vals[:k]),mean(vals[k:])] if n>=2 else [None,None]
    med=statistics.median(vals) if vals else None;mg=mean(vals);p=binom(w,n)
    dates=len(set(x["date"] for x in clusters))
    G=R["scientific_gate"]
    sci=bool(n>=G["min_clusters"] and dates>=G["min_triggered_days"] and mg is not None and mg>0 and med is not None and med>0 and w/n>G["win_cluster_rate_gt"] and all(x is not None and x>0 for x in halves) and p<G["exact_one_sided_binomial_p_lt"])
    net={str(c):(mg-c if mg is not None else None) for c in R["cost_scenarios_roundtrip_bps"]}
    netmed={str(c):(med-c if med is not None else None) for c in R["cost_scenarios_roundtrip_bps"]}
    robust=bool(sci and net["16"]>0 and netmed["16"]>0)
    verdict="ROBUST_API_FEE_SURVIVOR_FOUND__EXECUTION_VALIDATION_REQUIRED" if robust else ("SCIENTIFIC_PASS__FEE_BLOCKED" if sci else ("UNDERPOWERED_AT_FROZEN_V15_GATE" if n<G["min_clusters"] or dates<G["min_triggered_days"] else "NO_EDGE_AT_FROZEN_V15_GATE"))
    rep={"verdict":verdict,"cluster_count":n,"triggered_days":dates,"wins":w,"win_rate":w/n if n else None,"mean_gross_bps":mg,"median_gross_bps":med,"half_means_bps":halves,"p":p,"mean_net_bps":net,"median_net_bps":netmed,"scientific_pass":sci,"robust_fee_survivor":robust,"raw_event_count":sum(x["event_count"] for x in rec),"clusters":clusters,"orders":False,"live_trading":False}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"MEXC_SESSION_SHOCK_NEWASSETS_CLOSEOUT_V15.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({k:rep[k] for k in ["verdict","cluster_count","triggered_days","wins","win_rate","mean_gross_bps","median_gross_bps","half_means_bps","p","mean_net_bps","median_net_bps","scientific_pass","robust_fee_survivor","raw_event_count"]},indent=2))
if __name__=="__main__":main()
