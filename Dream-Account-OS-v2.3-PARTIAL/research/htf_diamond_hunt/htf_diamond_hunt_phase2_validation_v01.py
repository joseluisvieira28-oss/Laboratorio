from __future__ import annotations

import json, hashlib, sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from research.htf_diamond_hunt import htf_diamond_hunt_scale_transfers_v01 as core

ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/'research'/'htf_diamond_hunt'/'HTF_DIAMOND_HUNT_001_PHASE2_VALIDATION_FREEZE_V0.1.json'
BIND=ROOT/'research'/'htf_diamond_hunt'/'HTF_DIAMOND_HUNT_001_PHASE2_SOURCE_BINDING_V0.1.json'
OUT=ROOT/'research'/'local_data'/'htf_diamond_hunt_phase2_validation_v01'
SYMBOLS=core.SYMBOLS


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def classify(base:dict[str,Any],stress:dict[str,Any],boot:dict[str,Any])->tuple[str,list[str]]:
    n=int(base['resolved_trade_count'])
    if n<100: return 'INSUFFICIENT_SAMPLE',['resolved_trade_count_below_100']
    fails=[]
    checks=((base['net_expectancy_r'],0,'base_net_expectancy_not_positive'),(base['profit_factor_r'],1,'base_profit_factor_not_above_1'),(boot['lower'],0,'bootstrap_lower_95_not_positive'),(stress['net_expectancy_r'],0,'stress_expectancy_not_positive'))
    for v,t,r in checks:
        if v is None or float(v)<=t: fails.append(r)
    return ('VALIDATION_SURVIVES' if not fails else 'VALIDATION_FAIL'),fails

def main(argv:list[str])->int:
    if len(argv)!=2: raise SystemExit('usage: phase2_validation SOURCE_DIR')
    src=Path(argv[1]).resolve(); OUT.mkdir(parents=True,exist_ok=True)
    f=json.loads(FREEZE.read_text()); b=json.loads(BIND.read_text())
    assert f['status']=='FROZEN_BEFORE_PHASE2_SOURCE_ACCESS_OR_OUTCOMES'
    assert [x['cell_id'] for x in f['cells']]==['DH-02-V1','DH-03-V1']
    assert b['status']=='FROZEN_EXACT_PHASE2_SOURCE_BEFORE_VALIDATION_OUTCOMES'
    rec=json.loads((src/'HTF_DIAMOND_HUNT_001_PHASE2_SOURCE_GATE_V0.1.json').read_text())
    assert rec['status']=='SOURCE_DATA_PASS' and rec['source_fingerprint']==b['source_fingerprint']
    assert rec['outcome_evaluation_performed'] is False
    for y in (2021,2022,2023,2024,2025,2026): assert rec[f'access_{y}_performed'] is False
    source={}
    for s in SYMBOLS:
        p=src/'canonical_15m'/f'{s}_15m.csv'; assert sha256_file(p)==b['canonical_15m'][s]['sha256']; source[s]=core.load_15m(p)
    cells={x['cell_id']:x for x in f['cells']}; results={}; ledgers={}
    for cid,tf,ms in (('DH-02-V1','6H',21_600_000),('DH-03-V1','12H',43_200_000)):
        derived={}; counts={}; incomplete=0
        for s in SYMBOLS:
            bars,inc=core.aggregate(source[s],ms); derived[s]=bars; counts[s]=len(bars); incomplete+=inc
        rows,base=core.evaluate_cell(cid,'donchian',derived,ms,cells[cid]['rule'])
        stress=core.stress_metrics(rows); boot=core.bootstrap(rows); cls,fails=classify(base,stress,boot)
        result={'cell_id':cid,'lineage':cells[cid]['lineage'],'classification':cls,'failed_conditions':fails,'base':base,'stress':stress,'bootstrap':boot,'derived_bar_count_by_symbol':counts,'incomplete_bucket_count':incomplete}
        results[cid]=result; ledgers[cid]=rows; print(cid,json.dumps(result,sort_keys=True),flush=True)
    receipt={'campaign_id':'HTF-DIAMOND-HUNT-001','phase':'PHASE_2_DONCHIAN_FAMILY_TEMPORAL_VALIDATION','status':'PHASE2_VALIDATION_BLOCK_COMPLETE','source_artifact_id':b['artifact_id'],'source_artifact_digest':b['artifact_digest'],'source_fingerprint':b['source_fingerprint'],'results':results,'family_interpretation_policy':'Both 6H and 12H reported jointly; no winner timeframe selection.','access_2021_performed':False,'access_2022_performed':False,'access_2023_performed':False,'access_2024_performed':False,'access_2025_performed':False,'access_2026_performed':False,'post_outcome_tuning':False,'live_trading':False,'exchange_mutation':False}
    receipt['fingerprint']=core.canonical_hash(receipt)
    (OUT/'HTF_DIAMOND_HUNT_001_PHASE2_VALIDATION_RECEIPT_V0.1.json').write_text(json.dumps(receipt,indent=2,sort_keys=True))
    for cid,rows in ledgers.items(): (OUT/f'{cid}_LEDGER.json').write_text(json.dumps([asdict(r) for r in rows],indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main(sys.argv))
