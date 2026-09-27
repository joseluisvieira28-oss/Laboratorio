#!/usr/bin/env python3
import hashlib,json,os,sys,time,urllib.parse,urllib.request
from datetime import datetime,timezone

GAMMA='https://gamma-api.polymarket.com'
CLOB='https://clob.polymarket.com'
DOCS={
 'ctf':'https://raw.githubusercontent.com/Polymarket/agent-skills/main/ctf-operations.md',
 'market':'https://raw.githubusercontent.com/Polymarket/agent-skills/main/market-data.md'}
EVENT_IDS=['32228','48292','51456']
UA='CryptoLab-POLY-COMB-SOURCE/0.5'

def rawget(url,accept='*/*'):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':accept})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def getj(url):
    raw=rawget(url,'application/json'); return json.loads(raw.decode()),raw
def h(b):return hashlib.sha256(b).hexdigest()
def jish(x):
    if isinstance(x,(list,dict)):return x
    if isinstance(x,str):
        try:return json.loads(x)
        except:return x
    return x
def yes_token(m):
    outs=jish(m.get('outcomes')); ids=jish(m.get('clobTokenIds') or m.get('clob_token_ids'))
    if not isinstance(outs,list) or not isinstance(ids,list) or len(outs)!=len(ids):return None
    hits=[str(t) for o,t in zip(outs,ids) if str(o).strip().lower()=='yes']
    return hits[0] if len(hits)==1 else None

def fetch_event(eid):
    # ID query keeps the engineering fixture explicit and bounded.
    data,raw=getj(f'{GAMMA}/events?id={eid}')
    vals=data if isinstance(data,list) else (data.get('data') or data.get('events') or [])
    if not vals: raise RuntimeError('event id not found')
    exact=[x for x in vals if str(x.get('id'))==str(eid)]
    if len(exact)!=1: raise RuntimeError(f'event id ambiguity: {len(exact)}')
    return exact[0],raw

def main():
    R={'lab_id':'POLY-COMBINATORIAL-ARB-001','gate':'BOUNDED_SOURCE_ROUTE_V0.5',
       'started_at_utc':datetime.now(timezone.utc).isoformat(),
       'fixture_event_ids':EVENT_IDS,'economic_outputs_computed':False,
       'package_price_sums_computed':False,'arbitrage_spreads_computed':False,
       'profitability_computed':False,'authenticated_endpoints_used':False,'orders_sent':False,
       'future_nearest_joins':0,'silent_imputations':0,'docs':{},'events':[],'errors':[]}
    docs_pass=True
    requirements={
      'ctf':['Every Yes/No pair is backed by exactly $1.00','only one outcome can win','Neg Risk Adapter'],
      'market':['Gamma API','CLOB Orderbook','no auth']
    }
    for k,url in DOCS.items():
        try:
            raw=rawget(url); txt=raw.decode('utf-8','replace')
            found={q:(q.lower() in txt.lower()) for q in requirements[k]}
            R['docs'][k]={'url':url,'sha256':h(raw),'bytes':len(raw),'required':found}
            docs_pass &= all(found.values())
        except Exception as e:
            docs_pass=False;R['errors'].append({'stage':'docs','key':k,'error':repr(e)})
    R['docs_provenance_pass']=docs_pass

    for eid in EVENT_IDS:
        er={'event_id':eid,'legs':[]}
        try:
            ev,raw=fetch_event(eid)
            er.update({'event_sha256':h(raw),'slug':ev.get('slug'),'title':ev.get('title'),
                       'active':ev.get('active'),'closed':ev.get('closed'),
                       'neg_risk':ev.get('negRisk',ev.get('neg_risk')),
                       'neg_risk_augmented':ev.get('negRiskAugmented',ev.get('neg_risk_augmented'))})
            ms=ev.get('markets') or []; er['market_count']=len(ms)
            identity=(er['active'] is not False and er['closed'] is not True and er['neg_risk'] is True and er['neg_risk_augmented'] is not True)
            er['fixture_identity_pass']=identity
            for m in ms:
                tok=yes_token(m)
                lr={'market_id':m.get('id'),'condition_id':m.get('conditionId') or m.get('condition_id'),
                    'yes_token_id':tok,'enable_order_book':m.get('enableOrderBook')}
                if not tok:
                    lr['schema_error']='YES_TOKEN_UNRESOLVED'
                else:
                    try:
                        book,braw=getj(f'{CLOB}/book?token_id={urllib.parse.quote(tok)}')
                        lr.update({'book_sha256':h(braw),'bids_count':len(book.get('bids') or []),
                                   'asks_count':len(book.get('asks') or []),'has_timestamp':book.get('timestamp') is not None,
                                   'tick_size_present':book.get('tick_size') is not None,'min_order_size_present':book.get('min_order_size') is not None})
                    except Exception as e:lr['book_error']=repr(e)
                    try:
                        fee,fraw=getj(f'{CLOB}/fee-rate?token_id={urllib.parse.quote(tok)}')
                        lr.update({'fee_sha256':h(fraw),'fee_fields':sorted(fee.keys()) if isinstance(fee,dict) else [],
                                   'fee_schema_present':isinstance(fee,dict) and any(x in fee for x in ('base_fee','fee_rate_bps'))})
                    except Exception as e:lr['fee_error']=repr(e)
                lr['leg_source_complete']=(bool(tok) and m.get('enableOrderBook') is not False and not lr.get('book_error')
                    and lr.get('bids_count',0)>0 and lr.get('asks_count',0)>0 and lr.get('has_timestamp') is True
                    and lr.get('fee_schema_present') is True)
                er['legs'].append(lr);time.sleep(.03)
            er['source_package_complete']=identity and bool(er['legs']) and all(x['leg_source_complete'] for x in er['legs'])
        except Exception as e:
            er['event_error']=repr(e)
        R['events'].append(er)
    complete=sum(1 for e in R['events'] if e.get('source_package_complete'))
    identity=sum(1 for e in R['events'] if e.get('fixture_identity_pass'))
    legs=sum(len(e.get('legs',[])) for e in R['events'])
    good=sum(sum(1 for l in e.get('legs',[]) if l.get('leg_source_complete')) for e in R['events'])
    passed=(docs_pass and identity==3 and complete>=2 and not R['economic_outputs_computed']
            and not R['authenticated_endpoints_used'] and not R['orders_sent'])
    R['summary']={'fixture_identity_pass_events':identity,'source_package_complete_events':complete,
                  'legs_probed':legs,'legs_source_complete':good,'docs_provenance_pass':docs_pass,
                  'source_route_pass':passed}
    R['status']='SOURCE_ROUTE_PASS' if passed else 'SOURCE_ROUTE_INCOMPLETE'
    R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    with open('artifacts/POLY_COMB_SOURCE_ROUTE_V0.5.json','w') as f:json.dump(R,f,indent=2,sort_keys=True)
    print(json.dumps({'status':R['status'],**R['summary']},indent=2,sort_keys=True))
    return 0

if __name__=='__main__':sys.exit(main())
