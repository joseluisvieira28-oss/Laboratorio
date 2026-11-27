"""Stream PolyData5 frames, validate books, and emit normalized causal events."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip, hashlib, json, glob, os, sys
import heapq

def emit(out, fields):
    out.write(json.dumps(fields,separators=(',',':'))+'\n')

def levels(rows):
    return {round(float(row['price'])*1000):float(row['size']) for row in rows}

class Book:
    def __init__(self, m):
        self.sides=[levels(m['bids']),levels(m['asks'])]
        self.heaps=[[-p for p in self.sides[0]],[p for p in self.sides[1]]]
        for h in self.heaps: heapq.heapify(h)

    def change(self, c):
        i=int(c['side']=='SELL')
        p=round(float(c['price'])*1000)
        q=float(c['size'])
        cells=self.sides[i]
        if q:
            if p not in cells: heapq.heappush(self.heaps[i],p if i else -p)
            cells[p]=q
        else:
            cells.pop(p,None)

    def best(self,i):
        cells=self.sides[i]; h=self.heaps[i]; sign=1 if i else -1
        while h and sign*h[0] not in cells: heapq.heappop(h)
        return sign*h[0] if h else (1000 if i else 0)

    def view(self):
        b,a=self.best(0),self.best(1)
        return [b,a,self.sides[0].get(b,0),self.sides[1].get(a,0)]

authority=json.load(open('../seven/gamma.json'))+json.load(open('gamma-extra.json'))
markets={m['conditionId']:m for m in authority}
tokens={m['conditionId']:{k:i for i,k in enumerate(json.loads(m['clobTokenIds']))} for m in authority}
manifest={p['file']:p for s in json.load(open('manifest.json'))['sources'] for p in s['parts']}
counts={}; coverage=defaultdict(Counter); seen=defaultdict(set)
books={}; active=None; prior=None
with gzip.open('events.jsonl.gz','wt',compresslevel=2) as out:
    for path in sorted(glob.glob('BTC_clob*.gz'),key=lambda p:(p.split('.2026-')[1],p)):
        with open(path,'rb') as src: sha=hashlib.file_digest(src,'sha256').hexdigest()
        assert sha==manifest[path]['sha256'],path
        c=Counter(); counts[path]={'sha256':sha,'count':c}
        with gzip.open(path,'rb') as src:
            for line in src:
                c['lines']+=1
                f=json.loads(line); t=round(f['recv_ts']*1000)
                c['receive_regressions']+= int(prior is not None and f['recv_ts']<prior)
                prior=f['recv_ts']
                raw=f.get('raw')
                if not raw:
                    c['service:'+str(f.get('event'))]+=1
                    if active is not None: emit(out,[active,t,'gap'])
                    books.clear();active=None
                    continue
                decoded=json.loads(raw)
                for m in decoded if isinstance(decoded,list) else [decoded]:
                    typ=m.get('event_type','other');c[typ]+=1
                    cid=m.get('market')
                    if cid not in markets: continue
                    slug=markets[cid]['slug']; start=int(slug.rsplit('-',1)[1])*1000
                    if not start<=t<start+300000: continue
                    if active!=slug:
                        if active is not None: emit(out,[active,t,'gap'])
                        books.clear();active=slug
                    audited=coverage[slug]; audited[typ]+=1
                    origin=int(m['timestamp'])
                    audited['clock_ahead']+=origin>t
                    if typ=='book':
                        idx=tokens[cid].get(m['asset_id'])
                        if idx is None: continue
                        books[idx]=Book(m)
                    elif typ=='price_change':
                        for change in m['price_changes']:
                            idx=tokens[cid].get(change['asset_id'])
                            if idx not in books: continue
                            b=books[idx];b.change(change)
                            best=[round(float(change[k])*1000) for k in ('best_bid','best_ask')]
                            if [b.best(0),b.best(1)]!=best:
                                audited['best_disagreement']+=1
                                books.pop(idx)
                                emit(out,[slug,t,'gap'])
                    elif typ=='last_trade_price':
                        idx=tokens[cid].get(m['asset_id']); tx=m.get('transaction_hash')
                        if not tx or idx is None or m.get('side') not in ('BUY','SELL'):
                            audited['unidentified_trade']+=1
                            continue
                        if tx in seen[slug]:
                            audited['trade_tx_repeated']+=1
                            continue
                        seen[slug].add(tx)
                        if len(books)==2 and m['side']=='SELL':
                            emit(out,[slug,t,'sell',idx,round(float(m['price'])*1000),float(m['size']),origin])
                        continue
                    else:
                        if typ=='tick_size_change':
                            audited['tick_transition']+=1
                            books.clear();emit(out,[slug,t,'gap'])
                        continue
                    if len(books)==2:
                        q=[books[i].view() for i in (0,1)]
                        if any(row[0]>=row[1] for row in q):
                            audited['crossed']+=1
                            books.clear();emit(out,[slug,t,'gap'])
                            continue
                        if typ=='book' or q!=last_quote:
                            imbalances=[]
                            for i in (0,1):
                                bids,asks=books[i].sides
                                x=sum(bids[p] for p in sorted(bids,reverse=True)[:3])
                                y=sum(asks[p] for p in sorted(asks)[:3])
                                imbalances.append((x-y)/(x+y) if x+y else 0)
                            emit(out,[slug,t,'q',q,imbalances])
                            last_quote=q
        assert c['lines']==manifest[path]['lines'],path
json.dump({'files':counts,'markets':coverage},open('clob-audit.json','w'),indent=2)
