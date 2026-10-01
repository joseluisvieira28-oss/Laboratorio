import hashlib,json,re,sys,time,urllib.request
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path

P=Path(__file__).resolve()
ROOT=P.parents[2]
BASE=ROOT/"Dream-Account-OS-v2.3-PARTIAL/research/exchange_delisting_shock_001"
sys.path.insert(0,str(BASE))
import source_gate_v02 as v2
import source_gate_v03 as v3

AUTH=json.loads((P.parent/"SOURCE_CONTRACT_V0.1.json").read_text())
OUT=P.parent/"source_gate_receipt_v0.1.json"
FUT="https://data.binance.vision/data/futures/um/daily/klines"
START=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)

def title_symbols(title):
    m=re.search(r'^Binance Will Delist\s+(.+?)\s+on\s+20\d{2}-\d{2}-\d{2}\s*$',title,re.I)
    if not m:return []
    s=re.sub(r'\s+and\s+',',',m.group(1),flags=re.I)
    return [x.strip().upper() for x in s.split(',') if re.fullmatch(r'[A-Z0-9]{2,15}',x.strip().upper())]

def ceil_hour(dt):
    x=dt.replace(minute=0,second=0,microsecond=0)
    return x if x==dt else x+timedelta(hours=1)

def checksum(symbol,day):
    ds=day.isoformat()
    url=f"{FUT}/{symbol}/1m/{symbol}-1m-{ds}.zip.CHECKSUM"
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 BDPS/0.1'})
        with urllib.request.urlopen(req,timeout=20) as r:b=r.read().decode().split()
        dg=b[0].lower() if b else ''
        ok=len(dg)==64 and all(c in '0123456789abcdef' for c in dg)
        return {'ok':ok,'sha256':dg if ok else None,'url':url}
    except Exception as e:
        return {'ok':False,'sha256':None,'url':url,'error':type(e).__name__}

def main():
    assert AUTH["state"]=="FROZEN_PRE_SOURCE_OUTCOME_BLIND"
    candidates={}
    for page in range(1,201):
        _,j=v2.get_json(v2.LIST,{'type':1,'catalogId':161,'pageNo':page,'pageSize':50})
        arts=v2.find_articles(j)
        if not arts:break
        for a in arts:
            title=str(a.get('title',''))
            if title_symbols(title):
                candidates[str(a.get('code') or a.get('articleCode'))]=a

    raw=[];rejected=[];failures={}
    for code,a in sorted(candidates.items()):
        try:
            rawb,j=v2.get_json(v2.DETAIL,{'articleCode':code})
            d=v2.find_detail(j)
            pub=v2.parse_release(d.get('releaseDate') or a.get('releaseDate')) if d else None
            if pub is None or not START<=pub<=END:continue
            title=str(d.get('title') or a.get('title') or '')
            body=str(d.get('body') or '')
            txt=v2.textify(body)
            stop=v3.delist_ts(txt)
            pairs=v2.exact_pairs(txt)
            if stop is None or not pairs:
                rejected.append({'article_code':code,'reason':'MISSING_STOP_OR_PAIRS'})
                continue
            sides={z for p in pairs for z in p.split('/') if z}
            for sym in title_symbols(title):
                if sym not in sides:
                    rejected.append({'article_code':code,'symbol':sym,'reason':'TITLE_SYMBOL_NOT_IN_PAIRS'})
                    continue
                raw.append({'article_code':code,'title':title,
                    'publication_timestamp_utc':pub.isoformat().replace('+00:00','Z'),
                    'token_symbol':sym,
                    'all_pairs_cessation_timestamp_utc':stop.isoformat().replace('+00:00','Z'),
                    'exact_pairs_for_token':sorted(p for p in pairs if sym in p.split('/')),
                    'article_response_sha256':hashlib.sha256(rawb).hexdigest()})
        except Exception as e:
            failures[code]=type(e).__name__+":"+str(e)

    raw.sort(key=lambda x:(x['publication_timestamp_utc'],x['article_code'],x['token_symbol']))
    events=[];seen=set()
    for e in raw:
        if e['token_symbol'] in seen:continue
        seen.add(e['token_symbol']);events.append(e)

    yc=Counter(e['publication_timestamp_utc'][:4] for e in events)
    sm=AUTH['source_minimums']
    source_ok=len(events)>=sm['events'] and len(seen)>=sm['distinct_symbols'] and yc['2023']>=sm['year_2023'] and yc['2024']>=sm['year_2024']

    route=[]
    if source_ok:
        for e in events:
            pub=datetime.fromisoformat(e['publication_timestamp_utc'].replace('Z','+00:00'))
            ent=ceil_hour(pub+timedelta(hours=1)); ex=ent+timedelta(hours=24)
            if ex.year>=2025:
                route.append({'symbol':e['token_symbol'],'article_code':e['article_code'],'qualified':False,'reason':'PROTECTED_2025'})
                continue
            sym=e['token_symbol']+'USDT'
            checks=[checksum(sym,ent.date()),checksum(sym,ex.date()),checksum('BTCUSDT',ent.date()),checksum('BTCUSDT',ex.date())]
            route.append({'symbol':e['token_symbol'],'article_code':e['article_code'],
                'publication_timestamp_utc':e['publication_timestamp_utc'],
                'entry_boundary_utc':ent.isoformat().replace('+00:00','Z'),
                'exit_boundary_utc':ex.isoformat().replace('+00:00','Z'),
                'checks':checks,'qualified':all(x['ok'] for x in checks)})
    rq=[x for x in route if x.get('qualified')]
    lookup={(e['article_code'],e['token_symbol']):e for e in events}
    ry=Counter(lookup[(x['article_code'],x['symbol'])]['publication_timestamp_utc'][:4] for x in rq)
    rm=AUTH['execution_route']['route_minimums']
    route_ok=len(rq)>=rm['events'] and len({x['symbol'] for x in rq})>=rm['distinct_symbols'] and ry['2023']>=rm['year_2023'] and ry['2024']>=rm['year_2024']
    classification='SOURCE_DATA_PASS' if source_ok and route_ok else ('INSUFFICIENT_SOURCE_SAMPLE' if not source_ok else 'INSUFFICIENT_EXECUTION_ROUTE_SAMPLE')
    doc={'lab_id':AUTH['lab_id'],'classification':classification,'candidate_articles':len(candidates),
         'qualified_events':len(events),'distinct_symbols':len(seen),'year_counts':dict(yc),
         'route_qualified_events':len(rq),'route_distinct_symbols':len({x['symbol'] for x in rq}),
         'route_year_counts':dict(ry),'rejected_reason_counts':dict(Counter(x['reason'] for x in rejected)),
         'events':events,'route_checks':route,'failures':failures,'trading_authority':'NONE'}
    OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:doc[k] for k in ['classification','candidate_articles','qualified_events','distinct_symbols','year_counts','route_qualified_events','route_distinct_symbols','route_year_counts','rejected_reason_counts']},indent=2,sort_keys=True))

if __name__=='__main__':main()
