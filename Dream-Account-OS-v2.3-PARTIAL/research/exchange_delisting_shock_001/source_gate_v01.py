import hashlib, html, json, re, time, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTDIR = HERE / 'source_evidence'
OUT = OUTDIR / 'EDS_SOURCE_DATA_GATE_V01.json'
LIST = 'https://www.binance.com/bapi/composite/v1/public/cms/article/list/query'
DETAIL = 'https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query'
DV = 'https://data.binance.vision/data/spot/daily/klines'
START = datetime(2023,1,1,tzinfo=timezone.utc)
END = datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)
UA = {'User-Agent':'Mozilla/5.0 EXCHANGE-DELISTING-SHOCK-001/1.0','clienttype':'web'}

GUARDS = {
    'market_price_values_opened': False,
    'returns_computed': False,
    'pnl_computed': False,
    'year_2025_opened': False,
    'year_2026_opened': False,
    'live_trading': False,
    'exchange_mutation': False,
}

def get(url, attempts=4):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:
            last=e; time.sleep(.5*(2**i))
    raise last

def get_json(base, params):
    raw=get(base+'?'+urllib.parse.urlencode(params))
    return raw, json.loads(raw.decode('utf-8'))

def find_articles(obj):
    out=[]
    def walk(x):
        if isinstance(x,dict):
            title=x.get('title')
            code=x.get('code') or x.get('articleCode')
            if isinstance(title,str) and code:
                out.append(x)
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(obj)
    uniq={}
    for a in out:
        c=str(a.get('code') or a.get('articleCode'))
        uniq[c]=a
    return list(uniq.values())

def find_detail(obj):
    best=None
    def walk(x):
        nonlocal best
        if isinstance(x,dict):
            if isinstance(x.get('body'),str) and (x.get('title') or x.get('releaseDate')):
                if best is None or len(x.get('body',''))>len(best.get('body','')): best=x
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(obj)
    return best

def parse_release(v):
    if v is None: return None
    if isinstance(v,(int,float)):
        sec=float(v)/1000.0 if float(v)>1e11 else float(v)
        return datetime.fromtimestamp(sec,tz=timezone.utc)
    s=str(v).strip().replace('Z','+00:00')
    try:
        d=datetime.fromisoformat(s)
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    except Exception: return None

def textify(s):
    s=re.sub(r'(?i)<br\s*/?>|</p>|</li>|</h\d>', '\n', s)
    s=re.sub(r'<[^>]+>', ' ', s)
    s=html.unescape(s).replace('\xa0',' ')
    s=unicodedata.normalize('NFKC',s)
    s=''.join(ch for ch in s if unicodedata.category(ch)!='Cf')
    s=re.sub(r'[ \t\r\f\v]+',' ',s)
    return s

def li_items(body):
    items=[]
    for m in re.finditer(r'(?is)<li[^>]*>(.*?)</li>', body):
        t=textify(m.group(1)).strip()
        mm=re.search(r'^(.*?)\s*\(([A-Z0-9]{2,15})\)\s*$', t)
        if mm: items.append((mm.group(2),mm.group(1).strip(' -•')))
    return items

def title_symbols(title):
    m=re.search(r'(?i)^Binance Will Delist\s+(.+?)\s+on\s+(20\d\d-\d\d-\d\d)\s*$',title.strip())
    if not m: return [],None
    raw=m.group(1).replace(' and ',', ')
    syms=[]
    for part in raw.split(','):
        s=part.strip()
        if re.fullmatch(r'[A-Z0-9]{2,15}',s): syms.append(s)
    return syms,m.group(2)

def exact_pairs(text):
    m=re.search(r'(?is)exact\s+trading\s+pairs\s+being\s+removed\s+are\s*:\s*(.*?)(?:All\s+trade\s+orders|To\s+view\s+your\s+assets|Deposits\s+of|Withdrawals\s+of|Binance\s+Margin|Binance\s+Convert|$)', text)
    if not m: return []
    return sorted(set(re.findall(r'\b[A-Z0-9]{2,20}/[A-Z0-9]{2,20}\b',m.group(1))))

def full_delist_anchor(text):
    return re.search(r'(?is)delist\s+and\s+cease\s+trading\s+on\s+all(?:\s+spot)?\s+trading\s+pairs',text)

def delist_ts(text,title):
    anchor=full_delist_anchor(text)
    syms,title_date=title_symbols(title)
    if not anchor or not title_date: return None
    tail=text[anchor.start():anchor.start()+1800]
    stamps=[]
    for m in re.finditer(r'(20\d\d-\d\d-\d\d)\s+(\d\d:\d\d)\s*\(UTC\)',tail,re.I):
        stamps.append((m.group(1),m.group(2),m.start()))
    same=[x for x in stamps if x[0]==title_date]
    if not same: return None
    date,time_s,_=same[0]
    return datetime.strptime(date+' '+time_s,'%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)

def token_names(body,text,title):
    names=dict(li_items(body))
    anchor=full_delist_anchor(text)
    if anchor:
        tail=text[anchor.start():anchor.start()+1800]
        stop=re.search(r'(?is)Please\s+note\s*:?',tail)
        seg=tail[:stop.start()] if stop else tail
        for m in re.finditer(r'(?m)^\s*([^()\n]{1,100}?)\s*\(([A-Z0-9]{2,15})\)\s*$',seg):
            name=m.group(1).strip(' -•\t')
            if name: names.setdefault(m.group(2),name)
    syms,_=title_symbols(title)
    for sym in syms:
        names.setdefault(sym,None)
    return names

def ceil_hour(dt):
    x=dt.replace(minute=0,second=0,microsecond=0)
    return x if x==dt else x+timedelta(hours=1)

def checksum(sym, day):
    pair=sym+'USDT'; ds=day.isoformat()
    url=f'{DV}/{pair}/1h/{pair}-1h-{ds}.zip.CHECKSUM'
    try:
        b=get(url).decode('utf-8','replace').strip().split()
        dg=b[0].lower() if b else ''
        ok=len(dg)==64 and all(c in '0123456789abcdef' for c in dg)
        return {'ok':ok,'sha256':dg if ok else None,'url':url,'status':200}
    except Exception as e:
        return {'ok':False,'sha256':None,'url':url,'status':'ERROR:'+type(e).__name__}

def main():
    OUTDIR.mkdir(parents=True,exist_ok=True)
    candidates={}; list_pages=0; list_error=None
    try:
        for p in range(1,201):
            raw,j=get_json(LIST,{'type':1,'catalogId':161,'pageNo':p,'pageSize':50})
            arts=find_articles(j); list_pages=p
            if not arts: break
            for a in arts:
                code=str(a.get('code') or a.get('articleCode'))
                if re.search(r'^Binance Will Delist\b',str(a.get('title','')),re.I): candidates[code]=a
    except Exception as e:
        list_error=type(e).__name__+':'+str(e)

    qualified=[]; rejected=[]; detail_failures={}
    for code,a in sorted(candidates.items()):
        try:
            raw,j=get_json(DETAIL,{'articleCode':code})
            d=find_detail(j)
            if not d: raise RuntimeError('detail body absent')
            pub=parse_release(d.get('releaseDate') or a.get('releaseDate'))
            title=str(d.get('title') or a.get('title') or '')
            body=str(d.get('body') or '')
            txt=textify(body)
            if pub is None or not (START<=pub<=END): continue
            if not full_delist_anchor(txt):
                rejected.append({'article_code':code,'title':title,'reason':'NO_FULL_TOKEN_DELIST_PHRASE'}); continue
            stop=delist_ts(txt,title)
            if stop is None:
                rejected.append({'article_code':code,'title':title,'reason':'NO_TITLE_BOUND_CESSATION_TIMESTAMP'}); continue
            pairs=exact_pairs(txt)
            if not pairs:
                rejected.append({'article_code':code,'title':title,'reason':'NO_EXACT_TRADING_PAIR_SECTION'}); continue
            names=token_names(body,txt,title)
            title_syms,_=title_symbols(title)
            if not title_syms:
                rejected.append({'article_code':code,'title':title,'reason':'NO_TITLE_SYMBOL_SET'}); continue
            pair_symbols=set()
            for pair in pairs:
                left,right=pair.split('/',1); pair_symbols.add(left); pair_symbols.add(right)
            syms=[sym for sym in title_syms if sym in pair_symbols]
            if not syms:
                rejected.append({'article_code':code,'title':title,'reason':'TITLE_SYMBOLS_NOT_IN_EXACT_PAIR_SECTION'}); continue
            digest=hashlib.sha256(raw).hexdigest()
            anchor=full_delist_anchor(txt)
            evtext=re.sub(r'\s+',' ',txt[anchor.start():anchor.start()+900]).strip() if anchor else None
            for sym in syms:
                qualified.append({
                    'article_code':code,'official_url':f'https://www.binance.com/en/support/announcement/detail/{code}',
                    'title':title,'publication_timestamp_utc':pub.isoformat().replace('+00:00','Z'),
                    'token_symbol':sym,'token_name':names.get(sym),
                    'all_pairs_cessation_timestamp_utc':stop.isoformat().replace('+00:00','Z'),
                    'all_pairs_text_evidence':evtext,'exact_pairs':pairs,
                    'has_usdt_pair':f'{sym}/USDT' in pairs,'article_response_sha256':digest
                })
        except Exception as e:
            detail_failures[code]=type(e).__name__+':'+str(e)

    qualified.sort(key=lambda x:(x['publication_timestamp_utc'],x['token_symbol']))
    dedup=[]; seen=set()
    for e in qualified:
        k=(e['token_symbol'],e['all_pairs_cessation_timestamp_utc'])
        if k in seen: continue
        seen.add(k); dedup.append(e)
    qualified=dedup

    years=sorted(set(int(e['publication_timestamp_utc'][:4]) for e in qualified))
    tokens=sorted(set(e['token_symbol'] for e in qualified))
    source_pass=len(qualified)>=30 and len(tokens)>=15 and {2023,2024}.issubset(years)

    route=[]; protected=[]
    if source_pass:
        for e in qualified:
            pub=datetime.fromisoformat(e['publication_timestamp_utc'].replace('Z','+00:00'))
            stop=datetime.fromisoformat(e['all_pairs_cessation_timestamp_utc'].replace('Z','+00:00'))
            entry=ceil_hour(pub+timedelta(hours=1))
            if not e['has_usdt_pair']:
                route.append({'symbol':e['token_symbol'],'article_code':e['article_code'],'qualified':False,'reason':'NO_USDT_PAIR_IN_OFFICIAL_DELIST_NOTICE'}); continue
            if entry.year>=2025 or stop.year>=2025:
                protected.append({'symbol':e['token_symbol'],'article_code':e['article_code'],'reason':'PROTECTED_PERIOD_2025_REQUIRED'}); continue
            a=checksum(e['token_symbol'],entry.date()); b=checksum(e['token_symbol'],stop.date())
            route.append({'symbol':e['token_symbol'],'article_code':e['article_code'],'entry_boundary_utc':entry.isoformat().replace('+00:00','Z'),'cessation_utc':stop.isoformat().replace('+00:00','Z'),'entry_day_checksum':a,'cessation_day_checksum':b,'qualified':bool(a['ok'] and b['ok'])})

    rq=[r for r in route if r.get('qualified')]
    rq_tokens=sorted(set(r['symbol'] for r in rq))
    rq_years=sorted(set(int(next(e for e in qualified if e['article_code']==r['article_code'] and e['token_symbol']==r['symbol'])['publication_timestamp_utc'][:4]) for r in rq)) if rq else []
    route_pass=len(rq)>=30 and len(rq_tokens)>=15 and {2023,2024}.issubset(rq_years)

    if list_error and not candidates: classification='SOURCE_ACCESS_BLOCKED'
    elif not source_pass: classification='INSUFFICIENT_SOURCE_SAMPLE'
    elif not route_pass: classification='INSUFFICIENT_MARKET_ROUTE_SAMPLE'
    else: classification='SOURCE_DATA_PASS'

    doc={
      'lab_id':'EXCHANGE-DELISTING-SHOCK-001','mve_id':'EDS-BINANCE-FULLTOKEN-001','mode':'SOURCE_DATA_GATE_ONLY',
      'receipt':{
        'classification':classification,'list_pages_requested':list_pages,'list_error':list_error,
        'candidate_title_count':len(candidates),'qualified_token_events':len(qualified),'qualified_distinct_tokens':len(tokens),'qualified_years':years,
        'route_qualified_token_events':len(rq),'route_qualified_distinct_tokens':len(rq_tokens),'route_qualified_years':rq_years,
        'source_minimums':{'events':30,'tokens':15,'years':[2023,2024]},'route_minimums':{'events':30,'tokens':15,'years':[2023,2024]},
        'guards':GUARDS,
        'next_action':'If SOURCE_DATA_PASS, freeze FINAL_PRE_DISCOVERY_PROTOCOL before any price value. Otherwise preserve exact blocked/insufficient classification; no weakening.'
      },
      'qualified_events':qualified,'route_checks':route,'protected_exclusions':protected,'rejected':rejected,'detail_failures':detail_failures
    }
    OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(doc['receipt'],indent=2,sort_keys=True))
    if classification=='SOURCE_ACCESS_BLOCKED': raise SystemExit(21)
    if classification.startswith('INSUFFICIENT_'): raise SystemExit(22)

if __name__=='__main__': main()
