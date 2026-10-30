#!/usr/bin/env python3
"""V0.5 strictly public payout->first MEXC index within 5s, no forecast/outcome."""
import asyncio
import hashlib
import json
import math
import pathlib
import time
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import websockets

OUT=pathlib.Path("artifacts/event10m_payout_index_source_v05")
ENTRY="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
DETAIL="/api/platform/futures/api/v1/event_contract/detail"
BIN="wss://fstream.binance.com/market/stream?streams=btcusdt@aggTrade/ethusdt@aggTrade"
MEX="wss://futures.mexc.com/edge"
SYMS=("BTC_USDT","ETH_USDT")
DENY=("/private","/account","/balance","/wallet","/position","/order","/user","/api_key","/apikey","/withdraw","/deposit")
def clock():
    return {"utc_ms":time.time_ns()//1000000,"monotonic_ns":time.monotonic_ns()}
def hashraw(b):
    return hashlib.sha256(b.encode() if isinstance(b,str) else b).hexdigest()
def products(raw):
    d=json.loads(raw)
    if not isinstance(d,dict) or d.get("success") is not True or not isinstance(d.get("data"),list):
        raise ValueError("DETAIL_INVALID")
    v={}
    for s in SYMS:
        p=[x for x in d["data"] if isinstance(x,dict) and x.get("symbol")==s]
        if len(p)!=1:raise ValueError("PRODUCT_MISSING_OR_DUPLICATE_"+s)
        x=p[0]
        cfg=(x.get("cycleConfigMap") or {}).get("MINUTE")
        cycles=[row for row in cfg if row.get("val")==10] if isinstance(cfg,list) else []
        if len(cycles)!=1:raise ValueError("CYCLE_MISSING_"+s)
        u,dn=float(cycles[0]["upPayRate"]),float(cycles[0]["downPayRate"])
        if not all(math.isfinite(y) and y>0 for y in (u,dn)):raise ValueError("INVALID_PAYOUT_"+s)
        v[s]={"state":x.get("state"),"contract_id":x.get("contractId"),"q_up":u,"q_down":dn,
              "break_even_up":1/(1+u),"break_even_down":1/(1+dn)}
    return v
def index(j):
    if not isinstance(j,dict) or j.get("channel")!="push.index.price":return None
    d=j.get("data")
    if not isinstance(d,dict):return None
    s=j.get("symbol") or d.get("symbol")
    if s not in SYMS:return None
    try:p=float(d.get("price"))
    except (ValueError,TypeError):return None
    return s,p if math.isfinite(p) and p>0 else None
def trade(j):
    if not isinstance(j,dict):return None
    d=j.get("data",j)
    if not isinstance(d,dict) or d.get("e")!="aggTrade" or d.get("s") not in ("BTCUSDT","ETHUSDT"):return None
    try:p=float(d["p"]);q=float(d["q"])
    except (ValueError,TypeError,KeyError):return None
    if not all(math.isfinite(x) and x>0 for x in (p,q)):return None
    if not isinstance(d.get("E"),int) or not isinstance(d.get("T"),int):return None
    return d["s"].replace("USDT","_USDT")
def tests():
    demo={"success":True,"data":[{"symbol":s,"state":"ONLINE","cycleConfigMap":{"MINUTE":[{"val":10,"upPayRate":.7,"downPayRate":.8}]}} for s in SYMS]}
    assert len(products(json.dumps(demo).encode()))==2
    assert index({"channel":"push.index.price","symbol":"BTC_USDT","data":{"price":"100"}})==("BTC_USDT",100.)
    assert index({"channel":"push.order","symbol":"BTC_USDT","data":{"price":"100"}}) is None
    assert trade({"data":{"e":"aggTrade","s":"BTCUSDT","p":"100","q":"1","E":1790000000000,"T":1790000000000}})=="BTC_USDT"
async def run_bin(e,end):
    d=e["streams"]["binance"]
    try:
        async with websockets.connect(BIN,open_timeout=20,close_timeout=3,ping_interval=15,ping_timeout=10,max_size=2000000) as ws:
            d["opened"]=clock()
            while time.monotonic_ns()<end and d["frames"]<20000:
                try:raw=await asyncio.wait_for(ws.recv(),timeout=1)
                except asyncio.TimeoutError:continue
                d["frames"]+=1
                if isinstance(raw,bytes):continue
                try:s=trade(json.loads(raw))
                except ValueError:continue
                if s:
                    e["per_symbol"][s]["trades"]+=1
                    if len(e["per_symbol"][s]["trade_samples"])<3:
                        e["per_symbol"][s]["trade_samples"].append({**clock(),"raw_sha256":hashraw(raw)})
            d["closed"]=clock()
    except Exception as exc:d["error"]=type(exc).__name__+":"+str(exc)[:150]
async def run_mexc(e,end):
    d=e["streams"]["mexc"]
    try:
        async with websockets.connect(MEX,origin="https://www.mexc.com",open_timeout=20,close_timeout=3,ping_interval=15,ping_timeout=10,max_size=2000000) as ws:
            d["opened"]=clock()
            for s in SYMS:await ws.send(json.dumps({"method":"sub.index.price","param":{"symbol":s}},separators=(",",":")))
            next_ping=time.monotonic_ns()+15_000_000_000
            while time.monotonic_ns()<end and d["frames"]<5000:
                if time.monotonic_ns()>=next_ping:
                    await ws.send('{"method":"ping"}')
                    d["app_ping"]+=1
                    next_ping+=15_000_000_000
                try:raw=await asyncio.wait_for(ws.recv(),timeout=1)
                except asyncio.TimeoutError:continue
                recv=clock()
                d["frames"]+=1
                if isinstance(raw,bytes):continue
                try:j=json.loads(raw)
                except ValueError:continue
                if isinstance(j,dict) and j.get("channel")=="pong":
                    d["app_pong"]+=1
                    continue
                tick=index(j)
                if not tick or tick[1] is None:continue
                s,p=tick
                row=e["per_symbol"][s]
                row["index_ticks"]+=1
                observation={**recv,"source_ts":j.get("ts"),"public_index":p,"raw_sha256":hashraw(raw)}
                if len(row["index_samples"])<3:row["index_samples"].append(observation)
                if e["payout"] and row["first_index_after_payout"] is None:
                    if recv["monotonic_ns"]>=e["payout"]["received"]["monotonic_ns"]:
                        row["first_index_after_payout"]=observation
            for s in SYMS:
                try:await ws.send(json.dumps({"method":"unsub.index.price","param":{"symbol":s}},separators=(",",":")))
                except Exception:pass
            d["closed"]=clock()
    except Exception as exc:d["error"]=type(exc).__name__+":"+str(exc)[:150]
async def run_browser(e):
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(locale="en-GB",timezone_id="UTC",service_workers="block")
        await ctx.clear_cookies()
        async def guard(route):
            req=route.request
            path=urlparse(req.url.lower()).path
            if req.method.upper()!="GET" or any(x in path for x in DENY):await route.abort()
            else:await route.continue_()
        await ctx.route("**/*",guard)
        page=await ctx.new_page()
        done=asyncio.Event()
        async def response(resp):
            if DETAIL not in urlparse(resp.url).path or done.is_set():return
            try:
                if resp.status!=200:return
                raw=await resp.body()
                recv=clock()
                if len(raw)>4000000:raise ValueError("DETAIL_TOO_LARGE")
                v=products(raw)
                e["payout"]={"received":recv,"url":resp.url,"http":resp.status,
                             "bytes":len(raw),"sha256":hashraw(raw),"products":v}
                done.set()
            except Exception as exc:
                e["browser_errors"].append(type(exc).__name__+":"+str(exc)[:150])
        page.on("response",response)
        try:
            nav=await page.goto(ENTRY,wait_until="domcontentloaded",timeout=60000)
            e["page_http"]=nav.status if nav else None
            try:await asyncio.wait_for(done.wait(),timeout=30)
            except asyncio.TimeoutError:e["browser_errors"].append("NO_VALID_PRODUCT_DETAIL")
        except Exception as exc:e["browser_errors"].append(type(exc).__name__+":"+str(exc)[:150])
        await ctx.close()
        await browser.close()
async def main():
    tests()
    OUT.mkdir(parents=True,exist_ok=True)
    e={"study":"EVENT10M_EXACT_PAYOUT_FIRST_INDEX_SOURCE_V05",
       "payout":None,"browser_errors":[],"page_http":None,
       "streams":{"binance":{"frames":0},"mexc":{"frames":0,"app_ping":0,"app_pong":0}},
       "per_symbol":{s:{"trades":0,"index_ticks":0,"trade_samples":[],"index_samples":[],
                        "first_index_after_payout":None} for s in SYMS},
       "gate":"SOURCE_PENDING","market_direction_forecasts":0,
       "ten_minute_outcomes_opened":0,"orders":0,"private_api_calls":0,
       "nvidia_excluded":True,"protected_sep_holdout_unopened":True}
    begin=clock()
    e["started"]=begin
    end=begin["monotonic_ns"]+100_000_000_000
    try:
        await asyncio.gather(run_bin(e,end),run_mexc(e,end),run_browser(e))
        valid={}
        for s in SYMS:
            item=e["per_symbol"][s]
            first=item["first_index_after_payout"]
            config=(e["payout"] or {}).get("products",{}).get(s,{})
            delay=(first["monotonic_ns"]-e["payout"]["received"]["monotonic_ns"]) if first and e["payout"] else None
            item["payout_to_first_next_index_ms"]=round(delay/1e6,3) if delay is not None else None
            valid[s]=bool(config.get("state")=="ONLINE" and item["trades"]>=10 and item["index_ticks"]>=2
                          and delay is not None and 0<=delay<=5_000_000_000)
        e["source_join_per_symbol"]=valid
        streams=e["streams"]
        if all(k.get("opened") and k.get("closed") for k in streams.values()):
            a=max(z["opened"]["monotonic_ns"] for z in streams.values())
            b=min(z["closed"]["monotonic_ns"] for z in streams.values())
            e["overlap_seconds"]=round(max(0,b-a)/1e9,3)
        else:e["overlap_seconds"]=0
        ok=all(valid.values()) and e["overlap_seconds"]>=60 and streams["mexc"]["app_ping"]>=1 and streams["mexc"]["app_pong"]>=1
        ok=ok and all(not x.get("error") for x in streams.values())
        e["gate"]="PAYOUT_FIRST_INDEX_SOURCE_PASS" if ok else "SOURCE_BLOCKED_OR_INCOMPLETE"
    except Exception as exc:
        e["gate"]="SOURCE_BLOCKED_EXCEPTION"
        e["fatal"]=type(exc).__name__+":"+str(exc)[:180]
    finally:
        e["finished"]=clock()
        (OUT/"receipt.json").write_text(json.dumps(e,indent=2,sort_keys=True)+"\n")
        summary={"gate":e["gate"],"payout":e["payout"],"source_join_per_symbol":e.get("source_join_per_symbol"),
                 "per_symbol":{s:{"trades":x["trades"],"index_ticks":x["index_ticks"],
                  "payout_to_first_next_index_ms":x.get("payout_to_first_next_index_ms")} for s,x in e["per_symbol"].items()},
                 "overlap_seconds":e.get("overlap_seconds"),"streams":e["streams"],"browser_errors":e["browser_errors"],
                 "forecast_count":0,"outcome_count":0,"orders":0}
        print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
    if e["gate"]!="PAYOUT_FIRST_INDEX_SOURCE_PASS":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())
