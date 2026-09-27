#!/usr/bin/env python3
import hashlib,json,os,sys,time,urllib.parse,urllib.request
from datetime import datetime,timezone

GAMMA='https://gamma-api.polymarket.com'
CLOB='https://clob.polymarket.com'
DOC_CTF='https://raw.githubusercontent.com/Polymarket/agent-skills/main/ctf-operations.md'
DOC_MARKET='https://raw.githubusercontent.com/Polymarket/agent-skills/main/market-data.md'
UA='CryptoLab-POLY-COMB-SOURCE-ROUTE/0.2'

def get_bytes(url,timeout=25):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'*/*'})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
def get_json(url,timeout=25):
    raw=get_bytes(url,timeout); return json.loads(raw.decode()),raw
def h(b): return hashlib.sha256(b).hexdigest()
def jish(x):
    if isinstance(x,(list,dict)): return x
    if isinstance(x,str):
        try:return json.loads(x)
        except:return x
    return x
def yes_token(m):
    outs=jish(m.get('outcomes')); ids=jish(m.get('clobTokenIds') or m.get('clob_token_ids'))
    if not isinstance(outs,list) or not isinstance(ids,list) or len(outs)!=len(ids): return None
    for o,t in zip(outs,ids):
        if str(o).strip().lower()=='yes': return str(t)
    return None

def main():
    R={'lab_id':'POLY-COMBINATORIAL-ARB-001','gate':'SOURCE_ROUTE_PROBE_V0.2',
       'started_at_utc':datetime.now(timezone.utc).isoformat(),
       'economic_outputs_computed':False,'package_price_sums_computed':False,
       'profitability_computed':False,'orders_sent':False,'authenticated_endpoints_used':False,
       'future_nearest_joins':0,'silent_imputations':0,'docs':{},'events':[],'errors':[]}
    docs_ok=True
    for name,url,needles in [
      ('ctf_operations',DOC_CTF,['Negative Risk','only one outcome can win','negRisk']),
      ('market_data',DOC_MARKET,['Gamma API','CLOB Orderbook','No auth'])
    ]:
        try:
            raw=get_bytes(url); txt=raw.decode('utf-8','replace')
            found={n:(n.lower() in txt.lower()) for n in needles}
            R['docs'][name]={'url':url,'sha256':h(raw),'bytes':len(raw),'required_phrases':found}
            docs_ok=docs_ok and all(found.values())
        except Exception as e:
            docs_ok=False; R['errors'].append({'stage':'doc','name':name,'error':repr(e)})
    R['docs_provenance_pass']=docs_ok

    url=GAMMA+'/events?active=true&closed=false&limit=500&offset=0&order=volume_24hr&ascending=false'
    try:
        data,raw=get_json(url); R['gamma_sha256']=h(raw); R['gamma_count']=len(data) if isinstance(data,list) else None
    except Exception as e:
        R['errors'].append({'stage':'gamma','error':repr(e)}); data=[]
    if not isinstance(data,list): data=data.get('data') or data.get('events') or []

    eligible=[]
    for ev in data:
        neg=ev.get('negRisk',ev.get('neg_risk'))
        aug=ev.get('negRiskAugmented',ev.get('neg_risk_augmented'))
        markets=ev.get('markets') or []
        if neg is not True or aug is True or not isinstance(markets,list) or not (2<=len(markets)<=20): continue
        toks=[]; bad=False
        for m in markets:
            if m.get('closed') is True or m.get('active') is False or m.get('enableOrderBook') is False:
                bad=True; break
            tok=yes_token(m)
            if not tok: bad=True; break
            toks.append(tok)
        if bad or len(toks)!=len(markets): continue
        eligible.append((ev,toks))
        if len(eligible)>=8: break

    for ev,toks in eligible:
        er={'event_id':ev.get('id'),'slug':ev.get('slug'),'title':ev.get('title'),
            'neg_risk':True,'market_count':len(toks),'legs':[]}
        for tok in toks:
            lr={'token_id':tok}
            try:
                book,raw=get_json(CLOB+'/book?token_id='+urllib.parse.quote(tok))
                lr.update({'book_sha256':h(raw),'bids_count':len(book.get('bids') or []),
                           'asks_count':len(book.get('asks') or []),'has_timestamp':book.get('timestamp') is not None,
                           'has_tick_size':book.get('tick_size') is not None,'has_min_order_size':book.get('min_order_size') is not None})
            except Exception as e: lr['book_error']=repr(e)
            try:
                fee,raw=get_json(CLOB+'/fee-rate?token_id='+urllib.parse.quote(tok))
                lr.update({'fee_sha256':h(raw),'fee_schema_present':isinstance(fee,dict) and any(k in fee for k in ('base_fee','fee_rate_bps')),
                           'fee_fields':sorted(fee.keys()) if isinstance(fee,dict) else []})
            except Exception as e: lr['fee_error']=repr(e)
            lr['leg_source_complete']=(not lr.get('book_error') and lr.get('bids_count',0)>0 and lr.get('asks_count',0)>0
                                      and lr.get('has_timestamp') is True and lr.get('fee_schema_present') is True)
            er['legs'].append(lr); time.sleep(0.04)
        er['source_package_complete']=bool(er['legs']) and all(x['leg_source_complete'] for x in er['legs'])
        R['events'].append(er)

    complete=sum(1 for e in R['events'] if e['source_package_complete'])
    total_legs=sum(len(e['legs']) for e in R['events'])
    good_legs=sum(sum(1 for l in e['legs'] if l['leg_source_complete']) for e in R['events'])
    route_pass=(docs_ok and len(R['events'])>=3 and complete>=2 and R['authenticated_endpoints_used'] is False
                and R['economic_outputs_computed'] is False and R['package_price_sums_computed'] is False)
    R['summary']={'eligible_standard_negrisk_events':len(R['events']),'source_package_complete_events':complete,
                  'legs_probed':total_legs,'legs_source_complete':good_legs,'docs_provenance_pass':docs_ok,
                  'source_route_pass':route_pass}
    R['status']='SOURCE_ROUTE_PASS' if route_pass else 'SOURCE_ROUTE_INCOMPLETE'
    R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    with open('artifacts/POLY_COMB_SOURCE_ROUTE_V0.2.json','w') as f: json.dump(R,f,indent=2,sort_keys=True)
    print(json.dumps({'status':R['status'],**R['summary']},indent=2,sort_keys=True))
    return 0
if __name__=='__main__':sys.exit(main())
