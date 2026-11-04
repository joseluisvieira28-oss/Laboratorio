"""Public-only bounded observer. No execution or PnL code."""
import asyncio, contextlib, gzip, hashlib, json, math, time
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'paper_shadow_v2'))
from shadow import positive
ROOT=Path(__file__).parent
URL={'bybit':'wss://stream.bybit.com/v5/public/linear','mexc':'wss://contract.mexc.com/edge'}
SUB={'bybit':{'op':'subscribe','args':['allLiquidation.BTCUSDT','publicTrade.BTCUSDT','orderbook.1.BTCUSDT']},'mexc':{'method':'sub.depth.full','param':{'symbol':'BTC_USDT','limit':5}}}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def book(m,v):
    d=m['data']; sides=('b','a') if v=='bybit' else ('bids','asks')
    if v=='bybit':
        if m['type']!='snapshot' or d['s']!='BTCUSDT': raise ValueError('BYBIT_SNAPSHOT_SYMBOL')
    elif m['symbol']!='BTC_USDT': raise ValueError('MEXC_SYMBOL')
    prices=[]
    for k,reverse in zip(sides,(True,False)):
        levels=d[k]
        if len(levels)<(1 if v=='bybit' else 5): raise ValueError('SHORT_BOOK')
        p=[positive(x[0]) for x in levels]
        for x in levels: positive(x[1])
        if p!=sorted(set(p),reverse=reverse): raise ValueError('UNSORTED')
        prices.append(p[0])
    if prices[0]>=prices[1]: raise ValueError('CROSSED')
    return int(d['u'] if v=='bybit' else d['version']),json.dumps(d,sort_keys=True)

class Observer:
    def __init__(self):
        self.state={v:{'ack':False,'pong':-1e12,'book':-1e12,'version':None,'payload':None} for v in URL}
        self.count=Counter(); self.quarantine=0.; self.last=None; self.next_tick=1; self.good=[]; self.bad=[]
        self.seen=set(); self.liq=[]; self.trades=[]; self.cooldown=-1; self.episodes=[]; self.contract=None
    def reset(self,t,reason):
        self.quarantine=t+30; self.liq.clear(); self.trades.clear(); self.count['reset:'+reason]+=1
        for s in self.state.values(): s['book']=-1e12
    def healthy(self,t):
        return t>=self.quarantine and all(s['ack'] and 0<=t-s['pong']<=35 and 0<=t-s['book']<=1 for s in self.state.values())
    def tick(self,t):
        if any(s['book']>-1e11 and t-s['book']>1 for s in self.state.values()): self.reset(t,'STALE_BOOK')
        (self.good if self.healthy(t) else self.bad).append(t)
    def feed(self,r):
        t=r['elapsed']; v=r['venue']; k=r['kind']; s=self.state.get(v)
        # Strictly causal grid: equal-time tick can include current receipt.
        while self.next_tick<t:
            self.tick(self.next_tick); self.next_tick+=1
        if self.last and (r['seq']!=self.last['seq']+1 or r['mono_ns']<self.last['mono_ns'] or r['utc_ms']<self.last['utc_ms'] or abs((r['utc_ms']-self.last['utc_ms'])-(r['mono_ns']-self.last['mono_ns'])/1e6)>250):
            self.count['integrity']+=1; self.reset(t,'CLOCK_SEQUENCE')
        self.last=r
        try:
            if k=='contract':
                m=json.loads(r['raw']); d=m['data']; d=next(x for x in d if x['symbol']=='BTC_USDT') if isinstance(d,list) else d
                if m['success'] is not True or d['symbol']!='BTC_USDT': raise ValueError('CONTRACT')
                self.contract=positive(d['contractSize'])
            elif k=='connect':
                s.update(ack=False,pong=-1e12,book=-1e12,version=None,payload=None); self.reset(t,'CONNECT')
            elif k in ('disconnect','fault'):
                if s: s.update(ack=False,book=-1e12)
                self.reset(t,k); self.count[v+':'+k]+=1
            elif k=='frame':
                m=json.loads(r['raw']); self.count[v+':frames']+=1
                if m.get('success') is False or (m.get('channel','').startswith('rs.') and m.get('data') not in (0,'0','success')): raise ValueError('SUB_REJECT')
                if (v=='bybit' and m.get('op')=='subscribe' and m.get('success') is True) or (v=='mexc' and m.get('channel')=='rs.sub.depth.full' and m.get('data') in (0,'0','success')): s['ack']=True
                if (v=='mexc' and m.get('channel')=='pong') or (v=='bybit' and (m.get('op')=='pong' or m.get('ret_msg')=='pong')):
                    s['pong']=t; self.count[v+':pong']+=1
                topic=m.get('topic','')
                isbook=topic=='orderbook.1.BTCUSDT' if v=='bybit' else m.get('channel')=='push.depth.full'
                if isbook:
                    self.stamp(m['ts'],r['utc_ms']); version,payload=book(m,v)
                    old=s['version']
                    if old is not None and version==old and payload==s['payload']:
                        self.count[v+':duplicate_book']+=1
                    else:
                        if old is not None and version<=old: raise ValueError('VERSION_REGRESSION_CONFLICT')
                        s.update(book=t,version=version,payload=payload); self.count[v+':book']+=1
                if v=='bybit' and topic in ('publicTrade.BTCUSDT','allLiquidation.BTCUSDT'):
                    liq=topic.startswith('allLiquidation')
                    for d in m['data']:
                        self.stamp(d['T'],r['utc_ms'])
                        if d['s']!='BTCUSDT' or d['S'] not in ('Buy','Sell'): raise ValueError('EVENT_SYMBOL_SIDE')
                        value=positive(d['p'])*positive(d['v'])
                        key=('liq',d['T'],d['s'],d['S'],d['v'],d['p']) if liq else ('trade',d['i'])
                        if key in self.seen: self.count['duplicates']+=1; continue
                        self.seen.add(key); self.count['liquidations' if liq else 'trades']+=1
                        (self.liq if liq else self.trades).append((t,d['S'],value))
                if v=='bybit': self.detect(t,r['utc_ms'])
        except (ValueError,TypeError,KeyError,IndexError,OverflowError) as e:
            self.count['invalid:'+str(e)]+=1; self.reset(t,'INVALID')
        if self.next_tick==t:
            self.tick(t); self.next_tick+=1
    def stamp(self,x,now):
        if not now-1500<=float(x)<=now+250: raise ValueError('SOURCE_CLOCK')
    def detect(self,t,utc):
        self.liq=[x for x in self.liq if 0<=t-x[0]<=10]; self.trades=[x for x in self.trades if 0<=t-x[0]<=1]
        if t<self.cooldown: return
        for side in ('Buy','Sell'):
            events=[x for x in self.liq if x[1]==side]
            if len(events)<2 or sum(x[2] for x in events)<100000: continue
            flow=sum(x[2] for x in self.trades if x[1]==side)>=10000
            funding=120000<=utc%28800000<=28680000
            self.episodes.append({'elapsed':t,'utc_ms':utc,'side':side,'children':len(events),'notional_proxy':sum(x[2] for x in events),'flow':flow,'joint_good':self.healthy(t),'qualified':bool(flow and funding and self.healthy(t) and self.contract)})
            self.cooldown=t+120; break
    def report(self,reason):
        n=len(self.good)+len(self.bad); goodset=set(self.good)
        minutes=sum(sum(i in goodset for i in range(m*60+1,m*60+61))>=57 for m in range(n//60))
        passed=n>=7200 and len(self.good)/max(n,1)>=.95 and minutes>=100 and not self.count['integrity'] and reason=='WALL_LIMIT' and sum(self.count[v+':disconnect'] for v in URL)<=8 and self.count['liquidations']>=1
        intervals=[]
        for x in self.bad:
            if intervals and intervals[-1][1]==x-1: intervals[-1][1]=x
            else: intervals.append([x,x])
        return {'source_verdict':'SOURCE_PASS_LIMITED' if passed else 'SOURCE_BLOCKED','economic_verdict':'ECONOMIC_INSUFFICIENT','live_verdict':'NO_LIVE_GO','end_reason':reason,'seconds':n,'joint_good_seconds':len(self.good),'joint_coverage':len(self.good)/max(n,1),'good_full_minutes':minutes,'bad_second_intervals':intervals,'counts':dict(self.count),'contract_size':self.contract,'episodes':self.episodes,'qualified_signals':sum(e['qualified'] for e in self.episodes),'recommend_multiday':bool(passed and len(self.episodes)>=2 and any(e['qualified'] for e in self.episodes)),'pnl':'NOT_COMPUTED_GATE_CLOSED'}

async def capture(out):
    import urllib.request, websockets
    out.mkdir(exist_ok=False,parents=True); raw=out/'raw.jsonl.gz'; engine=Observer(); start=time.monotonic_ns(); stop=asyncio.Event(); reason='WALL_LIMIT'; seq=0; total=0
    f=gzip.open(raw,'xb',compresslevel=3)
    def record(v,k,payload,segment=0):
        nonlocal seq,total,reason
        seq+=1; mono=time.monotonic_ns(); r={'seq':seq,'utc_ms':time.time_ns()//1000000,'mono_ns':mono,'elapsed':(mono-start)/1e9,'venue':v,'kind':k,'segment':segment,'raw':payload}
        b=(json.dumps(r,separators=(',',':'))+'\n').encode(); f.write(b); total+=len(b); engine.feed(r)
        if total>=384*1024**2 or raw.stat().st_size>=128*1024**2:
            reason='STORAGE_CAP'; stop.set()
        return r
    record('system','start',json.dumps({'seconds':7200,'protocol_sha256':sha(ROOT/'PROTOCOL.md'),'code_sha256':sha(Path(__file__))}))
    try:
        def detail():
            with urllib.request.urlopen('https://contract.mexc.com/api/v1/contract/detail?symbol=BTC_USDT',timeout=10) as r: return r.read().decode()
        record('mexc','contract',await asyncio.to_thread(detail))
    except Exception as e: record('mexc','fault',repr(e))
    async def stream(v):
        nonlocal reason
        for segment in range(1,10):
            if stop.is_set() or (time.monotonic_ns()-start)/1e9>=7200: return
            if segment>1:
                try: await asyncio.wait_for(stop.wait(),[1,2,4,8,16,30,30,30][segment-2]); return
                except asyncio.TimeoutError: pass
            try:
                async with websockets.connect(URL[v],open_timeout=15,close_timeout=2,max_size=2000000,ping_interval=None) as ws:
                    record(v,'connect',URL[v],segment); await ws.send(json.dumps(SUB[v])); record(v,'subscription',json.dumps(SUB[v]),segment)
                    next_ping=0; connected=time.monotonic(); last_book=connected; pong=connected; expected=False
                    while not stop.is_set() and (time.monotonic_ns()-start)/1e9<7200:
                        now=time.monotonic()
                        if now>=next_ping:
                            ping={'op':'ping'} if v=='bybit' else {'method':'ping'}
                            await ws.send(json.dumps(ping)); record(v,'ping',json.dumps(ping),segment); next_ping=now+15; expected=True
                        if expected and now-pong>35: raise RuntimeError('PONG_TIMEOUT')
                        if now-last_book>10: raise RuntimeError('VALID_BOOK_TIMEOUT')
                        try: message=await asyncio.wait_for(ws.recv(),min(1,max(.001,7200-(time.monotonic_ns()-start)/1e9)))
                        except asyncio.TimeoutError: continue
                        if not isinstance(message,str): raise ValueError('BINARY_FRAME_UNSUPPORTED')
                        r=record(v,'frame',message,segment)
                        if engine.state[v]['book']==r['elapsed']: last_book=now
                        if engine.state[v]['pong']==r['elapsed']: pong=now
            except Exception as e:
                record(v,'disconnect',json.dumps({'exception':type(e).__name__,'reason':str(e),'received_close':str(getattr(e,'rcvd',None)),'sent_close':str(getattr(e,'sent',None))}),segment)
            if stop.is_set() or (time.monotonic_ns()-start)/1e9>=7200: return
        reason='RETRY_EXHAUSTED'; stop.set()
    async def wall():
        try: await asyncio.wait_for(stop.wait(),max(.001,7200-(time.monotonic_ns()-start)/1e9))
        except asyncio.TimeoutError: stop.set()
    try: await asyncio.wait_for(asyncio.gather(stream('bybit'),stream('mexc'),wall()),7250)
    except Exception as e: reason='PROCESS_FAILURE'; record('system','fault',repr(e))
    finally:
        record('system','end',reason); f.close()
        report=engine.report(reason); report['uncompressed_bytes']=total
        (out/'report.json').write_text(json.dumps(report,indent=2))
        h=hashlib.sha256()
        with gzip.open(raw,'rb') as z:
            for chunk in iter(lambda:z.read(1024*1024),b''): h.update(chunk)
        manifest={'raw_sha256':h.hexdigest(),'gzip_sha256':sha(raw),'protocol_sha256':sha(ROOT/'PROTOCOL.md'),'code_sha256':sha(Path(__file__)),'elapsed_seconds':(time.monotonic_ns()-start)/1e9,'receipt_rows':seq}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps(report),flush=True)
if __name__=='__main__': asyncio.run(capture(Path(sys.argv[1])))
