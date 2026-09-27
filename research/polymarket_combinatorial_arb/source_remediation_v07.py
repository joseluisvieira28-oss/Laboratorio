#!/usr/bin/env python3
import hashlib, json, math, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

GAMMA='https://gamma-api.polymarket.com'
CLOB='https://clob.polymarket.com'
WS='wss://ws-subscriptions-clob.polymarket.com/ws/market'
UA='CryptoLab-POLY-COMB-REMEDIATION/0.7'
PIN='292c11005d748c21342a9457d7c0ac89afc2e3f2'
EVENT_IDS=['32228','48292','51456']

PINNED_FILES={
 'client.py':f'https://raw.githubusercontent.com/Polymarket/py-clob-client-v2/{PIN}/py_clob_client_v2/client.py',
 'fees.py':f'https://raw.githubusercontent.com/Polymarket/py-clob-client-v2/{PIN}/py_clob_client_v2/fees.py',
 'endpoints.py':f'https://raw.githubusercontent.com/Polymarket/py-clob-client-v2/{PIN}/py_clob_client_v2/endpoints.py',
}

def rawget(url,accept='*/*'):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':accept})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def getj(url):
    raw=rawget(url,'application/json'); return json.loads(raw.decode()), raw
def postj(url,obj):
    data=json.dumps(obj,separators=(',',':')).encode()
    req=urllib.request.Request(url,data=data,method='POST',headers={'User-Agent':UA,'Accept':'application/json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=25) as r:
        raw=r.read()
    return json.loads(raw.decode()),raw
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
    z=[str(t) for o,t in zip(outs,ids) if str(o).strip().lower()=='yes']
    return z[0] if len(z)==1 else None
def finite_num(x):
    try:return math.isfinite(float(x))
    except:return False
def sanitized_book(b):
    return {
      'asset_id':str(b.get('asset_id') or b.get('token_id') or ''),
      'hash':b.get('hash'),
      'timestamp':b.get('timestamp'),
      'bid_levels':len(b.get('bids') or []),
      'ask_levels':len(b.get('asks') or []),
    }
def extract_ws_books(obj):
    out=[]
    items=obj if isinstance(obj,list) else [obj]
    for m in items:
        if not isinstance(m,dict):continue
        typ=m.get('event_type') or m.get('type')
        # Initial book events contain bids/asks and asset_id.
        if typ=='book' or ('asset_id' in m and ('bids' in m or 'asks' in m)):
            out.append(sanitized_book(m))
    return out

def main():
    R={
      'lab_id':'POLY-COMBINATORIAL-ARB-001','gate':'SOURCE_REMEDIATION_V0.7',
      'started_at_utc':datetime.now(timezone.utc).isoformat(),
      'economic_outputs_computed':False,'prices_serialized':False,'sizes_serialized':False,
      'package_sums_computed':False,'fee_dollars_computed':False,'arbitrage_labels_computed':False,
      'authenticated_endpoints_used':False,'orders_sent':False,'capital_used':False,
      'pinned_client_commit':PIN,'pinned_sources':{},'events':{},'conditions':{},'rest_books':{},'ws_books':{},
      'errors':[]
    }

    # Pin first-party semantics.
    source_ok=True
    for name,url in PINNED_FILES.items():
        try:
            raw=rawget(url)
            txt=raw.decode('utf-8','replace')
            checks={}
            if name=='client.py':
                checks={'uses_clob_market': 'GET_CLOB_MARKET' in txt,
                        'uses_fd_rate': 'rate=fd.get("r", 0.0)' in txt,
                        'uses_fd_exponent': 'exponent=fd.get("e", 0.0)' in txt}
            elif name=='fees.py':
                checks={'has_adjust_buy_amount_for_fees':'def adjust_buy_amount_for_fees' in txt,
                        'price_dependent_platform_fee':'(price * (1 - price)) ** fee_exponent' in txt}
            else:
                checks={'clob_market_endpoint':'GET_CLOB_MARKET = "/clob-markets/"' in txt,
                        'book_endpoint':'GET_ORDER_BOOK = "/book"' in txt}
            R['pinned_sources'][name]={'url':url,'sha256':h(raw),'bytes':len(raw),'checks':checks}
            source_ok &= all(checks.values())
        except Exception as e:
            source_ok=False;R['errors'].append({'stage':'pinned_source','name':name,'error':repr(e)})
    R['pinned_client_semantics_pass']=source_ok

    all_tokens=[]; token_condition={}; condition_tokens={}
    for eid in EVENT_IDS:
        try:
            data,_=getj(f'{GAMMA}/events?id={eid}')
            vals=data if isinstance(data,list) else (data.get('data') or data.get('events') or [])
            ev=[x for x in vals if str(x.get('id'))==eid]
            if len(ev)!=1: raise RuntimeError('EVENT_ID_UNRESOLVED')
            ev=ev[0];rows=[]
            for m in ev.get('markets') or []:
                t=yes_token(m); cid=str(m.get('conditionId') or m.get('condition_id') or '')
                if not t or not cid: raise RuntimeError(f'TOKEN_OR_CONDITION_UNRESOLVED:{m.get("id")}')
                rows.append({'market_id':str(m.get('id')),'condition_id':cid,'yes_token_id':t})
                all_tokens.append(t);token_condition[t]=cid
                condition_tokens.setdefault(cid,[]).append(t)
            R['events'][eid]={'market_count':len(rows),'rows':rows}
        except Exception as e:
            R['errors'].append({'stage':'gamma_identity','event_id':eid,'error':repr(e)})
    all_tokens=list(dict.fromkeys(all_tokens))
    all_conditions=list(dict.fromkeys(token_condition.values()))

    # Fee descriptor provenance, no prices.
    fee_ok=source_ok and bool(all_conditions)
    for cid in all_conditions:
        row={'condition_id':cid}
        try:
            meta,_=getj(f'{CLOB}/clob-markets/{urllib.parse.quote(cid)}')
            fd=meta.get('fd')
            toks=meta.get('t') or []
            returned_ids=[]
            for t in toks:
                if isinstance(t,dict) and t.get('t') is not None: returned_ids.append(str(t.get('t')))
            if fd is None:
                rate=0.0; exponent=0.0; source='official_client_default'
                valid=True
            elif isinstance(fd,dict):
                rate=fd.get('r'); exponent=fd.get('e');source='clob_market_fd'
                valid=finite_num(rate) and finite_num(exponent)
            else:
                rate=exponent=None;source='invalid_fd_type';valid=False
            expected=sorted(condition_tokens.get(cid,[]))
            mapping=all(t in returned_ids for t in expected)
            row.update({'fd':fd,'interpreted_rate_source_value':rate,'interpreted_exponent_source_value':exponent,
                        'fd_source':source,'nr':meta.get('nr'),'mts':meta.get('mts'),
                        'returned_token_ids':returned_ids,'expected_yes_token_ids':expected,
                        'token_mapping_pass':mapping,'fee_descriptor_valid':valid})
            fee_ok &= valid and mapping
        except Exception as e:
            fee_ok=False;row['error']=repr(e)
        R['conditions'][cid]=row
    R['fee_provenance_pass']=fee_ok and len(R['conditions'])==len(all_conditions)

    # One current REST batch. Store only hashes/timestamps/counts.
    rest_ok=False
    try:
        books,_=postj(CLOB+'/books',[{'token_id':t} for t in all_tokens])
        if not isinstance(books,list):raise RuntimeError('REST_BOOK_BATCH_NOT_LIST')
        for b in books:
            s=sanitized_book(b)
            if s['asset_id']:R['rest_books'][s['asset_id']]=s
        rest_ok=(len(R['rest_books'])==len(all_tokens))
    except Exception as e:
        R['errors'].append({'stage':'rest_books','error':repr(e)})

    # Public websocket. No auth. Keep only state identity, not prices/sizes.
    ws_ok=False
    try:
        import websocket
        sock=websocket.create_connection(WS,timeout=8,header=[f'User-Agent: {UA}'])
        sub={'assets_ids':all_tokens,'type':'market','custom_feature_enabled':True}
        sock.send(json.dumps(sub,separators=(',',':')))
        deadline=time.time()+30
        next_ping=time.time()+8
        while time.time()<deadline and len(R['ws_books'])<len(all_tokens):
            if time.time()>=next_ping:
                try:sock.send('PING')
                except:pass
                next_ping=time.time()+8
            try:
                msg=sock.recv()
            except Exception:
                continue
            recv=datetime.now(timezone.utc).isoformat()
            if not isinstance(msg,str) or not msg or msg=='PONG':continue
            try:obj=json.loads(msg)
            except:continue
            for s in extract_ws_books(obj):
                aid=s.get('asset_id')
                if aid in all_tokens:
                    s['local_receive_utc']=recv
                    R['ws_books'][aid]=s
        sock.close()
        ws_ok=(len(R['ws_books']) >= math.ceil(0.95*len(all_tokens)))
    except Exception as e:
        R['errors'].append({'stage':'websocket','error':repr(e)})

    common=sorted(set(R['rest_books']).intersection(R['ws_books']))
    equal=0;newer_ws=0;mismatch=0
    comparisons=[]
    for t in common:
        a=R['rest_books'][t];b=R['ws_books'][t]
        same=bool(a.get('hash')) and a.get('hash')==b.get('hash')
        if same:equal+=1
        else:
            mismatch+=1
            try:
                if int(b.get('timestamp'))>=int(a.get('timestamp')):newer_ws+=1
            except:pass
        comparisons.append({'asset_id':t,'hash_equal':same,
                            'rest_timestamp':a.get('timestamp'),'ws_timestamp':b.get('timestamp'),
                            'ws_not_older_than_rest': (int(b.get('timestamp'))>=int(a.get('timestamp')))
                              if str(b.get('timestamp','')).isdigit() and str(a.get('timestamp','')).isdigit() else None})
    R['book_state_comparisons']=comparisons
    ncommon=len(common)
    hash_ratio=(equal/ncommon) if ncommon else 0.0
    newer_or_equal_ratio=((equal+newer_ws)/ncommon) if ncommon else 0.0
    sync_ok=rest_ok and ws_ok and ncommon>=math.ceil(.95*len(all_tokens)) and (hash_ratio>=.95 or newer_or_equal_ratio>=.95)
    R['sync_source_pass']=sync_ok
    R['summary']={
      'frozen_yes_tokens':len(all_tokens),'frozen_conditions':len(all_conditions),
      'fee_provenance_pass':R['fee_provenance_pass'],
      'rest_books_received':len(R['rest_books']),'ws_books_received':len(R['ws_books']),
      'common_book_states':ncommon,'hash_equal_count':equal,'hash_equal_ratio':hash_ratio,
      'ws_newer_mismatch_count':newer_ws,'current_state_compatible_ratio':newer_or_equal_ratio,
      'sync_source_pass':sync_ok,
    }
    R['source_remediation_pass']=bool(R['fee_provenance_pass'] and sync_ok)
    R['status']='SOURCE_REMEDIATION_PASS' if R['source_remediation_pass'] else 'SOURCE_REMEDIATION_BLOCKED'
    R['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    with open('artifacts/POLY_COMB_SOURCE_REMEDIATION_V0.7.json','w') as f:json.dump(R,f,indent=2,sort_keys=True)
    print(json.dumps({'status':R['status'],**R['summary']},indent=2,sort_keys=True))
    return 0

if __name__=='__main__':sys.exit(main())
