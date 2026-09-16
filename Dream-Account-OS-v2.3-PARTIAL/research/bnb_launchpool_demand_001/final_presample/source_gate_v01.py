import hashlib, html, json, re, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FREEZE=ROOT/'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_HOLDOUT_FREEZE_V0.1.json'
OUTDIR=HERE/'source_gate_v01'; RAW=OUTDIR/'raw'; OUT=OUTDIR/'BNB_LAUNCHPOOL_DEMAND_001_FINAL_PRESAMPLE_SOURCE_GATE_V0.1.json'
LIST='https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo={}&pageSize=100'
DETAIL='https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode={}'
UA={'User-Agent':'Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-FINAL-HOLDOUT/1.0','Accept':'application/json,text/plain,*/*'}
HEX=re.compile(r'^[0-9a-fA-F]{32}$')
PROJ=re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)\s+project\s+on\s+Binance\s+Launchpool\b',re.I)

def get(url, tries=4):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=40) as r:return r.read()
        except Exception as e:
            last=e; time.sleep(.5*(2**i))
    raise last

def walk_dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk_dicts(v)
    elif isinstance(x,list):
        for v in x: yield from walk_dicts(v)

def flatten(x):
    vals=[]
    if isinstance(x,dict):
        for v in x.values(): vals.append(flatten(v))
    elif isinstance(x,list):
        for v in x: vals.append(flatten(v))
    elif isinstance(x,str): vals.append(x)
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',' '.join(vals)))).strip()

def first_hex(d):
    for k in ('articleCode','code','id'):
        v=d.get(k)
        if isinstance(v,str) and HEX.fullmatch(v): return v.lower()
    for v in d.values():
        if isinstance(v,str) and HEX.fullmatch(v): return v.lower()
    return None

def titleish(d):
    for k in ('title','articleTitle','name'):
        v=d.get(k)
        if isinstance(v,str) and v.strip(): return v.strip()
    return ''

def pub_ms(d):
    for k in ('releaseDate','publishDate','publishedAt','publishTime'):
        v=d.get(k)
        if isinstance(v,(int,float)): return int(v)
        if isinstance(v,str) and v.isdigit(): return int(v)
    return None

def iso_from_ms(v):
    if v is None:return None
    x=float(v)
    if x>1e14:x/=1e6
    elif x>1e11:x/=1e3
    return datetime.fromtimestamp(x,tz=timezone.utc).isoformat().replace('+00:00','Z')

def main():
    f=json.loads(FREEZE.read_text())
    assert f['status']=='FROZEN_BEFORE_PRESAMPLE_SOURCE_ENUMERATION_OR_MARKET_OUTCOME_ACCESS'
    OUTDIR.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
    candidates={}; pages=[]; earliest=None
    for p in range(1,121):
        body=get(LIST.format(p)); obj=json.loads(body.decode())
        found=0
        for d in walk_dicts(obj):
            t=titleish(d); code=first_hex(d)
            if not code or 'launchpool' not in t.lower(): continue
            found+=1
            ms=pub_ms(d); dt=iso_from_ms(ms)
            candidates.setdefault(code,{'article_code':code,'title':t,'feed_published_utc':dt})
            if dt and (earliest is None or dt<earliest): earliest=dt
        pages.append({'page':p,'launchpool_candidates':found,'sha256':hashlib.sha256(body).hexdigest(),'earliest_seen_utc':earliest})
        if p>=20 and found==0 and earliest and earliest<'2020-08-01T00:00:00Z': break
    recovered={}; detail_fail=[]
    for code,c in sorted(candidates.items()):
        try:
            b=get(DETAIL.format(code)); o=json.loads(b.decode()); txt=flatten(o); m=PROJ.search(txt)
            if not m: continue
            n=int(m.group(1))
            if not 1<=n<=30: continue
            low=txt.lower()
            bnb=bool(re.search(r'\bbnb\b',low)); stake=any(w in low for w in ('stake','staking','lock','locking','farm','farming'))
            pdt=None
            for d in walk_dicts(o):
                for k in ('publishDate','releaseDate'):
                    if k in d and isinstance(d[k],(int,float,str)):
                        try:pdt=iso_from_ms(int(d[k])); break
                        except Exception: pass
                if pdt: break
            raw=RAW/f'{n:02d}_{code}.json'; raw.write_bytes(b)
            rec={'n':n,'article_code':code,'title':c['title'],'official_support_url':f'https://www.binance.com/en/support/announcement/detail/{code}','published_timestamp_utc':pdt or c['feed_published_utc'],'bnb_pool_present':bnb,'staking_or_locking_present':stake,'raw_sha256':hashlib.sha256(b).hexdigest()}
            if n in recovered: detail_fail.append({'n':n,'error':'DUPLICATE_PROJECT_NUMBER','codes':[recovered[n]['article_code'],code]})
            else: recovered[n]=rec
        except Exception as e: detail_fail.append({'article_code':code,'error':f'{type(e).__name__}:{e}'})
    missing=[n for n in range(1,31) if n not in recovered]
    ineligible=[n for n,r in recovered.items() if not(r['bnb_pool_present'] and r['staking_or_locking_present'])]
    ordered=[recovered[n] for n in sorted(recovered)]
    manifest='\n'.join(f"{r['n']}|{r['article_code']}|{r['published_timestamp_utc']}|{r['raw_sha256']}|{int(r['bnb_pool_present'])}" for r in ordered).encode()
    classification='SOURCE_DATA_PASS' if not missing and not ineligible and not detail_fail else 'SOURCE_DATA_FAILURE'
    out={'protocol_id':f['protocol_id'],'classification':classification,'recovered_count':len(ordered),'missing_project_numbers':missing,'ineligible_project_numbers':ineligible,'detail_failures':detail_fail,'canonical_event_manifest_sha256':hashlib.sha256(manifest).hexdigest(),'canonical_events':ordered,'feed_pages':pages,'market_prices_opened':False,'returns_computed':False,'pnl_computed':False,'new_2025_market_access':False,'access_2026_market':False,'live_trading_authorized':False}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('classification','recovered_count','missing_project_numbers','ineligible_project_numbers','canonical_event_manifest_sha256')},indent=2))
if __name__=='__main__': main()
