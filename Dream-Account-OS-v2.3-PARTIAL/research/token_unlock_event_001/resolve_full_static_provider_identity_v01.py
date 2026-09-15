import argparse, hashlib, json, math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

LAB='TOKEN-UNLOCK-EVENT-001'; MVE='TUE-CLIFF-ADV30-001'

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def iso_dt(s): return datetime.fromisoformat(str(s).replace('Z','+00:00')).astimezone(timezone.utc)
def canonical_hash(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--provider-2023',required=True); ap.add_argument('--provider-2024',required=True)
    ap.add_argument('--identity-map',required=True); ap.add_argument('--out',required=True)
    args=ap.parse_args(); a=load(args.provider_2023); b=load(args.provider_2024); ident=load(args.identity_map)
    assert ident['status']=='FROZEN_PRE_IDENTITY_RESOLUTION'
    auth=ident['source_authority']
    if sha256_file(args.provider_2023)!=auth['full_static_2023_sha256']: raise RuntimeError('2023 full-static hash mismatch')
    if sha256_file(args.provider_2024)!=auth['full_static_2024_sha256']: raise RuntimeError('2024 full-static hash mismatch')
    mapping=ident['provider_adapter_to_symbol']; quarantine=ident['quarantined_adapters']
    included_files=set()
    for d in (a,b):
        r=d['receipt']; g=r['guards']
        assert r['identity_resolution_complete'] is False and r['binance_route_checked'] is False
        assert g['market_data_accessed'] is False and g['price_data_accessed'] is False
        assert g['returns_computed'] is False and g['pnl_computed'] is False
        for s in d['statuses']:
            if s.get('disposition')=='INCLUDED_RAW_IDENTITY_PENDING': included_files.add(s['file'])
    unresolved=sorted(included_files - set(mapping) - set(quarantine))
    extra=sorted((set(mapping)|set(quarantine))-included_files)
    if unresolved: raise RuntimeError(f'unresolved included adapters: {unresolved}')
    if extra: raise RuntimeError(f'identity freeze contains non-included adapters: {extra}')

    rows=[]; excluded=[]
    for d in (a,b):
        snap=d['receipt']['snapshot']
        for e in d['events']:
            f=e.get('file') or e.get('source_file')
            if f in quarantine:
                excluded.append({'reason':'IDENTITY_AMBIGUOUS_FAIL_CLOSED','source_file':f,'snapshot':snap,'scheduled_at_utc':e.get('scheduled_at_utc')})
                continue
            sym=mapping[f]
            if f=='liquity.ts' and str(e.get('known_at_utc','')).startswith('2023-'):
                excluded.append({'reason':'LIQUITY_2023_LUSD_LQTY_IDENTITY_CONFLICT','source_file':f,'symbol':sym,'snapshot':snap,'scheduled_at_utc':e.get('scheduled_at_utc')})
                continue
            amount=float(e.get('scheduled_unlock_tokens',0))
            if not math.isfinite(amount) or amount<=0: raise RuntimeError('non-positive amount survived full-static stage')
            dt=iso_dt(e['scheduled_at_utc'])
            if dt.year not in (2023,2024): raise RuntimeError('date firewall breach')
            row=dict(e); row['symbol']=sym; row['identity_status']='RESOLVED_PRE_ROUTE'; row['source_file']=f
            rows.append(row)

    by_key=defaultdict(list)
    for r in rows: by_key[(r['symbol'],r['scheduled_at_utc'])].append(r)
    manifest=[]; conflicts=[]; corroborated=[]
    for key, group in sorted(by_key.items()):
        amounts={float(x['scheduled_unlock_tokens']) for x in group}
        if len(amounts)>1:
            conflicts.append({'symbol':key[0],'scheduled_at_utc':key[1],'amounts':sorted(amounts),'rows':[{'snapshot':x['snapshot'],'known_at_utc':x['known_at_utc'],'source_file':x['source_file']} for x in group]})
            continue
        group=sorted(group,key=lambda x: iso_dt(x['known_at_utc']))
        keep=dict(group[0]);
        if len(group)>1:
            keep['corroborated_by']=[{'snapshot':x['snapshot'],'known_at_utc':x['known_at_utc'],'source_commit':x['source_commit'],'adapter_sha256':x.get('adapter_sha256')} for x in group[1:]]
            corroborated.append({'symbol':key[0],'scheduled_at_utc':key[1],'copies':len(group)})
        else: keep['corroborated_by']=[]
        manifest.append(keep)
    for c in conflicts:
        excluded.append({'reason':'SOURCE_CONFLICT','symbol':c['symbol'],'scheduled_at_utc':c['scheduled_at_utc'],'details':c})

    symbols=sorted({x['symbol'] for x in manifest}); years=sorted({iso_dt(x['scheduled_at_utc']).year for x in manifest})
    receipt={
      'lab_id':LAB,'mve_id':MVE,'mode':'SOURCE_ONLY_FULL_STATIC_IDENTITY_RESOLUTION_V01',
      'identity_resolution_complete':True,'binance_route_checked':False,
      'included_adapter_count':len(included_files),'mapped_adapter_count':len(mapping),'quarantined_adapter_count':len(quarantine),
      'raw_event_count':len(a['events'])+len(b['events']),'resolved_pre_dedup_event_count':len(rows),
      'frozen_manifest_event_count':len(manifest),'frozen_manifest_distinct_tokens':len(symbols),'frozen_manifest_tokens':symbols,
      'frozen_manifest_years':years,'cross_snapshot_conflict_count':len(conflicts),'corroborated_event_count':len(corroborated),
      'excluded_event_count':len(excluded),'identity_map_sha256':sha256_file(args.identity_map),
      'full_static_2023_sha256':sha256_file(args.provider_2023),'full_static_2024_sha256':sha256_file(args.provider_2024),
      'manifest_fingerprint_sha256':canonical_hash(manifest),
      'guards':{'binance_route_checked':False,'market_data_accessed':False,'price_data_accessed':False,'returns_computed':False,'pnl_computed':False,'profit_factor_computed':False,'year_2025_opened':False,'year_2026_opened':False,'live_trading':False,'exchange_mutation':False},
      'next_action':'Freeze this exact resolved provider manifest by SHA256/fingerprint before any Binance Data Vision route query.'
    }
    out={'receipt':receipt,'events':manifest,'excluded_events':excluded,'conflicts':conflicts,'corroborated_events':corroborated}
    Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=='__main__': main()
