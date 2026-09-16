import hashlib, html, json, re, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
FREEZE=HERE.parent/'BNB_LAUNCHPOOL_DEMAND_001_V2_OOS_2025_FREEZE_V0.1.json'
SEED=HERE/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_SOURCE_SEED_V0.1.json'
OUTDIR=HERE/'source_gate_v01'; RAW=OUTDIR/'raw'; OUT=OUTDIR/'BNB_LAUNCHPOOL_DEMAND_001_OOS_2025_SOURCE_GATE_V0.1.json'
ROUTE='https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode={}'
UA={'User-Agent':'Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-OOS-2025-SOURCE/1.0','Accept':'application/json,text/plain,*/*'}

def utc_iso(dt): return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def parse_ts(v):
    if v is None or isinstance(v,bool): return None
    if isinstance(v,(int,float)):
        x=float(v)
        if x>1e14: x/=1_000_000.0
        elif x>1e11: x/=1_000.0
        try: return utc_iso(datetime.fromtimestamp(x,tz=timezone.utc))
        except Exception: return None
    s=str(v).strip()
    if not s: return None
    if re.fullmatch(r'\d{10,18}',s): return parse_ts(int(s))
    try:
        dt=datetime.fromisoformat(s.replace('Z','+00:00'))
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return utc_iso(dt)
    except Exception: return None

def walk(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items():
            p=f'{path}.{k}' if path else str(k); yield p,v; yield from walk(v,p)
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            p=f'{path}[{i}]'; yield p,v; yield from walk(v,p)

def flatten(obj):
    s='\n'.join(v for _,v in walk(obj) if isinstance(v,str))
    s=html.unescape(re.sub(r'<[^>]+>',' ',s))
    return re.sub(r'\s+',' ',s).strip()

def pub_ts(obj):
    keys=['releasedate','release_time','releasetime','publishdate','publish_date','publishtime','publish_time','publishedat','published_at','publicationdate']
    found=[]
    for p,v in walk(obj):
        k=p.rsplit('.',1)[-1].lower().split('[')[0]
        if k in keys:
            ts=parse_ts(v)
            if ts: found.append((keys.index(k),p,ts))
    if not found: return None,None
    found.sort(key=lambda x:(x[0],x[1])); return found[0][2],found[0][1]

def get(url):
    last=None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=35) as r: return r.status,r.read()
        except Exception as e: last=e; time.sleep(0.5*(2**i))
    raise last

def ordinal(n):
    if 10<=n%100<=20: suf='th'
    else: suf={1:'st',2:'nd',3:'rd'}.get(n%10,'th')
    return f'{n}{suf}'

def main():
    OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
    f=json.loads(FREEZE.read_text()); s=json.loads(SEED.read_text()); events=s['events']
    assert f['status']=='FROZEN_PRE_2025_SOURCE_AND_MARKET_OUTCOME_ACCESS'
    assert f['protected_period']['2026_market_outcomes_forbidden'] is True
    assert [e['n'] for e in events]==list(range(64,72)) and len(events)==8
    rows=[]; canonical=[]; failures=[]
    for e in events:
        n=int(e['n']); symbol=e['symbol'].upper(); code=e['article_code'].lower(); url=ROUTE.format(code)
        try:
            status,body=get(url); dg=hashlib.sha256(body).hexdigest(); (RAW/f'{n}_{symbol}_{code}.json').write_bytes(body)
            if status!=200 or not body: raise RuntimeError(f'HTTP_{status}')
            obj=json.loads(body.decode('utf-8')); text=flatten(obj); tl=text.lower(); ts,path=pub_ts(obj)
            checks={
                'calendar_2025': bool(ts and ts.startswith('2025-')),
                'launchpool': 'launchpool' in tl,
                'bnb': re.search(r'\bbnb\b',tl) is not None,
                'staking_or_locking': any(x in tl for x in ('stake','staking','lock','locking','farm','farming')),
                'symbol': re.search(rf'(?<![A-Z0-9]){re.escape(symbol)}(?![A-Z0-9])',text,re.I) is not None,
                'project_number': (f'#{n}' in tl) or (ordinal(n).lower() in tl),
            }
            row={'n':n,'symbol':symbol,'article_code':code,'official_support_url':e['url'],'published_timestamp_utc':ts,'publication_field_path':path,'raw_response_sha256':dg,'checks':checks}
            if all(checks.values()):
                row['status']='CLEAN'; canonical.append({k:row[k] for k in ['n','symbol','article_code','official_support_url','published_timestamp_utc','raw_response_sha256']})
            else:
                row['status']='SOURCE_INTEGRITY_FAILURE'; failures.append({'n':n,'checks':checks})
            rows.append(row)
        except Exception as ex:
            failures.append({'n':n,'error':f'{type(ex).__name__}:{ex}'}); rows.append({'n':n,'symbol':symbol,'article_code':code,'status':'SOURCE_ACCESS_FAILURE'})
    canonical.sort(key=lambda x:x['published_timestamp_utc'])
    basis='\n'.join(f"{x['n']}|{x['symbol']}|{x['article_code']}|{x['published_timestamp_utc']}|{x['raw_response_sha256']}" for x in canonical).encode()
    classification='SOURCE_DATA_PASS' if len(canonical)==8 and not failures else 'SOURCE_OR_INTEGRITY_FAILURE'
    receipt={
      'protocol_id':f['protocol_id'],'classification':classification,'expected_events':8,'clean_events':len(canonical),'failures':failures,
      'canonical_events':canonical,'canonical_event_manifest_sha256':hashlib.sha256(basis).hexdigest(),
      'events':rows,'market_prices_opened':False,'returns_computed':False,'pnl_computed':False,'access_2026_market':False,
      'promotion_to_market_source_audit_authorized':classification=='SOURCE_DATA_PASS','live_trading_authorized':False
    }
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:receipt[k] for k in ['classification','clean_events','canonical_event_manifest_sha256']},indent=2))
if __name__=='__main__': main()
