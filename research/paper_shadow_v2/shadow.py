"""Public-only bounded capture. Replay is deterministic in local receive order."""
import asyncio, hashlib, json, math, time, urllib.request
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def positive(x):
    x=float(x)
    if not math.isfinite(x) or x <= 0: raise ValueError('nonpositive/nonfinite')
    return x

def sweep(levels, qty, contract):
    remaining=qty; cash=0.
    for price,volume,*_ in levels:
        capacity=positive(volume)*contract*.1
        take=min(remaining,capacity); cash+=take*positive(price); remaining-=take
        if remaining <= 1e-12: return cash/qty
    raise ValueError('INSUFFICIENT_DEPTH')

class Replay:
    def __init__(self, contract=None):
        self.contract=contract; self.count=Counter(); self.errors=[]; self.liq=[]; self.trades=[]
        self.seen=set(); self.book=None; self.mexc=None; self.version=None
        self.pending=None; self.decisions=[]; self.cooldown=-1; self.last=-1; self.last_utc=-1; self.last_mono=-1
    def reset(self, reason):
        self.errors.append(reason); self.book=self.mexc=None; self.liq=[]; self.trades=[]
        if self.pending:
            self.pending['status']='FAILED_ENTRY' if self.pending['status']=='PENDING_ENTRY' else 'UNRESOLVED'
            self.pending=None
    def stamp(self, ts, now):
        if not now-1500 <= float(ts) <= now+250: raise ValueError('SOURCE_CLOCK_AGE')
    def feed(self, row):
        now=row['utc_ms']; self.count[row['venue']+':frames']+=1
        if row['seq'] <= self.last: self.reset('RECEIVE_SEQUENCE'); return
        self.last=row['seq']
        if now < self.last_utc or row.get('mono_ns', self.last_mono+1) < self.last_mono:
            self.reset('CLOCK_REVERSAL'); return
        self.last_utc=now; self.last_mono=row.get('mono_ns',self.last_mono+1)
        if row['kind']=='error': self.reset(row['raw']); return
        if row['kind']!='frame': return
        try:
            m=json.loads(row['raw'])
            if row['venue']=='bybit':
                topic=m.get('topic','')
                if topic.startswith('orderbook.'):
                    self.stamp(m['ts'],now); d=m['data']
                    # Level 1 is snapshot-only; never interpret deltas as a full book.
                    if m['type']!='snapshot': raise ValueError('NOT_FULL_BYBIT_BOOK')
                    bid=positive(d['b'][0][0]); ask=positive(d['a'][0][0])
                    if bid>=ask: raise ValueError('CROSSED')
                    self.book=now; self.count['bybit:book']+=1
                elif topic.startswith('publicTrade.'):
                    for d in m['data']:
                        self.stamp(d['T'],now); key=('trade',d['i'])
                        if key in self.seen: self.count['duplicates']+=1; continue
                        self.seen.add(key); self.count['bybit:trades']+=1
                        self.trades.append((now,d['S'],positive(d['p'])*positive(d['v'])))
                elif topic.startswith('allLiquidation.'):
                    for d in m['data']:
                        self.stamp(d['T'],now)
                        if d['S'] not in ('Buy','Sell'): raise ValueError('SIDE')
                        key=('liq',d['T'],d['S'],d['v'],d['p'])
                        if key in self.seen: self.count['duplicates']+=1; continue
                        self.seen.add(key); self.count['bybit:liquidations']+=1
                        self.liq.append((now,d['S'],positive(d['v'])*positive(d['p'])))
                elif m.get('success') is False: raise ValueError('SUBSCRIPTION_REJECTED')
                self.detect(now)
            else:
                if m.get('channel')!='push.depth.full': return
                d=m['data']; self.stamp(m['ts'],now); version=int(d['version'])
                if self.version is not None and version<=self.version: raise ValueError('VERSION_REGRESSION')
                for side,reverse in [('bids',True),('asks',False)]:
                    levels=d[side]
                    if len(levels)<5: raise ValueError('SHORT_BOOK')
                    prices=[positive(x[0]) for x in levels]
                    for x in levels: positive(x[1])
                    if prices!=sorted(set(prices),reverse=reverse): raise ValueError('UNSORTED_BOOK')
                if float(d['bids'][0][0])>=float(d['asks'][0][0]): raise ValueError('CROSSED')
                self.version=version; self.mexc=(now,d); self.count['mexc:valid_depth']+=1
                self.execute(now,d)
        except (ValueError,KeyError,TypeError,IndexError) as e:
            self.reset(type(e).__name__+':'+str(e)); self.count['invalid']+=1
    def detect(self, now):
        self.liq=[x for x in self.liq if 0<=now-x[0]<=10000]
        self.trades=[x for x in self.trades if 0<=now-x[0]<=1000]
        if self.pending or now<self.cooldown: return
        for side in ('Buy','Sell'):
            events=[x for x in self.liq if x[1]==side]
            if len(events)<2 or sum(x[2] for x in events)<100000: continue
            if sum(x[2] for x in self.trades if x[1]==side)<10000: continue
            if self.book is None or now-self.book>1000 or self.mexc is None or now-self.mexc[0]>1000 or not self.contract:
                self.count['blocked_signal']+=1; return
            if now%28800000<120000 or now%28800000>28680000:
                self.count['funding_block']+=1; return
            d=self.mexc[1]; price=float(d['asks' if side=='Buy' else 'bids'][0][0])
            qty=math.floor(100/price/self.contract)*self.contract
            if qty<=0: self.count['size_block']+=1; return
            p={'decision_ms':now,'side':side,'qty_btc':qty,'due':now+1000,'status':'PENDING_ENTRY'}
            self.decisions.append(p); self.pending=p; self.cooldown=now+120000; return
    def execute(self,now,d):
        p=self.pending
        if not p or now<p['due']: return
        entry=p['status']=='PENDING_ENTRY'
        if now>p['due']+2000:
            p['status']='FAILED_ENTRY' if entry else 'UNRESOLVED'; self.pending=None; return
        buy=(p['side']=='Buy')==entry
        try: price=sweep(d['asks' if buy else 'bids'],p['qty_btc'],self.contract)
        except ValueError:
            p['status']='FAILED_ENTRY' if entry else 'UNRESOLVED'; self.pending=None; return
        if entry:
            p.update(entry=price,entry_ms=now,due=now+60000,status='OPEN')
        else:
            direction=1 if p['side']=='Buy' else -1
            p.update(exit=price,exit_ms=now,status='COMPLETE')
            # Fixed BTC quantity; fees/slippage charged on both leg notionals.
            gross=direction*(price-p['entry'])/p['entry']*10000
            p['base_bps']=gross-8*(1+price/p['entry'])
            p['stress_bps']=gross-15*(1+price/p['entry']); self.pending=None
    def finish(self):
        if self.pending:
            self.pending['status']='FAILED_ENTRY' if self.pending['status']=='PENDING_ENTRY' else 'UNRESOLVED'
        required=['bybit:book','bybit:trades','bybit:liquidations','mexc:valid_depth']
        source=not self.errors and self.contract and all(self.count[x] for x in required)
        # Economic gate is independent from transport/source classification.
        return {'verdict':'ECONOMIC_INSUFFICIENT_SAMPLE' if source else 'SOURCE_BLOCKED',
                'live_go':False,'economic_gate':economic_gate(self.decisions),
                'counts':dict(self.count),'errors':self.errors,'contract_size':self.contract,
                'decisions':self.decisions,'completed':sum(p['status']=='COMPLETE' for p in self.decisions),
                'limitation':'14-date gate cannot be satisfied by this bounded pilot; no positive economic certification'}


def economic_gate(decisions):
    """Frozen daily cluster bootstrap; incomplete decisions remain in denominator."""
    import random, statistics
    completed=[p for p in decisions if p['status']=='COMPLETE']
    days={}
    for p in completed: days.setdefault(p['decision_ms']//86400000,[]).append(p)
    if (len(completed)<60 or len(days)<14 or not decisions or
        len(completed)/len(decisions)<.95 or any(p['status']=='UNRESOLVED' for p in decisions)):
        return {'verdict':'ECONOMIC_INSUFFICIENT_SAMPLE','completed':len(completed),'dates':len(days)}
    rng=random.Random(334); clusters=list(days.values()); result={}
    for cost in ('base_bps','stress_bps'):
        means=[]
        for _ in range(10000):
            sample=[p[cost] for cluster in rng.choices(clusters,k=len(clusters)) for p in cluster]
            means.append(statistics.mean(sample))
        result[cost]={'mean':statistics.mean(p[cost] for p in completed),'lower95':sorted(means)[249]}
    verdict='PAPER_ECONOMIC_GATE_PASS' if all(x['mean']>0 and x['lower95']>0 for x in result.values()) else 'NO_EDGE'
    return {'verdict':verdict,'statistics':result,'live_go':False}

async def capture(out, seconds=180):
    import websockets
    if not 1<=seconds<=180: raise ValueError('bounded 1..180 seconds')
    out.mkdir(parents=True,exist_ok=False)
    raw=out/'raw.jsonl'; seq=0; start=time.monotonic(); contract=None
    with raw.open('x',encoding='utf-8',newline='\n') as f:
        def record(venue,kind,payload):
            nonlocal seq
            seq+=1
            f.write(json.dumps({'seq':seq,'utc_ms':time.time_ns()//1000000,'mono_ns':time.monotonic_ns(),'venue':venue,'kind':kind,'raw':payload})+'\n'); f.flush()
            if f.tell()>20000000: raise RuntimeError('RAW_CAP')
        try:
            # Literal public URL; no user URL, auth, headers or secret lookup.
            def detail():
                with urllib.request.urlopen('https://contract.mexc.com/api/v1/contract/detail?symbol=BTC_USDT',timeout=10) as r: return r.read().decode()
            response=await asyncio.to_thread(detail); record('mexc','contract',response)
            obj=json.loads(response); data=obj['data']
            if isinstance(data,list): data=next(x for x in data if x['symbol']=='BTC_USDT')
            if data['symbol']!='BTC_USDT' or obj['success'] is not True: raise ValueError('CONTRACT')
            contract=positive(data['contractSize'])
        except Exception as e: record('mexc','error',type(e).__name__+':'+str(e))
        async def stream(venue,url,subscription):
            try:
                async with websockets.connect(url,open_timeout=15,max_size=2000000) as ws:
                    await ws.send(json.dumps(subscription)); record(venue,'subscription',json.dumps(subscription))
                    while time.monotonic()-start<seconds:
                        remaining=seconds-(time.monotonic()-start)
                        try: message=await asyncio.wait_for(ws.recv(),min(10,remaining))
                        except asyncio.TimeoutError:
                            if time.monotonic()-start>=seconds: break
                            await ws.send(json.dumps({'op':'ping'} if venue=='bybit' else {'method':'ping'})); continue
                        record(venue,'frame',message)
            except Exception as e: record(venue,'error',type(e).__name__+':'+str(e))
        await asyncio.gather(stream('bybit','wss://stream.bybit.com/v5/public/linear',{'op':'subscribe','args':['allLiquidation.BTCUSDT','publicTrade.BTCUSDT','orderbook.1.BTCUSDT']}),stream('mexc','wss://contract.mexc.com/edge',{'method':'sub.depth.full','param':{'symbol':'BTC_USDT','limit':5}}))
    replay=Replay(contract)
    for line in raw.read_text(encoding='utf-8').splitlines(): replay.feed(json.loads(line))
    report=replay.finish(); report.update(raw_sha256=sha(raw),protocol_sha256=sha(ROOT/'PROTOCOL.md'),elapsed_seconds=time.monotonic()-start)
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('output',type=Path); parser.add_argument('--seconds',type=int,default=180)
    args=parser.parse_args(); asyncio.run(capture(args.output,args.seconds))
