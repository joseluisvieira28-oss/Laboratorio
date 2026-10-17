"""2023-25 descriptive model full rerun, original V5 vs one-stop-line child.

No OOS, no 2026, no venue prices, no orders, no authority.
"""
from __future__ import annotations
import argparse,csv,hashlib,inspect,json,math
from pathlib import Path
from research.convex_8alt_common_2023_25 import common_3yr
from research.convex_okx_l2_stop_v02 import monotonic_matrix as child

OLD=common_3yr.old
CONFIGS={
    "SOLUSDT":("1h",3600000,{"BASE":(2,84,59.38828758287287),"STRESS":(5,84,58.2954740758989)}),
    "BNBUSDT":("4h",14400000,{"BASE":(2,28,27.377927822564764),"STRESS":(5,28,27.05530670705589)}),
}
SOURCE={"5m":333216,"1h":27768,"funding":3288}
BEFORE='p["stop"]=(max(p["initial_stop"],p["peak"]*(1-TRAIL))\n                               if close_profit>=ACTIVATE else p["initial_stop"])'
AFTER='p["stop"]=max(p["stop"], (max(p["initial_stop"],p["peak"]*(1-TRAIL))\n                               if close_profit>=ACTIVATE else p["initial_stop"]))'

def verify_single_change():
    p=Path(OLD.base.__file__)
    q=Path(child.__file__)
    original=p.read_text()
    modified=q.read_text()
    if original.count(BEFORE)!=1 or modified!=original.replace(BEFORE,AFTER):
        raise ValueError("CHILD_SOURCE_NOT_EXACT_SINGLE_STOP_LINE_PATCH")
    return {"original_source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
            "child_source_sha256":hashlib.sha256(q.read_bytes()).hexdigest(),
            "one_stop_assignment_replaced":True}

def pack(model, rows):
    v={k:model[k] for k in (
        "marked_return_pct","cash_equity_usdt","closed_trades","wins",
        "profit_factor","max_5m_low_stress_dd_pct","fees_usdt","funding_usdt",
        "annual_closed_trade_pnl_usdt","end_position_open",
        "removed_3_biggest_net_pnl_sum_usdt","signal_bars","skipped_signals_active_slot")}
    v["closed_net_usdt"]=sum(z["net_pnl"] for z in rows)
    v["entry_time_sequence"]= [z["open_t"] for z in rows]
    v["exit_reason_counts"]=model["exit_reasons"]
    return v

def audit(symbol,out):
    if symbol not in CONFIGS:raise ValueError("ONLY_SOL_1H_BNB_4H_FROZEN")
    common_3yr.apply_locked_3year_window()
    child.START=OLD.base.START
    child.END=OLD.base.END
    child.PRE=OLD.base.PRE
    frozen=verify_single_change()
    f,one,funding,manifest=OLD.fetch_all(symbol)
    if {"5m":len(f),"1h":len(one),"funding":len(funding)}!=SOURCE or len(manifest)!=112:
        raise ValueError("SOURCE_FINGERPRINT_COUNTS_FAILED")
    name,tf,cases=CONFIGS[symbol]
    bars=OLD.base.resample(f,tf)
    old={}
    for label,(slip,ntr,net) in cases.items():
        d=OLD.base.simulate(tf,bars,f,funding,slip,include_trades=True)
        rows=d.pop("trades")
        if d["closed_trades"]!=ntr or not math.isclose(d["marked_return_pct"],net,abs_tol=1e-5):
            raise ValueError("ORIGINAL_HISTORICAL_BASELINE_PARITY_FAILED:"+label)
        old[label]=(d,rows)
    # Only now may already-known historical outcomes be computed for new child.
    childs={}
    for label,(slip,_,_) in cases.items():
        d=child.simulate(tf,bars,f,funding,slip,include_trades=True)
        rows=d.pop("trades")
        childs[label]=(d,rows)
    out.mkdir(parents=True,exist_ok=True)
    allarms={}
    for label in ("BASE","STRESS"):
        orig,orows=old[label]; new,nrows=childs[label]
        for prefix,rr in (("ORIGINAL",orows),("MONOTONIC_CHILD",nrows)):
            if rr:
                with (out/(label+"_"+prefix+"_TRADES.csv")).open("w",newline="",encoding="utf8") as fh:
                    writer=csv.DictWriter(fh,fieldnames=rr[0].keys());writer.writeheader();writer.writerows(rr)
        oldsum=pack(orig,orows)
        newsum=pack(new,nrows)
        allarms[label]={"original":oldsum,"monotonic_child":newsum,
                        "child_minus_parent_marked_return_percentage_points":
                            new["marked_return_pct"]-orig["marked_return_pct"],
                        "entry_sequence_identical":oldsum["entry_time_sequence"]==newsum["entry_time_sequence"]}
        # Sequence disclosed in immutable ledger artifacts, not duplicated in concise summary JSON
        del oldsum["entry_time_sequence"]
        del newsum["entry_time_sequence"]
    report={
        "symbol":symbol,"timeframe":name,
        "status":"HISTORICAL_DESCRIPTIVE_NOT_INDEPENDENT_OOS",
        "verified_parent_counts":SOURCE,"source_manifest_files":len(manifest),
        "frozen_single_stop_code_diff":frozen,
        "scenarios":allarms,
        "2026_holdout_used":False,"real_broker_stop_acks":False,
        "trading_authority":"NONE",
    }
    (out/"MONOTONIC_ONLY_COMPARISON.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for case,results in allarms.items():
        a=results["original"];b=results["monotonic_child"]
        print("MONOTONIC_RESULT",json.dumps({
            "symbol":symbol,"cost":case,"old_return_pct":a["marked_return_pct"],
            "child_return_pct":b["marked_return_pct"],
            "child_minus_parent_pp":results["child_minus_parent_marked_return_percentage_points"],
            "old_trades":a["closed_trades"],"new_trades":b["closed_trades"],
            "old_pf":a["profit_factor"],"new_pf":b["profit_factor"],
            "old_dd":a["max_5m_low_stress_dd_pct"],"new_dd":b["max_5m_low_stress_dd_pct"],
            "yearly_child":b["annual_closed_trade_pnl_usdt"],
        },sort_keys=True),flush=True)
    print("CHILD_VERDICT",symbol,report["status"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",choices=tuple(CONFIGS),required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    audit(a.symbol,a.output_dir)

if __name__=="__main__":
    main()
