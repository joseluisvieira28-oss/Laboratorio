"""Public, bounded source observation. No credentials, private endpoints or orders.

probe: same-session 6Nov straddle/strangle feasibility, NOT prospective PnL.
entry: first prospective decision in frozen 08:05..08:10 UTC window.
settle: official delivery only, immutable entry required, no mark substitution.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import urllib.parse
import urllib.request

FREEZE = 'e34ad0732abf1574735006b33307ddf5653fbaa9'
UTC = dt.timezone.utc
Q = .01
BASE = 'https://www.deribit.com/api/v2/public/'

def stamp():
    return dt.datetime.now(UTC).isoformat()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save(path, data):
    raw = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    with Path(path).open('xb') as f:
        f.write(raw)
    return digest(raw)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        raise ValueError('REDIRECT_REFUSED')

class Source:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.manifest = []

    def get(self, name, method, **params):
        assert method in {'get_instruments', 'get_index_price', 'get_book_summary_by_currency',
                          'get_delivery_prices', 'get_order_book'}
        assert len(self.manifest) < 8
        url = BASE+method+'?'+urllib.parse.urlencode(params)
        item = dict(name=name, url=url, started=stamp())
        self.manifest.append(item)
        request = urllib.request.Request(url, headers={'Accept':'application/json',
                                                     'User-Agent':'CryptoLab-Deribit-V2-Public-Research'})
        with urllib.request.build_opener(NoRedirect).open(request, timeout=15) as r:
            assert r.status == 200
            raw = r.read(12_000_001)
        item.update(received=stamp(), sha256=digest(raw), bytes=len(raw))
        assert 0 < len(raw) <= 12_000_000
        (self.root/(name+'.json')).write_bytes(raw)
        j = json.loads(raw)
        assert j.get('testnet') is False and 'result' in j and 'error' not in j
        return j['result']

def tick(meta, price):
    value = float(meta['tick_size'])
    for s in sorted(meta.get('tick_size_steps', []), key=lambda x:x['above_price']):
        if price > s['above_price']:
            value = float(s['tick_size'])
    assert value > 0
    return value

def fee(price, index, factor=1):
    return factor*Q*min(.0003*index, .125*price)

def metadata(m, expiry):
    expected = dict(kind='option', base_currency='BTC', quote_currency='USDC',
                    settlement_currency='USDC', price_index='btc_usdc')
    assert all(m.get(k) == v for k,v in expected.items()), 'METADATA_IDENTITY'
    assert m['instrument_name'].startswith('BTC_USDC-') and m['is_active'] is True
    assert m['contract_size'] == 1 and m['min_trade_amount'] == .01, 'SIZE_OR_STEP'
    assert abs(Q / m['min_trade_amount'] - round(Q / m['min_trade_amount'])) < 1e-9
    assert m['expiration_timestamp'] == int(expiry.timestamp()*1000), 'EXPIRY'
    if 'instrument_type' in m:
        assert m['instrument_type'] == 'linear'

def bookcheck(b, m, received, depth=.01):
    assert b['instrument_name'] == m['instrument_name'] and b['state'] == 'open', 'BOOK_STATE'
    age = dt.datetime.fromisoformat(received).timestamp() - b['timestamp']/1000
    assert -3 <= age <= 10, 'STALE_OR_FUTURE_BOOK'
    bid = max(b['bids'], key=lambda x:x[0]); ask = min(b['asks'], key=lambda x:x[0])
    assert all(math.isfinite(float(x)) for row in b['bids']+b['asks'] for x in row)
    assert 0 < bid[0] < ask[0] and min(bid[1],ask[1]) >= depth, 'PRICE_OR_DEPTH'
    assert math.isfinite(b['index_price']) and b['index_price'] > 0
    return dict(symbol=b['instrument_name'], bid=bid[0], ask=ask[0], bid_depth=bid[1],
                ask_depth=ask[1], index=b['index_price'], timestamp=b['timestamp'],
                age=age, tick=tick(m,ask[0]), strike=m['strike'], side=m['option_type'],
                expiry=dt.datetime.fromtimestamp(m['expiration_timestamp']/1000,UTC).isoformat())

def cost(legs, ticks=0, factor=1):
    return sum(Q*(x['ask']+ticks*x['tick'])+fee(x['ask']+ticks*x['tick'],x['index'],factor) for x in legs)

def payout(legs, terminal):
    assert math.isfinite(terminal) and terminal > 0
    gross = delivery = 0
    for x in legs:
        v = max(terminal-x['strike'],0) if x['side']=='call' else max(x['strike']-terminal,0)
        gross += Q*v
        friday = dt.datetime.fromisoformat(x['expiry']).weekday()==4
        delivery += Q*min(.00015*terminal,.125*v) if friday else 0
    return gross, delivery

def net(legs, terminal, ticks=0, factor=1):
    g,d = payout(legs,terminal)
    return g-d-cost(legs,ticks,factor)

def roots(legs, ticks=0):
    lo,hi=1.,min(x['strike'] for x in legs)
    if net(legs,lo,ticks)<0:
        down=None
    else:
        for _ in range(90):
            mid=(lo+hi)/2
            if net(legs,mid,ticks)>0: lo=mid
            else: hi=mid
        down=(lo+hi)/2
    lo,hi=max(x['strike'] for x in legs),10*max(x['strike'] for x in legs)
    assert net(legs,hi,ticks)>0
    for _ in range(90):
        mid=(lo+hi)/2
        if net(legs,mid,ticks)>0: hi=mid
        else: lo=mid
    return [down,(lo+hi)/2]

def economics(legs, index):
    premium=Q*sum(x['ask'] for x in legs)
    bid=Q*sum(x['bid'] for x in legs)
    entry=cost(legs)-premium
    exit_fee=sum(fee(x['bid'],x['index']) for x in legs)
    return dict(legs=legs, entry_premium=premium, entry_fee=entry, entry_allin=cost(legs),
                immediate_bid_proceeds=bid, exit_fee=exit_fee, spread=premium-bid,
                roundtrip_loss=premium-bid+entry+exit_fee,
                roundtrip_pct=100*(premium-bid+entry+exit_fee)/premium,
                one_tick_allin=cost(legs,1), stress_allin=cost(legs,2,1.5),
                expiry_breakeven=roots(legs), expiry_breakeven_one_tick=roots(legs,1),
                scenarios=[dict(terminal=s, gross=payout(legs,s)[0], delivery=payout(legs,s)[1],
                                net=net(legs,s), net_one_tick=net(legs,s,1), net_stress=net(legs,s,2,1.5))
                           for s in sorted(set([70000.,75000.,78000.,81000.,85000.,index]))])

def forecast(deliveries, day, index, horizon, legs):
    cutoff=day.date()
    rows={dt.date.fromisoformat(x['date']):float(x['delivery_price']) for x in deliveries['data']
          if dt.date.fromisoformat(x['date'])<=cutoff}
    dates=[cutoff-dt.timedelta(days=i) for i in reversed(range(61))]
    assert all(d in rows and math.isfinite(rows[d]) and rows[d]>0 for d in dates), 'MISSING_61_CONSECUTIVE_DELIVERIES'
    returns=[math.log(rows[b]/rows[a]) for a,b in zip(dates,dates[1:])]
    mean=statistics.mean(returns)
    multipliers=[math.exp((x-mean)*math.sqrt(horizon/86400)) for x in returns]
    avg=statistics.mean(multipliers)
    terminals=[index*x/avg for x in multipliers]
    value=statistics.mean(payout(legs,s)[0]-payout(legs,s)[1] for s in terminals)
    return dict(input_dates=[d.isoformat() for d in dates], prior_log_returns=returns,
                lagged_annualized_vol=statistics.stdev(returns)*math.sqrt(365),
                forecast_net_proceeds=value, ratio=value/cost(legs,1),
                selected=value>=1.2*cost(legs,1), historical_options_backtest=False)

def select(meta, index, expiry, mode):
    pool=[x for x in meta if x['instrument_name'].startswith('BTC_USDC-') and
          x.get('expiration_timestamp')==int(expiry.timestamp()*1000)]
    pairs={}
    for x in pool:
        pairs.setdefault(x['strike'],{})[x['option_type']]=x
    strikes=[k for k,v in pairs.items() if set(v)=={'call','put'}]
    assert strikes, 'NO_COMPLETE_ATM_PAIR'
    atm=min(strikes,key=lambda k:(abs(k-index),k))
    out={'atm_call':pairs[atm]['call'],'atm_put':pairs[atm]['put']}
    if mode=='probe':
        puts=[x for x in pool if x['option_type']=='put' and x['strike']<index]
        calls=[x for x in pool if x['option_type']=='call' and x['strike']>index]
        assert puts and calls, 'NO_OTM_PAIR'
        out['otm_call']=min(calls,key=lambda x:(abs(x['strike']-1.02*index),x['strike']))
        out['otm_put']=min(puts,key=lambda x:(abs(x['strike']-.98*index),x['strike']))
    return out

def collect(root, mode):
    t=dt.datetime.now(UTC)
    if mode=='entry':
        assert t.date()>=dt.date(2026,11,3) and t.hour==8 and 5<=t.minute<10, 'OUTSIDE_FROZEN_ENTRY_WINDOW'
    source=Source(root)
    receipt=dict(freeze=FREEZE, mode=mode, observed=stamp(), status='SOURCE_BLOCKED',
                 economic_edge_proven=False, simulation=True, orders=0, private_requests=0)
    try:
        expiry=dt.datetime(2026,11,6,8,tzinfo=UTC) if mode=='probe' else t.replace(hour=8,minute=0,second=0,microsecond=0)+dt.timedelta(days=1)
        assert t<expiry
        metas=source.get('instruments','get_instruments',currency='USDC',kind='option',expired='false')
        index=source.get('index','get_index_price',index_name='btc_usdc')['index_price']
        source.get('summaries','get_book_summary_by_currency',currency='USDC',kind='option')
        deliveries=source.get('deliveries','get_delivery_prices',index_name='btc_usdc',count=100)
        chosen=select(metas,index,expiry,mode)
        receipt.update(index=index, expiry=expiry.isoformat(), chosen={k:v['instrument_name'] for k,v in chosen.items()})
        legs={}
        for key,m in chosen.items():
            metadata(m,expiry)
            b=source.get(key,'get_order_book',instrument_name=m['instrument_name'],depth=5)
            legs[key]=bookcheck(b,m,source.manifest[-1]['received'],.05 if mode=='entry' else .01)
        times=[x['timestamp'] for x in legs.values()]
        assert max(times)-min(times)<= (1000 if mode=='entry' else 3000), 'ASYNCHRONOUS_BOOKS'
        index_time=dt.datetime.fromisoformat(next(x['received'] for x in source.manifest if x['name']=='index')).timestamp()
        assert abs(max(times)/1000-index_time)<=10, 'INDEX_TOO_OLD'
        receipt['structures']={'straddle':economics([legs['atm_call'],legs['atm_put']],index)}
        if mode=='probe':
            receipt['structures']['strangle']=economics([legs['otm_call'],legs['otm_put']],index)
            receipt['status']='FEASIBILITY_ONLY_NO_FORWARD_OUTCOME'
        else:
            e=receipt['structures']['straddle']
            assert abs(legs['atm_call']['strike']/index-1)<=.01 and e['roundtrip_pct']<=8, 'LIQUIDITY_COST_GATE'
            receipt['forecast']=forecast(deliveries,t,index,(expiry-t).total_seconds(),e['legs'])
            receipt['status']='SIMULATED_ENTRY_SELECTED' if receipt['forecast']['selected'] else 'ABSTAIN_FORECAST'
            receipt['control_selected']=True
    except Exception as exc:
        receipt['error']=type(exc).__name__+':'+str(exc)
    finally:
        receipt['manifest']=source.manifest
        save(source.root/'manifest.json',source.manifest)
        save(source.root/'receipt.json',receipt)
        print(json.dumps(receipt,sort_keys=True,allow_nan=False))
    return receipt

def settlement(entry, root, expected):
    entry=Path(entry)
    raw=entry.read_bytes()
    assert digest(raw)==expected, 'ENTRY_HASH_MISMATCH'
    r=json.loads(raw)
    assert r['freeze']==FREEZE and r['mode']=='entry' and r['status'] in {'SIMULATED_ENTRY_SELECTED','ABSTAIN_FORECAST'}
    expiry=dt.datetime.fromisoformat(r['expiry'])
    assert dt.datetime.now(UTC)>expiry, 'NOT_EXPIRED'
    source=Source(root)
    out=dict(entry_sha256=expected,freeze=FREEZE,status='UNSETTLED',simulation=True)
    try:
        rows=source.get('settlement','get_delivery_prices',index_name='btc_usdc',count=100)['data']
        values=[x['delivery_price'] for x in rows if x['date']==expiry.date().isoformat()]
        assert len(values)==1, 'OFFICIAL_DELIVERY_DATE_MISSING_OR_DUPLICATE'
        s=values[0]; legs=r['structures']['straddle']['legs']
        out.update(status='OFFICIAL_DELIVERY_SIMULATED_PNL',terminal=s,
                   control_net=net(legs,s,1),primary_net=net(legs,s,1) if r['forecast']['selected'] else 0,
                   stress_net=net(legs,s,2,1.5) if r['forecast']['selected'] else 0,
                   risk=cost(legs,1), gross=payout(legs,s)[0],delivery=payout(legs,s)[1])
    except Exception as exc:
        out['error']=str(exc)
    finally:
        out['manifest']=source.manifest
        save(source.root/'manifest.json',source.manifest)
        save(source.root/'receipt.json',out)
        print(json.dumps(out,sort_keys=True))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['probe','entry','settle'])
    p.add_argument('--out',required=True)
    p.add_argument('--entry');p.add_argument('--entry-sha256')
    a=p.parse_args()
    if a.mode=='settle':
        settlement(a.entry,a.out,a.entry_sha256)
    else:
        result=collect(a.out,a.mode)
        if result['status']=='SOURCE_BLOCKED':
            raise SystemExit(2)
