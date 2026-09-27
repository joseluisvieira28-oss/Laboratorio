#!/usr/bin/env python3
import json, math, os, sys, time, urllib.parse, urllib.request
from decimal import Decimal, getcontext
from datetime import datetime, timezone, timedelta
from statistics import median

getcontext().prec=40
GAMMA='https://gamma-api.polymarket.com'
CLOB='https://clob.polymarket.com'
UA='CryptoLab-POLY-COMB-ECONOMIC/0.8'
EVENT_IDS=['32228','48292','51456']
Q=Decimal('10')
BASE_BUFFER=Decimal('0.05')
STRESS_BUFFER=Decimal('0.10')
MAX_RTT_MS=Decimal('2000')
ATTEMPTS=120
CADENCE=1.5

EXPECTED_FD_RAW={"0x0808de4f0cfd47947f2d1be51f9a9c52ea0fec76f73a75cfbe79ddec98d8a908":["0.04","1"],"0x08b39100a4d3d6ad1099e076fb69f781313c5b16975adf189d63542bd1ecca04":["0.04","1"],"0x16c63b7cc37f012b9f59ee164ec03877914c701d06d48291ae8d6fc08a088b0d":["0.04","1"],"0x1adf074e048fa613f4ddbc0766088748a48d120a3a713b0183e219032a411ae3":["0.05","1"],"0x2368d2604c9c2b95bc98c51bd50c66e5351caebf05b9fe79d3398c387fe29a89":["0.05","1"],"0x3849e1d62e0807801913d3e2427e8caf3cc6dd1c8ef42d8d5c08c6f9c449dc5e":["0.04","1"],"0x3f9f68feccc892303834833665bf204632438b028254fc2d5bceea757ff61ed3":["0.04","1"],"0x4914bfdd892a48c341b5e0f41ec10475a815f2277273110b16f95e21084bfe75":["0.05","1"],"0x4a8005d19b41af72c1cd5c619640d9d51da548dd7c3544b12ae0c520d9e6805b":["0.04","1"],"0x4ec6fcb43fe1a32163c7da09d54a99ab9bf6abdc6fd49939d7ad67d696a3248b":["0.05","1"],"0x5e082f0b57f47a29044aa35b4c5658393122e659d5feae521c06b57cdd7f905c":["0.05","1"],"0x602a7a6c7d65b55932e6cf8b6904cb7acdc728ca423ffd3ccb1988dd5501de13":["0.04","1"],"0x757c144993b3cb831e04c42bfcff8c18864c7da4f4688a5939d2f62e031cbc87":["0.05","1"],"0x7987a821b8032824f1805ee39eb5dfb8f64603e4e9e673259eb76f82b439fd3d":["0.04","1"],"0x7ee722a07e0f84405f1267bc1c84eb95bd6348454453abf445618e778af8fd18":["0.05","1"],"0x8d4966e84ae80f24b2e14643fdd45364e354229e11e2c17903b4b1763cfbe67c":["0.05","1"],"0x998bc71817b2d76921d1999ce0f3431cfd5945583667a371280ca2b430b0c06e":["0.04","1"],"0xa281783fc73b1a6927a301ee34cd90795470dc64b500673e445ba5e54f697c09":["0.04","1"],"0xaece8d6062d3e3eb9845b32441a4ab06eb2ef332c0228bc6a36add450647c7c4":["0.05","1"],"0xb77424a53b7480164118374fb5e97b859bd12b696b1aea55d383ce798c060cf4":["0.04","1"],"0xc5eae79d1ffe716572353962eb926b1e3964c500a4880a7a94f58408218ee76b":["0.04","1"],"0xd4e77ba6f29fc093509d24f508631abd445ecf506bbdc9c4c80e60256a318527":["0.05","1"],"0xe0d9f508a249e0070db06eb7d1e1fb17eb23c963f6fb722c4c3f81e23240c1cd":["0.05","1"],"0xfe28cb84a714b1a964290d7fd2587e71d57e905678c8ab64488449b24be78e52":["0.05","1"],"0xffa0accb74987c0dc33a70eb3780c1da160206bcfb3ef5d16c1667bc5c459c78":["0.05","1"]}
EXPECTED_FD={k:(Decimal(v[0]),Decimal(v[1])) for k,v in EXPECTED_FD_RAW.items()}

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
def D(x):return Decimal(str(x))
def parse_dt(s):
    if not s:return None
    try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).astimezone(timezone.utc)
    except:return None
def walk_cost_with_fee(book,q,rate,exp):
    levels=[]
    for a in book.get('asks') or []:
        try:
            p=D(a['price']); sz=D(a['size'])
            if Decimal('0')<p<Decimal('1') and sz>0:levels.append((p,sz))
        except:pass
    levels.sort(key=lambda x:x[0])
    rem=q;cash=Decimal('0');fee=Decimal('0')
    for p,sz in levels:
        take=min(rem,sz)
        cash += take*p
        platform_fee_rate=rate * (p*(Decimal('1')-p))**exp
        fee += take*platform_fee_rate
        rem -= take
        if rem<=0:break
    if rem>0:return None
    return cash,fee,cash+fee

def main():
    started=datetime.now(timezone.utc)
    R={
      'lab_id':'POLY-COMBINATORIAL-ARB-001','mve':'PROSPECTIVE_ECONOMIC_V0.8',
      'started_at_utc':started.isoformat(),'runtime_commit':os.environ.get('GITHUB_SHA'),
      'q_shares':str(Q),'base_buffer_usdc':str(BASE_BUFFER),'stress_buffer_usdc':str(STRESS_BUFFER),
      'max_http_rtt_ms':str(MAX_RTT_MS),'attempts_frozen':ATTEMPTS,'cadence_seconds':CADENCE,
      'authenticated_endpoints_used':False,'orders_sent':False,'capital_used':False,
      'event_meta':{},'snapshots':[],'errors':[]
    }
    all_tokens=[]; event_legs={}
    # Resolve frozen identities.
    for eid in EVENT_IDS:
        data=getj(f'{GAMMA}/events?id={eid}')
        vals=data if isinstance(data,list) else (data.get('data') or data.get('events') or [])
        ev=[x for x in vals if str(x.get('id'))==eid]
        if len(ev)!=1:
            R['errors'].append({'stage':'event_identity','event_id':eid,'error':'UNRESOLVED'})
            continue
        ev=ev[0];legs=[]
        for m in ev.get('markets') or []:
            tok=yes_token(m);cid=str(m.get('conditionId') or m.get('condition_id') or '')
            if not tok or cid not in EXPECTED_FD:
                R['errors'].append({'stage':'leg_identity','event_id':eid,'market_id':m.get('id'),'error':'UNFROZEN_TOKEN_OR_CONDITION'})
                continue
            legs.append({'market_id':str(m.get('id')),'condition_id':cid,'token_id':tok})
            all_tokens.append(tok)
        event_legs[eid]=legs
        R['event_meta'][eid]={'title':ev.get('title'),'endDate':ev.get('endDate'),
                              'market_count':len(ev.get('markets') or []),'leg_count':len(legs),
                              'negRisk':ev.get('negRisk',ev.get('neg_risk')),
                              'negRiskAugmented':ev.get('negRiskAugmented',ev.get('neg_risk_augmented'))}
    all_tokens=list(dict.fromkeys(all_tokens))

    # Fail closed on fee descriptor drift before any orderbook economics.
    drift=[]
    fee_by_condition={}
    for cid,(er,ee) in EXPECTED_FD.items():
        try:
            m=getj(f'{CLOB}/clob-markets/{urllib.parse.quote(cid)}')
            fd=m.get('fd') or {}
            r=D(fd.get('r',0));e=D(fd.get('e',0))
            fee_by_condition[cid]=(r,e)
            if r!=er or e!=ee:drift.append({'condition_id':cid,'expected':[str(er),str(ee)],'observed':[str(r),str(e)]})
        except Exception as ex:
            drift.append({'condition_id':cid,'error':repr(ex)})
    R['fee_descriptor_drift']=drift
    if drift or len(all_tokens)!=25 or any(len(event_legs.get(e,[]))!=R['event_meta'].get(e,{}).get('market_count') for e in EVENT_IDS):
        R['summary']={'pilot_adjudication':'FAIL_CLOSED_IDENTITY_OR_FEE_DRIFT','valid_event_snapshots':0,'positive_stress_observations':0}
        R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        os.makedirs('artifacts',exist_ok=True)
        with open('artifacts/POLY_COMB_PROSPECTIVE_ECONOMIC_V0.8.json','w') as f:json.dump(R,f,indent=2,sort_keys=True)
        print(json.dumps(R['summary'],indent=2));return 0

    payload=[{'token_id':t} for t in all_tokens]
    for k in range(ATTEMPTS):
        target=started.timestamp()+k*CADENCE
        if target>time.time():time.sleep(target-time.time())
        t0=time.perf_counter()
        snap={'attempt':k+1,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'events':{}}
        try:
            books=postj(CLOB+'/books',payload)
            rtt=D((time.perf_counter()-t0)*1000)
            snap['http_roundtrip_ms']=str(rtt)
            if not isinstance(books,list):raise RuntimeError('BOOK_BATCH_NOT_LIST')
            bm={str(b.get('asset_id') or b.get('token_id')):b for b in books if b.get('asset_id') or b.get('token_id')}
            snap['books_returned']=len(bm)
            if rtt>MAX_RTT_MS or len(bm)!=len(all_tokens):
                snap['transport_status']='TRANSPORT_GATE_FAIL'
                R['snapshots'].append(snap);continue
            snap['transport_status']='PASS'
            for eid,legs in event_legs.items():
                er={'leg_count':len(legs)}
                costs=[];provider_ts=[]
                for leg in legs:
                    b=bm.get(leg['token_id'])
                    if not b:
                        er['status']='BOOK_MISSING';break
                    cid=leg['condition_id'];rate,exp=fee_by_condition[cid]
                    c=walk_cost_with_fee(b,Q,rate,exp)
                    if c is None:
                        er['status']='DEPTH_INSUFFICIENT';break
                    costs.append(c)
                    if b.get('timestamp') is not None:provider_ts.append(str(b.get('timestamp')))
                else:
                    cash=sum((x[0] for x in costs),Decimal('0'))
                    fee=sum((x[1] for x in costs),Decimal('0'))
                    total=sum((x[2] for x in costs),Decimal('0'))
                    raw=Q-total;base=raw-BASE_BUFFER;stress=raw-STRESS_BUFFER
                    er.update({
                      'status':'ECONOMICALLY_VALID',
                      'cash_ask_cost':str(cash),'platform_fee_cost':str(fee),'total_cost':str(total),
                      'raw_margin':str(raw),'base_margin':str(base),'stress_margin':str(stress),
                      'positive_raw':raw>0,'positive_base':base>0,'positive_stress':stress>0,
                      'provider_timestamp_min':min(provider_ts) if provider_ts else None,
                      'provider_timestamp_max':max(provider_ts) if provider_ts else None
                    })
                    end=parse_dt(R['event_meta'][eid].get('endDate'))
                    if end and total>0:
                        locked=max(Decimal('1'),D(((end+timedelta(days=7))-datetime.now(timezone.utc)).total_seconds())/D(86400))
                        er['locked_days_stress']=str(locked)
                        er['simple_annualized_stress_yield']=str((stress/total)*D(365)/locked)
                snap['events'][eid]=er
        except Exception as ex:
            snap['request_error']=repr(ex)
        R['snapshots'].append(snap)

    per={};valid_total=0;positive_total=0;pos_events=[];all_pos_margins=[]
    for eid in EVENT_IDS:
        rows=[s.get('events',{}).get(eid,{}) for s in R['snapshots']]
        valid=[r for r in rows if r.get('status')=='ECONOMICALLY_VALID']
        pos=[r for r in valid if r.get('positive_stress')]
        valid_total+=len(valid);positive_total+=len(pos)
        if pos:pos_events.append(eid)
        pm=[D(r['stress_margin']) for r in pos]
        all_pos_margins.extend(pm)
        stress=[D(r['stress_margin']) for r in valid]
        total_cost=[D(r['total_cost']) for r in valid]
        max_consec=0;cur=0
        for r in rows:
            if r.get('positive_stress'):cur+=1;max_consec=max(max_consec,cur)
            else:cur=0
        per[eid]={
          'attempted':len(rows),'valid_snapshots':len(valid),'positive_stress_count':len(pos),
          'positive_base_count':sum(1 for r in valid if r.get('positive_base')),
          'positive_raw_count':sum(1 for r in valid if r.get('positive_raw')),
          'max_stress_margin':str(max(stress)) if stress else None,
          'median_stress_margin':str(median(stress)) if stress else None,
          'min_total_cost':str(min(total_cost)) if total_cost else None,
          'max_consecutive_positive_stress':max_consec
        }
    sufficient=(valid_total>=120 and sum(1 for e in EVENT_IDS if per[e]['valid_snapshots']>=30)>=2)
    if not sufficient:verdict='PILOT_DATA_INSUFFICIENT'
    elif positive_total>0:verdict='PROSPECTIVE_BOOK_EXECUTABLE_SIGNAL_OBSERVED'
    else:verdict='NO_IMMEDIATE_EXECUTABLE_PACKAGE_OBSERVED'
    R['summary']={
      'valid_event_snapshots':valid_total,
      'events_with_at_least_30_valid':sum(1 for e in EVENT_IDS if per[e]['valid_snapshots']>=30),
      'positive_stress_observations':positive_total,
      'distinct_positive_stress_events':pos_events,
      'max_positive_stress_margin':str(max(all_pos_margins)) if all_pos_margins else None,
      'median_positive_stress_margin':str(median(all_pos_margins)) if all_pos_margins else None,
      'per_event':per,
      'pilot_adjudication':verdict
    }
    R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    with open('artifacts/POLY_COMB_PROSPECTIVE_ECONOMIC_V0.8.json','w') as f:json.dump(R,f,indent=2,sort_keys=True)
    print(json.dumps(R['summary'],indent=2,sort_keys=True))
    return 0

if __name__=='__main__':sys.exit(main())
