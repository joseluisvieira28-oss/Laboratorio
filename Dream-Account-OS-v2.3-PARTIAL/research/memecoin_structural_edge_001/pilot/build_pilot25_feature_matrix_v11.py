#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib

COHORT_SHA="7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9"
V07_SHA="7516861dd86a2b302e4a1360acbaa68f3360b4ddd802352db93f2eccc3012090"
V10A_SHA="149d55f5abb8b781236070fd4d3ba01dd5a3a5b7a2bf054f6b22dd178a36cb95"
H=300

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p): return json.loads(p.read_text(encoding="utf-8"))
def jl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def dumpj(p,o):
    p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return sha(p)
def dumpjl(p,rows):
    with p.open("w",encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r,sort_keys=True)+"\n")
    return sha(p)
def k(r): return (str(r["mint"]),int(r["cohort_rank"]),int(r["snapshot_deadline"]))

def main():
    here=pathlib.Path(__file__).resolve().parent
    d5=here/"data"/"msel001_funding_v05"; d9=here/"data"/"msel001_holder_funding_v09"
    cohort=here/"data"/"msel001_pilot25_blockscan"/"cohort_25.jsonl"
    m7p=d5/"cluster_manifest_v07.json"; s7p=d5/"snapshots_clustered_v07.jsonl"
    m10p=d9/"holder_cluster_manifest_v10.json"; s10p=d9/"holder_hidden_concentration_v10.jsonl"
    out=here/"data"/"msel001_pilot25_feature_v11"; out.mkdir(parents=True,exist_ok=True)
    for p in (cohort,m7p,s7p,m10p,s10p):
        if not p.exists(): raise RuntimeError(f"MISSING_INPUT {p}")
    if sha(cohort)!=COHORT_SHA: raise RuntimeError("COHORT_HASH_MISMATCH")
    if sha(m7p)!=V07_SHA: raise RuntimeError("V07_MANIFEST_HASH_MISMATCH")
    if sha(m10p)!=V10A_SHA: raise RuntimeError("V10A_MANIFEST_HASH_MISMATCH")
    m7,m10=j(m7p),j(m10p)
    if m7.get("outcomes_opened") is not False or m10.get("outcomes_opened") is not False: raise RuntimeError("OUTCOME_LOCK_FAILURE")
    if m10.get("artifact")!="MSEL_HOLDER_PIT_CLUSTERING_V10A": raise RuntimeError("V10A_ARTIFACT_MISMATCH")
    if m7.get("snapshots_clustered_v07_sha256")!=sha(s7p): raise RuntimeError("V07_DATA_HASH_MISMATCH")
    if m10.get("holder_hidden_concentration_v10_sha256")!=sha(s10p): raise RuntimeError("V10A_DATA_HASH_MISMATCH")
    s7=[r for r in jl(s7p) if int(r["snapshot_horizon_seconds"])==H]
    s10=[r for r in jl(s10p) if int(r["snapshot_horizon_seconds"])==H]
    if len(s7)!=25 or len(s10)!=25: raise RuntimeError(f"T5_COUNT_FAILURE {len(s7)}/{len(s10)}")
    b7,b10={k(r):r for r in s7},{k(r):r for r in s10}
    if set(b7)!=set(b10) or len(b7)!=25: raise RuntimeError("JOIN_KEY_FAILURE")
    rows=[]
    for key in sorted(b7,key=lambda x:(x[1],x[0])):
        a,h=b7[key],b10[key]
        c=h.get("entity_top1_share"); o=a.get("cluster_adjusted_organicity_candidate")
        if c is None or o is None: raise RuntimeError(f"PRIMARY_FEATURE_MISSING mint={key[0]}")
        rows.append({"mint":key[0],"cohort_rank":key[1],"snapshot_deadline":key[2],
                     "entity_top1_share_5m":float(c),"organicity_candidate_5m":float(o),
                     "flow_v07":a,"holder_v10a":h,"outcomes_opened":False})
    # Deterministic fractional risk ranks: high concentration riskier; low Organicity riskier.
    byc=sorted(rows,key=lambda r:(r["entity_top1_share_5m"],r["cohort_rank"],r["mint"]))
    byo=sorted(rows,key=lambda r:(-r["organicity_candidate_5m"],r["cohort_rank"],r["mint"]))
    cr={r["mint"]:i/24 for i,r in enumerate(byc)}; orr={r["mint"]:i/24 for i,r in enumerate(byo)}
    for r in rows:
        r["concentration_rank_risk"]=cr[r["mint"]]; r["organicity_rank_risk"]=orr[r["mint"]]
        r["primary_pilot_risk_score"]=(cr[r["mint"]]+orr[r["mint"]])/2
    order=sorted(rows,key=lambda r:(r["primary_pilot_risk_score"],r["cohort_rank"],r["mint"]))
    safe20={r["mint"] for r in order[:5]}; safe50={r["mint"] for r in order[:13]}; risky20={r["mint"] for r in order[-5:]}
    for i,r in enumerate(order,1):
        r["primary_risk_rank_1_is_safest"]=i; r["slice_safest20"]=r["mint"] in safe20
        r["slice_safest50"]=r["mint"] in safe50; r["slice_riskiest20"]=r["mint"] in risky20
    matrix=sorted(order,key=lambda r:(r["cohort_rank"],r["mint"]))
    mp=out/"pilot25_feature_matrix_v11.jsonl"; rp=out/"pilot25_primary_risk_order_v11.jsonl"
    msha=dumpjl(mp,matrix); rsha=dumpjl(rp,order)
    manifest={"artifact":"MSEL_PILOT25_FEATURE_MATRIX_V11","pilot_only":True,"full_mve_verdict_authorized":False,
              "source_cohort_sha256":COHORT_SHA,"source_v07_manifest_sha256":V07_SHA,"source_v10a_manifest_sha256":V10A_SHA,
              "decision_horizon_seconds":300,"matrix_rows":25,
              "primary_score_formula":"0.50*rank_risk(entity_top1_share_5m)+0.50*rank_risk_low(organicity_candidate_5m)",
              "safest20_count":5,"safest50_count":13,"riskiest20_count":5,
              "feature_matrix_sha256":msha,"risk_order_sha256":rsha,"outcome_schema_frozen":False,"outcomes_opened":False}
    manp=out/"pilot25_feature_manifest_v11.json"; mansha=dumpj(manp,manifest)
    print("PASS: Pilot25 T+5 pre-outcome feature matrix V11 frozen")
    print("matrix rows: 25")
    print("primary score: 50% entity-top1 risk rank + 50% inverse-organicity risk rank")
    print("safest20/safest50/riskiest20: 5/13/5")
    print(f"feature matrix sha256: {msha}")
    print(f"risk order sha256: {rsha}")
    print(f"manifest sha256: {mansha}")
    print("PILOT ONLY — FULL MVE VERDICT NOT AUTHORIZED")
    print("OUTCOME / EXECUTION SCHEMA STILL MUST BE FROZEN BEFORE OUTCOMES")
    print("OUTCOMES REMAIN LOCKED")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e:
        print(f"FAIL-CLOSED: {e}",file=__import__("sys").stderr); raise
