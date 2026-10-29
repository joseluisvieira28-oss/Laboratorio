#!/usr/bin/env python3
"""Public-only MEXC NVIDIA event 10m payout + index websocket source audit."""
import asyncio,datetime as dt,hashlib,json,math,pathlib,time
from urllib.parse import urlparse
import websockets
from playwright.async_api import async_playwright
OUT=pathlib.Path("artifacts/nvda_event10m_exact_source_v04")
OUT.mkdir(parents=True,exist_ok=True)
TARGET="NVIDIA_USDT"
PAGE="https://www.mexc.com/en-GB/futures/event-futures/NVIDIA_USDT"
DETAIL="/api/platform/futures/api/v1/event_contract/detail"
SENSITIVE=("/private/","/account","/balance","/wallet","/positions","/order","/user/","/api_key","/apikey")
def ms():return int(time.time()*1000)
def sha(raw):return hashlib.sha256(raw).hexdigest()
async def product():
    rec={"source":"EVENT_CONTRACT_EXACT_PUBLIC_GET","url":PAGE,"status":"STARTING",
      "requests_blocked_non_get":0,"requests_blocked_sensitive":0}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(locale="en-GB",service_workers="block",
                  extra_http_headers={"Accept-Language":"en-GB,en;q=0.9"})
        await ctx.clear_cookies()
        page=await ctx.new_page()
        async def restrict(route):
            req=route.request
            u=req.url.lower()
            if req.method.upper()!="GET":
                rec["requests_blocked_non_get"]+=1;await route.abort()
            elif any(t in u for t in SENSITIVE):
                rec["requests_blocked_sensitive"]+=1;await route.abort()
            else:
                await route.continue_()
        await ctx.route("**/*",restrict)
        captures=[]
        async def response(resp):
            if DETAIL not in resp.url or resp.status!=200:return
            try:
                raw=await resp.body()
                if len(raw)>4_000_000:return
                obj=json.loads(raw)
                if obj.get("success") is True and isinstance(obj.get("data"),list):
                    captures.append((ms(),resp.url,raw,obj))
            except Exception:return
        page.on("response",response)
        try:
            await page.goto(PAGE,wait_until="domcontentloaded",timeout=55000)
            for _ in range(24):
                if captures:break
                await asyncio.sleep(.5)
            # source freshness: explicit GET, no form POST and no login.
            result=await page.evaluate("""async ()=> {
               const r=await fetch('/api/platform/futures/api/v1/event_contract/detail',
                {method:'GET',credentials:'omit',cache:'no-store',headers:{accept:'application/json'}});
               return {status:r.status,ok:r.ok};
            }""")
            await asyncio.sleep(.8)
            rec["refresh_http_status"]=result.get("status")
            if not captures:raise RuntimeError("NO_PUBLIC_EVENT_DETAIL")
            received,url,raw,obj=captures[-1]
            rows=[x for x in obj["data"] if x.get("symbol")==TARGET]
            if len(rows)!=1:raise RuntimeError("NVIDIA_EVENT_PRODUCT_NOT_UNIQUE")
            prod=rows[0]
            cfgs=(prod.get("cycleConfigMap") or {}).get("MINUTE") or []
            matches=[x for x in cfgs if x.get("val")==10]
            if len(matches)!=1:raise RuntimeError("NO_EXACT_10M_CYCLE")
            item=matches[0]
            up,down=float(item["upPayRate"]),float(item["downPayRate"])
            if prod.get("state")!="ONLINE" or not(math.isfinite(up) and up>0 and math.isfinite(down) and down>0):
                raise RuntimeError("EVENT_PRODUCT_NOT_ONLINE_OR_BAD_PAYOUT")
            rec.update(status="PUBLIC_PRODUCT_10M_PASS",product_symbol=TARGET,
               contract_id=prod.get("contractId"),product_state=prod.get("state"),
               up_pay_rate=up,down_pay_rate=down,
               raw_sha256=sha(raw),response_received_ms=received,
               response_url=url,raw_body_bytes=len(raw),captures=len(captures))
        except Exception as e:
            rec.update(status="SOURCE_BLOCKED",error=type(e).__name__+":"+str(e)[:160])
        finally:
            await browser.close()
    return rec
async def index():
    rec={"source":"MEXC_PUBLIC_INDEX_WEBSOCKET","url":"wss://futures.mexc.com/edge",
       "status":"STARTING","symbol":TARGET,"ticks":0}
    try:
        async with websockets.connect(rec["url"],origin="https://www.mexc.com",
           open_timeout=20,close_timeout=5,ping_interval=15,ping_timeout=10,max_size=2_000_000) as ws:
            await ws.send(json.dumps({"method":"sub.index.price","param":{"symbol":TARGET}},separators=(",",":")))
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                try:raw=await asyncio.wait_for(ws.recv(),timeout=min(5,deadline-time.monotonic()))
                except asyncio.TimeoutError:continue
                if not isinstance(raw,str):continue
                try:msg=json.loads(raw)
                except Exception:continue
                if msg.get("channel")!="push.index.price":continue
                data=msg.get("data") or {}
                sym=msg.get("symbol") or data.get("symbol")
                if sym!=TARGET:continue
                px=float(data.get("price") or 0)
                if not(math.isfinite(px) and px>0):continue
                rec.update(status="PUBLIC_INDEX_TICK_PASS",index_price=px,
                   index_raw_sha256=sha(raw.encode()),received_ms=ms(),
                   server_ts=msg.get("ts"),ticks=rec["ticks"]+1)
                break
    except Exception as e:
        rec.update(status="SOURCE_BLOCKED",error=type(e).__name__+":"+str(e)[:200])
    if rec["status"]=="STARTING":rec["status"]="SOURCE_BLOCKED_NO_NVIDIA_TICK"
    return rec
async def main():
    a,b=await asyncio.gather(product(),index())
    out={"study":"NVIDIA_EVENT10M_EXACT_PRODUCT_AND_INDEX_SOURCE_V04",
       "scope":"SOURCE_ONLY","observed_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "product":a,"index":b,
       "protected_old_nvda_forward_read":False,"market_outcomes_scored":0,
       "forecasts_issued":0,"accounts_orders_private_calls":0,
       "event_real_order_openprice_parity_proven":False,
       "gate":"PUBLIC_PRODUCT_AND_INDEX_SOURCE_PASS" if a["status"]=="PUBLIC_PRODUCT_10M_PASS"
         and b["status"]=="PUBLIC_INDEX_TICK_PASS" else "SOURCE_INCOMPLETE"}
    (OUT/"receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True),flush=True)
    if out["gate"]!="PUBLIC_PRODUCT_AND_INDEX_SOURCE_PASS":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())
