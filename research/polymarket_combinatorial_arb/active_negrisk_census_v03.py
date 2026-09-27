#!/usr/bin/env python3
import hashlib,json,os,sys,urllib.request
from collections import Counter
from datetime import datetime,timezone

BASE='https://gamma-api.polymarket.com'
UA='CryptoLab-POLY-COMB-CENSUS/0.3'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
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
    R={'lab_id':'POLY-COMBINATORIAL-ARB-001','gate':'ACTIVE_NEGRISK_CENSUS_V0.3',
       'started_at_utc':datetime.now(timezone.utc).isoformat(),
       'prices_opened':False,'books_opened':False,'fees_opened':False,'economic_outputs_computed':False,
       'authenticated_endpoints_used':False,'orders_sent':False,'pages':[]}
    events=[]
    for page in range(20):
        off=page*500
        data,raw=get(f'{BASE}/events?active=true&closed=false&limit=500&offset={off}')
        if not isinstance(data,list):
            vals=data.get('data') or data.get('events') or []
        else: vals=data
        R['pages'].append({'offset':off,'count':len(vals),'sha256':h(raw)})
        events.extend(vals)
        if len(vals)<500: break

    std=[]; aug=[]; other=[]
    for ev in events:
        neg=ev.get('negRisk',ev.get('neg_risk'))
        augmented=ev.get('negRiskAugmented',ev.get('neg_risk_augmented'))
        if neg is True and augmented is True: aug.append(ev)
        elif neg is True: std.append(ev)
        else: other.append(ev)

    dist=Counter(bucket(len(e.get('markets') or [])) for e in std)
    exact_counts=Counter(len(e.get('markets') or []) for e in std)
    schema_complete=0; all_books_enabled=0; live_markets_complete=0
    sample=[]
    for ev in std:
        ms=ev.get('markets') or []
        schema=bool(ms) and all(yes_schema_ok(m) for m in ms)
        books=bool(ms) and all(m.get('enableOrderBook') is not False for m in ms)
        live=bool(ms) and all(m.get('closed') is not True and m.get('active') is not False for m in ms)
        schema_complete+=int(schema); all_books_enabled+=int(books); live_markets_complete+=int(live)
        sample.append({'event_id':ev.get('id'),'market_count':len(ms),'schema_complete':schema,
                       'all_orderbooks_enabled':books,'all_markets_live':live})
    sample=sorted(sample,key=lambda x:(x['market_count'],str(x['event_id'])))[:25]
    R['summary']={
      'active_events_total':len(events),'standard_negrisk_events':len(std),'augmented_negrisk_events':len(aug),
      'non_negrisk_events':len(other),'standard_negrisk_market_count_buckets':dict(sorted(dist.items())),
      'standard_negrisk_exact_market_counts':dict(sorted(exact_counts.items())),
      'schema_complete_standard_negrisk_events':schema_complete,
      'all_orderbooks_enabled_standard_negrisk_events':all_books_enabled,
      'all_markets_live_standard_negrisk_events':live_markets_complete,
      'pagination_complete': bool(R['pages']) and R['pages'][-1]['count']<500
    }
    R['sample_geometry']=sample
    R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    with open('artifacts/POLY_COMB_ACTIVE_NEGRISK_CENSUS_V0.3.json','w') as f: json.dump(R,f,indent=2,sort_keys=True)
    print(json.dumps(R['summary'],indent=2,sort_keys=True))
    return 0
if __name__=='__main__':sys.exit(main())
