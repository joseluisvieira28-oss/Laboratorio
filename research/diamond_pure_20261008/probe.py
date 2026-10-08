"""Public source and quote-only diagnostic. No exchange authentication or order code."""
import argparse, concurrent.futures, datetime as dt, gzip, hashlib, json, math, pathlib, threading, time, urllib.parse, urllib.request
BASE='https://www.deribit.com/api/v2/public/'
ALLOWED={'get_instruments','get_index_price','get_order_book','get_combo_ids','get_combo_details','get_time'}
ROOT=pathlib.Path(__file__).resolve().parent
LOCK=threading.Lock()

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def dump(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def api(method,params,out):
    if method not in ALLOWED: raise ValueError('endpoint not permitted')
    url=BASE+method+'?'+urllib.parse.urlencode(params)
    key=hashlib.sha256(url.encode()).hexdigest()[:16]
    for attempt in range(2):
        started=utc(); ts=time.time(); rec={'url':url,'request_utc':started,'attempt':attempt+1}
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CryptoLab-PublicResearch/1.0'}),timeout=25) as response:
                raw=response.read(); rec['http_status']=response.status
            rec.update(receive_utc=utc(),rtt_ms=1000*(time.time()-ts),raw_sha256=hashlib.sha256(raw).hexdigest())
            filename=f'{key}-{time.time_ns()}.json.gz'
            (out/filename).write_bytes(gzip.compress(raw,mtime=0)); rec['raw_file']=filename
            obj=json.loads(raw)
            if 'error' in obj: raise ValueError(str(obj['error']))
            with LOCK:
                with (out/'manifest.jsonl').open('a') as f: f.write(json.dumps(rec)+'\n')
            return {'data':obj['result'],'received_ms':int(time.time()*1000),'receipt':rec}
        except Exception as exc:
            rec.update(error=f'{type(exc).__name__}: {exc}',receive_utc=utc())
            with LOCK:
                with (out/'manifest.jsonl').open('a') as f: f.write(json.dumps(rec)+'\n')
            if attempt: return {'error':rec['error'],'receipt':rec}

def payoff(s,k1,k2): return max(s-k1,0)-max(k1-s,0)-max(s-k2,0)+max(k2-s,0)
def fee(index,premium,q,rate=.0003): return min(rate*index,.125*abs(premium))*q

def assess(group,books):
    row={k:v for k,v in group.items() if k!='legs'}; errors=[]
    legs=group['legs']; q=group['quantity']; ts=[]; prices=[]; indices=[]
    for i,(leg,wrapper) in enumerate(zip(legs,books)):
        if 'error' in wrapper: errors.append('transport:'+leg['instrument_name']); continue
        b=wrapper['data']; ts.append(b.get('timestamp',0)); indices.append(b.get('index_price',0))
        if b.get('instrument_name')!=leg['instrument_name']: errors.append('identity')
        if b.get('state')!='open': errors.append('not_open')
        if not b.get('asks') or not b.get('bids'): errors.append('missing_two_sided_book'); continue
        ask,asksize=b['asks'][0]; bid,bidsize=b['bids'][0]
        if not 0<bid<=ask: errors.append('crossed_or_invalid_book')
        side='asks' if i in (0,3) else 'bids'
        p,size=b[side][0]; prices.append(p)
        if size+1e-12<q: errors.append('insufficient_touch_size')
        age=wrapper['received_ms']-b['timestamp']
        if not -1000<=age<=5000: errors.append('quote_age')
        if leg.get('contract_size')!=1 or leg.get('settlement_currency')!='USDC': errors.append('units')
        if not math.isclose(leg.get('taker_commission',-1),.0003,abs_tol=1e-10): errors.append('fee_mismatch')
    if ts and max(ts)-min(ts)>2000: errors.append('noncontemporaneous_quartet')
    row['errors']=sorted(set(errors)); row['quote_span_ms']=max(ts)-min(ts) if ts else None
    row['source_status']='INVALID_SOURCE' if errors else 'VALID_LEG_QUOTE'
    if errors or len(prices)!=4: return row
    debit=q*(prices[0]-prices[1]-prices[2]+prices[3]); face=q*(group['k2']-group['k1'])
    fees=sum(fee(ix,p,q) for ix,p in zip(indices,prices))
    row.update(leg_prices=prices,index_prices=indices,debit_usdc=debit,terminal_gross_payoff_usdc=face,entry_fees_usdc=fees,gross_cashflow_upper_bound_usdc=face-debit,entry_fee_adjusted_upper_bound_usdc=face-debit-fees)
    row['all_cost_net_usdc']=None
    row['atomic_execution_proven']=False
    # Public SM estimate, not a reserve guaranteed to prevent liquidation.
    p1=books[1]['data']; c2=books[2]['data']; ix=sum(indices)/4
    u1=p1.get('underlying_price'); u2=c2.get('underlying_price')
    if u1 and u2:
        put_im=max((.15-max(u1-group['k1'],0)/u1)*p1['index_price'],.1*group['k1'])+p1['mark_price']
        call_im=max(.15-max(group['k2']-u2,0)/u2,.1)*c2['index_price']+c2['mark_price']
        im=q*(put_im+call_im)
        row.update(short_initial_margin_estimate_usdc=im,initial_capital_indication_usdc=debit+fees+im)
        row['annualized_upper_bound_on_initial_capital']=((face-debit-fees)/(debit+fees+im))*365/group['dte'] if debit+fees+im>0 else None
        row['stress_intrinsic_only_short_im_lower_bounds']={}
        for ratio in (.5,1,2):
            s=ix*ratio
            cp=max(.15-max(group['k2']-s,0)/s,.1)*s+max(s-group['k2'],0)
            pp=max((.15-max(s-group['k1'],0)/s)*s,.1*group['k1'])+max(group['k1']-s,0)
            row['stress_intrinsic_only_short_im_lower_bounds'][str(ratio)]=q*(cp+pp)
    row['economic_status']='OBSERVED_LEG_ROUTE_ECONOMIC_REJECT' if face-debit-fees<=0 else 'POSITIVE_UPPER_BOUND_NOT_EXECUTABLE_PROOF'
    return row

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    started=utc(); now=time.time()*1000
    meta=api('get_instruments',{'currency':'USDC','kind':'option','expired':'false'},out)
    combo=api('get_combo_ids',{'currency':'USDC','state':'active'},out)
    if 'error' in meta or 'error' in combo:
        dump(out/'summary.json',{'status':'SOURCE_BLOCKED_TRANSPORT','started_utc':started}); return
    universe=[x for x in meta['data'] if x['instrument_name'].startswith(('BTC_USDC-','ETH_USDC-'))]
    groups=[]
    for asset in ('BTC','ETH'):
        index=api('get_index_price',{'index_name':asset.lower()+'_usdc'},out)
        if 'error' in index: continue
        ix=index['data']['index_price']
        expiries=sorted({x['expiration_timestamp'] for x in universe if x['instrument_name'].startswith(asset+'_') and 30<=(x['expiration_timestamp']-now)/86400000<=120})
        for expiry in expiries:
            cells={(x['strike'],x['option_type']):x for x in universe if x['instrument_name'].startswith(asset+'_') and x['expiration_timestamp']==expiry}
            ks=sorted(k for k,t in cells if t=='call' and (k,'put') in cells)
            if not ks: continue
            k1=min(ks,key=lambda k:(abs(k-.9*ix),k)); k2=min(ks,key=lambda k:(abs(k-1.1*ix),k))
            if k1>=k2: continue
            legs=[cells[k1,'call'],cells[k1,'put'],cells[k2,'call'],cells[k2,'put']]
            q=max(x['min_trade_amount'] for x in legs)
            groups.append({'asset':asset,'expiry':expiry,'dte':(expiry-now)/86400000,'k1':k1,'k2':k2,'quantity':q,'legs':legs,'instruments':[x['instrument_name'] for x in legs]})
    dump(out/'selected_geometry.json',groups)
    boxids=[x for x in combo['data'] if '-BOX-' in x and x.startswith(('BTC_USDC-','ETH_USDC-'))]
    combo_evidence=[]
    for name in boxids:
        details=api('get_combo_details',{'combo_id':name},out)
        book=api('get_order_book',{'instrument_name':name,'depth':5},out)
        combo_evidence.append({'name':name,'details':details,'book':book})
    dump(out/'atomic_combo_evidence.json',combo_evidence)
    rows=[]
    for snapshot in (1,2):
        for group in groups:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                books=list(pool.map(lambda leg:api('get_order_book',{'instrument_name':leg['instrument_name'],'depth':5},out),group['legs']))
            row=assess(group,books); row['snapshot']=snapshot; rows.append(row)
            dump(out/'quote_diagnostics.json',rows)
    valid=[r for r in rows if r['source_status']=='VALID_LEG_QUOTE']
    summary={'experiment':'BOX-FINANCING-USDC-001','started_utc':started,'finished_utc':utc(),'active_usdc_option_count':len(meta['data']),'btc_eth_option_count':len(universe),'active_usdc_combo_count':len(combo['data']),'active_btc_eth_box_count':len(boxids),'selected_geometries':len(groups),'quote_snapshots':len(rows),'valid_leg_snapshots':len(valid),'positive_entry_fee_upper_bounds':sum(r['entry_fee_adjusted_upper_bound_usdc']>0 for r in valid),'status':'SOURCE_BLOCKED_ATOMIC_EXECUTION' if not boxids else 'ATOMIC_CANDIDATES_REQUIRE_DETAILS_REVIEW','economic_leg_verdict':'OBSERVED_LEG_ROUTE_ECONOMIC_REJECT' if valid and all(r['entry_fee_adjusted_upper_bound_usdc']<=0 for r in valid) else 'INCONCLUSIVE','future_outcomes_opened':False,'trades_executed':0,'independent_realised_observations':0,'pf':None,'drawdown':None,'all_cost_expected_profit':None,'freeze_commit':'f2591d34f9d7ce2949d2f209dde65653be04bc8f'}
    dump(out/'summary.json',summary); print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=pathlib.Path,required=True); args=p.parse_args(); run(args.out)
