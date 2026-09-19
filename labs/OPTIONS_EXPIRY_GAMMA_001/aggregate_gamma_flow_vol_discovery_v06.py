#!/usr/bin/env python3
import json,math,random,statistics,sys
from pathlib import Path
ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"GAMMA_FLOW_VOL_DISCOVERY_AUTHORITY_V0.6.json").read_text())
IN=Path("artifacts/oeg_gamma_flow_vol_discovery_v06_inputs")
OUT=Path("artifacts/oeg_gamma_flow_vol_discovery_v06");OUT.mkdir(parents=True,exist_ok=True)

def rankdata(xs):
    idx=sorted(range(len(xs)),key=lambda i:xs[i]);r=[0.0]*len(xs);k=0
    while k<len(idx):
        j=k
        while j+1<len(idx) and xs[idx[j+1]]==xs[idx[k]]:j+=1
        avg=(k+j+2)/2.0
        for q in range(k,j+1):r[idx[q]]=avg
        k=j+1
    return r

def pearson(x,y):
    n=len(x);mx=sum(x)/n;my=sum(y)/n
    a=sum((u-mx)*(v-my) for u,v in zip(x,y));b=sum((u-mx)**2 for u in x);c=sum((v-my)**2 for v in y)
    return a/math.sqrt(b*c) if b>0 and c>0 else 0.0

def spear(rows):
    return pearson(rankdata([x["gamma_flow_balance"] for x in rows]),rankdata([x["log_realized_variance_12h"] for x in rows]))

def pctile(xs,p):
    ys=sorted(xs);q=(len(ys)-1)*p;lo=int(math.floor(q));hi=int(math.ceil(q))
    if lo==hi:return ys[lo]
    w=q-lo;return ys[lo]*(1-w)+ys[hi]*w

def main():
    files=sorted(IN.glob("shard_*.json"))
    if len(files)!=AUTH["shard_count"]:raise SystemExit(f"FAIL_CLOSED expected {AUTH['shard_count']} shards got {len(files)}")
    allrows=[];seen=set()
    for f in files:
        obj=json.loads(f.read_text())
        if obj["discovery_id"]!=AUTH["discovery_id"]:raise SystemExit("discovery id mismatch")
        for x in obj["rows"]:
            if x["date"] in seen:raise SystemExit("duplicate date")
            seen.add(x["date"]);allrows.append(x)
    if set(seen)!=set(AUTH["deterministic_dates"]):raise SystemExit("date coverage mismatch")
    tech=[x for x in allrows if x.get("technical_error")]
    rows=[x for x in allrows if x.get("eligible") and not x.get("technical_error")]
    years={y:[x for x in rows if x["year"]==y] for y in (2021,2022,2023,2024)}
    sg=AUTH["sample_gates"]
    sample_checks={"dates_ge_min":len(rows)>=sg["minimum_eligible_dates"],"years_complete":len(years)==sg["required_calendar_years"],
      "per_year_ge_min":all(len(v)>=sg["minimum_eligible_dates_per_year"] for v in years.values()),"technical_errors_eq_zero":len(tech)==0}
    if len(rows)>=2:rho=spear(rows)
    else:rho=0.0
    rng=random.Random(AUTH["primary_test"]["seed"]);reps=AUTH["primary_test"]["permutation_replications"]
    perm_ge=0
    ys=[x["log_realized_variance_12h"] for x in rows]
    for _ in range(reps):
        yy=ys[:];rng.shuffle(yy)
        rr=[dict(x,log_realized_variance_12h=v) for x,v in zip(rows,yy)]
        if spear(rr)>=rho:perm_ge+=1
    pval=(perm_ge+1)/(reps+1)
    rng=random.Random(AUTH["primary_test"]["seed"]+1);boots=[]
    breps=AUTH["primary_test"]["bootstrap_replications"];n=len(rows)
    for _ in range(breps):
        sample=[rows[rng.randrange(n)] for __ in range(n)]
        boots.append(spear(sample))
    ci=[pctile(boots,0.025),pctile(boots,0.975)] if boots else [None,None]
    yrhos={str(y):spear(v) if len(v)>=2 else None for y,v in years.items()}
    posyears=sum(1 for v in yrhos.values() if v is not None and v>0)
    g=AUTH["statistical_gates"]
    stat_checks={"rho_gte":rho>=g["spearman_rho_gte"],"permutation_p_lte":pval<=g["one_sided_permutation_p_lte"],
      "bootstrap_lower_gt_zero":ci[0] is not None and ci[0]>g["bootstrap_lower_95_gt"],"positive_year_rhos_gte":posyears>=g["minimum_positive_year_rhos"]}
    if not all(sample_checks.values()):cls=AUTH["classifications"]["insufficient"]
    elif all(stat_checks.values()):cls=AUTH["classifications"]["pass"]
    else:cls=AUTH["classifications"]["no_signal"]
    result={"lab_id":AUTH["lab_id"],"discovery_id":AUTH["discovery_id"],"classification":cls,
      "eligible_dates":len(rows),"technical_error_dates":len(tech),"eligible_dates_by_year":{str(y):len(v) for y,v in years.items()},
      "spearman_rho":rho,"one_sided_permutation_p":pval,"bootstrap_95_ci":ci,"year_rhos":yrhos,"positive_year_rhos":posyears,
      "sample_checks":sample_checks,"statistical_checks":stat_checks,
      "dealer_inventory_inferred":False,"dealer_gamma_sign_inferred":False,"option_strategy_pnl_opened":False,
      "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
    p=OUT/"discovery_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0
if __name__=="__main__":sys.exit(main())
