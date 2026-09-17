#!/usr/bin/env python3
"""Prior Binance Spot proof for BINANCE-MARGIN-BORROW-ACCESS-001.
Source-only / outcome-blind. Reads parser receipts and requests only Binance Vision
.CHECKSUM metadata; never downloads market-data ZIPs or parses price values.
"""
from __future__ import annotations
import argparse, glob, hashlib, json, re, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import requests

LAB_ID='BINANCE-MARGIN-BORROW-ACCESS-001'
SHARD_COUNT=8
QUOTES=['USDT','BTC','BNB','BUSD','FDUSD','USDC','TUSD','ETH','EUR','TRY','BRL','GBP','AUD','BIDR','DAI','PAX','USDP','IDRT','NGN','RUB','UAH','BKRW','BVND','ZAR']
BASE='https://data.binance.vision/data/spot/daily/klines'
EXPECTED={'ADD':54,'REMOVE':6,'OTHER':9}
SAFETY={
 'market_data_zip_downloaded':False,'market_data_values_opened':False,'price_data_opened':False,
 'ohlcv_opened':False,'returns_opened':False,'basis_opened':False,'borrow_rate_opened':False,
 'borrow_inventory_opened':False,'authenticated_exchange_api_used':False,'account_data_opened':False,
 'pnl_opened':False,'win_rate_opened':False,'pf_opened':False,'drawdown_opened':False,
 'protected_2025_2026_path_requested':False,'live_trading':False,'exchange_mutation':False,
 'checksum_metadata_only':True,
}
SESSION=requests.Session(); SESSION.headers.update({'User-Agent':'Crypto-Lab-source-provenance/1.0'})
CHECKSUM_RE=re.compile(r'^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$')

def stable_sha(obj:Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def load_parser_records(root:Path)->list[dict[str,Any]]:
    files=sorted(glob.glob(str(root/'**/event_parse_v011_shard_*.json'),recursive=True))
    if len(files)!=4: raise RuntimeError(f'expected 4 parser shard receipts, found {len(files)}')
    records=[]; shards=set()
    for p in files:
        d=json.loads(Path(p).read_text())
        if d.get('classification')!='EVENT_PARSE_SHARD_PASS': raise RuntimeError(f'non-pass parser shard {p}')
        shards.add(int(d['shard'])); records.extend(d.get('records',[]))
    if shards!={0,1,2,3} or len(records)!=69 or len({r['code'] for r in records})!=69:
        raise RuntimeError('parser coverage invariant failed')
    directions={k:sum(r.get('direction')==k for r in records) for k in ('ADD','REMOVE','OTHER')}
    if directions!=EXPECTED: raise RuntimeError(f'parser direction invariant failed: {directions}')
    if sum(len(r.get('cross_margin_borrowable_assets',[])) for r in records if r.get('direction')=='ADD')!=100:
        raise RuntimeError('parser asset-mention invariant failed')
    return records

def cmd_manifest(parser_dir:Path,out_dir:Path)->int:
    try:
        records=load_parser_records(parser_dir); rows=[]
        for r in sorted(records,key=lambda x:(x.get('official_publish_ms',0),x['code'])):
            if r.get('direction')!='ADD': continue
            for asset in r.get('cross_margin_borrowable_assets',[]):
                row={
                  'candidate_id':f"{r['code']}:{asset}",'article_code':r['code'],'asset':asset,
                  'event_information_ms':int(r['event_information_ms']),'effective_ms':r.get('effective_ms'),
                  'body_sha256':r.get('body_sha256'),'same_announcement_spot_confound':bool(r.get('confounds',{}).get('spot_listing_or_start')),
                  'official_title':r.get('official_title'),
                }
                rows.append(row)
        if len(rows)!=100 or len({x['candidate_id'] for x in rows})!=100: raise RuntimeError(f'asset-event invariant failed rows={len(rows)}')
        conf=sum(x['same_announcement_spot_confound'] for x in rows)
        if conf!=4: raise RuntimeError(f'expected 4 same-announcement Spot-confounded asset-events, found {conf}')
        core={'lab_id':LAB_ID,'phase':'PRIOR_SPOT_V0_1_MANIFEST','shard_count':SHARD_COUNT,'quote_order':QUOTES,'rows':rows}
        digest=stable_sha(core)
        out={**core,'classification':'PRIOR_SPOT_MANIFEST_PASS','manifest_sha256':digest,'asset_event_rows':len(rows),'access_confound_rows':conf,'rows_requiring_archive_proof':len(rows)-conf,'safety':SAFETY}
        out_dir.mkdir(parents=True,exist_ok=True); (out_dir/'prior_spot_manifest.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'classification':out['classification'],'rows':len(rows),'access_confound':conf,'to_probe':len(rows)-conf,'manifest_sha256':digest}))
        return 0
    except Exception as exc:
        out_dir.mkdir(parents=True,exist_ok=True); f={'lab_id':LAB_ID,'phase':'PRIOR_SPOT_V0_1_MANIFEST','classification':'PROVENANCE_FAILURE','failure':f'{type(exc).__name__}: {str(exc)[:1000]}','safety':SAFETY}; (out_dir/'prior_spot_manifest_failure.json').write_text(json.dumps(f,indent=2,sort_keys=True)+'\n'); print(json.dumps(f)); return 2

def request_checksum(pair:str,date_str:str,attempts:int=4)->dict[str,Any]:
    filename=f'{pair}-1d-{date_str}.zip'; url=f'{BASE}/{pair}/1d/{filename}.CHECKSUM'; last=None
    for attempt in range(attempts):
        try:
            r=SESSION.get(url,timeout=30,allow_redirects=True)
            status=r.status_code; raw=r.content
            if status==404: return {'http_status':404,'url':url,'valid':False,'response_sha256':hashlib.sha256(raw).hexdigest()}
            if status==429 or 500<=status<600: raise RuntimeError(f'HTTP {status}')
            r.raise_for_status(); text=raw.decode('utf-8','replace').strip(); m=CHECKSUM_RE.match(text)
            valid=bool(m and m.group(2).strip()==filename)
            return {'http_status':status,'url':url,'valid':valid,'archive_sha256':m.group(1).lower() if m else None,'checksum_filename':m.group(2).strip() if m else None,'response_sha256':hashlib.sha256(raw).hexdigest()}
        except Exception as exc:
            last=exc
            if attempt+1<attempts: time.sleep(1.0*(2**attempt))
    raise RuntimeError(str(last))

def cmd_shard(manifest_path:Path,shard:int,out_dir:Path)->int:
    m=json.loads(manifest_path.read_text()); rows=m['rows']; digest=m['manifest_sha256']; assigned=[r for i,r in enumerate(rows) if i%SHARD_COUNT==shard]
    results=[]; failure=None; classification='PRIOR_SPOT_SHARD_PASS'
    try:
        for row in assigned:
            if row['same_announcement_spot_confound']:
                results.append({**row,'status':'ACCESS_CONFOUND','proof':None}); continue
            t=datetime.fromtimestamp(row['event_information_ms']/1000,tz=timezone.utc); d=(t.date()-timedelta(days=1)); date_str=d.isoformat()
            if d.year>=2025: raise RuntimeError('protected-period path construction blocked')
            attempts=[]; proof=None
            for quote in QUOTES:
                if row['asset']==quote: continue
                pair=f"{row['asset']}{quote}"; q=request_checksum(pair,date_str); attempts.append({'pair':pair,'http_status':q['http_status'],'valid':q['valid']})
                if q['valid']:
                    proof={'pair':pair,'proof_date':date_str,**q}; break
                time.sleep(0.08)
            status='PRIOR_SPOT_ARCHIVE_PASS' if proof else 'PRIOR_SPOT_PRIMARY_UNRESOLVED'
            results.append({**row,'status':status,'proof':proof,'attempts':attempts})
    except Exception as exc:
        classification='SOURCE_ACQUISITION_TECHNICAL_FAILURE'; failure=f'{type(exc).__name__}: {str(exc)[:1000]}'
    out={'lab_id':LAB_ID,'phase':'PRIOR_SPOT_V0_1_SHARD','classification':classification,'manifest_sha256':digest,'shard':shard,'assigned_rows':len(assigned),'resolved_rows':len(results),'results':results,'failure':failure,'safety':SAFETY}
    out_dir.mkdir(parents=True,exist_ok=True); (out_dir/f'prior_spot_shard_{shard}.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    counts={s:sum(x.get('status')==s for x in results) for s in ('ACCESS_CONFOUND','PRIOR_SPOT_ARCHIVE_PASS','PRIOR_SPOT_PRIMARY_UNRESOLVED')}; print(json.dumps({'classification':classification,'shard':shard,'assigned':len(assigned),'resolved':len(results),'counts':counts,'failure':failure}))
    return 0 if classification=='PRIOR_SPOT_SHARD_PASS' else 2

def cmd_aggregate(manifest_path:Path,shards_dir:Path,out_dir:Path)->int:
    m=json.loads(manifest_path.read_text()); expected={r['candidate_id'] for r in m['rows']}; digest=m['manifest_sha256']; results=[]; receipts=[]
    try:
        files=sorted(glob.glob(str(shards_dir/'**/prior_spot_shard_*.json'),recursive=True))
        if len(files)!=SHARD_COUNT: raise RuntimeError(f'expected {SHARD_COUNT} shards, got {len(files)}')
        for p in files:
            d=json.loads(Path(p).read_text()); receipts.append({k:d.get(k) for k in ('shard','classification','assigned_rows','resolved_rows','failure')})
            if d.get('classification')!='PRIOR_SPOT_SHARD_PASS' or d.get('manifest_sha256')!=digest: raise RuntimeError('non-pass shard or manifest digest mismatch')
            results.extend(d['results'])
        ids=[r['candidate_id'] for r in results]; missing=expected-set(ids); dupes={x for x in ids if ids.count(x)>1}
        if missing or dupes or len(results)!=len(expected): raise RuntimeError(f'coverage fail missing={len(missing)} dupes={len(dupes)} rows={len(results)}')
        counts={s:sum(r['status']==s for r in results) for s in ('ACCESS_CONFOUND','PRIOR_SPOT_ARCHIVE_PASS','PRIOR_SPOT_PRIMARY_UNRESOLVED')}
        tech=sum(r.get('status')=='SOURCE_ACQUISITION_TECHNICAL_FAILURE' for r in results)
        years=sorted({datetime.fromtimestamp(r['event_information_ms']/1000,tz=timezone.utc).year for r in results if r['status']=='PRIOR_SPOT_ARCHIVE_PASS'})
        classification='PRIOR_SPOT_PRIMARY_PASS' if counts['PRIOR_SPOT_PRIMARY_UNRESOLVED']==0 and tech==0 else 'PRIOR_SPOT_FALLBACK_REQUIRED'
        failure=None
    except Exception as exc:
        classification='PROVENANCE_FAILURE'; failure=f'{type(exc).__name__}: {str(exc)[:1000]}'; counts={}; years=[]
    out={'lab_id':LAB_ID,'phase':'PRIOR_SPOT_V0_1_CANONICAL','classification':classification,'manifest_sha256':digest,'counts':counts,'proved_years':years,'results':sorted(results,key=lambda x:x.get('candidate_id','')),'shards':receipts,'failure':failure,'safety':SAFETY}
    out_dir.mkdir(parents=True,exist_ok=True); (out_dir/'BINANCE_MARGIN_BORROW_ACCESS_001_PRIOR_SPOT_RECEIPT_V0_1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'classification':classification,'counts':counts,'proved_years':years,'failure':failure}))
    return 0 if classification in {'PRIOR_SPOT_PRIMARY_PASS','PRIOR_SPOT_FALLBACK_REQUIRED'} else 2

def main()->int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('manifest'); a.add_argument('--parser-dir',type=Path,required=True); a.add_argument('--out',type=Path,required=True)
    s=sub.add_parser('shard'); s.add_argument('--manifest',type=Path,required=True); s.add_argument('--shard',type=int,required=True); s.add_argument('--out',type=Path,required=True)
    g=sub.add_parser('aggregate'); g.add_argument('--manifest',type=Path,required=True); g.add_argument('--shards',type=Path,required=True); g.add_argument('--out',type=Path,required=True)
    x=ap.parse_args()
    if x.cmd=='manifest': return cmd_manifest(x.parser_dir,x.out)
    if x.cmd=='shard': return cmd_shard(x.manifest,x.shard,x.out)
    return cmd_aggregate(x.manifest,x.shards,x.out)
if __name__=='__main__': sys.exit(main())
