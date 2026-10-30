#!/usr/bin/env python3
"""SPCX index authority: public MEXC rest metadata + anonymous event contract UI only."""
import asyncio,datetime as dt,hashlib,json,math,pathlib,time,urllib.request
from playwright.async_api import async_playwright
OUT=pathlib.Path("artifacts/spcx_event10m_index_lineage_v02")
SYMBOL="SPCXSTOCK_USDT"
PAGE="https://www.mexc.com/en-GB/futures/event-futures/SPCXSTOCK_USDT"
EVENT_DETAIL="/api/platform/futures/api/v1/event_contract/detail"
SENSITIVE=("/private/","/account","/balance","/wallet","/positions","/order","/user/","/api_key","/apikey")
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def milli():return int(time.time()*1000)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def public_get(path):
    url="https://contract.mexc.com"+path
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-SPCX-Lineage-PublicSource/0.2"})
    with urllib.request.urlopen(req,timeout=25) as resp:
        if resp.status!=200:raise RuntimeError("PUBLIC_MEXC_HTTP_"+str(resp.status))
        body=resp.read(2000001)
    if len(body)>2000000:raise RuntimeError("PUBLIC_MEXC_RESPONSE_TOO_LARGE")
    return json.loads(body),{"url":url,"sha256":sha(body),"bytes":len(body),"received_ms":milli()}
def futures_metadata():
    out={"source":"MEXC_OFFICIAL_PUBLIC_FUTURES_CONTRACT_DETAIL","status":"BLOCKED"}
    try:
        data,receipt=public_get("/api/v1/contract/detail?symbol="+SYMBOL)
        if data.get("success") is not True:raise RuntimeError("FUTURES_CONTRACT_DETAIL_FAILED")
        body=data.get("data")
        if isinstance(body,list):matches=[x for x in body if x.get("symbol")==SYMBOL]
        elif isinstance(body,dict):matches=[body] if body.get("symbol")==SYMBOL else []
        else:matches=[]
        if len(matches)!=1:raise RuntimeError("FUTURES_CONTRACT_NOT_UNIQUE_OR_MISSING")
        contract=matches[0]
        out.update(status="FUTURES_CONTRACT_METADATA_PRESENT",receipt=receipt,
          symbol=SYMBOL,indexOrigin=contract.get("indexOrigin"),
          contract_state=contract.get("state"),baseCoin=contract.get("baseCoin"),
          priceScale=contract.get("priceScale"),contract_fields=sorted(contract.keys()))
    except Exception as ex:
        out["error"]=type(ex).__name__+":"+str(ex)[:180]
    return out
def index_now():
    out={"source":"MEXC_OFFICIAL_PUBLIC_STANDARD_FUTURES_INDEX","status":"BLOCKED"}
    try:
        value,receipt=public_get("/api/v1/contract/index_price/"+SYMBOL)
        if value.get("success") is not True:raise RuntimeError("INDEX_REQUEST_FAILED")
        p=value.get("data") or {}
        if p.get("symbol")!=SYMBOL:raise RuntimeError("INDEX_SYMBOL_WRONG")
        price=float(p.get("indexPrice"))
        timestamp=p.get("timestamp")
        if not math.isfinite(price) or price<=0 or type(timestamp) is not int:
            raise ValueError("INDEX_PRICE_OR_CLOCK_BAD")
        out.update(status="PUBLIC_INDEX_PRICE_PRESENT",receipt=receipt,
          symbol=SYMBOL,index_price=price,server_timestamp_ms=timestamp,
          local_minus_server_ms=receipt["received_ms"]-timestamp)
    except Exception as ex:
        out["error"]=type(ex).__name__+":"+str(ex)[:180]
    return out
async def event_product():
    out={"source":"MEXC_EVENT_FUTURES_PUBLIC_DETAIL_UI","status":"BLOCKED","page":PAGE,
          "blocked_non_get":0,"blocked_sensitive":0}
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        try:
            context=await browser.new_context(locale="en-GB",service_workers="block")
            await context.clear_cookies()
            page=await context.new_page()
            async def guard(route):
                req=route.request;url=req.url.lower()
                if req.method.upper()!="GET":
                    out["blocked_non_get"]+=1;await route.abort()
                elif any(x in url for x in SENSITIVE):
                    out["blocked_sensitive"]+=1;await route.abort()
                else:await route.continue_()
            await context.route("**/*",guard)
            captures=[]
            async def capture(res):
                if EVENT_DETAIL not in res.url or res.status!=200:return
                try:
                    raw=await res.body()
                    if len(raw)>3000000:return
                    obj=json.loads(raw)
                    if obj.get("success") is True and isinstance(obj.get("data"),list):
                        captures.append((milli(),res.url,raw,obj))
                except Exception:return
            page.on("response",capture)
            await page.goto(PAGE,wait_until="domcontentloaded",timeout=55000)
            for _ in range(15):
                if captures:break
                await asyncio.sleep(.7)
            try:
                refreshed=await page.evaluate("""async()=>{const r=await fetch(
                  '/api/platform/futures/api/v1/event_contract/detail',
                  {method:'GET',credentials:'omit',cache:'no-store'}); return r.status;}""")
                out["public_get_status"]=refreshed
            except Exception as e:out["refresh_error"]=type(e).__name__
            await asyncio.sleep(.8)
            if not captures:raise RuntimeError("NO_ANONYMOUS_EVENT_DETAIL_CAPTURED")
            received,url,raw,obj=captures[-1]
            allrows=obj["data"]
            # Search a narrow alias set solely to report ambiguity; no equivalence assumed.
            related=[v for v in allrows if any(x in str(v.get("symbol","")).upper() for x in ("SPCX","SPACEX"))]
            matches=[v for v in related if v.get("symbol")==SYMBOL]
            out.update(receipt={"url":url,"sha256":sha(raw),"bytes":len(raw),"received_ms":received},
               related_symbols=[{"symbol":x.get("symbol"),"state":x.get("state")} for x in related[:12]],
               exact_matches=len(matches))
            if len(matches)!=1:raise RuntimeError("NO_EXACT_SPCXSTOCK_EVENT_FUTURES_CONTRACT")
            prod=matches[0]
            config=(prod.get("cycleConfigMap") or {}).get("MINUTE") or []
            ten=[x for x in config if x.get("val")==10]
            out["product_fields"]=sorted(prod.keys())
            out["product_state"]=prod.get("state")
            out["contract_id"]=prod.get("contractId")
            out["minute_cycles"]=sorted(x.get("val") for x in config if isinstance(x.get("val"),int))
            if len(ten)!=1:raise RuntimeError("SPCXSTOCK_10M_EVENT_NOT_AVAILABLE")
            item=ten[0]
            up=float(item.get("upPayRate"));down=float(item.get("downPayRate"))
            if prod.get("state")!="ONLINE" or not (math.isfinite(up) and up>0 and math.isfinite(down) and down>0):
                raise RuntimeError("SPCXSTOCK_EVENT_NOT_ONLINE")
            out.update(status="EXACT_PUBLIC_EVENT_PRODUCT_10M_PRESENT",payout_up=up,
                       payout_down=down,cycle_keys=sorted(item.keys()))
        except Exception as ex:
            out["error"]=type(ex).__name__+":"+str(ex)[:200]
        finally:await browser.close()
    return out
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x,y=await asyncio.gather(asyncio.to_thread(futures_metadata),
                             asyncio.to_thread(index_now))
    z=await event_product()
    report={"study":"SPCX_EVENT10M_V02_REFERENCE_LINEAGE_PUBLIC_METADATA",
       "received_at_utc":utc(),"futures":x,"index":y,"event":z,
       "source_transport_gate":"ALL_THREE_PRESENT" if
          x["status"]=="FUTURES_CONTRACT_METADATA_PRESENT" and
          y["status"]=="PUBLIC_INDEX_PRICE_PRESENT" and
          z["status"]=="EXACT_PUBLIC_EVENT_PRODUCT_10M_PRESENT" else "SOURCE_INCOMPLETE",
       "provider_defined_cash_to_tracker_relation_certified":False,
       "provider_defined_tracker_to_event_expiry_index_certified":False,
       "actual_event_server_openprice_settlement_parity_certified":False,
       "economic_gate":"REFERENCE_AUTHORITY_NOT_CERTIFIED",
       "directional_outcomes_read":0,"forecasts_scored":0,"trades":0,
       "private_or_account_reads":0,"protected_holdouts_opened":0}
    (OUT/"lineage_receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    if report["source_transport_gate"]!="ALL_THREE_PRESENT":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())
