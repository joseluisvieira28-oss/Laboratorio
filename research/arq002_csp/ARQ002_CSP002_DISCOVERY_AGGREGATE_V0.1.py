#!/usr/bin/env python3
"""ARQ-002-CSP-002 frozen annual Discovery adjudicator."""
from pathlib import Path
import csv,hashlib,json,math,random,statistics,sys

ROOT=Path("month_artifacts")
OUT=Path("ARQ002_CSP002_DISCOVERY_RESULT_V0.1.json")
MONTHS=[f"2024-{m:02d}" for m in range(1,13)]
SEED=2002001
REPS=10000

def mean(xs):
    return float(statistics.fmean(xs)) if xs else None

def percentile_linear(sorted_vals,p):
    n=len(sorted_vals)
    if n==0:return None
    pos=p*(n-1);lo=math.floor(pos);hi=math.ceil(pos)
    if lo==hi:return float(sorted_vals[lo])
    w=pos-lo
    return float(sorted_vals[lo]*(1-w)+sorted_vals[hi]*w)

def internal_receipt_ok(r):
    given=r.get("receipt_sha256")
    x=dict(r);x.pop("receipt_sha256",None)
    calc=hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return given==calc

def main():
    receipts={};rows=[]
    for ym in MONTHS:
        rp=ROOT/f"ARQ002_CSP002_MONTH_{ym}_RECEIPT.json"
        op=ROOT/f"ARQ002_CSP002_OBS_{ym}.csv"
        if not rp.exists() or not op.exists():
            raise SystemExit(f"MISSING_MONTH_ARTIFACT:{ym}")
        r=json.loads(rp.read_text())
        if r.get("classification")!="MONTH_OBSERVATIONS_MATERIALIZED":
            raise SystemExit(f"MONTH_CLASSIFICATION:{ym}:{r.get('classification')}")
        if not internal_receipt_ok(r):raise SystemExit(f"MONTH_RECEIPT_HASH:{ym}")
        if hashlib.sha256(op.read_bytes()).hexdigest()!=r["observation_sha256"]:
            raise SystemExit(f"OBS_HASH:{ym}")
        if r.get("source_manifest_sha256")!="67058b6e4575f1a3a442c05cf4a57a66e354ee058848aa9b10caaa0648cf36ea":
            raise SystemExit(f"MANIFEST_BINDING:{ym}")
        receipts[ym]=r
        with op.open(newline="",encoding="utf-8") as f:
            for x in csv.DictReader(f):
                rows.append({
                    "event_ts_ms":int(x["event_ts_ms"]),"utc_date":x["utc_date"],"month":x["month"],
                    "side":x["side"],"direction":int(x["direction"]),
                    "B":int(x["B_cvd"]),"C":int(x["C_oi"]),"D":int(x["D_full"]),
                    "gross":float(x["gross"]),"net10":float(x["net10"]),
                    "net14":float(x["net14"]),"net20":float(x["net20"]),
                })
    if len({x["event_ts_ms"] for x in rows})!=len(rows):
        raise SystemExit("DUPLICATE_EVENT_TIMESTAMP")

    conf=[x for x in rows if x["D"]==1]
    rej=[x for x in rows if x["D"]==0]
    base14=mean([x["net14"] for x in conf]);stress20=mean([x["net20"] for x in conf])
    rej14=mean([x["net14"] for x in rej])
    delta=None if base14 is None or rej14 is None else base14-rej14

    byday={}
    for x in conf:byday.setdefault(x["utc_date"],[]).append(x["net14"])
    days=sorted(byday)
    boot=[]
    if days:
        rng=random.Random(SEED);K=len(days)
        for _ in range(REPS):
            vals=[]
            for _j in range(K):
                d=days[rng.randrange(K)]
                vals.extend(byday[d])
            boot.append(statistics.fmean(vals))
        boot.sort()
        ci_low=percentile_linear(boot,0.025);ci_high=percentile_linear(boot,0.975)
        boot_mean=statistics.fmean(boot)
    else:
        ci_low=ci_high=boot_mean=None

    side_means={
        "HIGH_SHORT":mean([x["net14"] for x in conf if x["side"]=="HIGH_SHORT"]),
        "LOW_LONG":mean([x["net14"] for x in conf if x["side"]=="LOW_LONG"]),
    }
    month_stats={}
    positive_months=0
    for ym in MONTHS:
        xs=[x["net14"] for x in conf if x["month"]==ym]
        m=mean(xs)
        month_stats[ym]={"n":len(xs),"base14_mean":m}
        if m is not None and m>0:positive_months+=1

    if conf:
        k=max(1,math.ceil(0.01*len(conf)))
        ranked=sorted(conf,key=lambda x:(-x["net14"],x["event_ts_ms"]))
        trimmed=ranked[k:]
        trimmed_mean=mean([x["net14"] for x in trimmed])
        max_month_conc=max(month_stats[m]["n"]/len(conf) for m in MONTHS)
    else:
        k=0;trimmed_mean=None;max_month_conc=1.0

    gates={
        "source_mask_pass":True,
        "d_confirmed_n_gte_200":len(conf)>=200,
        "d_confirmed_unique_days_gte_60":len(days)>=60,
        "base14_mean_gt_0":base14 is not None and base14>0,
        "stress20_mean_gt_0":stress20 is not None and stress20>0,
        "confirmed_minus_rejected_base14_gt_0":delta is not None and delta>0,
        "bootstrap_95_lower_gt_0":ci_low is not None and ci_low>0,
        "high_short_base14_gt_0":side_means["HIGH_SHORT"] is not None and side_means["HIGH_SHORT"]>0,
        "low_long_base14_gt_0":side_means["LOW_LONG"] is not None and side_means["LOW_LONG"]>0,
        "positive_months_gte_7_of_12":positive_months>=7,
        "remove_best_1pct_still_positive":trimmed_mean is not None and trimmed_mean>0,
        "max_month_concentration_lte_25pct":max_month_conc<=0.25,
    }
    passed=all(gates.values())
    out={
        "lab_id":"ARQ-002-CSP-002","date_utc":"2026-09-23",
        "classification":"DISCOVERY_SURVIVES_NOT_EDGE" if passed else "DISCOVERY_FAIL_NO_PROMOTION",
        "source":{
            "source_mask_classification":"SOURCE_MASK_PASS",
            "source_mask_run":35900923026,
            "source_mask_receipt_sha256":"5d4bc118faf14234465dbcf124b895f16224f847c828651faa08f081c5602b18",
            "source_manifest_sha256":"67058b6e4575f1a3a442c05cf4a57a66e354ee058848aa9b10caaa0648cf36ea",
            "masked_days":["2024-02-16","2024-10-28"],
            "eligible_days":364
        },
        "counts":{
            "baseline_A":len(rows),
            "B_cvd":sum(x["B"] for x in rows),
            "C_oi":sum(x["C"] for x in rows),
            "D_full":len(conf),
            "D_rejected":len(rej),
            "D_unique_utc_days":len(days)
        },
        "primary":{
            "D_base14_mean":base14,"D_stress20_mean":stress20,
            "D_rejected_base14_mean":rej14,
            "D_minus_rejected_base14_delta":delta,
            "bootstrap_repetitions":REPS,"bootstrap_seed":SEED,
            "bootstrap_ci95_low":ci_low,"bootstrap_ci95_high":ci_high,
            "bootstrap_mean":boot_mean
        },
        "sides":side_means,
        "months":month_stats,
        "positive_month_count":positive_months,
        "best_1pct_removed_count":k,
        "best_1pct_removed_base14_mean":trimmed_mean,
        "max_month_concentration":max_month_conc,
        "gates":gates,"all_gates_pass":passed,
        "monthly_receipts":{m:receipts[m]["receipt_sha256"] for m in MONTHS},
        "firewall":{
            "confirmation_2025_accessed":False,"final_holdout_2026_accessed":False,
            "live_trading":False,"orders":False,"exchange_mutation":False,
            "wallet_access":False,"main_merge":False
        }
    }
    out["receipt_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":out["classification"],"counts":out["counts"],
        "primary":out["primary"],"sides":out["sides"],
        "positive_month_count":positive_months,
        "best_1pct_removed_base14_mean":trimmed_mean,
        "max_month_concentration":max_month_conc,
        "gates":gates,"receipt_sha256":out["receipt_sha256"],
        "confirmation_2025_accessed":False,"final_holdout_2026_accessed":False
    },sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
