#!/usr/bin/env python3
"""Strict V0.1.1 event parser for BINANCE-MARGIN-BORROW-ACCESS-001.
Frozen by EVENT_PARSER_SEMANTIC_ERRATUM_V0_1_1. Source-only/outcome-blind.
"""
from __future__ import annotations
import argparse, glob, hashlib, json, re, sys, time
from pathlib import Path
from typing import Any
import event_parser_v01 as v01
import source_census_v04 as base

SHARD_COUNT=4
START_MS=base.START_MS
END_MS=base.END_MS
OPEN_ENDED_RE=re.compile(r"\band\s+more\s+as\s+(?:a\s+)?new\s+borrowable\s+assets?\b", re.I)


def parse_one(code:str)->dict[str,Any]:
    obj,status,raw_sha,retries=base.detail_request(code)
    data=obj.get('data',obj)
    if not isinstance(data,dict): raise RuntimeError(f'canonical article data is not object: {code}')
    payload_code=str(data.get('code') or '').lower()
    if payload_code and payload_code!=code.lower(): raise RuntimeError(f'article identity mismatch {code}!={payload_code}')
    title=v01.norm(str(data.get('title') or ''))
    publish_ms=base.parse_timestamp_value(data.get('publishDate'))
    if not title or publish_ms is None or not (START_MS<=publish_ms<=END_MS):
        raise RuntimeError(f'missing/invalid canonical title or publishDate for {code}')
    ast=v01.parse_body_ast(data.get('body'))
    blocks=v01.scientific_blocks(ast)
    full_text=v01.norm(v01.node_text(ast)); main_text=v01.norm(v01.strip_disclaimer(full_text))
    body_sha=hashlib.sha256(str(data.get('body') or '').encode()).hexdigest()
    exclusion_reason=None

    if re.search(r'\b(delist|remove|removal)\b',title,re.I) and re.search(r'borrowable assets?',title,re.I):
        direction='REMOVE'; assets=[]; route='TITLE_REMOVE'; evidence=title
    elif re.search(r'Introduces Collateral Haircuts',title,re.I):
        direction='OTHER'; assets=[]; route='TITLE_OTHER'; evidence=title; exclusion_reason='DIFFERENT_MECHANISM'
    else:
        assets,evidence=v01.extract_clause_assets(blocks)
        route='CLAUSE' if assets else ''
        if assets and evidence and OPEN_ENDED_RE.search(evidence):
            direction='OTHER'; assets=[]; route='ASSET_LIST_OPEN_ENDED'; exclusion_reason='ASSET_LIST_OPEN_ENDED'
        elif assets:
            direction='ADD'
        else:
            assets,evidence=v01.extract_table_assets(ast)
            route='TABLE' if assets else 'NO_EXPLICIT_CROSS_BORROW_ADD'
            if assets:
                direction='ADD'
            else:
                direction='OTHER'; assets=[]; exclusion_reason='NO_EXPLICIT_CROSS_BORROW_CLAUSE'

    title_body=v01.norm(title+' '+main_text)
    confounds={
      'new_cross_margin_pair':bool(re.search(r'\bnew\s+(?:cross\s+margin|margin|trading)\s+pairs?\b|new trading pairs? on Cross Margin',title_body,re.I)),
      'isolated_margin':bool(re.search(r'\bIsolated Margin\b',title_body,re.I)),
      'spot_listing_or_start':bool(re.search(r'\bBinance will list\b|\bSpot trading (?:will )?(?:open|start|commence)\b|\blisted on Binance Spot\b|\binitial Spot trading\b',title_body,re.I)),
      'convert':bool(re.search(r'\bConvert\b',title_body,re.I)),
      'earn':bool(re.search(r'\bEarn\b',title_body,re.I)),
      'buy_crypto':bool(re.search(r'\bBuy Crypto\b',title_body,re.I)),
      'futures_or_perpetual':bool(re.search(r'\bFutures?\b|\bPerpetual\b',title_body,re.I)),
    }
    times=v01.explicit_times(main_text,publish_ms); effective_ms=times[0] if times else None
    return {
      'code':code.lower(),'http_status':status,'request_retries':retries,'response_sha256':raw_sha,
      'official_title':title,'official_publish_ms':publish_ms,'event_information_ms':publish_ms,
      'effective_ms':effective_ms,'explicit_utc_times':times[:12],'direction':direction,
      'cross_margin_borrowable_assets':assets,'asset_parse_ambiguous':False,'parser_route':route,
      'exclusion_reason':exclusion_reason,'confounds':confounds,'body_sha256':body_sha,
      'evidence_snippet':v01.norm(evidence or '')[:1200],
    }


def cmd_shard(input_path:Path,shard:int,out_dir:Path)->int:
    source=json.loads(input_path.read_text()); codes=source.get('codes',[])
    if source.get('structural_articles')!=69 or len(codes)!=69 or len(set(codes))!=69: raise SystemExit('frozen input invariant failed')
    assigned=[c for i,c in enumerate(codes) if i%SHARD_COUNT==shard]; records=[]; failure=None; classification='EVENT_PARSE_SHARD_PASS'
    try:
      for code in assigned:
        records.append(parse_one(code)); time.sleep(2.5)
    except Exception as exc:
      classification='SOURCE_ACQUISITION_TECHNICAL_FAILURE'; failure=f'{type(exc).__name__}: {str(exc)[:1000]}'
    out={'lab_id':base.LAB_ID,'phase':'EVENT_PARSE_V0_1_1_SHARD','classification':classification,'shard':shard,'shard_count':SHARD_COUNT,'assigned_codes':len(assigned),'resolved_codes':len(records),'records':records,'failure':failure,'safety':base.SAFETY}
    out_dir.mkdir(parents=True,exist_ok=True); (out_dir/f'event_parse_v011_shard_{shard}.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'classification':classification,'shard':shard,'assigned':len(assigned),'resolved':len(records),'failure':failure}))
    return 0 if classification=='EVENT_PARSE_SHARD_PASS' else 2


def cmd_aggregate(input_path:Path,shards_dir:Path,out_dir:Path)->int:
    source=json.loads(input_path.read_text()); expected=set(source['codes']); records=[]; receipts=[]
    for p in sorted(glob.glob(str(shards_dir/'**/event_parse_v011_shard_*.json'),recursive=True)):
      d=json.loads(Path(p).read_text()); receipts.append({k:d.get(k) for k in ('shard','classification','assigned_codes','resolved_codes','failure')})
      if d.get('classification')!='EVENT_PARSE_SHARD_PASS': raise SystemExit('non-pass shard encountered')
      records.extend(d.get('records',[]))
    codes=[r.get('code') for r in records]; missing=sorted(expected-set(codes)); dupes=sorted({c for c in codes if codes.count(c)>1})
    invalid=[r for r in records if r.get('direction')=='ADD' and not r.get('cross_margin_borrowable_assets')]
    if len(receipts)!=SHARD_COUNT or len(records)!=69 or missing or dupes or invalid:
      classification='PROVENANCE_FAILURE'; failure=f'coverage/ADD invariant failed shards={len(receipts)} records={len(records)} missing={len(missing)} dupes={len(dupes)} invalid_add={len(invalid)}'
    else:
      classification='EVENT_PARSE_PASS'; failure=None
    directions={k:sum(1 for r in records if r.get('direction')==k) for k in ('ADD','REMOVE','OTHER')}
    exclusions={}
    for r in records:
      if r.get('exclusion_reason'): exclusions[r['exclusion_reason']]=exclusions.get(r['exclusion_reason'],0)+1
    out={'lab_id':base.LAB_ID,'phase':'EVENT_PARSE_V0_1_1_CANONICAL','classification':classification,'failure':failure,'frozen_input_articles':69,'resolved_articles':len(records),'directions':directions,'add_asset_mentions':sum(len(r.get('cross_margin_borrowable_assets',[])) for r in records if r.get('direction')=='ADD'),'exclusion_counts':exclusions,'records':sorted(records,key=lambda r:(r.get('official_publish_ms') or 0,r.get('code'))),'shards':sorted(receipts,key=lambda x:x['shard']),'safety':base.SAFETY}
    out_dir.mkdir(parents=True,exist_ok=True); (out_dir/'BINANCE_MARGIN_BORROW_ACCESS_001_EVENT_PARSE_RECEIPT_V0_1_1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'classification':classification,'directions':directions,'add_asset_mentions':out['add_asset_mentions'],'exclusions':exclusions,'failure':failure}))
    return 0 if classification=='EVENT_PARSE_PASS' else 2


def main()->int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('shard'); s.add_argument('--input',type=Path,required=True); s.add_argument('--shard',type=int,required=True); s.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('aggregate'); a.add_argument('--input',type=Path,required=True); a.add_argument('--shards',type=Path,required=True); a.add_argument('--out',type=Path,required=True)
    x=ap.parse_args(); return cmd_shard(x.input,x.shard,x.out) if x.cmd=='shard' else cmd_aggregate(x.input,x.shards,x.out)
if __name__=='__main__': sys.exit(main())
