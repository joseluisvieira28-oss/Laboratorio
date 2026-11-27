"""Causal offline simulation with conservative single-transaction tape."""
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone
import gzip, hashlib, itertools, json, math, os
from oracle import build

def day(slug):
    return datetime.fromtimestamp(int(slug.rsplit('-',1)[1]),timezone.utc).strftime('%Y-%m-%d')

PROFILE=os.environ.get('REPLAY_PROFILE','frozen')
RATE=.01 if PROFILE=='published_terms' else .07

def fees(p):
    return RATE*p*(1-p)

def simulate(slug, ev, actual, horizon, rule, cash, stress, probabilities):
    start=int(slug.rsplit('-',1)[1])*1000
    decision=start+horizon*1000
    end=start+300000
    expires=decision+30000
    lag=1000 if stress else 500
    haircut=.10 if stress else .25
    slip=.01 if stress else .005
    first=int(hashlib.sha256(slug.encode()).hexdigest(),16)%2
    if rule=='control': first=1-first
    quote=None; imbalance=None; orders={}; pending={}; cancels={}
    fills=[]; orders_log=[]; quantities=[0.,0.]; spends=[0.,0.]
    next_first=decision; next_hedge=decision; eligible=False; active_gap=0
    first_price_limit=None; first_target=None; cost_total=0.; first_enabled=None
    def order(side, ts, qty, price, kind):
        qty=math.floor(qty*100+1e-7)/100
        if qty<5 and kind=='maker' or qty*price<1 and kind=='ioc':
            return False
        pending[side]=(ts+lag,qty,price,kind)
        orders_log.append([ts,side,qty,price,kind])
        return True
    def record(t,s,q,p,mode):
        nonlocal cost_total
        fee=q*fees(p) if mode=='ioc' else 0.
        surcharge=q*(min(1,p+slip)-p) if mode=='ioc' else 0.
        quantities[s]+=q;spends[s]+=p*q;cost_total+=fee+surcharge
        fills.append([t,s,q,p,mode,fee,surcharge])
    i=bisect_left(ev,decision,key=lambda x:x[0])
    for prior in reversed(ev[:i]):
        if prior[1]=='gap':break
        if prior[1]=='q':
            quote,imbalance=prior[2:]
            break
    for event in itertools.islice(ev,i,None):
        t,typ,*data=event
        if t>=expires+lag and not orders and not pending and (not fills or abs(quantities[0]-quantities[1])<1e-8):
            break
        if t>=end:break
        if typ=='gap':
            active_gap+=bool(orders or pending)
            quote=None;orders.clear();pending.clear();cancels.clear()
            continue
        if typ=='q':
            quote,imbalance=data
        if quote is None:continue
        for side, deadline in list(cancels.items()):
            if t>=deadline:
                orders.pop(side,None);cancels.pop(side)
        for side,(arrival,qty,price,kind) in list(pending.items()):
            if t<arrival:continue
            pending.pop(side)
            bid,ask,bsize,asize=quote[side]
            if kind=='maker' and round(price*1000)==bid and bid<ask and ts_valid(ask):
                orders[side]=[t,qty,price,bsize]
            if kind=='ioc' and ts_valid(ask):
                p=ask/1000
                q=min(qty,math.floor(asize*haircut*100)/100)
                if p+fees(p)+slip<=price and q*p>=1:
                    record(t,side,q,p,kind)
        if typ=='sell':
            side,p,qty,origin=data
            if side in orders:
                arrival,remain,price,ahead=orders[side]
                p/=1000
                if origin>arrival and ((stress and p<price) or (not stress and p==price)):
                    if not stress:
                        used=min(qty,ahead)
                        qty-=used;ahead-=used
                    executed=min(qty,remain)
                    if executed>0:
                        record(t,side,executed,price,'maker')
                    remain-=executed
                    if remain<=1e-8:
                        orders.pop(side)
                    else:
                        orders[side]=[arrival,remain,price,ahead]
        if t<decision:continue
        if first_enabled is None:
            eligible=t<decision+3000
            if not eligible:break
            if rule=='oracle':
                pr=probabilities.get((slug,horizon))
                b,a=quote[0][:2]; mid=(b+a)/2000
                if pr is None or not ts_valid(a) or b<=0:break
                first=int(pr<mid)
                edge=pr if first==0 else 1-pr
                offer=quote[first][1]/1000
                if abs(pr-mid)<.05 or edge<=offer+fees(offer)+slip:break
            if rule=='micro' and imbalance[first]<=.25:break
            first_enabled=True
        if t>=expires:
            if first in orders and first not in cancels:cancels[first]=t+lag
        elif t>=next_first and first not in pending:
            bid,ask,*_=quote[first];p=bid/1000
            if first not in orders and p>0 and ts_valid(ask):
                if first_target is None:
                    first_target=math.floor(min(.05*cash/p,.05*cash)*100)/100
                    first_price_limit=.05*cash
                qty=min(first_target-quantities[first],(first_price_limit-spends[first])/p)
                if rule=='inventory' and quantities[first]-quantities[1-first]>=first_target/2:
                    qty*=.5
                order(first,t,qty,p,'maker')
                next_first=t+5000
            elif first in orders and first not in cancels and orders[first][2]!=p:
                cancels[first]=t+lag
                next_first=t+5000
        other=1-first
        residual=quantities[first]-quantities[other]
        if rule in ('maker','hybrid','oracle','inventory','micro','control') and residual>=.01 and t>=next_hedge:
            worst_first=max(f[3] for f in fills if f[1]==first)
            limit=.99-worst_first
            bid,ask,*_=quote[other]
            ioc=rule=='hybrid'
            p=ask/1000 if ioc else bid/1000
            estimated=p+fees(p)+slip if ioc else p
            if other in orders and (orders[other][2]!=p or estimated>limit):
                if other not in cancels:cancels[other]=t+lag
            elif other not in pending and other not in orders and 0<p<1 and estimated<=limit:
                if order(other,t,residual,limit if ioc else p,'ioc' if ioc else 'maker'):
                    next_hedge=t+(lag if ioc else 5000)
    mids=[(x[0],[(r[0]+r[1])/2000 if r[0]>0 and r[1]<1000 else None for r in x[2]]) for x in ev if x[1]=='q'] if fills else []
    markouts={}
    if fills:
        stamps=[x[0] for x in mids]
        first_fill=next(f for f in fills if f[1]==first)
        for sec in (1,5,30):
            target=first_fill[0]+1000*sec
            i=bisect_left(stamps,target)
            if i<len(mids) and stamps[i]-target<=500 and mids[i][1][first] is not None:
                markouts[sec]=mids[i][1][first]-first_fill[3]
    paired=min(quantities)
    gross=quantities[actual]-sum(spends)
    pair_pnl=paired*(1-sum(spends[s]/quantities[s] for s in (0,1))) if paired else 0.
    return {'eligible':eligible,'orders':orders_log,'fills':fills,'paired_shares':paired,
            'complete_pair':paired>0 and abs(quantities[0]-quantities[1])<1e-8,
            'residual':abs(quantities[0]-quantities[1]),'gross':gross,'costs':cost_total,
            'net':gross-cost_total,'paired_gross_average_cost':pair_pnl,
            'residual_gross_average_cost':gross-pair_pnl,'spent':sum(spends)+cost_total,
            'gap_with_active_order':active_gap,'quantities':quantities,'markouts':markouts,
            'first_pair_delay_s':(next(f[0] for f in fills if f[1]!=first)-next(f[0] for f in fills if f[1]==first))/1000 if paired else None}

def ts_valid(ask):
    return 0<ask<1000

markets=json.load(open('../seven/gamma.json'))+json.load(open('gamma-extra.json'))
winner={}
for m in markets:
    sides=json.loads(m['outcomes']);p=json.loads(m['outcomePrices'])
    assert m['umaResolutionStatus']=='resolved' and sorted(map(float,p))==[0,1]
    assert m['resolutionSource'].endswith('twap-60s-streams')
    winner[m['slug']]=max(range(2),key=lambda i:float(p[i]))
    assert [x.lower() for x in sides]==['up','down']
probabilities,pools,n_features=build(markets)
events=defaultdict(list)
with gzip.open('events.jsonl.gz') as tape:
    for l in tape:
        slug,*event=json.loads(l);events[slug].append(event)
if PROFILE=='published_terms':
    terms={m['slug']:m for m in json.load(open('market-terms.json'))}
    assert all(m['feeSchedule']['rate']==.01 and m['feeSchedule']['exponent']==1 for m in terms.values())
    release={s:round(datetime.fromisoformat(m['closedTime']).timestamp()*1000) for s,m in terms.items()}
keys=list(itertools.product(('maker','hybrid','oracle','inventory','micro','control'),(60,120,180),(100,250,500,1000,5000) if PROFILE=='frozen' else (500,), (False,True)))
output=[]
with gzip.open('ledger.jsonl.gz' if PROFILE=='frozen' else 'ledger-published.jsonl.gz','wt') as ledger:
    for rule,h,capital,stress in keys:
        for date,slugs in itertools.groupby(sorted(winner),key=day):
            free=capital; acc=[]; clock=0.; high=0.; dd=0.; locked=[]
            for slug in slugs:
                if PROFILE=='published_terms':
                    now=int(slug.rsplit('-',1)[1])*1000
                    free+=sum(cash for time,cash in locked if time<=now)
                    locked=[(time,cash) for time,cash in locked if time>now]
                r=simulate(slug,events[slug],winner[slug],h,rule,free,stress,probabilities)
                if PROFILE=='published_terms':
                    locked.append((release[slug]+(1800000 if stress else 900000),r['net']+r['spent']))
                free-=r['spent'];clock+=r['net'];high=max(high,clock);dd=max(dd,high-clock)
                record=dict(rule=rule,horizon=h,capital=capital,stress=stress,slug=slug,**r)
                ledger.write(json.dumps(record,separators=(',',':'))+'\n'); acc.append(r)
            entry=dict(rule=rule,horizon=h,capital=capital,stress=stress,date=date,drawdown=dd)
            for field in ('eligible','complete_pair','paired_shares','residual','gross','costs','net','spent','gap_with_active_order'):
                entry[field]=sum(x[field] for x in acc)
            entry['orders']=sum(len(x['orders']) for x in acc)
            entry['fills']=sum(len(x['fills']) for x in acc)
            entry['unhedged_first_markets']=sum(bool(x['fills']) and not x['paired_shares'] for x in acc)
            entry['worst']=min(x['net'] for x in acc)
            entry['positive_concentration']=max(x['net'] for x in acc)/sum(max(x['net'],0) for x in acc) if any(x['net']>0 for x in acc) else None
            output.append(entry)
json.dump({'oracle_calibration_n':pools,'oracle_features':n_features,'aggregate':output},open('economic.json' if PROFILE=='frozen' else 'economic-published.json','w'),indent=1)
