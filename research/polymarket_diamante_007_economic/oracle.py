"""Estimate conditional up probabilities from discovery trades on the oracle clock."""
import bisect
import glob
import gzip
import json

def stream(path):
    updates=[]
    exact={}
    with gzip.open(path) as src:
        for line in src:
            f=json.loads(line)
            if not f.get('raw'): continue
            event=json.loads(f['raw'])
            if event.get('topic')!='crypto_prices_twap_sixty':continue
            p=event['payload']; recv=round(f['recv_ts']*1000)
            for a in p.get('data',[p]):
                t=int(a['timestamp'])
                if t>recv:continue
                v=int(a['full_accuracy_value'])/1e18
                exact.setdefault(t,(v,recv))
                updates.append((recv,t,v))
    updates.sort()
    return exact,updates

def build(markets):
    files=sorted(glob.glob('../seven/BTC_rtds*.gz'))
    sources={}
    for f in files:
        with gzip.open(f) as g: utc=int(json.loads(g.readline())['recv_ts'])//86400
        if utc not in sources: sources[utc]=stream(f)
    features={}
    for m in markets:
        slug=m['slug']; start=int(slug.rsplit('-',1)[1])*1000
        exact,updates=sources[start//86400000]
        opening=exact.get(start); closing=exact.get(start+300000)
        for sec in (60,120,180):
            now=start+sec*1000
            i=bisect.bisect_right(updates,(now,float('inf'),float('inf')))
            visible=[x for x in updates[max(0,i-500):i] if now-x[1]<=3000]
            if not opening or opening[1]>now or not visible:continue
            value=max(visible,key=lambda x:(x[1],-x[0]))[2]
            features[(slug,sec)]=(value-opening[0],closing[0]-value if closing else None)
    pools={sec:[v[1] for (slug,h),v in features.items()
                if h==sec and int(slug.rsplit('-',1)[1])//86400==1794009600//86400 and v[1] is not None]
           for sec in (60,120,180)}
    result={}
    for (slug,h),(difference,_) in features.items():
        if len(pools[h])>=20:
            result[(slug,h)]=sum(difference+future>=0 for future in pools[h])/len(pools[h])
    return result,{h:len(p) for h,p in pools.items()},len(features)
