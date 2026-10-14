#!/usr/bin/env python3
import asyncio,bisect,json,statistics,time
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


def qtile(xs,p):
    s=sorted(xs)
    return s[int((len(s)-1)*p)] if s else None


def mono_ms():
    return time.monotonic_ns()/1_000_000.0


def wall_ms():
    return int(time.time()*1000)


async def binance_collector(out,stop):
    import websockets
    async with websockets.connect(
        BINANCE_WS,ping_interval=None,close_timeout=5,max_size=2_000_000
    ) as ws:
        while not stop.is_set():
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError:
                continue
            m=json.loads(raw)
            try:
                b=float(m["b"]);a=float(m["a"])
            except Exception:
                continue
            if b>0 and a>b:
                out.append((mono_ms(),wall_ms(),b,a,m.get("E"),m.get("T"),m.get("u")))


async def bybit_collector(out,stop):
    import websockets
    async with websockets.connect(
        BYBIT_WS,ping_interval=20,ping_timeout=20,close_timeout=5,max_size=4_000_000
    ) as ws:
        await ws.send(json.dumps({"op":"subscribe","args":["orderbook.1.BTCUSDT"]}))
        while not stop.is_set():
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError:
                continue
            m=json.loads(raw)
            if m.get("topic")!="orderbook.1.BTCUSDT":
                continue
            d=m.get("data") or {}
            try:
                b=float(d["b"][0][0]);a=float(d["a"][0][0])
            except Exception:
                continue
            if b>0 and a>b:
                out.append((mono_ms(),wall_ms(),b,a,m.get("ts"),m.get("cts"),d.get("u")))


async def mexc_collector(out,stop,diag):
    """Use depth.step because each message exposes current market-level bid/ask.

    No incremental-book reconstruction is required for BBO lead/lag analysis.
    Version skips are diagnostic only; non-monotonic versions fail closed.
    """
    import websockets
    last_version=None
    async with websockets.connect(
        MEXC_WS,ping_interval=None,close_timeout=5,max_size=8_000_000
    ) as ws:
        await ws.send(json.dumps({
            "method":"sub.depth.step",
            "param":{"symbol":"BTC_USDT","step":"10"},
            "gzip":False
        }))
        last_ping=mono_ms()
        while not stop.is_set():
            if mono_ms()-last_ping>10000:
                await ws.send(json.dumps({"method":"ping"}))
                last_ping=mono_ms()
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError:
                continue
            if isinstance(raw,bytes):
                raw=raw.decode("utf-8","replace")
            m=json.loads(raw)
            if m.get("channel")!="push.depth.step":
                continue
            d=m.get("data") or {}
            try:
                b=float(d["bidMarketLevelPrice"])
                a=float(d["askMarketLevelPrice"])
                v=int(d["version"])
            except Exception:
                continue
            if last_version is not None:
                if v<last_version:
                    diag["mexc_nonmonotonic_versions"]+=1
                    diag["invalid_mexc_sequence"]=True
                elif v>last_version+1:
                    diag["mexc_version_skips"]+=1
            last_version=v
            if b>0 and a>b:
                out.append((mono_ms(),wall_ms(),b,a,m.get("ts"),d.get("ct"),v))
    diag["mexc_last_version"]=last_version


def build_grid(series,start,end):
    ts_cache={k:[x[0] for x in v] for k,v in series.items()}
    grid=[]
    t=start
    while t<=end:
        rec={"t":t};ok=True
        for k,rows in series.items():
            idx=bisect.bisect_right(ts_cache[k],t)-1
            if idx<0:
                ok=False;break
            x=rows[idx]
            if t-x[0]>1000:
                ok=False;break
            rec[k]={"bid":x[2],"ask":x[3],"mid":(x[2]+x[3])/2.0}
        if ok:
            grid.append(rec)
        t+=GRID_MS
    return grid


def bps(a,b):
    return (b-a)/a*10000.0


def value_at(grid,i,delta_ms):
    steps=int(round(delta_ms/GRID_MS))
    j=i+steps
    return grid[j] if 0<=j<len(grid) else None


def main_analysis(series,diag):
    counts={k:len(v) for k,v in series.items()}
    if diag.get("invalid_mexc_sequence"):
        return {"decision":"BLOCKED_MEXC_NONMONOTONIC_VERSION","counts":counts,"diag":diag}
    if min(counts.values())<20:
        return {"decision":"BLOCKED_INSUFFICIENT_QUOTES","counts":counts,"diag":diag}

    start=max(v[0][0] for v in series.values())
    end=min(v[-1][0] for v in series.values())
    grid=build_grid(series,start,end)
    if len(grid)<int(120000/GRID_MS):
        return {
            "decision":"BLOCKED_INSUFFICIENT_OVERLAP",
            "counts":counts,"grid_points":len(grid),"diag":diag
        }

    cal_end=start+CALIBRATION_S*1000
    cal_idx=next((i for i,x in enumerate(grid) if x["t"]>=cal_end),None)
    if cal_idx is None:
        return {"decision":"BLOCKED_NO_CALIBRATION_SPLIT","counts":counts,"diag":diag}

    thresholds={}
    for leader in ("binance","bybit"):
        thresholds[leader]={}
        for w in LEADER_WINDOWS:
            step=int(w/GRID_MS)
            vals=[
                abs(bps(grid[i-step][leader]["mid"],grid[i][leader]["mid"]))
                for i in range(step,cal_idx)
            ]
            thresholds[leader][str(w)]={
                str(int(p*100)):qtile(vals,p) for p in PCTS
            }

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
            if last_t is not None and grid[i]["t"]-last_t<500:
                continue
            lr=bps(grid[i-back][leader]["mid"],grid[i][leader]["mid"])
            if abs(lr)<thr or lr==0:
                continue
            mr=bps(grid[i-back]["mexc"]["mid"],grid[i]["mexc"]["mid"])
            if abs(mr)>0.5*abs(lr):
                continue
            d=1 if lr>0 else -1
            if mr!=0 and (1 if mr>0 else -1)!=d:
                continue
            events.append((i,d,lr,mr))
            last_t=grid[i]["t"]

        hr={}
        for h in FUTURES:
            vals_mid=[];vals_taker=[];vals_maker=[]
            for i,d,lr,mr in events:
                f=value_at(grid,i,h)
                if f is None:
                    continue
                cur=grid[i]["mexc"];fu=f["mexc"]
                vals_mid.append(d*bps(cur["mid"],fu["mid"]))
                if d>0:
                    tg=bps(cur["ask"],fu["bid"])
                    mg=bps(cur["bid"],fu["ask"])
                else:
                    tg=bps(fu["ask"],cur["bid"])
                    mg=bps(fu["bid"],cur["ask"])
                vals_taker.append(tg)
                vals_maker.append(mg)
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
                survivors.append({
                    "variant":name,"horizon_ms":h,"n":rec["n"],
                    "mean_net_bps":rec["mean_mexc_maker_ceiling_net_bps"]
                })
            hr[str(h)]=rec
        variants[name]={"threshold_bps":thr,"events":len(events),"horizons":hr}

    return {
      "decision":"FORWARD_CEILING_SIGNAL" if survivors else "NO_FORWARD_CEILING_SIGNAL_SAMPLE",
      "counts":counts,
      "grid_points":len(grid),
      "capture_overlap_ms":end-start,
      "calibration_ms":CALIBRATION_S*1000,
      "thresholds":thresholds,
      "variants":variants,
      "survivors":survivors,
      "diag":diag,
    }


async def capture():
    series={"binance":[],"bybit":[],"mexc":[]}
    stop=asyncio.Event()
    diag={
        "mexc_version_skips":0,
        "mexc_nonmonotonic_versions":0,
        "invalid_mexc_sequence":False,
        "collector_errors":{}
    }
    tasks={
      "binance":asyncio.create_task(binance_collector(series["binance"],stop)),
      "bybit":asyncio.create_task(bybit_collector(series["bybit"],stop)),
      "mexc":asyncio.create_task(mexc_collector(series["mexc"],stop,diag)),
    }
    await asyncio.sleep(DURATION)
    stop.set()
    for t in tasks.values():
        t.cancel()
    results=await asyncio.gather(*tasks.values(),return_exceptions=True)
    for name,res in zip(tasks.keys(),results):
        if isinstance(res,BaseException) and not isinstance(res,asyncio.CancelledError):
            diag["collector_errors"][name]=repr(res)
    return series,diag


def main():
    receipt={
      "status":"XVENUE_LAG_004_FORWARD_PUBLIC_MVE",
      "technical_revision":"V0.2_MEXC_DEPTH_STEP_BBO",
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

    out=Path("research/microstructure_scalping/receipts")
    out.mkdir(parents=True,exist_ok=True)
    (out/"xvenue_lag_004_forward_v01.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if not receipt["analysis"]["decision"].startswith("BLOCKED") else 2


if __name__=="__main__":
    raise SystemExit(main())
