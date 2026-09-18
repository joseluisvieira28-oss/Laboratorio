import hashlib, html, json, re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
import source_gate_v02 as v2
import source_gate_v03 as v3

HERE=Path(__file__).resolve().parent
AUTH=json.loads((HERE/'SOURCE_CONTRACT_V04.json').read_text(encoding='utf-8'))
OUTDIR=HERE/'source_evidence'
OUT=OUTDIR/'EDS_SOURCE_DATA_GATE_V04.json'
START=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)
ZERO_WIDTH='\u200b\u200c\u200d\u2060\ufeff'

GUARDS={
  'market_price_values_opened':False,'returns_computed':False,'pnl_computed':False,
  'year_2025_opened':False,'year_2026_opened':False,'live_trading':False,
  'exchange_mutation':False,'wallet_access':False,'merge_to_main':False
}

def semantic_token_identities(body):
    raw=html.unescape(body).translate({ord(c):None for c in ZERO_WIDTH}).replace('\xa0',' ')
    txt=v2.textify(raw)
    # Bound parsing to the semantic full-token declaration, never to the pair list.
    anchor=re.search(r'(?is)decided\\s+to\\s+delist\\s+and\\s+cease\\s+trading\\s+on\\s+all(?:\\s+spot)?\\s+trading\\s+pairs\\s+for\\s+the\\s+following\\s+token(?:\\(s\\)|s)?(?=\\s|:)',txt)
    if not anchor:
        return {}
    tail=txt[anchor.end():]
    cut=re.search(r'(?is)\bPlease\s+note\s*:',tail)
    section=tail[:cut.start()] if cut else tail[:1800]

    items={}
    # Primary route: each visible token item is normally a short text line.
    for line in section.splitlines():
        s=re.sub(r'[ \t]+',' ',line).strip(' \t\r\n-•*')
        if not s or len(s)>140:
            continue
        for m in re.finditer(r'([^()]{1,110}?)\s*\(([A-Z0-9]{2,15})\)',s):
            name=re.sub(r'\s+',' ',m.group(1)).strip(' -•*:;,.')
            sym=m.group(2).upper()
            if sym in {'UTC','FAQ'} or not name or re.search(r'\b\d{2}:\d{2}\b',name):
                continue
            items.setdefault(sym,name)

    # Fallback for CMS bodies whose list separators are flattened.
    if not items:
        compact=re.sub(r'[ \t]+',' ',section)
        for m in re.finditer(r'(?:^|\n|•|\*)\s*([^()\n]{1,110}?)\s*\(([A-Z0-9]{2,15})\)',compact):
            name=re.sub(r'\s+',' ',m.group(1)).strip(' -•*:;,.')
            sym=m.group(2).upper()
            if sym in {'UTC','FAQ'} or not name or re.search(r'\b\d{2}:\d{2}\b',name):
                continue
            items.setdefault(sym,name)
    return items

def ceil_hour(dt):
    x=dt.replace(minute=0,second=0,microsecond=0)
    return x if x==dt else x+timedelta(hours=1)

def main():
    OUTDIR.mkdir(parents=True,exist_ok=True)
    assert AUTH['status']=='FROZEN_NEW_SOURCE_CONTRACT_OUTCOME_BLIND'
    assert AUTH['source_event_gate']['minimum_qualified_token_events']==30
    assert AUTH['source_event_gate']['minimum_distinct_tokens']==15
    assert AUTH['source_event_gate']['required_calendar_years']==[2023,2024]
    assert all(x is False for x in AUTH['hard_firewalls'].values())

    candidates={};list_pages=0;list_error=None
    try:
        for p in range(1,201):
            raw,j=v2.get_json(v2.LIST,{'type':1,'catalogId':161,'pageNo':p,'pageSize':50})
            arts=v2.find_articles(j);list_pages=p
            if not arts: break
            for a in arts:
                code=str(a.get('code') or a.get('articleCode'))
                if re.search(r'^Binance Will Delist\b',str(a.get('title','')),re.I):
                    candidates[code]=a
    except Exception as e:
        list_error=type(e).__name__+':'+str(e)

    raw_events=[];rejected=[];detail_failures={};article_diagnostics=[]
    for code,a in sorted(candidates.items()):
        try:
            raw,j=v2.get_json(v2.DETAIL,{'articleCode':code})
            d=v2.find_detail(j)
            if not d: raise RuntimeError('detail body absent')
            pub=v2.parse_release(d.get('releaseDate') or a.get('releaseDate'))
            if pub is None or not (START<=pub<=END): continue
            title=str(d.get('title') or a.get('title') or '')
            body=str(d.get('body') or '')
            txt=v2.textify(body)
            stop=v3.delist_ts(txt)
            if stop is None:
                rejected.append({'article_code':code,'title':title,'reason':'NO_EXACT_ALL_PAIRS_CESSATION_TIMESTAMP'})
                continue
            pairs=v2.exact_pairs(txt)
            if not pairs:
                rejected.append({'article_code':code,'title':title,'reason':'NO_EXACT_TRADING_PAIR_SECTION'})
                continue
            identities=semantic_token_identities(body)
            if not identities:
                rejected.append({'article_code':code,'title':title,'reason':'NO_OFFICIAL_NAME_SYMBOL_DELIST_LIST'})
                article_diagnostics.append({'article_code':code,'title':title,'identity_count':0,'pair_count':len(pairs)})
                continue

            pair_sides=set()
            for pair in pairs:
                bits=pair.split('/')
                if len(bits)==2: pair_sides.update(bits)
            digest=hashlib.sha256(raw).hexdigest()
            evtext=v3.evidence_text(txt)
            accepted_here=0
            for sym,name in sorted(identities.items()):
                if sym not in pair_sides:
                    rejected.append({'article_code':code,'symbol':sym,'title':title,'reason':'OFFICIAL_TOKEN_NOT_PRESENT_IN_EXACT_PAIRS'})
                    continue
                token_pairs=sorted(p for p in pairs if sym in p.split('/'))
                raw_events.append({
                  'article_code':code,
                  'official_url':f'https://www.binance.com/en/support/announcement/detail/{code}',
                  'title':title,
                  'publication_timestamp_utc':pub.isoformat().replace('+00:00','Z'),
                  'token_symbol':sym,'token_name':name,
                  'identity_source':'OFFICIAL_SEMANTIC_NAME_SYMBOL_DELIST_LIST',
                  'all_pairs_cessation_timestamp_utc':stop.isoformat().replace('+00:00','Z'),
                  'all_pairs_text_evidence':evtext,
                  'exact_pairs_for_token':token_pairs,
                  'has_symbol_usdt_pair':f'{sym}/USDT' in pairs,
                  'article_response_sha256':digest
                })
                accepted_here+=1
            article_diagnostics.append({
              'article_code':code,'title':title,'identity_count':len(identities),
              'identity_symbols':sorted(identities),'pair_count':len(pairs),
              'accepted_token_events':accepted_here
            })
        except Exception as e:
            detail_failures[code]=type(e).__name__+':'+str(e)

    # First qualifying public announcement only, prospectively by publication time.
    raw_events.sort(key=lambda x:(x['publication_timestamp_utc'],x['article_code'],x['token_symbol']))
    qualified=[];seen_symbols=set()
    for e in raw_events:
        if e['token_symbol'] in seen_symbols:
            rejected.append({'article_code':e['article_code'],'symbol':e['token_symbol'],'title':e['title'],'reason':'LATER_REPEAT_ANNOUNCEMENT'})
            continue
        seen_symbols.add(e['token_symbol']);qualified.append(e)

    years=sorted(set(int(e['publication_timestamp_utc'][:4]) for e in qualified))
    tokens=sorted(set(e['token_symbol'] for e in qualified))
    source_pass=len(qualified)>=30 and len(tokens)>=15 and {2023,2024}.issubset(set(years))

    route=[];protected=[]
    if source_pass:
        bykey={(e['article_code'],e['token_symbol']):e for e in qualified}
        for e in qualified:
            pub=datetime.fromisoformat(e['publication_timestamp_utc'].replace('Z','+00:00'))
            stop=datetime.fromisoformat(e['all_pairs_cessation_timestamp_utc'].replace('Z','+00:00'))
            entry=ceil_hour(pub+timedelta(hours=1))
            if not e['has_symbol_usdt_pair']:
                route.append({'symbol':e['token_symbol'],'article_code':e['article_code'],'qualified':False,'reason':'NO_SYMBOL_USDT_PAIR_IN_OFFICIAL_DELIST_NOTICE'})
                continue
            if entry.year>=2025 or stop.year>=2025:
                protected.append({'symbol':e['token_symbol'],'article_code':e['article_code'],'reason':'PROTECTED_PERIOD_2025_REQUIRED'})
                continue
            a=v2.checksum(e['token_symbol'],entry.date())
            b=v2.checksum(e['token_symbol'],stop.date())
            route.append({
              'symbol':e['token_symbol'],'article_code':e['article_code'],
              'entry_boundary_utc':entry.isoformat().replace('+00:00','Z'),
              'cessation_utc':stop.isoformat().replace('+00:00','Z'),
              'entry_day_checksum':a,'cessation_day_checksum':b,
              'qualified':bool(a['ok'] and b['ok'])
            })

    rq=[x for x in route if x.get('qualified')]
    rq_tokens=sorted(set(x['symbol'] for x in rq))
    event_lookup={(e['article_code'],e['token_symbol']):e for e in qualified}
    rq_years=sorted(set(int(event_lookup[(x['article_code'],x['symbol'])]['publication_timestamp_utc'][:4]) for x in rq)) if rq else []
    route_pass=len(rq)>=30 and len(rq_tokens)>=15 and {2023,2024}.issubset(set(rq_years))

    if list_error and not candidates: classification='SOURCE_ACCESS_BLOCKED'
    elif not source_pass: classification='INSUFFICIENT_SOURCE_SAMPLE'
    elif not route_pass: classification='INSUFFICIENT_MARKET_ROUTE_SAMPLE'
    else: classification='SOURCE_DATA_PASS'

    doc={
      'lab_id':AUTH['lab_id'],'source_gate_id':AUTH['source_gate_id'],
      'mode':'NEW_SOURCE_CONTRACT_OUTCOME_BLIND','classification':classification,
      'receipt':{
        'list_pages_requested':list_pages,'list_error':list_error,
        'candidate_title_count':len(candidates),'detail_failure_count':len(detail_failures),
        'qualified_token_events':len(qualified),'qualified_distinct_tokens':len(tokens),'qualified_years':years,
        'route_qualified_token_events':len(rq),'route_qualified_distinct_tokens':len(rq_tokens),'route_qualified_years':rq_years,
        'rejected_reason_counts':dict(Counter(x.get('reason','UNKNOWN') for x in rejected)),
        'source_minimums':{'events':30,'tokens':15,'years':[2023,2024]},
        'route_minimums':{'events':30,'tokens':15,'years':[2023,2024]},
        'guards':GUARDS,
        'next_action':'If SOURCE_DATA_PASS, STOP and freeze FINAL_PRE_DISCOVERY_PROTOCOL before any market price value.'
      },
      'qualified_events':qualified,'route_checks':route,'protected_exclusions':protected,
      'rejected':rejected,'detail_failures':detail_failures,'article_diagnostics':article_diagnostics,
      'parent_v03_preserved':{'run_id':34982070979,'classification':'INSUFFICIENT_SOURCE_SAMPLE'}
    }
    OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'classification':classification,**doc['receipt']},indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
