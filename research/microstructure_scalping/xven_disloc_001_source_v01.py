#!/usr/bin/env python3
import asyncio, json, statistics, time
from pathlib import Path
import websockets

BINANCE="wss://fstream.binance.com/ws/btcusdt@bookTicker"
MEXC="wss://contract.mexc.com/edge"
SECONDS=60
STALE_MS=1000

async def binance(q,stop):
    count=0; crossed=0; regress=0; last_local=None
    async with websockets.connect(BINANCE,ping_interval=20,ping_timeout=20,max_size=2**20) as ws:
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError: continue
            now=time.monotonic_ns()
            m=json.loads(raw)
            bid=float(m["b"]); ask=float(m["a"])
            if bid>=ask: crossed+=1
            if last_local is not None and now<last_local: regress+=1
            last_local=now; count+=1
            await q.put(("binance",now,{"bid":bid,"ask":ask,"venue_ts":m.get("E")}))
    return {"count":count,"crossed":crossed,"local_clock_regressions":regress}

async def mexc(q,stop):
    count=0; crossed=0; regress=0; last_local=None
    bids={}; asks={}
    async with websockets.connect(MEXC,ping_interval=None,max_size=2**22) as ws:
        sub={"method":"sub.depth","param":{"symbol":"BTC_USDT"}}
        await ws.send(json.dumps(sub))
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError:
                try: await ws.send(json.dumps({"method":"ping"}))
                except Exception: pass
                continue
            now=time.monotonic_ns()
            m=json.loads(raw)
            if m.get("channel")!="push.depth": continue
            d=m.get("data") or {}
            for p,qy,*_ in d.get("bids",[]):
                p=float(p); qy=float(qy)
                if qy==0: bids.pop(p,None)
                else: bids[p]=qy
            for p,qy,*_ in d.get("asks",[]):
                p=float(p); qy=float(qy)
                if qy==0: asks.pop(p,None)
                else: asks[p]=qy
            if not bids or not asks: continue
            bid=max(bids); ask=min(asks)
            if bid>=ask: crossed+=1
            if last_local is not None and now<last_local: regress+=1
            last_local=now; count+=1
            await q.put(("mexc",now,{"bid":bid,"ask":ask,"venue_ts":d.get("timestamp") or m.get("ts")}))
    return {"count":count,"crossed":crossed,"local_clock_regressions":regress}

async def observe(q,stop):
    latest={}; gaps=[]; fresh_gaps=[]; obs=0
    while not stop.is_set() or not q.empty():
        try: venue,now,x=await asyncio.wait_for(q.get(),timeout=.2)
        except asyncio.TimeoutError: continue
        latest[venue]=(now,x)
        if len(latest)<2: continue
        b_t,b=latest["binance"]; m_t,m=latest["mexc"]
        age_b=(now-b_t)/1e6; age_m=(now-m_t)/1e6
        g1=(b["bid"]-m["ask"])/m["ask"]*10000.0
        g2=(m["bid"]-b["ask"])/b["ask"]*10000.0
        mx=max(g1,g2); gaps.append(mx); obs+=1
        if age_b<=STALE_MS and age_m<=STALE_MS: fresh_gaps.append(mx)
    return {"paired_observations":obs,"fresh_paired_observations":len(fresh_gaps),
            "max_executable_gap_bps":max(gaps) if gaps else None,
            "max_fresh_executable_gap_bps":max(fresh_gaps) if fresh_gaps else None,
            "median_fresh_executable_gap_bps":statistics.median(fresh_gaps) if fresh_gaps else None}

async def main_async():
    q=asyncio.Queue(); stop=asyncio.Event()
    tasks=[asyncio.create_task(binance(q,stop)),asyncio.create_task(mexc(q,stop))]
    obs=asyncio.create_task(observe(q,stop))
    await asyncio.sleep(SECONDS); stop.set()
    src=await asyncio.gather(*tasks,return_exceptions=True)
    o=await obs
    def norm(x):
        return {"error":repr(x)} if isinstance(x,Exception) else x
    receipt={"status":"SOURCE_GATE_SAMPLE","seconds":SECONDS,"stale_ms":STALE_MS,
             "binance":norm(src[0]),"mexc":norm(src[1]),"paired":o}
    good=all(isinstance(x,dict) and x.get("count",0)>=50 and x.get("crossed")==0 and x.get("local_clock_regressions")==0 for x in src)
    # Source feasibility is about continuous valid coverage, not an arbitrary venue update rate.
    receipt["gate"]="PASS_SAMPLE" if good and o["fresh_paired_observations"]>=100 else "BLOCKED"
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"xven_disloc_001_source_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if receipt["gate"]=="PASS_SAMPLE" else 2

def main():
    raise SystemExit(asyncio.run(main_async()))

if __name__=="__main__": main()
