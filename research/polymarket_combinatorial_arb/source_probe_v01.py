#!/usr/bin/env python3
import hashlib, json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

GAMMA='https://gamma-api.polymarket.com'
CLOB='https://clob.polymarket.com'
UA='CryptoLab-POLY-COMB-SOURCE-GATE/0.1'

def get_json(url, timeout=20):
    req=urllib.request.Request(url, headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw=r.read()
        return json.loads(raw.decode('utf-8')), raw

def sha(b): return hashlib.sha256(b).hexdigest()

def parse_jsonish(x):
    if isinstance(x,(list,dict)): return x
    if isinstance(x,str):
        try: return json.loads(x)
        except Exception: return x
    return x

def main():
    receipt={
      'lab_id':'POLY-COMBINATORIAL-ARB-001','gate':'SOURCE_PROBE_V0.1',
      'started_at_utc':datetime.now(timezone.utc).isoformat(),
      'economic_outputs_computed':False,'profitability_computed':False,
      'orders_sent':False,'authenticated_endpoints_used':False,
      'future_nearest_joins':0,'silent_imputations':0,
      'pages':[],'candidate_events':[],'book_probes':[],'errors':[]
    }
    events=[]
    for offset in (0,100,200):
        url=f'{GAMMA}/events?active=true&closed=false&limit=100&offset={offset}'
        try:
            data,raw=get_json(url)
            receipt['pages'].append({'offset':offset,'sha256':sha(raw),'type':type(data).__name__,'count':len(data) if isinstance(data,list) else None})
            if isinstance(data,list): events.extend(data)
            elif isinstance(data,dict):
                vals=data.get('data') or data.get('events') or []
                if isinstance(vals,list): events.extend(vals)
        except Exception as e:
            receipt['errors'].append({'stage':'gamma_events','offset':offset,'error':repr(e)})
            break

    seen=set(); candidates=[]
    for ev in events:
        eid=str(ev.get('id') or ev.get('eventId') or ev.get('slug') or '')
        if not eid or eid in seen: continue
        seen.add(eid)
        markets=ev.get('markets') or []
        if not isinstance(markets,list) or len(markets)<2: continue
        neg=ev.get('negRisk')
        if neg is None: neg=ev.get('neg_risk')
        token_rows=[]
        for m in markets:
            outs=parse_jsonish(m.get('outcomes'))
            ids=parse_jsonish(m.get('clobTokenIds') or m.get('clob_token_ids'))
            if isinstance(ids,list):
                for i,tok in enumerate(ids):
                    token_rows.append({
                      'token_id':str(tok),
                      'outcome':outs[i] if isinstance(outs,list) and i<len(outs) else None,
                      'condition_id':m.get('conditionId') or m.get('condition_id'),
                      'market_id':m.get('id'),'enable_order_book':m.get('enableOrderBook')
                    })
        if neg is True or len(markets)>=3:
            candidates.append((ev,token_rows))
    candidates=candidates[:20]

    for ev,tokens in candidates:
        receipt['candidate_events'].append({
          'event_id':ev.get('id'),'slug':ev.get('slug'),'title':ev.get('title'),
          'neg_risk':ev.get('negRisk',ev.get('neg_risk')),
          'market_count':len(ev.get('markets') or []),'token_count':len(tokens),
          'token_schema_complete':bool(tokens) and all(t.get('token_id') and t.get('condition_id') for t in tokens)
        })

    probe_tokens=[]
    for ev,tokens in candidates:
        for t in tokens:
            if t.get('token_id') and t['token_id'] not in probe_tokens:
                probe_tokens.append(t['token_id'])
            if len(probe_tokens)>=40: break
        if len(probe_tokens)>=40: break

    for tok in probe_tokens:
        row={'token_id':tok}
        try:
            book,raw=get_json(f'{CLOB}/book?token_id={urllib.parse.quote(tok)}')
            row.update({
              'book_sha256':sha(raw),'bids_count':len(book.get('bids') or []),
              'asks_count':len(book.get('asks') or []),
              'has_tick_size':book.get('tick_size') is not None,
              'has_min_order_size':book.get('min_order_size') is not None,
              'has_timestamp':book.get('timestamp') is not None,
              'neg_risk':book.get('neg_risk')
            })
        except Exception as e: row['book_error']=repr(e)
        try:
            fee,raw=get_json(f'{CLOB}/fee-rate?token_id={urllib.parse.quote(tok)}')
            row.update({
              'fee_sha256':sha(raw),
              'fee_fields':sorted(list(fee.keys())) if isinstance(fee,dict) else [],
              'fee_schema_present':isinstance(fee,dict) and any(k in fee for k in ('base_fee','fee_rate_bps'))
            })
        except Exception as e: row['fee_error']=repr(e)
        receipt['book_probes'].append(row)
        time.sleep(0.05)

    receipt['summary']={
      'events_seen':len(seen),'candidate_event_count':len(candidates),
      'candidate_events_with_tokens':sum(1 for x in receipt['candidate_events'] if x['token_count']>0),
      'books_attempted':len(receipt['book_probes']),
      'books_with_both_sides':sum(1 for x in receipt['book_probes'] if x.get('bids_count',0)>0 and x.get('asks_count',0)>0),
      'books_with_timestamp':sum(1 for x in receipt['book_probes'] if x.get('has_timestamp')),
      'fee_schema_present':sum(1 for x in receipt['book_probes'] if x.get('fee_schema_present')),
      'errors':len(receipt['errors']) + sum(1 for x in receipt['book_probes'] if x.get('book_error') or x.get('fee_error'))
    }
    receipt['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    os.makedirs('artifacts',exist_ok=True)
    out='artifacts/POLY_COMB_SOURCE_PROBE_V0.1.json'
    with open(out,'w',encoding='utf-8') as f: json.dump(receipt,f,indent=2,sort_keys=True)
    print(json.dumps(receipt['summary'],indent=2,sort_keys=True))
    return 0

if __name__=='__main__': sys.exit(main())
