#!/usr/bin/env python3
import asyncio,bisect,json,math,statistics,time,urllib.request
from pathlib import Path

DURATION=180
CALIBRATION_S=60
GRID_MS=50
LEADER_WINDOWS=(100,250)
PCTS=(0.95,0.99)
FUTURES=(100,250,500,1000)

BINANCE_WS="wss://fstream.binance.com/ws/btcusdt@bookTicker"
BYBIT_WS="wss://stream.bybit.com/v5/public/linear"
MEXC_WS="wss://contract.mexc.com/edge"
MEXC_REST="https://api.mexc.com/api/v1/contract/depth/BTC_USDT?limit=20"


def qtile(xs,p):
    s=sorted(xs)
    return s[int((len(s)-1)*p)] if s else None


def mono_ms():
    return time.monotonic_ns()/1_000_000.0


def wall_ms():
    return int(time.time()*1000)


def row_price_qty(row):
    p=float(row[0])
    q=float(row[-1])
    return p,q


async def binance_collector(out,stop):
    import websockets
    async with websockets.connect(BINANCE_WS,ping_interval=None,close_timeout=5,max_size=2_000_000) as ws:
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError: continue
            m=json.loads(raw)
            try:
                b=float(m["b"]);a=float(m["a"])
                if b>0 and a>b:
                    out.append((mono_ms(),wall_ms(),b,a,m.get("E"),m.get("T"),m.get("u")))
            except Exception:
                continue


async def bybit_collector(out,stop):
    import websockets
    async with websockets.connect(BYBIT_WS,ping_interval=20,ping_timeout=20,close_timeout=5,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"op":"subscribe","args":["orderbook.1.BTCUSDT"]}))
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError: continue
            m=json.loads(raw)
            if m.get("topic")!="orderbook.1.BTCUSDT": continue
            d=m.get("data") or {}
            try:
                b=float(d["b"][0][0]);a=float(d["a"][0][0])
                if b>0 and a>b:
                    out.append((mono_ms(),wall_ms(),b,a,m.get("ts"),d.get("cts"),d.get("u")))
            except Exception:
                continue


def mexc_snapshot():
    req=urllib.request.Request(MEXC_REST,headers={"User-Agent":"Crypto-Lab-XVenue/0.1"})
    with urllib.request.urlopen(req,timeout=15) as r:
        j=json.loads(r.read().decode("utf-8"))
    d=j["data"]
    bids={};asks={}
    for row in d.get("bids",[]):
        p,q=row_price_qty(row)
        if q>0:bids[p]=q
    for row in d.get("asks",[]):
        p,q=row_price_qty(row)
        if q>0:asks[p]=q
    return bids,asks,int(d["version"]),d.get("timestamp")


async def mexc_collector(out,stop,diag):
    import websockets
    bids,asks,last_version,snap_ts=await asyncio.to_thread(mexc_snapshot)
    diag["snapshot_version"]=last_version
    diag["snapshot_ts"]=snap_ts
    async with websockets.connect(MEXC_WS,ping_interval=None,close_timeout=5,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"BTC_USDT"},"gzip":False}))
        last_ping=mono_ms()
        while not stop.is_set():
            if mono_ms()-last_ping>10000:
                await ws.send(json.dumps({"method":"ping"}));last_ping=mono_ms()
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError: continue
            if isinstance(raw,bytes): raw=raw.decode("utf-8","replace")
            m=json.loads(raw)
            if m.get("channel")!="push.depth": continue
            d=m.get("data") or {}
            try:v=int(d["version"])
            except Exception:continue
            if v<=last_version:
                continue
            if v!=last_version+1:
                diag["version_gaps"]+=1
                # Fail closed for analysis after any gap.
                diag["invalid_after_gap"]=True
                stop.set()
                break
            for row in d.get("bids",[]):
                p,q=row_price_qty(row)
                if q==0:bids.pop(p,None)
                else:bids[p]=q
            for row in d.get("asks",[]):
                p,q=row_price_qty(row)
                if q==0:asks.pop(p,None)
                else:asks[p]=q
            last_version=v
            if bids and asks:
                b=max(bids);a=min(asks)
                if a>b:
                    out.append((mono_ms(),wall_ms(),b,a,m.get("ts"),d.get("cts"),v))
    diag["last_version"]=last_version


def latest_at(rows,t):
    ts=[x[0] for x in rows]
    i=bisect.bisect_right(ts,t)-1
    return rows[i] if i>=0 else None


def build_grid(series,start,end):
    ts_cache={k:[x[0] for x in v] for k,v in series.items()}
    grid=[]
    t=start
    while t<=end:
        rec={"t":t};ok=True
        for k,rows in series.items():
            idx=bisect.bisect_right(ts_cache[k],t)-1
            if idx<0:ok=False;break
            x=rows[idx]
            # Stale quote >1s invalidates this grid point.
            if t-x[0]>1000:ok=False;break
            rec[k]={"bid":x[2],"ask":x[3],"mid":(x[2]+x[3])/2.0}
        if ok:grid.append(rec)
        t+=GRID_MS
    return grid


def bps(a,b):
    return (b-a)/a*10000.0


def value_at(grid,i,delta_ms):
    steps=int(round(delta_ms/GRID_MS))
    j=i+steps
    return grid[j] if 0<=j<len(grid) else None


def main_analysis(series,diag):
    if diag.get("invalid_after_gap"):
        return {"decision":"BLOCKED_MEXC_VERSION_GAP","diag":diag}
    counts={k:len(v) for k,v in series.items()}
    if min(counts.values())<20:
        return {"decision":"BLOCKED_INSUFFICIENT_QUOTES","counts":counts,"diag":diag}

    start=max(v[0][0] for v in series.values())
    end=min(v[-1][0] for v in series.values())
    grid=build_grid(series,start,end)
    if len(grid)<int(120000/GRID_MS):
        return {"decision":"BLOCKED_INSUFFICIENT_OVERLAP","counts":counts,"grid_points":len(grid),"diag":diag}

    cal_end=start+CALIBRATION_S*1000
    cal_idx=next((i for i,x in enumerate(grid) if x["t"]>=cal_end),None)
    if cal_idx is None:
        return {"decision":"BLOCKED_NO_CALIBRATION_SPLIT"}

    thresholds={}
    for leader in ("binance","bybit"):
        thresholds[leader]={}
        for w in LEADER_WINDOWS:
            step=int(w/GRID_MS)
            vals=[]
            for i in range(step,cal_idx):
                vals.append(abs(bps(grid[i-step][leader]["mid"],grid[i][leader]["mid"])))
            thresholds[leader][str(w)]={str(int(p*100)):qtile(vals,p) for p in PCTS}

    variants={}
    survivors=[]
    for leader in ("binance","bybit"):
      for w in LEADER_WINDOWS:
       back=int(w/GRID_MS)
       for p in ("95","99"):
        name=f"{leader}_W{w}_P{p}"
        thr=thresholds[leader][str(w)][p]
        events=[]
        last_t=None
        for i in range(max(cal_idx,back),len(grid)):
            if last_t is not None and grid[i]["t"]-last_t<500:continue
            lr=bps(grid[i-back][leader]["mid"],grid[i][leader]["mid"])
            if abs(lr)<thr or lr==0:continue
            mr=bps(grid[i-back]["mexc"]["mid"],grid[i]["mexc"]["mid"])
            if abs(mr)>0.5*abs(lr):continue
            d=1 if lr>0 else -1
            if mr!=0 and (1 if mr>0 else -1)!=d:continue
            events.append((i,d,lr,mr));last_t=grid[i]["t"]

        hr={}
        for h in FUTURES:
            vals_mid=[];vals_taker=[];vals_maker=[]
            for i,d,lr,mr in events:
                f=value_at(grid,i,h)
                if f is None:continue
                cur=grid[i]["mexc"];fu=f["mexc"]
                vals_mid.append(d*bps(cur["mid"],fu["mid"]))
                if d>0:
                    tg=bps(cur["ask"],fu["bid"])
                    mg=bps(cur["bid"],fu["ask"])
                else:
                    tg=bps(fu["ask"],cur["bid"])
                    mg=bps(fu["bid"],cur["ask"])
                vals_taker.append(tg);vals_maker.append(mg)
            rec={
              "n":len(vals_maker),
              "mean_directional_mid_bps":statistics.fmean(vals_mid) if vals_mid else None,
              "mean_taker_gross_bps":statistics.fmean(vals_taker) if vals_taker else None,
              "mean_mexc_taker_net_bps":statistics.fmean(vals_taker)-16 if vals_taker else None,
              "mean_maker_ceiling_gross_bps":statistics.fmean(vals_maker) if vals_maker else None,
              "mean_mexc_maker_ceiling_net_bps":statistics.fmean(vals_maker)-12 if vals_maker else None,
              "p95_maker_ceiling_gross_bps":qtile(vals_maker,.95) if vals_maker else None
            }
            if rec["n"]>=20 and rec["mean_mexc_maker_ceiling_net_bps"]>0:
                survivors.append({"variant":name,"horizon_ms":h,"n":rec["n"],
                                  "mean_net_bps":rec["mean_mexc_maker_ceiling_net_bps"]})
            hr[str(h)]=rec
        variants[name]={"threshold_bps":thr,"events":len(events),"horizons":hr}

    return {
      "decision":"FORWARD_CEILING_SIGNAL" if survivors else "NO_FORWARD_CEILING_SIGNAL_SAMPLE",
      "counts":counts,"grid_points":len(grid),
      "capture_overlap_ms":end-start,
      "calibration_ms":CALIBRATION_S*1000,
      "thresholds":thresholds,"variants":variants,"survivors":survivors,"diag":diag,
    }


async def capture():
    import websockets
    series={"binance":[],"bybit":[],"mexc":[]}
    stop=asyncio.Event()
    diag={"version_gaps":0,"invalid_after_gap":False}
    tasks=[
      asyncio.create_task(binance_collector(series["binance"],stop)),
      asyncio.create_task(bybit_collector(series["bybit"],stop)),
      asyncio.create_task(mexc_collector(series["mexc"],stop,diag)),
    ]
    try:
        await asyncio.sleep(DURATION)
    finally:
        stop.set()
        for t in tasks:t.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
    return series,diag


def main():
    receipt={
      "status":"XVENUE_LAG_004_FORWARD_PUBLIC_MVE",
      "started_wall_ms":wall_ms(),
      "public_market_data_only":True,
      "orders_sent":0,
      "exchange_mutations":0,
    }
    try:
        series,diag=asyncio.run(capture())
        receipt["analysis"]=main_analysis(series,diag)
        receipt["raw_counts"]={k:len(v) for k,v in series.items()}
        receipt["ended_wall_ms"]=wall_ms()
    except Exception as e:
        receipt["analysis"]={"decision":"BLOCKED_RUNTIME","error":repr(e)}
        receipt["ended_wall_ms"]=wall_ms()
    out=Path("research/microstructure_scalping/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"xvenue_lag_004_forward_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if not receipt["analysis"]["decision"].startswith("BLOCKED") else 2

if __name__=="__main__":
    raise SystemExit(main())
