#!/usr/bin/env python3
import asyncio,json,statistics,time
from pathlib import Path
import websockets

BINANCE="wss://fstream.binance.com/ws/btcusdt@bookTicker"
MEXC="wss://contract.mexc.com/edge"
SECONDS=600
STALE_MS=1000
BINS=(1,2,5,10,12,16,20)

async def bstream(q,stop):
    async with websockets.connect(BINANCE,ping_interval=20,ping_timeout=20,max_size=2**20) as ws:
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError: continue
            m=json.loads(raw); now=time.monotonic_ns()
            await q.put(("binance",now,float(m["b"]),float(m["a"])))

async def mstream(q,stop):
    bids={};asks={}
    async with websockets.connect(MEXC,ping_interval=None,max_size=2**22) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"BTC_USDT"}}))
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError:
                try: await ws.send(json.dumps({"method":"ping"}))
                except: pass
                continue
            m=json.loads(raw)
            if m.get("channel")!="push.depth": continue
            d=m.get("data") or {}
            for p,qy,*_ in d.get("bids",[]):
                p=float(p);qy=float(qy)
                if qy==0:bids.pop(p,None)
                else:bids[p]=qy
            for p,qy,*_ in d.get("asks",[]):
                p=float(p);qy=float(qy)
                if qy==0:asks.pop(p,None)
                else:asks[p]=qy
            if bids and asks:
                await q.put(("mexc",time.monotonic_ns(),max(bids),min(asks)))

async def observer(q,stop):
    latest={}; vals=[]; counts={str(b):0 for b in BINS}; episodes=[]; ep=None
    fresh=0; total=0
    while not stop.is_set() or not q.empty():
        try:v,now,bid,ask=await asyncio.wait_for(q.get(),.2)
        except asyncio.TimeoutError:continue
        latest[v]=(now,bid,ask)
        if len(latest)<2:continue
        total+=1
        bt,bb,ba=latest["binance"]; mt,mb,ma=latest["mexc"]
        ages=((now-bt)/1e6,(now-mt)/1e6)
        if max(ages)>STALE_MS:
            if ep:
                ep["end_ns"]=now;ep["duration_ms"]=(now-ep["start_ns"])/1e6;episodes.append(ep);ep=None
            continue
        fresh+=1
        g_m_to_b=(bb-ma)/ma*10000
        g_b_to_m=(mb-ba)/ba*10000
        g=max(g_m_to_b,g_b_to_m)
        direction="BUY_MEXC_SELL_BINANCE" if g_m_to_b>=g_b_to_m else "BUY_BINANCE_SELL_MEXC"
        vals.append(g)
        for b in BINS:
            if g>b:counts[str(b)]+=1
        if g>1:
            if ep is None:
                ep={"start_ns":now,"peak_bps":g,"direction":direction,"updates":1}
            else:
                ep["updates"]+=1
                if g>ep["peak_bps"]:ep["peak_bps"]=g;ep["direction"]=direction
        elif ep:
            ep["end_ns"]=now;ep["duration_ms"]=(now-ep["start_ns"])/1e6;episodes.append(ep);ep=None
    if ep:
        now=time.monotonic_ns();ep["end_ns"]=now;ep["duration_ms"]=(now-ep["start_ns"])/1e6;episodes.append(ep)
    vals_sorted=sorted(vals)
    def pct(p):
        return vals_sorted[int((len(vals_sorted)-1)*p)] if vals_sorted else None
    return {"total_paired_updates":total,"fresh_updates":fresh,"counts_above_bps":counts,
            "median_gap_bps":statistics.median(vals) if vals else None,
            "p95_gap_bps":pct(.95),"p99_gap_bps":pct(.99),
            "max_gap_bps":max(vals) if vals else None,
            "episodes":episodes,
            "episode_count":len(episodes)}

async def main_async():
    q=asyncio.Queue();stop=asyncio.Event()
    a=asyncio.create_task(bstream(q,stop));b=asyncio.create_task(mstream(q,stop));o=asyncio.create_task(observer(q,stop))
    await asyncio.sleep(SECONDS);stop.set()
    await asyncio.gather(a,b,return_exceptions=True)
    res=await o
    receipt={"status":"FORWARD_OBSERVATION","seconds":SECONDS,"stale_ms":STALE_MS,**res}
    out=Path("research/microstructure_scalping/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"xven_disloc_001_forward_10m_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":asyncio.run(main_async())
