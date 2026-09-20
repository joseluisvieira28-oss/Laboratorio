#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

LAB_ID='MSEL-002'
SOURCE_RUN_ID=35449436752
SOURCE_ARTIFACT_ID=10592246992
SOURCE_ARTIFACT_DIGEST='sha256:659e2b03e95fbaa867f0ef20df1c44eb5a34f579aebae3b918b11b5d8c45a64f'
SOURCE_FEATURE_SHA256='59cda61a7d7284d233bd1ad93424d87db35229ac1e8876d80174591a85d36e0a'
SEED='MSEL-002-ECONOMIC-OUTCOME-CONTROLS-V1|2026-09-20'
WINDOW_SECONDS=300
CONTROLS_PER_EXPOSURE=10
EXPECTED_EXPOSURES=51
EXPECTED_IMMUTABLE_CANDIDATES=2595

KEEP=('mint','signature','slot','block_time','origin_creator','identity_key','name','symbol')

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def canon(obj)->bytes:
    return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')

def slim(r):
    return {k:r.get(k) for k in KEEP}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    p=Path(a.input); raw=p.read_bytes()
    got=sha256_bytes(raw)
    if got!=SOURCE_FEATURE_SHA256:
        raise SystemExit(f'SOURCE_FEATURE_SHA256_MISMATCH expected={SOURCE_FEATURE_SHA256} got={got}')
    rows=[json.loads(x) for x in raw.decode('utf-8').splitlines() if x.strip()]
    eligible=[r for r in rows if r.get('candidate') is True and r.get('immutable_uri_eligible') is True]
    exposures=[r for r in eligible if r.get('prior_exact_immutable_identity_reuse_6h') is True]
    controls=[r for r in eligible if r.get('prior_exact_immutable_identity_reuse_6h') is False and r.get('same_creator_clone_6h') is False]
    if len(eligible)!=EXPECTED_IMMUTABLE_CANDIDATES: raise SystemExit(f'IMMUTABLE_COUNT_MISMATCH {len(eligible)}')
    if len(exposures)!=EXPECTED_EXPOSURES: raise SystemExit(f'EXPOSURE_COUNT_MISMATCH {len(exposures)}')
    exposures=sorted(exposures,key=lambda r:(int(r['block_time']),int(r['slot']),r['mint']))
    unused={r['mint']:r for r in controls}
    sets=[]; candidate_pool_sizes=[]
    for e in exposures:
        pool=[]
        for c in unused.values():
            if abs(int(c['block_time'])-int(e['block_time']))>WINDOW_SECONDS: continue
            if c.get('origin_creator')==e.get('origin_creator'): continue
            if c.get('identity_key')==e.get('identity_key'): continue
            h=hashlib.sha256(f"{SEED}|{e['mint']}|{c['mint']}".encode()).hexdigest()
            pool.append((abs(int(c['block_time'])-int(e['block_time'])),h,int(c['slot']),c['mint'],c))
        pool.sort(key=lambda x:(x[0],x[1],x[2],x[3]))
        candidate_pool_sizes.append(len(pool))
        if len(pool)<CONTROLS_PER_EXPOSURE:
            raise SystemExit(f'CONTROL_POOL_INSUFFICIENT exposure={e["mint"]} n={len(pool)}')
        chosen=[x[4] for x in pool[:CONTROLS_PER_EXPOSURE]]
        for c in chosen: unused.pop(c['mint'])
        sets.append({
            'exposure': slim(e),
            'controls':[slim(c) for c in chosen],
            'control_time_deltas_seconds':[int(c['block_time'])-int(e['block_time']) for c in chosen],
        })
    control_mints=[c['mint'] for s in sets for c in s['controls']]
    if len(control_mints)!=EXPECTED_EXPOSURES*CONTROLS_PER_EXPOSURE or len(set(control_mints))!=len(control_mints):
        raise SystemExit('CONTROL_UNIQUENESS_FAILURE')
    payload={
        'lab_id':LAB_ID,
        'cohort_id':'MSEL-002-ECONOMIC-COHORT-V0.1',
        'status':'COHORT_FROZEN_OUTCOME_BLIND',
        'source':{
            'run_id':SOURCE_RUN_ID,'artifact_id':SOURCE_ARTIFACT_ID,'artifact_digest':SOURCE_ARTIFACT_DIGEST,
            'candidate_identity_features_sha256':SOURCE_FEATURE_SHA256,
        },
        'selection':{
            'seed':SEED,'candidate_window_seconds_each_side':WINDOW_SECONDS,
            'controls_per_exposure':CONTROLS_PER_EXPOSURE,
            'exposure_rule':'candidate && immutable_uri_eligible && prior_exact_immutable_identity_reuse_6h',
            'control_rule':'candidate && immutable_uri_eligible && !prior_exact_immutable_identity_reuse_6h && !same_creator_clone_6h && different origin_creator && different identity_key',
            'exposure_order':'block_time,slot,mint ascending',
            'control_rank':'abs_time_delta, sha256(seed|exposure_mint|control_mint), slot, mint',
            'controls_globally_unique':True,
        },
        'counts':{
            'immutable_candidates':len(eligible),'exposures':len(exposures),'controls':len(control_mints),
            'sets':len(sets),'min_preselection_control_pool':min(candidate_pool_sizes),
            'median_preselection_control_pool':sorted(candidate_pool_sizes)[len(candidate_pool_sizes)//2],
        },
        'sets':sets,
        'safety':{'outcomes_opened':False,'prices_opened':False,'returns_opened':False,'pnl_opened':False,'live_trading':False,'wallets':False,'exchange_mutation':False},
    }
    payload_hash=sha256_bytes(canon(payload))
    receipt={
        'lab_id':LAB_ID,'classification':'ECONOMIC_COHORT_FREEZE_PASS','cohort_payload_sha256':payload_hash,
        'source_feature_sha256':SOURCE_FEATURE_SHA256,'exposures':len(exposures),'controls':len(control_mints),
        'controls_unique':len(set(control_mints))==len(control_mints),'min_preselection_control_pool':min(candidate_pool_sizes),
        'outcomes_opened':False,'prices_opened':False,'returns_opened':False,'pnl_opened':False,
    }
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    (out/'MSEL_002_ECONOMIC_COHORT_V0_1.json').write_bytes(canon(payload))
    (out/'MSEL_002_ECONOMIC_COHORT_RECEIPT_V0_1.json').write_bytes(canon(receipt))
    print(json.dumps(receipt,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
