import hashlib, io, json, re, time, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
FREEZE=HERE.parent/'BNB_LAUNCHPOOL_DEMAND_001_V2_OOS_2025_FREEZE_V0.1.json'
SOURCE=HERE/'source_gate_v01'/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_SOURCE_GATE_V0.1.json'
OUTDIR=HERE/'market_source_v01'; RAW=OUTDIR/'raw'; OUT=OUTDIR/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_MARKET_SOURCE_V0.1.json'
BASE='https://data.binance.vision/data/spot/monthly/klines/BNBBTC/15m'
UA={'User-Agent':'Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-OOS-2025-MARKET-SOURCE/1.0'}

def get(url):
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=45) as r: return r.read()
        except Exception as e: last=e; time.sleep(0.5*(2**i))
    raise last

def parse_checksum(raw,name):
    p=raw.decode('utf-8','replace').strip().split(); dg=p[0].lower()
    if len(dg)!=64 or any(c not in '0123456789abcdef' for c in dg): raise RuntimeError('MALFORMED_CHECKSUM')
    if len(p)>1 and p[-1].lstrip('*')!=name: raise RuntimeError('CHECKSUM_FILENAME_MISMATCH')
    return dg

def parse_epoch(b):
    s=b.decode('ascii','strict').strip()
    if not re.fullmatch(r'\d{10,18}',s): return None
    x=int(s); sec=x/1_000_000.0 if x>10**14 else x/1_000.0 if x>10**11 else float(x)
    return int(round(sec))
def iso(sec): return datetime.fromtimestamp(sec,tz=timezone.utc).isoformat().replace('+00:00','Z')
def ceil_next_15m(dt): return ((int(dt.timestamp())//900)+1)*900

def selected_paths(events):
    ev=[]
    for e in events:
        dt=datetime.fromisoformat(e['published_timestamp_utc'].replace('Z','+00:00')).astimezone(timezone.utc)
        ev.append({'n':e['n'],'symbol':e['symbol'],'dt':dt,'published':e['published_timestamp_utc']})
    ev.sort(key=lambda x:x['dt']); clusters=[]
    for e in ev:
        if not clusters or (e['dt']-clusters[-1][-1]['dt']).total_seconds()>3600: clusters.append([e])
        else: clusters[-1].append(e)
    candidates=[]
    for c in clusters:
        ent=ceil_next_15m(c[0]['dt']); ex=ent+86400
        candidates.append({'project_numbers':[x['n'] for x in c],'symbols':[x['symbol'] for x in c],'signal_time_utc':c[0]['published'],'entry_epoch':ent,'exit_epoch':ex,'entry_time_utc':iso(ent),'exit_time_utc':iso(ex)})
    selected=[]; suppressed=[]; right_edge=[]; active_exit=None
    cutoff=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())
    for c in candidates:
        if c['exit_epoch']>=cutoff: right_edge.append(c); continue
        if active_exit is not None and c['entry_epoch']<active_exit: suppressed.append(c); continue
        selected.append(c); active_exit=c['exit_epoch']
    return clusters,candidates,selected,suppressed,right_edge

def main():
    OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
    f=json.loads(FREEZE.read_text()); s=json.loads(SOURCE.read_text())
    assert f['status']=='FROZEN_PRE_2025_SOURCE_AND_MARKET_OUTCOME_ACCESS'; assert s['classification']=='SOURCE_DATA_PASS'; assert s['clean_events']==8
    months=[f'2025-{m:02d}' for m in range(1,13)]; manifest=[]; all_ts=[]; failures=[]
    for ym in months:
        name=f'BNBBTC-15m-{ym}.zip'; url=f'{BASE}/{name}'
        try:
            cb=get(url+'.CHECKSUM'); official=parse_checksum(cb,name); zb=get(url); calc=hashlib.sha256(zb).hexdigest()
            if calc!=official: raise RuntimeError('SHA256_MISMATCH')
            (RAW/name).write_bytes(zb); (RAW/(name+'.CHECKSUM')).write_bytes(cb)
            with zipfile.ZipFile(io.BytesIO(zb)) as z:
                bad=z.testzip()
                if bad is not None: raise RuntimeError(f'ZIP_CRC_FAILURE:{bad}')
                members=[n for n in z.namelist() if not n.endswith('/')]
                if len(members)!=1: raise RuntimeError('ZIP_MEMBER_COUNT_NOT_ONE')
                ts=[]
                with z.open(members[0]) as fh:
                    for line in fh:
                        if not line.strip(): continue
                        sec=parse_epoch(line.split(b',',1)[0])
                        if sec is not None: ts.append(sec)
                if not ts: raise RuntimeError('NO_TIMESTAMPS')
                if len(ts)!=len(set(ts)): raise RuntimeError('DUPLICATE_TIMESTAMP_WITHIN_MONTH')
                all_ts.extend(ts); manifest.append({'month':ym,'archive':name,'sha256':calc,'timestamp_rows':len(ts),'first_timestamp_utc':iso(min(ts)),'last_timestamp_utc':iso(max(ts))})
        except Exception as ex: failures.append({'month':ym,'error':f'{type(ex).__name__}:{ex}'})
    clusters,candidates,selected,suppressed,right_edge=selected_paths(s['canonical_events']); aset=set(all_ts)
    global_dupes=len(all_ts)-len(aset); path_fail=[]
    for x in selected:
        req=list(range(x['entry_epoch'],x['exit_epoch']+1,900)); miss=[t for t in req if t not in aset]
        if miss: path_fail.append({'project_numbers':x['project_numbers'],'missing_count':len(miss),'first_missing_utc':iso(miss[0])})
    ok=(len(manifest)==12 and not failures and global_dupes==0 and not path_fail and len(selected)>=8)
    basis='\n'.join(f"{x['month']}|{x['sha256']}|{x['timestamp_rows']}|{x['first_timestamp_utc']}|{x['last_timestamp_utc']}" for x in manifest).encode()
    strip=lambda x:{k:v for k,v in x.items() if not k.endswith('_epoch')}
    receipt={
      'protocol_id':f['protocol_id'],'classification':'MARKET_SOURCE_DATA_PASS' if ok else 'SOURCE_OR_EXECUTION_FAILURE',
      'archive_count':len(manifest),'expected_archive_count':12,'archive_manifest_sha256':hashlib.sha256(basis).hexdigest(),'archive_manifest':manifest,
      'technical_failures':failures,'global_duplicate_timestamp_count':global_dupes,'event_clusters':len(clusters),'candidate_clusters':len(candidates),
      'selected_trade_paths':len(selected),'suppressed_trade_paths':len(suppressed),'right_edge_unresolved':len(right_edge),
      'selected':[strip(x) for x in selected],'suppressed':[strip(x) for x in suppressed],'right_edge':[strip(x) for x in right_edge],
      'execution_path_failures':path_fail,'market_price_values_opened':False,'open_parsed':False,'high_low_close_volume_parsed':False,'returns_computed':False,
      'access_2026_market':False,'live_trading_authorized':False
    }
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:receipt[k] for k in ['classification','archive_count','event_clusters','selected_trade_paths','suppressed_trade_paths','right_edge_unresolved','archive_manifest_sha256']},indent=2))
if __name__=='__main__': main()
