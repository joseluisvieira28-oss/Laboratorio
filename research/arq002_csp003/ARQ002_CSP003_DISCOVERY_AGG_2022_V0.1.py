#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import json,hashlib,math,random,statistics,sys
REPS=10000;SEED=2002001
files=sorted(Path("monthly").glob("arq002_csp003_discovery_2022-*.json"))
r={"lab_id":"ARQ-002-CSP-003","classification":"RUNNING","discovery_year":2022,
   "replication_2023_accessed":False,"year_2024_scored":False,"protected_2025_accessed":False,
   "protected_2026_accessed":False,"live_trading":False,"exchange_mutation":False,"main_merge":False,"errors":[]}
mean=lambda xs: float(statistics.fmean(xs)) if xs else None
try:
    if len(files)!=12:raise RuntimeError(f"MONTH_COUNT:{len(files)}/12")
    events=[];ab={"A":0,"B":0,"C":0,"D":0};masked=amb=nocvd=0
    for p in files:
        x=json.loads(p.read_text())
        if x.get("classification")!="DISCOVERY_MONTH_COMPLETE":raise RuntimeError(f"MONTH_FAIL:{x.get('month')}")
        for k in ab:ab[k]+=int(x["ablation_counts"][k])
        masked+=x["source_masked_sweep_events"];amb+=x["ambiguous_both_sides"];nocvd+=x["no_cvd_notional_events"];events+=x["events"]
    c=[e for e in events if e["d_confirmed"]];rej=[e for e in events if not e["d_confirmed"]]
    base=mean([e["base14"] for e in c]);stress=mean([e["stress20"] for e in c]);rm=mean([e["base14"] for e in rej])
    delta=None if base is None or rm is None else base-rm
    days=sorted(set(e["utc_day"] for e in c));by=defaultdict(list)
    for e in c:by[e["utc_day"]].append(e["base14"])
    rng=random.Random(SEED);boots=[]
    if days:
        for _ in range(REPS):
            vals=[]
            for __ in range(len(days)):vals+=by[days[rng.randrange(len(days))]]
            boots.append(sum(vals)/len(vals))
        boots.sort();lo=boots[int(.025*REPS)];hi=boots[min(REPS-1,int(.975*REPS))]
    else:lo=hi=None
    sh=[e for e in c if e["direction"]=="SHORT"];lg=[e for e in c if e["direction"]=="LONG"]
    sm=mean([e["base14"] for e in sh]);lm=mean([e["base14"] for e in lg])
    months={};pos=0
    for m in [f"2022-{i:02d}" for i in range(1,13)]:
        xs=[e["base14"] for e in c if e["month"]==m];mm=mean(xs);pos+=int(mm is not None and mm>0);months[m]={"n":len(xs),"base14_mean":mm}
    conc=max((v["n"]/len(c) for v in months.values()),default=1.0)
    k=max(1,math.ceil(.01*len(c))) if c else 0;ranked=sorted(c,key=lambda e:(-e["base14"],e["event_ts_ms"]))
    trim=mean([e["base14"] for e in ranked[k:]]) if k else None
    gates={"source_census_pass":True,"d_confirmed_n_gte_200":len(c)>=200,"unique_utc_days_gte_60":len(days)>=60,
      "base14_mean_gt_0":base is not None and base>0,"stress20_mean_gt_0":stress is not None and stress>0,
      "confirmed_minus_rejected_gt_0":delta is not None and delta>0,"bootstrap_95_lower_gt_0":lo is not None and lo>0,
      "short_side_base14_gt_0":sm is not None and sm>0,"long_side_base14_gt_0":lm is not None and lm>0,
      "positive_months_gte_7":pos>=7,"remove_best_1pct_still_positive":trim is not None and trim>0,
      "max_month_concentration_lte_25pct":conc<=.25}
    ok=all(gates.values())
    r.update({"classification":"DISCOVERY_SURVIVES_NOT_EDGE" if ok else "DISCOVERY_FAIL_NO_PROMOTION",
      "ablation_counts":ab,"baseline_A_n":len(events),"d_confirmed_n":len(c),"d_rejected_n":len(rej),
      "source_masked_sweep_events":masked,"ambiguous_both_sides":amb,"no_cvd_notional_events":nocvd,
      "d_confirmed_low10_mean":mean([e["low10"] for e in c]),"d_confirmed_base14_mean":base,
      "d_confirmed_stress20_mean":stress,"d_rejected_base14_mean":rm,"confirmed_minus_rejected_base14_delta":delta,
      "unique_utc_days":len(days),"bootstrap_utc_day":{"repetitions":REPS,"seed":SEED,"ci95_low":lo,"ci95_high":hi},
      "short_side":{"n":len(sh),"base14_mean":sm},"long_side":{"n":len(lg),"base14_mean":lm},
      "months":months,"positive_month_count":pos,"max_month_concentration":conc,
      "best_1pct_removed_count":k,"best_1pct_removed_base14_mean":trim,"gates":gates,"all_gates_pass":ok})
except Exception as e:
    r["classification"]="TECHNICAL_FAIL_CLOSED";r["errors"].append(f"{type(e).__name__}:{e}")
r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path("ARQ002_CSP003_DISCOVERY_RECEIPT_2022_V0.1.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":r["classification"],"A":(r.get("ablation_counts")or{}).get("A"),"D":(r.get("ablation_counts")or{}).get("D"),
"base14":r.get("d_confirmed_base14_mean"),"stress20":r.get("d_confirmed_stress20_mean"),"delta":r.get("confirmed_minus_rejected_base14_delta"),
"bootstrap":r.get("bootstrap_utc_day"),"gates":r.get("gates"),"errors":r["errors"],"receipt_sha256":r["receipt_sha256"]},sort_keys=True))
sys.exit(0 if r["classification"] in {"DISCOVERY_SURVIVES_NOT_EDGE","DISCOVERY_FAIL_NO_PROMOTION"} else 1)
