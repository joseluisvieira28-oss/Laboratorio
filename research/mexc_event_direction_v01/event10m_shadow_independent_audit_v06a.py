#!/usr/bin/env python3
"""Reaudit V0.6 10m shadow mechanics from original archived GitHub receipt; zero market access."""
import bisect,hashlib,json,math,pathlib,re
SRC=pathlib.Path("downloaded")
OUT=pathlib.Path("artifacts/event10m_v06a_independent_audit")
SYMS=("BTC_USDT","ETH_USDT")
def require(x,err):
    if not x:raise ValueError(err)
def sha(x):
    return isinstance(x,str) and re.fullmatch("[0-9a-f]{64}",x) is not None
def close(a,b,tolerance=1e-8):
    return math.isclose(float(a),float(b),rel_tol=tolerance,abs_tol=tolerance)
def baseline(side,a,b,q):
    require(side in ("UP","DOWN"),"INVALID_SIDE")
    if a==b:return {"label":"TIE","hypothetical_unit_return":0.0}
    win=(b>a) if side=="UP" else (b<a)
    return {"label":"WIN" if win else "LOSS","hypothetical_unit_return":float(q) if win else -1.}
def asof(history,t):
    times=[int(z[0]) for z in history]
    i=bisect.bisect_right(times,t)-1
    if i<0:return None
    row=history[i]
    if not 0<=t-row[0]<=5_000_000_000:return None
    return row
def validate(one,opened):
    require(one["study"]=="EVENT10M_SHADOW_EXPIRY_MECHANICS_V06","STUDY_ID")
    require(one.get("orders")==0 and one.get("private_api_calls")==0,"ORDER_OR_PRIVATE")
    require(one.get("nvidia_excluded") is True and one.get("protected_sep_holdout_unopened") is True,"SCOPE_CROSS")
    p=one.get("payout") or {}
    require(p.get("http")==200 and sha(p.get("sha256")),"MISSING_PUBLIC_PAYOUT")
    data=(p.get("raw_public_json") or {}).get("data")
    require(isinstance(data,list) and data,"PUBLIC_RAW_PARSE_MISSING")
    require(len(opened)==2 and set(x.get("symbol") for x in opened)==set(SYMS),"OPENED_RECEIPT_SCOPE")
    xout={}
    for sym in SYMS:
        product=[z for z in data if z.get("symbol")==sym]
        require(len(product)==1,"MISSING_PUBLIC_RAW_PRODUCT_"+sym)
        prod=product[0]
        cfg=(prod.get("cycleConfigMap") or {}).get("MINUTE")
        conf=[z for z in cfg if z.get("val")==10] if isinstance(cfg,list) else []
        require(len(conf)==1 and prod.get("state")=="ONLINE","INVALID_PUBLIC_10M_CONFIG_"+sym)
        qu,qd=float(conf[0]["upPayRate"]),float(conf[0]["downPayRate"])
        require(qu>0 and qd>0,"INVALID_PAYOUT_RATE")
        require(close((p.get("products") or {})[sym]["q_up"],qu) and close((p.get("products") or {})[sym]["q_down"],qd),"PAYOUT_NORMALIZATION")
        item=one["per_symbol"][sym];dec=item.get("shadow_decision");ex=item.get("shadow_expiry")
        require(isinstance(dec,dict) and isinstance(ex,dict),"MISSING_SHADOW_MECHANICS_"+sym)
        opened_one=next(z for z in opened if z["symbol"]==sym)
        require(dec==opened_one,"OPENED_BEFORE_EXPIRY_LEDGER_DIFF_"+sym)
        first=item.get("first_index_after_payout")
        require(first is not None,"NO_FIRST_INDEX_"+sym)
        require(sha(first.get("raw_sha256")) and sha(dec.get("decision_raw_sha256")),"INDEX_RAW_HASH")
        require(dec["decision_raw_sha256"]==first["raw_sha256"],"DECISION_NOT_FIRST_INDEX")
        require(close(dec["decision_index"],first["public_index"]),"DECISION_PRICE_CHANGED")
        require(dec["decision_local_monotonic_ns"]==first["monotonic_ns"],"DECISION_TIME_CHANGED")
        rec=p["received"]["monotonic_ns"]
        age=dec["decision_local_monotonic_ns"]-rec
        require(0<=age<=5_000_000_000,"PAYOUT_JOIN_OVER_5SEC")
        require(sha(dec.get("payout_raw_sha256")) and dec["payout_raw_sha256"]==p["sha256"],"PAYOUT_HASH_CHANGED")
        require(close(dec["payout_up"],qu) and close(dec["payout_down"],qd),"DECISION_Q_CHANGED")
        hist=item["bin_history"]
        require(hist and all(hist[i][0]<=hist[i+1][0] for i in range(len(hist)-1)),"BIN_HISTORY_NONCAUSAL")
        t=dec["decision_local_monotonic_ns"]
        newer=asof(hist,t);older=asof(hist,t-15_000_000_000)
        require(newer is not None and older is not None,"MISSING_PRIOR_15S_CAUSAL_FEATURE")
        bps=10000*math.log(newer[1]/older[1])
        feature=dec.get("asof_feature") or {}
        require(close(feature["binance_trailing15s_log_bps"],bps),"FEATURE_VALUE_WRONG")
        require(feature["current_trade_hash"]==newer[2] and feature["earlier_trade_hash"]==older[2],"FEATURE_HASH_MISMATCH")
        require(sha(newer[2]) and sha(older[2]),"FEATURE_INVALID_HASH")
        expected=("UP" if bps>0 else "DOWN") if abs(bps)>=5.0 else None
        require(dec.get("event_shock_side")==expected,"EVENT_SHOCK_THRESHOLD_CHANGED")
        require(dec.get("shock_rule_threshold_bps")==5.0,"THRESHOLD_CHANGED")
        require(dec["expiry_target_mono_ns"]==t+600_000_000_000,"NOT_EXACT_10M_TARGET")
        final=ex.get("expiry_tick")
        require(ex.get("status")=="SHADOW_INDEX_RESOLVED" and isinstance(final,dict),"EXPIRED_SOURCE_BLOCKED")
        late=final["monotonic_ns"]-dec["expiry_target_mono_ns"]
        require(0<=late<=5_000_000_000 and close(ex["lateness_ms"],late/1e6,1e-6),"FIRST_EXPIRY_TOO_LATE")
        require(sha(final["raw_sha256"]) and final["public_index"]>0,"BAD_EXPIRY_HASH_OR_PRICE")
        a=float(dec["decision_index"]);b=float(final["public_index"])
        require(ex["always_up"]==baseline("UP",a,b,qu),"NEGATIVE_UP_WRONG")
        require(ex["always_down"]==baseline("DOWN",a,b,qd),"NEGATIVE_DOWN_WRONG")
        if expected is None:require(ex["conditional_shock"]=="ABSTAIN","MUST_ABSTAIN")
        else:
            qq=qu if expected=="UP" else qd
            require(ex["conditional_shock"]==baseline(expected,a,b,qq),"SHOCK_RULE_WRONG")
        xout[sym]={"q_up":qu,"q_down":qd,"join_ms":round(age/1e6,3),
           "expiry_lateness_ms":round(late/1e6,3),
           "trades":len(hist),"index_ticks":item["index_ticks"],
           "feature_bps":round(bps,6),"shock_side":expected,
           "controls":{"UP":ex["always_up"],"DOWN":ex["always_down"]},
           "shock_shadow":ex["conditional_shock"]}
    return xout
def main():
    OUT.mkdir(exist_ok=True,parents=True)
    audit={"study":"EVENT10M_SHADOW_V06A_OFFLINE_FORENSIC","parent_workflow_run":41044422560,
      "new_market_source_calls":0,"actual_trades":0,
      "economic_edge_certified":False,"independent_p_model_available":False,
      "research_sample_floor_met":False,"notarized_source_custody":False,
      "true_event_futures_executed_openprice":False}
    try:
        path=SRC/"receipt.json";line=SRC/"opened_before_expiry.jsonl"
        require(path.exists() and line.exists(),"MISSING_PARENT_RECEIPT_OR_OPENED_LEDGER")
        one=json.loads(path.read_text())
        opened=[json.loads(v) for v in line.read_text().splitlines() if v.strip()]
        audit["by_symbol"]=validate(one,opened)
        audit["verdict"]="INDEPENDENT_SHADOW_MECHANICS_VERIFIED_NO_EDGE_PROOF"
    except Exception as ex:
        audit["verdict"]="INDEPENDENT_AUDIT_BLOCKED"
        audit["reason"]=type(ex).__name__+":"+str(ex)[:200]
    audit["limit"]="Original wire payout exact JSON bytes not independently preserved: SHA from parent cannot be reverified from parsed object; raw MEXC full tick stream not preserved so earliest expiry-tick claim relies on frozen script control flow, not independent tick enumeration."
    (OUT/"receipt.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    print(json.dumps(audit,indent=2,sort_keys=True),flush=True)
    if audit["verdict"]!="INDEPENDENT_SHADOW_MECHANICS_VERIFIED_NO_EDGE_PROOF":raise SystemExit(2)
if __name__=="__main__":main()
