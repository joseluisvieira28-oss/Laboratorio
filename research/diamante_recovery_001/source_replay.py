"""Frozen before new archive access. Source qualification + separate historical diagnostic.
Never publish raw/derived row-level data. Not exact prospective BINANCE004 replication.
"""
import datetime as dt, urllib.request as u, urllib.parse as p, pathlib, hashlib, json, tempfile, itertools, statistics, collections, math
from decimal import Decimal as D
import pyarrow.parquet as pq
import zstandard as zstd
SYMBOL="SOLUSDT"
HOUR="2026-11-20/12"
START=int(dt.datetime(2026,11,20,12,tzinfo=dt.timezone.utc).timestamp())*10**9
NS=10**9
CAP=80*1024**2
COLS=["received_time","event_time","symbol","event_type","first_update_id","final_update_id","last_update_id","side","price","quantity"]
TRCOLS=["received_time","event_time","trade_time","symbol","trade_id","price","quantity","is_buyer_maker"]
def fail(reason):raise ValueError(reason)
def fetch(root,kind,report):
    path=f"binance_spot/{HOUR}/{SYMBOL}_{kind}.parquet"
    url="https://api.cryptohftdata.com/v1/download?"+p.urlencode({"file":path})
    raw=root/(kind+".bin"); out=root/(kind+".parquet")
    h=hashlib.sha256();n=0
    with u.urlopen(u.Request(url,headers={"User-Agent":"RECOVERY-001-internal-research"}),timeout=40) as res, raw.open("wb") as f:
        report[kind]={"http":res.status,"path":path}
        while chunk:=res.read(1024*1024):
            n+=len(chunk)
            if n>CAP:fail("compressed_cap")
            h.update(chunk);f.write(chunk)
    report[kind].update(bytes=n,sha256=h.hexdigest())
    with raw.open("rb") as f:
        magic=f.read(4);f.seek(0)
        if magic==b"PAR1":out=raw
        elif magic==bytes.fromhex("28b52ffd"):
            with zstd.ZstdDecompressor().stream_reader(f) as z,out.open("wb") as o:
                size=0
                while chunk:=z.read(1024*1024):
                    size+=len(chunk)
                    if size>512*1024**2:fail("decompressed_cap")
                    o.write(chunk)
        else:fail("container_magic")
    pf=pq.ParquetFile(out)
    report[kind].update(rows=pf.metadata.num_rows,columns=pf.schema_arrow.names)
    if not 0<pf.metadata.num_rows<=4_000_000:fail("row_cap_or_empty")
    return pf
def rows(pf,cols):
    if not set(cols)<=set(pf.schema_arrow.names):fail("missing_schema")
    for batch in pf.iter_batches(batch_size=8192,columns=cols):
        yield from batch.to_pylist()
def clock(r,trade=False):
    t=r["received_time"]
    if type(t)!=int or not START<=t<START+3600*NS:fail("received_clock_outside_hour")
    times=[r["event_time"]]+([r["trade_time"]] if trade else [])
    return all(type(x)==int and -1000<=t//10**6-x<=3000 for x in times)
def dec(x,positive=False):
    v=D(str(x))
    if not v.is_finite() or v<0 or (positive and v==0):fail("invalid_numeric")
    return v
def key(r):
    return tuple(r[k] for k in COLS[:7])
def book_events(pf):
    for k,g in itertools.groupby(rows(pf,COLS),key):
        yield k,list(g)
def check_source(book,trade):
    b={};a={};last=None;prev=None;counts=collections.Counter();first=None;last_t=None;bad_clocks=0;max_gap=0;prev_update=None
    for k,rr in book_events(book):
        t,e,s,kind,U,v,L=k
        if s!=SYMBOL or (prev is not None and t<prev):fail("book_identity_or_order")
        fresh=clock(rr[0]);prev=t;first=t if first is None else first;last_t=t
        if kind=="snapshot":
            if type(L)!=int or v!=L:fail("snapshot_ID")
            if counts["snapshot"]>0:fail("extra_snapshot_or_reset")
            b.clear();a.clear();last=L;counts["snapshot"]+=1
        elif kind=="update":
            if last is None or type(U)!=int or type(v)!=int or U>v:fail("missing_initial_snapshot_or_sequence")
            if v<=last:fail("duplicate_or_reordered_update")
            if not U<=last+1<=v:fail("sequence_gap")
            last=v;counts["update"]+=1
            if not fresh:bad_clocks+=1
            if prev_update is not None:max_gap=max(max_gap,t-prev_update)
            prev_update=t
        else:fail("event_type")
        seen=set()
        for r in rr:
            side=r["side"]
            if side=="noop":
                if len(rr)!=1 or dec(r["price"])!=0 or dec(r["quantity"])!=0:fail("bad_noop")
                continue
            if side not in ("bid","ask"):fail("unknown_side")
            price=dec(r["price"],True);qty=dec(r["quantity"])
            if (side,price) in seen:fail("duplicate_level")
            seen.add((side,price));d=b if side=="bid" else a
            if qty:d[price]=qty
            else:d.pop(price,None)
        if not b or not a or max(b)>=min(a):fail("empty_or_crossed_book")
        if len(b)+len(a)>200000:fail("book_level_cap")
    if counts["snapshot"]!=1 or counts["update"]<500:fail("insufficient_updates")
    if first>START+2*NS or last_t<START+3598*NS or max_gap>3*NS:fail("hour_coverage")
    prev=None;last_id=None;tc=0;trade_bad=0
    for r in rows(trade,TRCOLS):
        t=r["received_time"]
        if r["symbol"]!=SYMBOL or (prev is not None and t<prev):fail("trade_identity_or_order")
        if not clock(r,True):trade_bad+=1
        i=r["trade_id"]
        if type(i)!=int or (last_id is not None and i!=last_id+1):fail("trade_id_gap_or_duplicate")
        if type(r["is_buyer_maker"])!=bool:fail("trade_side")
        dec(r["price"],True);dec(r["quantity"],True)
        prev=t;last_id=i;tc+=1
    if tc<1:fail("no_trades")
    return dict(book_messages=dict(counts),trade_rows=tc,max_book_update_gap_ms=max_gap/1e6,bad_update_clocks=bad_clocks,bad_trade_clocks=trade_bad,full_hour_bounds=True)
def pilot(book,trade):
    # Distinct one-symbol historical provider-clock adaptation. 30s UTC buckets,
    # begin at hour+30s, no pre-snapshot trades, last decision at +3510s.
    # Only observed 10bps band inside original snapshot price envelope.
    b={};a={};lo=hi=None;start=None;last_time=None;last_dec={};events=[];idx=1;win_updates=0;sell=buy=D(0);valid=pressure=primary=0
    trade_iter=iter(rows(trade,TRCOLS));tr=next(trade_iter,None)
    def snap(t):
        if not b or not a or last_time is None or t-last_time>2*NS:return None
        bid=max(b);ask=min(a);mid=(bid+ask)/2
        floor=mid*D("0.999")
        if floor<lo or ask>hi or bid<lo:return None
        depth=sum((p*q for p,q in b.items() if floor<=p<=mid),D(0))
        return (mid,depth) if depth>0 else None
    def buyq(n):
        left=n;units=D(0)
        for p in sorted(a):
            if p>hi:break
            take=min(left,p*a[p]);left-=take;units+=take/p
            if left<=0:return units
        return None
    def sellq(units):
        left=units;out=D(0)
        for p in sorted(b,reverse=True):
            if p<lo:break
            take=min(left,b[p]);left-=take;out+=take*p
            if left<=0:return out
        return None
    def close(t):
        nonlocal idx,start,win_updates,sell,buy,valid,pressure,primary
        end=snap(t)
        if idx>=2 and start and end and win_updates:
            valid+=1;total=sell+buy
            pressured=total>=5000 and sell/total>=D(".65")
            resilient=pressured and end[1]/start[1]>=D(".8") and (end[0]/start[0]-1)*10000>=-3
            pressure+=pressured;primary+=resilient
            kinds=[]
            if pressured:kinds.append("PRIMARY" if resilient else "FLOW_ONLY_CONTROL")
            if (idx-2)%4==3:kinds.append("UNCONDITIONAL_BASELINE")
            if t<=START+3510*NS:
                for kind in kinds:
                    if t-last_dec.get(kind,-10**30)>=120*NS:
                        last_dec[kind]=t;events.append({"kind":kind,"decision":t,"state":"WAIT"})
        start=end;idx+=1;win_updates=0;sell=buy=D(0)
    for k,rr in book_events(book):
        t,e,s,kind,U,v,L=k
        while True:
            boundary=START+idx*30*NS
            nxt=tr["received_time"] if tr is not None else 10**30
            if boundary<=t and boundary<=nxt:close(boundary);continue
            if nxt<t:
                q=dec(tr["price"],True)*dec(tr["quantity"],True)
                if tr["is_buyer_maker"]:sell+=q
                else:buy+=q
                tr=next(trade_iter,None);continue
            break
        if kind=="snapshot":b.clear();a.clear()
        for r in rr:
            if r["side"]=="noop":continue
            p=dec(r["price"],True);q=dec(r["quantity"])
            d=b if r["side"]=="bid" else a
            if q:d[p]=q
            else:d.pop(p,None)
        if kind=="snapshot":lo=min(b);hi=max(a)
        last_time=t
        if kind!="update":continue
        win_updates+=1
        for ev in events:
            if ev["state"]=="WAIT" and t>ev["decision"]:
                if t-ev["decision"]>3*NS:ev["state"]="CENSORED";continue
                units={n:buyq(D(n)) for n in (100,1000)} if min(a)<=hi and max(b)>=lo else {}
                if len(units)!=2 or any(v is None for v in units.values()):ev["state"]="CENSORED";continue
                ev.update(state="OPEN",entry=t,units=units)
            elif ev["state"]=="OPEN" and t>=ev["entry"]+60*NS:
                if t-ev["entry"]-60*NS>3*NS:ev["state"]="CENSORED";continue
                proceeds={n:sellq(v) for n,v in ev["units"].items()} if min(a)<=hi and max(b)>=lo else {}
                if len(proceeds)!=2 or any(v is None for v in proceeds.values()):ev["state"]="CENSORED";continue
                ev["net"]={f"{n}_{slip}":float((proceeds[n]*(1-D(10+slip)/10000)/(D(n)*(1+D(10+slip)/10000))-1)*10000) for n in proceeds for slip in (2,5)}
                ev["state"]="MATURED"
    stats={}
    for kind in ("PRIMARY","FLOW_ONLY_CONTROL","UNCONDITIONAL_BASELINE"):
        ev=[x for x in events if x["kind"]==kind];m=[x for x in ev if x["state"]=="MATURED"]
        stats[kind]={"decisions":len(ev),"matured":len(m),"censored":len(ev)-len(m),"net_bps":{f"{n}_{s}":{"mean":statistics.mean(v),"positive":sum(x>0 for x in v)} if (v:=[x["net"][f"{n}_{s}"] for x in m]) else None for n in (100,1000) for s in (2,5)}}
    return dict(valid_windows=valid,sell_pressure_windows=pressure,resilient_windows=primary,groups=stats,independent_days=1)
def main():
    report={"classification":"SOURCE_BLOCKED","source":{},"scope":f"binance_spot/{HOUR}/{SYMBOL}","economic_go":False,"raw_data_published":False}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            book=fetch(pathlib.Path(tmp),"orderbook",report["source"])
            trade=fetch(pathlib.Path(tmp),"trades",report["source"])
            qual=check_source(book,trade);report["qualification"]=qual
            if qual["bad_update_clocks"] or qual["bad_trade_clocks"]:fail("source_clock_invalid")
            report["classification"]="BOUNDED_SOURCE_REPLAY_PASS"
            report["historical_proxy"]=pilot(book,trade)
            report["classification"]="ONE_HOUR_HISTORICAL_PROXY_INCONCLUSIVE"
    except Exception as e:
        report["classification"]="SOURCE_OR_PILOT_BLOCKED"
        # Never print market rows/exception values beyond our own controlled errors.
        report["error_type"]=type(e).__name__
        if type(e)==ValueError and len(e.args)==1 and isinstance(e.args[0],str) and e.args[0].replace("_","").isalnum():report["reason"]=e.args[0]
        if hasattr(e,"code"):report["http_error"]=e.code
    print("RECOVERY_RECEIPT",json.dumps(report,sort_keys=True))
if __name__=="__main__":main()
