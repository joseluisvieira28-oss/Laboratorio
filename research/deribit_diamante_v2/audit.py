"""Independent Decimal reconstruction; does not import primary code.
Closed-form piecewise delivery-fee roots vs probe's numerical bisection.
Original artifact and new raw bodies required, never trusts primary BBO fields.
"""
import argparse
import datetime as dt
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path

ORIGINAL={
 'btc_usdc_index':'b43dfbd3044606e37e31bbb12c8c7cc92d4cf8ab8da8e28145ed3c19802ecd22',
 'btc_usdc_linear_option_summaries':'5134d63d0f602ee8271208eb7a141c2e78ab2f53ebfc302bacc8089751d1cac7',
 'call_selected_option_book':'88e505bbe2a4df33fa8fcc903efd22a0160d97679f18c21968181ac9a592616b',
 'put_selected_option_book':'ef8bcb5d6040c80f445d5a9b552356d33d36028ed3307f72640d6bb7011c3cce'}
Q=D('.01')

def num(x):
    n=D(str(x)); assert n.is_finite();return n

def read(path, sha):
    raw=Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==sha,'RAW_HASH_MISMATCH'
    x=json.loads(raw,parse_float=D)
    assert x.get('testnet') is False and 'error' not in x
    return x['result']

def close(a,b):
    assert abs(num(a)-num(b))<D('0.00000001'),(str(a),str(b))

def fees(price,index):
    return Q*min(num(index)*D('.0003'),num(price)/8)

def original(root):
    root=Path(root)
    r={k:read(root/('ORIGINAL_'+k+'.json'),v) for k,v in ORIGINAL.items()}
    index=r['btc_usdc_index']['index_price']
    books=[r[s+'_selected_option_book'] for s in ['call','put']]
    a=[min(b['asks'])[0] for b in books];bid=[max(b['bids'])[0] for b in books]
    for b in books:
        assert b['state']=='open' and b['instrument_name'] in {'BTC_USDC-6NOV26-78000-C','BTC_USDC-6NOV26-78000-P'}
        assert min(min(b['asks'])[1],max(b['bids'])[1])>=Q
    cost=Q*(sum(a)-sum(bid))+sum(fees(p,index) for p in a+bid)
    close(cost,'1.33490044')
    receipt=json.loads((root/'receipt.json').read_text())
    for item in receipt['http_sources']:
        assert item['raw_body_sha256']==ORIGINAL[item['name']]
    selection=dt.datetime.fromisoformat(receipt['frozen_candidate_selection_time_utc'].replace('Z','+00:00'))
    pairs={}
    for s in r['btc_usdc_linear_option_summaries']:
        parts=s['instrument_name'].split('-')
        if len(parts)!=4 or parts[0]!='BTC_USDC':continue
        expiry=dt.datetime.strptime(parts[1],'%d%b%y').replace(hour=8,tzinfo=dt.timezone.utc)
        days=D(str((expiry-selection).total_seconds()))/86400
        strike=D(parts[2]);b=s.get('bid_price');a_=s.get('ask_price')
        if not (3<=days<=14 and abs(strike/index-1)<=D('.025')):continue
        if b is None or a_ is None or not (0<num(b)<num(a_)):continue
        pairs.setdefault((expiry,strike),{})[parts[3]]=s['instrument_name']
    valid=[(abs(D(str((e-selection).total_seconds()))/86400-7),abs(k/index-1),e,k,v)
           for (e,k),v in pairs.items() if set(v)=={'C','P'}]
    chosen=min(valid,key=lambda x:x[:4])[-1]
    assert len(valid)==12 and set(chosen.values())=={b['instrument_name'] for b in books}
    return dict(original_sha_verified=4,original_frictions_usdc=str(cost),selection_reconstructed=True)

def decode(root):
    root=Path(root)
    manifest=json.loads((root/'manifest.json').read_text())
    sources={i['name']:read(root/(i['name']+'.json'),i['sha256']) for i in manifest}
    return sources,manifest

def leg_from_raw(book,meta,item,expiry):
    assert book['instrument_name']==meta['instrument_name'] and book['state']=='open'
    assert meta['base_currency']=='BTC' and meta['kind']=='option'
    assert meta['price_index']=='btc_usdc' and meta['quote_currency']==meta['settlement_currency']=='USDC'
    assert meta['contract_size']==1 and num(meta['min_trade_amount'])==Q and meta['is_active'] is True
    assert meta['expiration_timestamp']==int(dt.datetime.fromisoformat(expiry).timestamp()*1000)
    age=dt.datetime.fromisoformat(item['received']).timestamp()-book['timestamp']/1000
    assert -3<=age<=10,'AUDIT_STALE_BOOK'
    bids=[(num(p),num(q)) for p,q in book['bids']];asks=[(num(p),num(q)) for p,q in book['asks']]
    bid=max(bids);ask=min(asks)
    assert 0<bid[0]<ask[0] and min(bid[1],ask[1])>=Q,'AUDIT_DEPTH'
    tick=num(meta['tick_size'])
    for step in sorted(meta.get('tick_size_steps',[]),key=lambda x:x['above_price']):
        if ask[0]>num(step['above_price']):tick=num(step['tick_size'])
    return dict(bid=bid[0],ask=ask[0],tick=tick,index=num(book['index_price']),
                strike=num(meta['strike']),side=meta['option_type'],expiry=expiry)

def amount(legs,ticks=0,factor=D(1)):
    return sum(Q*(l['ask']+ticks*l['tick'])+factor*fees(l['ask']+ticks*l['tick'],l['index']) for l in legs)

def pnl(legs,s,ticks=0,factor=D(1)):
    s=num(s);assert s>0
    gross=delivery=D(0)
    for l in legs:
        v=max(s-l['strike'],D(0)) if l['side']=='call' else max(l['strike']-s,D(0))
        gross+=Q*v
        if dt.datetime.fromisoformat(l['expiry']).weekday()==4:
            delivery+=Q*min(D('.00015')*s,v/8)
    return gross,delivery,gross-delivery-amount(legs,ticks,factor)

def analytical_roots(legs,ticks=0):
    # Straddle or non-overlapping OTM strangle: only one leg ITM at either root.
    cost=amount(legs,ticks)/Q
    friday=dt.datetime.fromisoformat(legs[0]['expiry']).weekday()==4
    kc=next(l['strike'] for l in legs if l['side']=='call')
    kp=next(l['strike'] for l in legs if l['side']=='put')
    assert kp<=kc
    if not friday:return [kp-cost,kc+cost]
    down=[(kp-cost)/(1+D('.00015')),kp-cost/(1-D('.125'))]
    up=[(kc+cost)/(1-D('.00015')),kc+cost/(1-D('.125'))]
    return [next(s for s in down if abs(pnl(legs,s,ticks)[2])<D('1e-20')),
            next(s for s in up if abs(pnl(legs,s,ticks)[2])<D('1e-20'))]

def fresh(root):
    sources,manifest=decode(root)
    receipt=json.loads((Path(root)/'receipt.json').read_text())
    assert receipt['status']=='FEASIBILITY_ONLY_NO_FORWARD_OUTCOME', receipt
    metas={m['instrument_name']:m for m in sources['instruments']}
    idx=num(sources['index']['index_price'])
    expiry=receipt['expiry'];expected_ms=int(dt.datetime.fromisoformat(expiry).timestamp()*1000)
    pool=[m for m in sources['instruments'] if m['instrument_name'].startswith('BTC_USDC-') and m['expiration_timestamp']==expected_ms]
    bystrike={}
    for m in pool:bystrike.setdefault(num(m['strike']),{})[m['option_type']]=m
    k=min((k for k,v in bystrike.items() if set(v)=={'call','put'}),key=lambda k:(abs(k-idx),k))
    choices={'atm_call':bystrike[k]['call'],'atm_put':bystrike[k]['put']}
    for side,target,key in [('put',D('.98'),'otm_put'),('call',D('1.02'),'otm_call')]:
        valid=[m for m in pool if m['option_type']==side and (num(m['strike'])<idx if side=='put' else num(m['strike'])>idx)]
        choices[key]=min(valid,key=lambda m:(abs(num(m['strike'])-target*idx),num(m['strike'])))
    assert receipt['chosen']=={k:v['instrument_name'] for k,v in choices.items()},'SELECTION_MISMATCH'
    times=[sources[k]['timestamp'] for k in choices]
    assert max(times)-min(times)<=3000,'AUDIT_SKEW'
    results={}
    for name,keys in [('straddle',['atm_call','atm_put']),('strangle',['otm_call','otm_put'])]:
        legs=[leg_from_raw(sources[k],choices[k],next(i for i in manifest if i['name']==k),expiry) for k in keys]
        primary=receipt['structures'][name]
        premium=sum(l['ask'] for l in legs)*Q
        exitvalue=sum(l['bid'] for l in legs)*Q
        entryfee=sum(fees(l['ask'],l['index']) for l in legs)
        exitfee=sum(fees(l['bid'],l['index']) for l in legs)
        expected=dict(entry_premium=premium,entry_fee=entryfee,entry_allin=amount(legs),
                      immediate_bid_proceeds=exitvalue,exit_fee=exitfee,spread=premium-exitvalue,
                      roundtrip_loss=premium-exitvalue+entryfee+exitfee,
                      one_tick_allin=amount(legs,1),stress_allin=amount(legs,2,D('1.5')))
        for key,value in expected.items():close(value,primary[key])
        for tickcount,field in [(0,'expiry_breakeven'),(1,'expiry_breakeven_one_tick')]:
            for a,b in zip(analytical_roots(legs,tickcount),primary[field]):close(a,b)
        for row in primary['scenarios']:
            g,d,n=pnl(legs,row['terminal']);close(g,row['gross']);close(d,row['delivery']);close(n,row['net'])
            close(pnl(legs,row['terminal'],1)[2],row['net_one_tick'])
            close(pnl(legs,row['terminal'],2,D('1.5'))[2],row['net_stress'])
        results[name]={k:str(v) for k,v in expected.items()}
        results[name]['analytical_expiry_roots']=[str(x) for x in analytical_roots(legs)]
    return dict(new_raw_sha_verified=len(manifest),independent_selection=True,
                independent_decimal_costs_and_closed_form_roots=results)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original',required=True);p.add_argument('--fresh',required=True);p.add_argument('--out',required=True)
    a=p.parse_args()
    out=dict(original(a.original),**fresh(a.fresh),status='INDEPENDENT_SOURCE_AND_MATH_PASS_NOT_ECONOMIC_EDGE',
             economic_edge_proven=False,simulation=True)
    Path(a.out).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))
