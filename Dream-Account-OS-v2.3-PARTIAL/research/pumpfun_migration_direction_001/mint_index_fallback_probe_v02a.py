#!/usr/bin/env python3
"""PMD-001 V0.2A redundant mint-index fallback probe.

PRE-OUTCOME / SOURCE-INTEGRITY ONLY.

For the same deterministic 50-observation sample, query bonding-curve history first.
Only when that source is zero/unresolved in [T0-300,T0) do we query the mint index,
anchored before the nearest curve-index transaction at/after T0 when possible.
Recovered signatures are deduplicated. No post-T0 transaction can become a feature.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys,time
from typing import Any
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import exact_population_public_rpc_probe_v02 as core  # noqa

PROBE_N=50
MAX_PAGES=20


def query_history(address:str,t0:int,before:str|None=None)->tuple[list[dict[str,Any]],bool,str|None,int]:
    out=[]; pages=0; err=None; boundary=False; cursor=before
    while pages<MAX_PAGES:
        cfg:dict[str,Any]={"commitment":"finalized","limit":core.SIG_LIMIT}
        if cursor: cfg["before"]=cursor
        try: obj=core.rpc("getSignaturesForAddress",[address,cfg])
        except Exception as exc: err=repr(exc); break
        pages+=1; batch=obj.get("result") or []
        if not isinstance(batch,list): err="SIGNATURE_RESULT_SHAPE_FAILURE"; break
        out.extend(batch)
        if not batch: boundary=True; break
        times=[int(x['blockTime']) for x in batch if isinstance(x,dict) and x.get('blockTime') is not None]
        if times and min(times)<t0-300: boundary=True; break
        cursor=batch[-1].get('signature') if isinstance(batch[-1],dict) else None
        if not cursor: boundary=True; break
        time.sleep(.18)
    return out,boundary,err,pages


def successful_pre(sigs:list[dict[str,Any]],t0:int,sec:int)->set[str]:
    return {x['signature'] for x in sigs if isinstance(x,dict) and x.get('signature') and x.get('err') is None and x.get('blockTime') is not None and t0-sec<=int(x['blockTime'])<t0}


def main()->int:
    root=Path('artifacts/pmd001_mint_index_fallback_probe_v02a'); data=root/'source_data'; root.mkdir(parents=True,exist_ok=True); data.mkdir(parents=True,exist_ok=True)
    paths=core.download_and_verify(data); manifest=core.build_exact_manifest(paths); sample=core.even_sample(manifest,PROBE_N)
    audit=[]; provider_errors=0; recovered=0
    for rank,row in enumerate(sample,1):
        curve_sigs,curve_boundary,curve_err,curve_pages=query_history(row['bonding_curve_key'],row['t0_epoch'])
        if curve_err: provider_errors+=1
        curve300=successful_pre(curve_sigs,row['t0_epoch'],300) if curve_boundary else set()
        need_fallback=(not curve_boundary or not curve300)
        mint_sigs=[]; mint_boundary=False; mint_err=None; mint_pages=0; anchor=None
        if need_fallback:
            at_or_after=[x for x in curve_sigs if isinstance(x,dict) and x.get('signature') and x.get('blockTime') is not None and int(x['blockTime'])>=row['t0_epoch']]
            if at_or_after:
                # nearest in blockTime to the migration boundary; deterministic tie by signature.
                at_or_after.sort(key=lambda x:(int(x['blockTime']),str(x['signature'])))
                anchor=at_or_after[0]['signature']
            mint_sigs,mint_boundary,mint_err,mint_pages=query_history(row['mint'],row['t0_epoch'],anchor)
            if mint_err: provider_errors+=1
        mint300=successful_pre(mint_sigs,row['t0_epoch'],300) if mint_boundary else set()
        union300=curve300|mint300
        if need_fallback and not curve300 and union300: recovered+=1
        union60=(successful_pre(curve_sigs,row['t0_epoch'],60) if curve_boundary else set()) | (successful_pre(mint_sigs,row['t0_epoch'],60) if mint_boundary else set())
        union30=(successful_pre(curve_sigs,row['t0_epoch'],30) if curve_boundary else set()) | (successful_pre(mint_sigs,row['t0_epoch'],30) if mint_boundary else set())
        resolved=curve_boundary or mint_boundary
        audit.append({
          'probe_rank':rank,'mint':row['mint'],'t0_epoch':row['t0_epoch'],'need_mint_fallback':need_fallback,'migration_anchor_signature':anchor,
          'curve_pages':curve_pages,'curve_boundary_resolved':curve_boundary,'curve_n300':len(curve300),'curve_error':curve_err,
          'mint_pages':mint_pages,'mint_boundary_resolved':mint_boundary,'mint_n300':len(mint300),'mint_error':mint_err,
          'union_n300':len(union300) if resolved else None,'union_n60':len(union60) if resolved else None,'union_n30':len(union30) if resolved else None,
          'source_window_resolved':resolved,
        })
        time.sleep(.18)
    core.write_jsonl(root/'audit.jsonl',audit)
    resolved=[r for r in audit if r['source_window_resolved']]
    receipt={
      'lab':'PMD-001','stage':'MINT_INDEX_FALLBACK_PROBE_V02A','probe_n':PROBE_N,'provider_errors':provider_errors,
      'curve_only_with_300_activity':sum((r['curve_n300'] or 0)>0 for r in audit),'fallback_recovered_zero_curve_cases':recovered,
      'union_with_300_activity':sum((r.get('union_n300') or 0)>0 for r in resolved),'resolved_rows':len(resolved),'unresolved_rows':PROBE_N-len(resolved),
      'classification':'MINT_INDEX_FALLBACK_PROBE_COMPLETE','outcomes_opened':False,'forbidden_outcome_file_acquired':False,
    }
    core.write_json(root/'receipt.json',receipt); print(json.dumps(receipt,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
