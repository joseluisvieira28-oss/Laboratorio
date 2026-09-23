#!/usr/bin/env python3
"""ARQ-002-CSP-002 frozen 2024 Discovery aggregate."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,math,random,statistics,sys

REPS=10000
SEED=2002001
OUT=Path("ARQ002_CSP002_DISCOVERY_RECEIPT_V0.1.json")

def mean(xs): return float(statistics.fmean(xs)) if xs else None

files=sorted(Path("monthly_discovery").glob("arq002_csp002_discovery_2024-*.json"))
rec={
  "lab_id":"ARQ-002-CSP-002","classification":"RUNNING",
  "confirmation_2025_accessed":False,"final_holdout_2026_accessed":False,
  "live_trading":False,"exchange_mutation":False,"main_merge":False,"errors":[]
}
try:
    if len(files)!=12: raise RuntimeError(f"MONTH_COUNT:{len(files)}/12")
    events=[]; ab={"A":0,"B":0,"C":0,"D":0}; masked=ambig=nocvd=0
    source_hashes=set()
    for p in files:
        r=json.loads(p.read_text())
        if r.get("classification")!="DISCOVERY_MONTH_COMPLETE":
            raise RuntimeError(f"MONTH_FAIL:{r.get('month')}")
        source_hashes.add(r.get("source_closeout_receipt_sha256"))
        for k in ab: ab[k]+=int(r["ablation_counts"][k])
        masked+=int(r["source_masked_sweep_events"])
        ambig+=int(r["ambiguous_both_sides"])
        nocvd+=int(r["no_cvd_notional_events"])
        events.extend(r["events"])
    if len(source_hashes)!=1: raise RuntimeError(f"SOURCE_BINDING_MISMATCH:{source_hashes}")

    confirmed=[e for e in events if e["d_confirmed"]]
    rejected=[e for e in events if not e["d_confirmed"]]
    base=mean([e["base14"] for e in confirmed])
    stress=mean([e["stress20"] for e in confirmed])
    rej=mean([e["base14"] for e in rejected])
    delta=None if base is None or rej is None else base-rej

    days=sorted(set(e["utc_day"] for e in confirmed))
    byday=defaultdict(list)
    for e in confirmed: byday[e["utc_day"]].append(e["base14"])
    rng=random.Random(SEED)
    boots=[]
    if days:
        for _ in range(REPS):
            s=0.0;n=0
            for _j in range(len(days)):
                d=days[rng.randrange(len(days))]
                vals=byday[d]; s+=sum(vals); n+=len(vals)
            boots.append(s/n)
        boots.sort()
        lo=boots[int(0.025*REPS)]
        hi=boots[min(REPS-1,int(0.975*REPS))]
    else:
        lo=hi=None

    short=[e for e in confirmed if e["direction"]=="SHORT"]
    long=[e for e in confirmed if e["direction"]=="LONG"]
    short_mean=mean([e["base14"] for e in short])
    long_mean=mean([e["base14"] for e in long])

    month_stats={}
    positive_months=0
    for m in [f"2024-{i:02d}" for i in range(1,13)]:
        xs=[e["base14"] for e in confirmed if e["month"]==m]
        mm=mean(xs)
        if mm is not None and mm>0: positive_months+=1
        month_stats[m]={"n":len(xs),"base14_mean":mm}
    max_month_conc=max((v["n"]/len(confirmed) for v in month_stats.values()),default=1.0)

    k=max(1,math.ceil(0.01*len(confirmed))) if confirmed else 0
    ranked=sorted(confirmed,key=lambda e:(-e["base14"],e["event_ts_ms"]))
    trimmed=ranked[k:] if k else []
    trimmed_mean=mean([e["base14"] for e in trimmed])

    gates={
      "source_census_pass":True,
      "d_confirmed_n_gte_200":len(confirmed)>=200,
      "unique_utc_days_gte_60":len(days)>=60,
      "base14_mean_gt_0":base is not None and base>0,
      "stress20_mean_gt_0":stress is not None and stress>0,
      "confirmed_minus_rejected_gt_0":delta is not None and delta>0,
      "bootstrap_95_lower_gt_0":lo is not None and lo>0,
      "short_side_base14_gt_0":short_mean is not None and short_mean>0,
      "long_side_base14_gt_0":long_mean is not None and long_mean>0,
      "positive_months_gte_7":positive_months>=7,
      "remove_best_1pct_still_positive":trimmed_mean is not None and trimmed_mean>0,
      "max_month_concentration_lte_25pct":max_month_conc<=0.25,
    }
    survived=all(gates.values())
    rec.update({
      "classification":"DISCOVERY_SURVIVES_NOT_EDGE" if survived else "DISCOVERY_FAIL_NO_PROMOTION",
      "source_closeout_receipt_sha256":next(iter(source_hashes)),
      "ablation_counts":ab,
      "baseline_A_n":len(events),
      "d_confirmed_n":len(confirmed),"d_rejected_n":len(rejected),
      "source_masked_sweep_events":masked,"ambiguous_both_sides":ambig,"no_cvd_notional_events":nocvd,
      "d_confirmed_low10_mean":mean([e["low10"] for e in confirmed]),
      "d_confirmed_base14_mean":base,
      "d_confirmed_stress20_mean":stress,
      "d_rejected_base14_mean":rej,
      "confirmed_minus_rejected_base14_delta":delta,
      "unique_utc_days":len(days),
      "bootstrap_utc_day":{"repetitions":REPS,"seed":SEED,"ci95_low":lo,"ci95_high":hi},
      "short_side":{"n":len(short),"base14_mean":short_mean},
      "long_side":{"n":len(long),"base14_mean":long_mean},
      "months":month_stats,"positive_month_count":positive_months,
      "max_month_concentration":max_month_conc,
      "best_1pct_removed_count":k,"best_1pct_removed_base14_mean":trimmed_mean,
      "gates":gates,"all_gates_pass":survived
    })
except Exception as e:
    rec["classification"]="TECHNICAL_FAIL_CLOSED"; rec["errors"].append(f"{type(e).__name__}:{e}")

rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
OUT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps({
  "classification":rec["classification"],
  "A":(rec.get("ablation_counts") or {}).get("A"),
  "B":(rec.get("ablation_counts") or {}).get("B"),
  "C":(rec.get("ablation_counts") or {}).get("C"),
  "D":(rec.get("ablation_counts") or {}).get("D"),
  "d_confirmed_n":rec.get("d_confirmed_n"),
  "base14_mean":rec.get("d_confirmed_base14_mean"),
  "stress20_mean":rec.get("d_confirmed_stress20_mean"),
  "delta":rec.get("confirmed_minus_rejected_base14_delta"),
  "bootstrap":rec.get("bootstrap_utc_day"),
  "gates":rec.get("gates"),
  "errors":rec["errors"],"receipt_sha256":rec["receipt_sha256"]
},sort_keys=True))
sys.exit(0 if rec["classification"] in {"DISCOVERY_SURVIVES_NOT_EDGE","DISCOVERY_FAIL_NO_PROMOTION"} else 1)
