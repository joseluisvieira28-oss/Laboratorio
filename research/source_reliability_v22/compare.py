"""Source Reliability V2.2 — paired public L1/50 source-only observer.

PAPER/READ-ONLY. No orders, credentials, private exchange endpoints, PnL
or background schedules. Frozen rules in PROTOCOL_FROZEN.md.
"""
from __future__ import annotations
import asyncio
import gzip
import hashlib
import json
import math
import sys
import time
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
BYBIT = "wss://stream.bybit.com/v5/public/linear"
MEXC = "wss://contract.mexc.com/edge"
SUB_BYBIT = {"op":"subscribe", "args":["orderbook.1.BTCUSDT","orderbook.50.BTCUSDT"]}
SUB_MEXC = {"method":"sub.depth.full","param":{"symbol":"BTC_USDT","limit":5}}
WINDOW = 600
QUARANTINE = 30

class SourceFault(Exception):
    pass

def number(x, allow_zero=False):
    try: d=Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError): raise SourceFault("BAD_DECIMAL")
    if not d.is_finite() or d<0 or (d==0 and not allow_zero):
        raise SourceFault("NONPOSITIVE_DECIMAL")
    return d

def timestamp(ms, receive_ms):
    try: val=int(ms)
    except (ValueError,TypeError): raise SourceFault("NO_TIMESTAMP")
    if not receive_ms-1500<=val<=receive_ms+250:
        raise SourceFault("PUBLISHER_CLOCK")
    return val

def sides_valid(bids, asks):
    if not bids or not asks or max(bids)>=min(asks):
        raise SourceFault("CROSSED_OR_EMPTY_BOOK")

class L50:
    def __init__(self):
        self.reset()
    def reset(self):
        self.bids={};self.asks={};self.u=None;self.seq=None;self.ready=False
        self.snapshot_count=0;self.delta_count=0
    def _updates(self, arr, mode, out):
        if not isinstance(arr,list): raise SourceFault("SIDE_NOT_LIST")
        entries=[]
        seen=set()
        for item in arr:
            if not isinstance(item,list) or len(item)!=2:
                raise SourceFault("LEVEL_SHAPE")
            p=number(item[0]);q=number(item[1],allow_zero=True)
            if p in seen: raise SourceFault("DUPLICATE_PRICE_IN_FRAME")
            seen.add(p);entries.append((p,q))
        ps=[x[0] for x in entries]
        if ps!=sorted(ps,reverse=(mode=="bids")):
            raise SourceFault("LEVEL_UNSORTED")
        for p,q in entries:
            if q==0:out.pop(p,None)
            else:out[p]=q
    def consume(self, m):
        if m.get("topic")!="orderbook.50.BTCUSDT":
            raise SourceFault("TOPIC_MISMATCH")
        d=m.get("data",{})
        if d.get("s")!="BTCUSDT":raise SourceFault("SYMBOL_MISMATCH")
        try:u=int(d["u"]);seq=int(d["seq"])
        except (KeyError,TypeError,ValueError):raise SourceFault("MISSING_ORDERBOOK_VERSION")
        typ=m.get("type")
        if typ=="snapshot":
            b,a={},{}
            self._updates(d.get("b"),"bids",b)
            self._updates(d.get("a"),"asks",a)
            sides_valid(b,a)
            self.bids,self.asks,self.u,self.seq,self.ready=b,a,u,seq,True
            self.snapshot_count+=1
            return "SNAPSHOT"
        if typ!="delta": raise SourceFault("INVALID_ORDERBOOK_TYPE")
        if u==1:
            self.reset()
            return "RESET_U1_NEEDS_SNAPSHOT"
        if not self.ready:
            return "WAIT_FOR_SNAPSHOT"
        if u<=self.u or seq<=self.seq:
            self.reset()
            raise SourceFault("BOOK_VERSION_OR_SEQUENCE_REGRESSION")
        b=self.bids.copy();a=self.asks.copy()
        self._updates(d.get("b"),"bids",b)
        self._updates(d.get("a"),"asks",a)
        try:sides_valid(b,a)
        except SourceFault:
            self.reset()
            raise
        self.bids,self.asks,self.u,self.seq=b,a,u,seq
        self.delta_count+=1
        return "DELTA"

class L1:
    def __init__(self, refresh_duplicate):
        self.refresh_duplicate=refresh_duplicate
        self.u=None;self.payload=None;self.last=None
    def reset(self):
        self.u=None;self.payload=None;self.last=None
    def consume(self,m,t):
        if m.get("topic")!="orderbook.1.BTCUSDT" or m.get("type")!="snapshot":
            raise SourceFault("L1_TOPIC_OR_TYPE")
        d=m.get("data",{})
        if d.get("s")!="BTCUSDT":raise SourceFault("L1_SYMBOL")
        bs=d.get("b");asks=d.get("a")
        if not isinstance(bs,list) or not isinstance(asks,list) or not bs or not asks:
            raise SourceFault("L1_SHORT")
        b=number(bs[0][0]);a=number(asks[0][0])
        number(bs[0][1]);number(asks[0][1])
        if b>=a: raise SourceFault("L1_CROSSED")
        try:u=int(d["u"])
        except (KeyError,TypeError,ValueError):raise SourceFault("L1_VERSION")
        signature=(str(b),str(a),str(bs[0][1]),str(asks[0][1]))
        if self.u==u:
            if signature!=self.payload: raise SourceFault("L1_SAME_VERSION_CONFLICT")
            if self.refresh_duplicate:self.last=t
            return "DUPLICATE_REFRESH" if self.refresh_duplicate else "DUPLICATE_IGNORED"
        if self.u is not None and u<self.u and u!=1:
            self.reset()
            raise SourceFault("L1_VERSION_REGRESSION")
        self.u=u;self.payload=signature;self.last=t
        return "CHANGED"

class PairObserver:
    """One observer receives persisted records in strict causal order."""
    def __init__(self):
        self.bybit_ack=False;self.mexc_ack=False
        self.bybit_pong=-1e12;self.mexc_pong=-1e12
        self.mexc_time=None;self.mexc_version=None
        self.l1a=L1(False);self.l1b=L1(True);self.l50=L50()
        self.times={"A":None,"B":None,"C":None}
        self.quarantine={"A":QUARANTINE,"B":QUARANTINE,"C":QUARANTINE}
        self.good={k:0 for k in "ABC"};self.bad={k:[] for k in "ABC"}
        self.stale={k:0 for k in "ABC"}
        self.count=Counter();self.last_record=None;self.last_seq=0;self.next_tick=1
        self.integrity=0;self.failures=0
    def reset(self,t,venue,reason):
        self.count["reset:"+venue+":"+reason]+=1
        if venue=="bybit":
            self.bybit_ack=False;self.bybit_pong=-1e12
            self.l1a.reset();self.l1b.reset();self.l50.reset()
            for k in "ABC":
                self.times[k]=None;self.quarantine[k]=max(self.quarantine[k],t+QUARANTINE)
        elif venue=="mexc":
            self.mexc_ack=False;self.mexc_pong=-1e12
            self.mexc_time=None;self.mexc_version=None
            for k in "ABC":self.quarantine[k]=max(self.quarantine[k],t+QUARANTINE)
    def healthy(self,key,t):
        own=self.times[key]
        return (t>=self.quarantine[key] and self.bybit_ack and self.mexc_ack
                and 0<=t-self.bybit_pong<=35 and 0<=t-self.mexc_pong<=35
                and self.mexc_time is not None and 0<=t-self.mexc_time<=1
                and own is not None and 0<=t-own<=1
                and (key!="C" or self.l50.ready))
    def tick(self,t):
        for k in "ABC":
            if self.times[k] is not None and t-self.times[k]>1:
                self.stale[k]+=1
                self.quarantine[k]=max(self.quarantine[k],t+QUARANTINE)
                self.times[k]=None
            if self.healthy(k,t):self.good[k]+=1
            else:self.bad[k].append(t)
    def feed(self,r):
        t=r["elapsed"];v=r["venue"];kind=r["kind"]
        while self.next_tick<t and self.next_tick<=WINDOW:
            self.tick(self.next_tick);self.next_tick+=1
        if self.last_record:
            p=self.last_record
            dtms=r["utc_ms"]-p["utc_ms"]
            dmono=(r["mono_ns"]-p["mono_ns"])/1e6
            if r["seq"]!=p["seq"]+1 or dmono<0 or dtms<-1 or abs(dtms-dmono)>250:
                self.integrity+=1
                self.reset(t,"bybit","CLOCK_SEQUENCE")
                self.reset(t,"mexc","CLOCK_SEQUENCE")
        self.last_record=r
        if kind in ("disconnect","fault"):
            self.failures+=1
            if v in ("bybit","mexc"):self.reset(t,v,kind.upper())
        elif kind=="connect":
            self.reset(t,v,"CONNECT")
        elif kind=="frame":
            try:
                m=json.loads(r["raw"])
                if v=="bybit":self._bybit(m,r,t)
                elif v=="mexc":self._mexc(m,r,t)
            except (SourceFault,ValueError,KeyError,TypeError,IndexError) as e:
                self.count["INVALID_"+v+":"+str(e)]+=1
                if v in ("bybit","mexc"):self.reset(t,v,"INVALID")
        if self.next_tick==t and self.next_tick<=WINDOW:
            self.tick(t);self.next_tick+=1
    def _bybit(self,m,r,t):
        if m.get("op")=="subscribe":
            if m.get("success") is not True:raise SourceFault("SUBSCRIPTION_REJECTED")
            self.bybit_ack=True;self.count["bybit_ack"]+=1
        if m.get("op")=="pong" or m.get("ret_msg")=="pong":
            self.bybit_pong=t;self.count["bybit_pong"]+=1
        topic=m.get("topic","")
        if topic=="orderbook.1.BTCUSDT":
            timestamp(m.get("ts"),r["utc_ms"])
            a=self.l1a.consume(m,t);b=self.l1b.consume(m,t)
            if a=="CHANGED":self.times["A"]=t
            if b in ("CHANGED","DUPLICATE_REFRESH"):self.times["B"]=t
            self.count["l1_"+a]+=1
        elif topic=="orderbook.50.BTCUSDT":
            timestamp(m.get("ts"),r["utc_ms"])
            status=self.l50.consume(m)
            if status in ("SNAPSHOT","DELTA"):self.times["C"]=t
            elif status=="RESET_U1_NEEDS_SNAPSHOT":self.times["C"]=None;self.quarantine["C"]=t+QUARANTINE
            self.count["l50_"+status]+=1
    def _mexc(self,m,r,t):
        channel=m.get("channel")
        if channel=="rs.sub.depth.full":
            if m.get("data") not in ("success",0,"0"):raise SourceFault("MEXC_SUB_FAIL")
            self.mexc_ack=True;self.count["mexc_ack"]+=1
        elif channel=="pong":
            self.mexc_pong=t;self.count["mexc_pong"]+=1
        elif channel=="push.depth.full":
            if m.get("symbol")!="BTC_USDT":raise SourceFault("MEXC_SYMBOL")
            timestamp(m.get("ts"),r["utc_ms"])
            d=m.get("data",{})
            try:version=int(d["version"])
            except (KeyError,ValueError,TypeError):raise SourceFault("MEXC_VERSION")
            if self.mexc_version is not None and version<=self.mexc_version:
                raise SourceFault("MEXC_VERSION_REGRESSION")
            for side in ("bids","asks"):
                rows=d.get(side)
                if not isinstance(rows,list) or len(rows)<5:raise SourceFault("MEXC_SHORT_BOOK")
                ps=[number(row[0]) for row in rows]
                for row in rows:number(row[1])
                if ps!=sorted(set(ps),reverse=side=="bids"):raise SourceFault("MEXC_UNSORTED")
            if number(d["bids"][0][0])>=number(d["asks"][0][0]):
                raise SourceFault("MEXC_CROSSED")
            self.mexc_version=version;self.mexc_time=t;self.count["mexc_full_book"]+=1
    def finish(self):
        while self.next_tick<=WINDOW:
            self.tick(self.next_tick);self.next_tick+=1
    def report(self,end_reason,elapsed,raw_bytes):
        def intervals(items):
            out=[]
            for x in items:
                if out and x==out[-1][-1]+1:out[-1][-1]=x
                else:out.append([x,x])
            return out
        cov={k:{"good":self.good[k],"bad":len(self.bad[k]),
                "fraction":self.good[k]/WINDOW,"stale_resets":self.stale[k],
                "bad_intervals":intervals(self.bad[k])} for k in "ABC"}
        candidate=(elapsed>=WINDOW and end_reason=="WALL_LIMIT"
                   and cov["C"]["fraction"]>=.95
                   and cov["C"]["fraction"]-cov["A"]["fraction"]>=.05
                   and self.integrity==0
                   and not any(key.startswith("INVALID_bybit") for key in self.count)
                   and not any(key.startswith("INVALID_mexc") for key in self.count)
                   and self.failures<=2 and self.l50.snapshot_count>0)
        adequate=(elapsed>=WINDOW and end_reason=="WALL_LIMIT"
                 and self.integrity==0 and self.l50.snapshot_count>0)
        verdict=("SOURCE_COMPARE_CANDIDATE" if candidate
                 else ("SOURCE_COMPARE_NO_GAIN" if adequate
                       else "SOURCE_COMPARE_BLOCKED"))
        return {"source_verdict":verdict,"economic_verdict":"ECONOMIC_INSUFFICIENT",
                "live_verdict":"NO_LIVE_GO","reason":end_reason,
                "elapsed_seconds":elapsed,"grid_seconds":WINDOW,
                "comparison":cov,"l50_snapshot_count":self.count["l50_SNAPSHOT"],
                "l50_delta_count":self.count["l50_DELTA"],
                "l1_duplicate_no_refresh":self.count["l1_DUPLICATE_IGNORED"],
                "mexc_books":self.count["mexc_full_book"],
                "integrity":self.integrity,"transport_faults":self.failures,
                "counts":dict(self.count),"raw_uncompressed_bytes":raw_bytes,
                "pnl":"NOT_COMPUTED_SOURCE_ONLY",
                "multiday_authorization":False}

async def capture(out):
    import websockets
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    engine=PairObserver();raw=out/"raw.jsonl.gz"
    start=time.monotonic_ns();seq=0;uncompressed=0;stop=asyncio.Event()
    reason="WALL_LIMIT";data_sha=hashlib.sha256()
    f=gzip.open(raw,"xb",compresslevel=4)
    def record(v,kind,payload,segment=0):
        nonlocal seq,uncompressed,reason
        seq+=1;mono=time.monotonic_ns()
        r={"seq":seq,"mono_ns":mono,"utc_ms":time.time_ns()//1_000_000,
           "elapsed":(mono-start)/1e9,"venue":v,"kind":kind,
           "segment":segment,"raw":payload}
        b=(json.dumps(r,separators=(",",":"),ensure_ascii=True)+"\n").encode()
        f.write(b);data_sha.update(b);uncompressed+=len(b)
        engine.feed(r)
        if uncompressed>256*1024**2 or f.tell()>64*1024**2:
            reason="STORAGE_CAP";stop.set()
    record("system","start",json.dumps({"protocol_sha256":hashlib.sha256(
        (HERE/"PROTOCOL_FROZEN.md").read_bytes()).hexdigest(),"window":WINDOW}))
    async def stream(v):
        nonlocal reason
        uri=BYBIT if v=="bybit" else MEXC
        sub=SUB_BYBIT if v=="bybit" else SUB_MEXC
        for segment in range(1,3):
            if stop.is_set():return
            if segment>1:
                try:await asyncio.wait_for(stop.wait(),timeout=2);return
                except asyncio.TimeoutError:pass
            try:
                async with websockets.connect(uri,open_timeout=10,close_timeout=2,
                           max_size=2_000_000,ping_interval=None) as ws:
                    record(v,"connect",uri,segment)
                    await ws.send(json.dumps(sub))
                    record(v,"subscription",json.dumps(sub),segment)
                    ping_due=0.;pong_time=time.monotonic()
                    while not stop.is_set():
                        now=time.monotonic()
                        elapsed=(time.monotonic_ns()-start)/1e9
                        if elapsed>=WINDOW:break
                        if now>=ping_due:
                            ping={"op":"ping"} if v=="bybit" else {"method":"ping"}
                            await ws.send(json.dumps(ping))
                            record(v,"ping",json.dumps(ping),segment)
                            ping_due=now+15
                        if now-pong_time>35:raise SourceFault("APPLICATION_PONG_TIMEOUT")
                        try:frame=await asyncio.wait_for(ws.recv(),timeout=min(1,max(.01,WINDOW-elapsed)))
                        except asyncio.TimeoutError:continue
                        if not isinstance(frame,str):raise SourceFault("UNSUPPORTED_BINARY")
                        record(v,"frame",frame,segment)
                        if engine.bybit_pong>=elapsed if v=="bybit" else engine.mexc_pong>=elapsed:
                            pong_time=time.monotonic()
            except Exception as e:
                record(v,"disconnect",json.dumps({"class":type(e).__name__,
                     "reason":str(e),"received_close":str(getattr(e,"rcvd",None)),
                     "sent_close":str(getattr(e,"sent",None))}),segment)
            if stop.is_set() or (time.monotonic_ns()-start)/1e9>=WINDOW:return
        reason="RECONNECT_EXHAUSTED";stop.set()
    async def timer():
        try:await asyncio.wait_for(stop.wait(),timeout=max(.001,WINDOW-(time.monotonic_ns()-start)/1e9))
        except asyncio.TimeoutError:stop.set()
    try:
        await asyncio.wait_for(asyncio.gather(stream("bybit"),stream("mexc"),timer()),
                               timeout=WINDOW+60)
    except Exception as e:
        reason="PROCESS_FAILURE";record("system","fault",repr(e))
    finally:
        elapsed=(time.monotonic_ns()-start)/1e9
        if elapsed<WINDOW and reason=="WALL_LIMIT":reason="EARLY_TERMINATION"
        record("system","end",reason);f.close()
        engine.finish()
        report=engine.report(reason,elapsed,uncompressed)
        (out/"report.json").write_text(json.dumps(report,indent=2))
        h=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
        manifest={"protocol_sha256":h(HERE/"PROTOCOL_FROZEN.md"),
                  "source_sha256":h(Path(__file__)),
                  "raw_sha256":data_sha.hexdigest(),
                  "gzip_sha256":h(raw),
                  "rows":seq,"end_reason":reason}
        (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
        print(json.dumps(report),flush=True)

def live_enabled():
    return False

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: python compare.py OUTPUT_DIRECTORY")
    asyncio.run(capture(Path(sys.argv[1])))
