#!/usr/bin/env python3
import asyncio, bisect, json, statistics, time, urllib.request
from pathlib import Path

BINANCE_WS="wss://fstream.binance.com/ws/btcusdt@bookTicker"
MEXC_WS="wss://contract.mexc.com/edge"
MEXC_REST="https://contract.mexc.com/api/v1/contract/depth/BTC_USDT?limit=200"
DURATION=180
WINDOWS_MS=(250,500,1000)
THRESHOLDS_BPS=(2.0,5.0,10.0)
HORIZONS_MS=(100,250,500,1000,2000,5000)
COOLDOWN_MS=1000
MAX_STATE_AGE_MS=500
MEXC_TAKER_RT_BPS=16.0


def rest_snapshot():
    req=urllib.request.Request(MEXC_REST,headers={"User-Agent":"Crypto-Lab-XVenue/0.1"})
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))["data"]


class MexcBook:
    def __init__(self,snap):
        self.bids={float(x[0]):float(x[1]) for x in snap["bids"] if float(x[1])!=0}
        self.asks={float(x[0]):float(x[1]) for x in snap["asks"] if float(x[1])!=0}
        self.version=int(snap["version"])

    @staticmethod
    def apply_side(book,rows):
        for row in rows or []:
            p=float(row[0]); q=float(row[1])
            if q==0: book.pop(p,None)
            else: book[p]=q

    def apply(self,d):
        v=int(d["version"])
        if v != self.version+1:
            raise RuntimeError(f"MEXC_VERSION_GAP:{self.version}->{v}")
        self.apply_side(self.bids,d.get("bids"))
        self.apply_side(self.asks,d.get("asks"))
        self.version=v
        if not self.bids or not self.asks:
            raise RuntimeError("MEXC_EMPTY_BOOK")
        b=max(self.bids); a=min(self.asks)
        if b>=a: raise RuntimeError(f"MEXC_CROSSED:{b}>={a}")
        return b,a


async def binance_collect(stop_at):
    import websockets
    rows=[]
    async with websockets.connect(BINANCE_WS,ping_interval=20,close_timeout=5,max_size=2_000_000) as ws:
        while time.monotonic()<stop_at:
            try: raw=await asyncio.wait_for(ws.recv(),timeout=5)
            except asyncio.TimeoutError: continue
            recv_ns=time.time_ns()
            if isinstance(raw,bytes): raw=raw.decode()
            m=json.loads(raw)
            b=float(m["b"]); a=float(m["a"])
            if b>=a: raise RuntimeError("BINANCE_CROSSED")
            rows.append((recv_ns,b,a,int(m.get("E",0)),int(m.get("T",0))))
    return rows


async def mexc_collect(stop_at):
    import websockets
    q=asyncio.Queue()
    stats={"sync_attempts":0,"discarded_pre_snapshot":0,"applied":0,"version_gaps":0}

    async with websockets.connect(MEXC_WS,ping_interval=None,close_timeout=5,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"BTC_USDT","compress":False}}))

        async def recv_loop():
            last_ping=time.monotonic()
            while time.monotonic()<stop_at:
                if time.monotonic()-last_ping>10:
                    await ws.send(json.dumps({"method":"ping"})); last_ping=time.monotonic()
                try: raw=await asyncio.wait_for(ws.recv(),timeout=3)
                except asyncio.TimeoutError: continue
                recv_ns=time.time_ns()
                if isinstance(raw,bytes): raw=raw.decode("utf-8","replace")
                m=json.loads(raw)
                if m.get("channel")=="push.depth":
                    await q.put((recv_ns,m.get("data") or {}))

        receiver=asyncio.create_task(recv_loop())
        book=None; first_state=None

        for attempt in range(5):
            stats["sync_attempts"]+=1
            snap=await asyncio.to_thread(rest_snapshot)
            candidate=MexcBook(snap)
            deadline=time.monotonic()+5
            synced=False
            while time.monotonic()<deadline:
                try: recv_ns,d=await asyncio.wait_for(q.get(),timeout=1)
                except asyncio.TimeoutError: continue
                v=int(d.get("version",0))
                if v<=candidate.version:
                    stats["discarded_pre_snapshot"]+=1
                    continue
                if v!=candidate.version+1:
                    stats["version_gaps"]+=1
                    break
                b,a=candidate.apply(d)
                book=candidate
                first_state=(recv_ns,b,a,book.version)
                synced=True
                break
            if synced: break

        if book is None:
            receiver.cancel()
            raise RuntimeError("MEXC_SNAPSHOT_DELTA_SYNC_FAILED")

        rows=[first_state]
        while time.monotonic()<stop_at:
            try: recv_ns,d=await asyncio.wait_for(q.get(),timeout=2)
            except asyncio.TimeoutError: continue
            v=int(d.get("version",0))
            if v<=book.version: continue
            if v!=book.version+1:
                stats["version_gaps"]+=1
                receiver.cancel()
                raise RuntimeError(f"MEXC_VERSION_GAP:{book.version}->{v}")
            b,a=book.apply(d); stats["applied"]+=1
            if rows and rows[-1][1]==b and rows[-1][2]==a:
                continue
            rows.append((recv_ns,b,a,book.version))

        receiver.cancel()
        try: await receiver
        except BaseException: pass
        return rows,stats


def latest_state(times,rows,t_ns):
    i=bisect.bisect_right(times,t_ns)-1
    if i<0: return None
    age_ms=(t_ns-times[i])/1_000_000
    if age_ms>MAX_STATE_AGE_MS: return None
    return rows[i]


def leader_prior_mid(times,mids,t_ns,window_ms):
    target=t_ns-window_ms*1_000_000
    i=bisect.bisect_right(times,target)-1
    if i<0: return None
    return mids[i]


def percentile(xs,p):
    if not xs: return None
    s=sorted(xs); return s[int((len(s)-1)*p)]


def analyze(bin_rows,mex_rows):
    bt=[x[0] for x in bin_rows]; bm=[(x[1]+x[2])/2 for x in bin_rows]
    mt=[x[0] for x in mex_rows]
    start=max(bt[0],mt[0]); end=min(bt[-1],mt[-1])
    variants={}
    economic=False

    for w in WINDOWS_MS:
        for th in THRESHOLDS_BPS:
            key=f"W{w}_T{th:g}"
            events=[]; last_event_ns=None
            for i,t in enumerate(bt):
                if t<start or t>end: continue
                p0=leader_prior_mid(bt,bm,t,w)
                if p0 is None: continue
                shock=(bm[i]-p0)/p0*10000.0
                if abs(shock)<th: continue
                if last_event_ns is not None and (t-last_event_ns)/1_000_000<COOLDOWN_MS: continue
                entry=latest_state(mt,mex_rows,t)
                if entry is None: continue
                d=1 if shock>0 else -1
                rec={"t_ns":t,"shock_bps":shock,"direction":d,"entry_bid":entry[1],"entry_ask":entry[2]}
                events.append(rec); last_event_ns=t

            hs={}
            for h in HORIZONS_MS:
                mids=[]; gross=[]
                for e in events:
                    fut=latest_state(mt,mex_rows,e["t_ns"]+h*1_000_000)
                    if fut is None: continue
                    eb,ea=e["entry_bid"],e["entry_ask"]; fb,fa=fut[1],fut[2]
                    em=(eb+ea)/2; fm=(fb+fa)/2; d=e["direction"]
                    mids.append(d*(fm-em)/em*10000.0)
                    if d>0: gross.append((fb-ea)/ea*10000.0)
                    else: gross.append((eb-fa)/eb*10000.0)
                rec={
                  "n":len(gross),
                  "mean_directional_mid_bps":statistics.fmean(mids) if mids else None,
                  "mean_taker_gross_bps":statistics.fmean(gross) if gross else None,
                  "mean_taker_fee_net_bps":statistics.fmean(gross)-MEXC_TAKER_RT_BPS if gross else None,
                  "p95_taker_gross_bps":percentile(gross,.95) if gross else None,
                }
                if rec["n"]>=5 and rec["mean_taker_fee_net_bps"]>0:
                    economic=True
                hs[str(h)]=rec

            catch=[]
            for e in events:
                target=.5*abs(e["shock_bps"])
                base=(e["entry_bid"]+e["entry_ask"])/2
                i=bisect.bisect_left(mt,e["t_ns"])
                for j in range(i,len(mex_rows)):
                    delay=(mt[j]-e["t_ns"])/1_000_000
                    if delay<0: continue
                    if delay>5000: break
                    mid=(mex_rows[j][1]+mex_rows[j][2])/2
                    move=e["direction"]*(mid-base)/base*10000.0
                    if move>=target:
                        catch.append(delay); break

            variants[key]={
              "event_count":len(events),
              "horizons":hs,
              "catchup_50pct":{
                "n":len(catch),
                "median_ms":statistics.median(catch) if catch else None,
                "p95_ms":percentile(catch,.95) if catch else None,
              }
            }

    return {
      "overlap_seconds":(end-start)/1e9,
      "binance_states":len(bin_rows),
      "mexc_bbo_states":len(mex_rows),
      "variants":variants,
      "economic_signal_sample":economic,
    }


async def run():
    stop_at=time.monotonic()+DURATION
    btask=asyncio.create_task(binance_collect(stop_at))
    mtask=asyncio.create_task(mexc_collect(stop_at))
    b,(m,stats)=await asyncio.gather(btask,mtask)
    return b,m,stats


def main():
    result={"purpose":"PUBLIC FORWARD LEAD-LAG MVE — NO ORDERS","duration_seconds":DURATION}
    try:
        b,m,stats=asyncio.run(run())
        result["mexc_integrity"]=stats
        result["analysis"]=analyze(b,m)
        result["decision"]="FORWARD_ECONOMIC_SIGNAL_SAMPLE" if result["analysis"]["economic_signal_sample"] else "FORWARD_PLUMBING_PASS_NO_ECONOMIC_SIGNAL"
    except Exception as e:
        result["decision"]="BLOCKED"; result["error"]=repr(e)
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"xvenue_lag_005_forward_mve_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"]!="BLOCKED" else 2)

if __name__=="__main__":
    main()
