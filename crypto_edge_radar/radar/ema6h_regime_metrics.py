from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Any

SIGNAL_EVENT="EMA6H_REGIME_FORWARD_SIGNAL"
RESOLUTION_EVENT="EMA6H_REGIME_FORWARD_RESOLUTION"
BOUNDARY_EVENT="EMA6H_REGIME_FORWARD_BOUNDARY"
DEVIATION_EVENT="EMA6H_REGIME_FORWARD_RULE_DEVIATION"
MIN_REVIEW=10
STRONG_REVIEW=25

def _pf(vals:list[float])->float|None:
    pos=sum(x for x in vals if x>0);neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else (float("inf") if pos>0 else None)

def _metrics(vals:list[float])->dict[str,Any]:
    if not vals:return {"n":0,"mean_bps":None,"pf":None,"positive_fraction":None}
    return {"n":len(vals),"mean_bps":sum(vals)/len(vals),"pf":_pf(vals),"positive_fraction":sum(x>0 for x in vals)/len(vals)}

def evaluate_ema6h_regime_forward(store)->dict[str,Any]:
    signals=store.read_payloads(SIGNAL_EVENT)
    resolutions=store.read_payloads(RESOLUTION_EVENT)
    boundaries=store.read_payloads(BOUNDARY_EVENT)
    deviations=store.read_payloads(DEVIATION_EVENT)

    signal_keys=[str(x.get("event_key")) for x in signals]
    resolution_keys=[str(x.get("event_key")) for x in resolutions]
    sigset=set(signal_keys);resset=set(resolution_keys)
    duplicates_signals=len(signal_keys)-len(sigset)
    duplicates_resolutions=len(resolution_keys)-len(resset)
    unresolved=sorted(sigset-resset)

    by_bucket=defaultdict(list);by_matrix=defaultdict(list);all_base=[];all_stress=[]
    for x in resolutions:
        t=x.get("paper_trade") or {};o=x.get("outcome") or {}
        b=o.get("base_net_bps");s=o.get("stress_net_bps")
        if not isinstance(b,(int,float)) or not isinstance(s,(int,float)) or not isfinite(float(b)) or not isfinite(float(s)):
            raise ValueError("EMA6H regime resolution missing finite economics")
        b=float(b);s=float(s);all_base.append(b);all_stress.append(s)
        bucket=str(t.get("regime_bucket") or "MISSING")
        state=str(t.get("regime_state") or "MISSING")
        direction="BULL_CROSS" if int(t.get("direction",0))==1 else "BEAR_CROSS"
        by_bucket[bucket].append(b);by_matrix[f"{state}:{direction}"].append(b)

    clean=(len(deviations)==0 and duplicates_signals==0 and duplicates_resolutions==0)
    n=len(all_base)
    if n>=STRONG_REVIEW and clean:classification="V3_ADJUDICATION_REVIEW_ELIGIBLE"
    elif n>=MIN_REVIEW and clean:classification="REGIME_MECHANISM_REVIEW_ELIGIBLE"
    else:classification="FORWARD_EVIDENCE_ACCUMULATING"

    return {
      "strategy_id":"EMA6H-50X200-REGIME-DEPENDENCY-001",
      "classification":classification,
      "resolved_forward_crosses":n,
      "first_review_minimum":MIN_REVIEW,
      "strong_review_minimum":STRONG_REVIEW,
      "progress_first_review":f"{n}/{MIN_REVIEW}",
      "progress_strong_review":f"{n}/{STRONG_REVIEW}",
      "all_base":_metrics(all_base),
      "all_stress":_metrics(all_stress),
      "by_regime_bucket":{k:_metrics(v) for k,v in sorted(by_bucket.items())},
      "direction_x_regime":{k:_metrics(v) for k,v in sorted(by_matrix.items())},
      "signals":len(signals),
      "boundaries_audited":len(boundaries),
      "unresolved_signals":len(unresolved),
      "unresolved_event_keys":unresolved,
      "rule_deviations":len(deviations),
      "duplicate_signals":duplicates_signals,
      "duplicate_resolutions":duplicates_resolutions,
      "integrity_clean":clean,
      "automatic_promotion":False,
      "live_trading_authorized":False,
      "next_action":"Separate frozen V3 review only after evidence threshold; no automatic rule change or promotion."
    }
