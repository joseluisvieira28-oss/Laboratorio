#!/usr/bin/env python3
import hashlib,json,os,sys,urllib.request
from collections import Counter
from datetime import datetime,timezone

BASE='https://gamma-api.polymarket.com'
UA='CryptoLab-POLY-COMB-CENSUS/0.4'
LIMIT=100

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r: raw=r.read()
    return json.loads(raw.decode()),raw
def h(b): return hashlib.sha256(b).hexdigest()
def jish(x):
    if isinstance(x,(list,dict)): return x
    if isinstance(x,str):
        try:return json.loads(x)
        except:return x
    return x
def yes_schema_ok(m):
    outs=jish(m.get('outcomes')); ids=jish(m.get('clobTokenIds') or m.get('clob_token_ids'))
    if not isinstance(outs,list) or not isinstance(ids,list) or len(outs)!=len(ids): return False
    return sum(1 for o in outs if str(o).strip().lower()=='yes')==1 and len(ids)>=2 and all(str(x) for x in ids)
def bucket(n):
    if n<=2:return '2'
    if n<=5:return '3-5'
    if n<=10:return '6-10'
    if n<=20:return '11-20'
    if n<=50:return '21-50'
    if n<=100:return '51-100'
    if n<=200:return '101-200'
    return '201+'

def main():
    R={'lab_id':'POLY-COMBINATORIAL-ARB-001','gate':'ACTIVE_NEGRISK_CENSUS_V0.4',
       'started_at_utc':datetime.now(timezone.utc).isoformat(),
       'prices_opened':False,'books_opened':False,'fees_opened':False,'economic_outputs_computed':False,
       'authenticated_endpoints_used':False,'orders_sent':False,'pages':[]}
    events=[]; offset=0; terminal=False
    for page in range(100):
        data,raw=get(f'{BASE}/events?active=true&closed=false&limit={LIMIT}&offset={offset}')
        vals=data if isinstance(data,list) else (data.get('data') or data.get('events') or [])
        R['pages'].append({'page':page+1,'offset':offset,'count':len(vals),'sha256':h(raw)})
        events.extend(vals)
        if len(vals)<LIMIT:
            terminal=True; break
        offset += len(vals)
    ids=[str(e.get('id') or e.get('slug') or '') for e in events]
    unique_ids=set(ids)
    duplicates=len(ids)-len(unique_ids)

    std=[]; aug=[]; other=[]
    for ev in events:
        neg=ev.get('negRisk',ev.get('neg_risk'))
        augmented=ev.get('negRiskAugmented',ev.get('neg_risk_augmented'))
        if neg is True and augmented is True: aug.append(ev)
        elif neg is True: std.append(ev)
        else: other.append(ev)

    dist=Counter(bucket(len(e.get('markets') or [])) for e in std)
    exact=Counter(len(e.get('markets') or []) for e in std)
    schema=books=live=0; geometry=[]
    for ev in std:
        ms=ev.get('markets') or []
        s=bool(ms) and all(yes_schema_ok(m) for m in ms)
        b=bool(ms) and all(m.get('enableOrderBook') is not False for m in ms)
        l=bool(ms) and all(m.get('closed') is not True and m.get('active') is not False for m in ms)
        schema+=int(s); books+=int(b); live+=int(l)
        geometry.append({'event_id':ev.get('id'),'slug':ev.get('slug'),'market_count':len(ms),
                         'schema_complete':s,'all_orderbooks_enabled':b,'all_markets_live':l})
    geometry=sorted(geometry,key=lambda x:(x['market_count'],str(x['event_id'])))
    complete=terminal and duplicates==0
    R['summary']={
      'active_events_rows':len(events),'unique_active_events':len(unique_ids),'duplicate_event_rows':duplicates,
      'standard_negrisk_events':len(std),'augmented_negrisk_events':len(aug),'non_negrisk_events':len(other),
      'standard_negrisk_market_count_buckets':dict(sorted(dist.items())),
      'standard_negrisk_exact_market_counts':dict(sorted(exact.items())),
      'schema_complete_standard_negrisk_events':schema,
      'all_orderbooks_enabled_standard_negrisk_events':books,
      'all_markets_live_standard_negrisk_events':live,
      'pages_fetched':len(R['pages']),'terminal_page_seen':terminal,'pagination_integrity_pass':complete
    }
    R['standard_negrisk_geometry']=geometry
    R['status']='CENSUS_PASS' if complete else 'CENSUS_INCOMPLETE'
    R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    with open('artifacts/POLY_COMB_ACTIVE_NEGRISK_CENSUS_V0.4.json','w') as f: json.dump(R,f,indent=2,sort_keys=True)
    print(json.dumps({'status':R['status'],**R['summary']},indent=2,sort_keys=True))
    return 0 if complete else 2
if __name__=='__main__':sys.exit(main())
