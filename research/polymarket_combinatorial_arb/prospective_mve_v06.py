#!/usr/bin/env python3
import json, os, sys, time, urllib.request
from decimal import Decimal, getcontext
from datetime import datetime, timezone, timedelta
from statistics import median

getcontext().prec=28
GAMMA='https://gamma-api.polymarket.com'
CLOB='https://clob.polymarket.com'
UA='CryptoLab-POLY-COMB-MVE/0.6'
EVENT_IDS=['32228','48292','51456']
Q=Decimal('10')
BASE_BUF=Decimal('0.05')
STRESS_BUF=Decimal('0.10')
SYNC_MS=2000
ATTEMPTS=60
CADENCE=2.0

def getj(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read().decode())
def postj(url,obj):
    data=json.dumps(obj,separators=(',',':')).encode()
    req=urllib.request.Request(url,data=data,method='POST',headers={'User-Agent':UA,'Accept':'application/json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read().decode())
def jish(x):
    if isinstance(x,(list,dict)):return x
    if isinstance(x,str):
        try:return json.loads(x)
        except:return x
    return x
def yes_token(m):
    outs=jish(m.get('outcomes')); ids=jish(m.get('clobTokenIds') or m.get('clob_token_ids'))
    if not isinstance(outs,list) or not isinstance(ids,list) or len(outs)!=len(ids):return None
    z=[str(t) for o,t in zip(outs,ids) if str(o).strip().lower()=='yes']
    return z[0] if len(z)==1 else None
def parse_dt(s):
    if not s:return None
    try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).astimezone(timezone.utc)
    except:return None
def D(x):return Decimal(str(x))
def walk_asks(book,q):
    asks=book.get('asks') or []
    levels=[]
    for a in asks:
        try:
            p=D(a['price']); sz=D(a['size'])
            if p>0 and sz>0: levels.append((p,sz))
        except: pass
    levels.sort(key=lambda x:x[0])
    rem=q; cost=Decimal('0')
    for p,sz in levels:
        take=min(rem,sz); cost += take*p; rem -= take
        if rem<=0:break
    if rem>0:return None
    return cost
def ts_ms(book):
    try:return int(book.get('timestamp'))
    except:return None

def main():
    freeze_commit=os.environ.get('GITHUB_SHA')
    started=datetime.now(timezone.utc)
    R={'lab_id':'POLY-COMBINATORIAL-ARB-001','mve':'PROSPECTIVE_MVE_V0.6',
       'freeze_runtime_commit':freeze_commit,'started_at_utc':started.isoformat(),
       'q_shares':str(Q),'base_buffer_usdc':str(BASE_BUF),'stress_buffer_usdc':str(STRESS_BUF),
       'sync_tolerance_ms':SYNC_MS,'attempts_frozen':ATTEMPTS,'cadence_seconds':CADENCE,
       'authenticated_endpoints_used':False,'orders_sent':False,'capital_used':False,'snapshots':[],
       'event_meta':{},'fee_state':{},'errors':[]}
    all_tokens=[]; token_event={}; event_tokens={}
    for eid in EVENT_IDS:
        data=getj(f'{GAMMA}/events?id={eid}')
        vals=data if isinstance(data,list) else (data.get('data') or data.get('events') or [])
        ev=[e for e in vals if str(e.get('id'))==eid]
        if len(ev)!=1:
            R['errors'].append({'event_id':eid,'stage':'metadata','error':'EVENT_ID_UNRESOLVED'})
            continue
        ev=ev[0]; toks=[]
        for m in ev.get('markets') or []:
            t=yes_token(m)
            if not t:
                R['errors'].append({'event_id':eid,'market_id':m.get('id'),'stage':'metadata','error':'YES_TOKEN_UNRESOLVED'})
                continue
            toks.append(t);token_event[t]=eid
        event_tokens[eid]=toks
        R['event_meta'][eid]={'title':ev.get('title'),'slug':ev.get('slug'),'market_count':len(ev.get('markets') or []),
                              'yes_token_count':len(toks),'endDate':ev.get('endDate'),
                              'negRisk':ev.get('negRisk',ev.get('neg_risk')),
                              'negRiskAugmented':ev.get('negRiskAugmented',ev.get('neg_risk_augmented'))}
        all_tokens.extend(toks)
    all_tokens=list(dict.fromkeys(all_tokens))

    for t in all_tokens:
        try:
            f=getj(f'{CLOB}/fee-rate?token_id={t}')
            base=f.get('base_fee')
            if base is None:base=f.get('fee_rate_bps')
            R['fee_state'][t]={'raw':f,'resolved_zero':str(base) in ('0','0.0','None') and base is not None}
        except Exception as e:
            R['fee_state'][t]={'error':repr(e),'resolved_zero':False}

    payload=[{'token_id':t} for t in all_tokens]
    for k in range(ATTEMPTS):
        target=started.timestamp()+k*CADENCE
        now=time.time()
        if target>now:time.sleep(target-now)
        recv_start=time.time()
        snap={'attempt':k+1,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'events':{}}
        try:
            books=postj(CLOB+'/books',payload)
            snap['http_roundtrip_ms']=round((time.time()-recv_start)*1000,3)
            if not isinstance(books,list):raise RuntimeError('BOOK_BATCH_NOT_LIST')
            bm={}
            for b in books:
                key=str(b.get('asset_id') or b.get('token_id') or '')
                if key:bm[key]=b
            snap['books_returned']=len(books);snap['books_mapped']=len(bm)
            if len(bm)!=len(all_tokens):
                snap['batch_mapping_error']=f'{len(bm)}/{len(all_tokens)}'
            for eid,toks in event_tokens.items():
                er={'token_count':len(toks)}
                fee_ok=bool(toks) and all(R['fee_state'].get(t,{}).get('resolved_zero') for t in toks)
                er['fee_resolved_zero']=fee_ok
                obs=[bm.get(t) for t in toks]
                er['books_present']=sum(1 for b in obs if b is not None)
                if len(obs)!=len(toks) or any(b is None for b in obs):
                    er['status']='BOOKS_MISSING';snap['events'][eid]=er;continue
                times=[ts_ms(b) for b in obs]
                if any(x is None for x in times):
                    er['status']='TIMESTAMP_MISSING';snap['events'][eid]=er;continue
                disp=max(times)-min(times);er['timestamp_dispersion_ms']=disp
                if disp>SYNC_MS:
                    er['status']='UNSYNCED';snap['events'][eid]=er;continue
                costs=[walk_asks(b,Q) for b in obs]
                er['q_fillable_legs']=sum(1 for c in costs if c is not None)
                if any(c is None for c in costs):
                    er['status']='DEPTH_INSUFFICIENT';snap['events'][eid]=er;continue
                if not fee_ok:
                    er['status']='FEE_FORMULA_UNRESOLVED';snap['events'][eid]=er;continue
                total=sum(costs,Decimal('0'))
                raw=Q-total;base=raw-BASE_BUF;stress=raw-STRESS_BUF
                er.update({'status':'ECONOMICALLY_CLASSIFIED','package_ask_cost':str(total),
                           'raw_margin':str(raw),'base_margin':str(base),'stress_margin':str(stress),
                           'positive_raw':raw>0,'positive_base':base>0,'positive_stress':stress>0})
                end=parse_dt(R['event_meta'].get(eid,{}).get('endDate'))
                if end:
                    locked=max(Decimal('1'),D(((end+timedelta(days=7))-datetime.now(timezone.utc)).total_seconds())/D(86400))
                    er['locked_days_stress']=str(locked)
                    if total>0:er['simple_annualized_stress_yield']=str((stress/total)*D(365)/locked)
                snap['events'][eid]=er
        except Exception as e:
            snap['request_error']=repr(e)
        R['snapshots'].append(snap)

    per={}
    total_valid=0;positive=0;positive_events=set()
    for eid in EVENT_IDS:
        rows=[s.get('events',{}).get(eid,{}) for s in R['snapshots']]
        valid=[r for r in rows if r.get('status')=='ECONOMICALLY_CLASSIFIED']
        total_valid+=len(valid)
        ps=[r for r in valid if r.get('positive_stress')]
        positive+=len(ps)
        if ps:positive_events.add(eid)
        def decs(k):return [D(r[k]) for r in valid if k in r]
        stress=decs('stress_margin');raw=decs('raw_margin');base=decs('base_margin')
        disps=[r.get('timestamp_dispersion_ms') for r in rows if isinstance(r.get('timestamp_dispersion_ms'),int)]
        per[eid]={
          'attempted':len(rows),'valid_economic_snapshots':len(valid),
          'positive_raw_count':sum(1 for r in valid if r.get('positive_raw')),
          'positive_base_count':sum(1 for r in valid if r.get('positive_base')),
          'positive_stress_count':len(ps),
          'max_raw_margin':str(max(raw)) if raw else None,
          'max_base_margin':str(max(base)) if base else None,
          'max_stress_margin':str(max(stress)) if stress else None,
          'median_stress_margin':str(median(stress)) if stress else None,
          'max_timestamp_dispersion_ms':max(disps) if disps else None,
          'fee_all_zero':bool(event_tokens.get(eid)) and all(R['fee_state'].get(t,{}).get('resolved_zero') for t in event_tokens.get(eid,[]))
        }
    if total_valid<60: verdict='PILOT_DATA_INSUFFICIENT'
    elif positive>0: verdict='PROSPECTIVE_BOOK_EXECUTABLE_SIGNAL_OBSERVED'
    else: verdict='NO_IMMEDIATE_EXECUTABLE_PACKAGE_OBSERVED'
    R['summary']={'total_valid_event_snapshots':total_valid,'positive_stress_observations':positive,
                  'distinct_positive_stress_events':sorted(positive_events),'per_event':per,
                  'pilot_adjudication':verdict}
    R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    with open('artifacts/POLY_COMB_PROSPECTIVE_MVE_V0.6.json','w') as f:json.dump(R,f,indent=2,sort_keys=True)
    print(json.dumps(R['summary'],indent=2,sort_keys=True))
    return 0

if __name__=='__main__':sys.exit(main())
