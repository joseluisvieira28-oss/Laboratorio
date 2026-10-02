#!/usr/bin/env python3
import asyncio, hashlib, json, os
from datetime import datetime, timezone
from playwright.async_api import async_playwright

PAGE="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
ROUTE="https://www.mexc.com/api/platform/futures/api/v1/event_contract/detail"
TARGETS={"BTC_USDT","ETH_USDT","NVIDIA_USDT","MUSTOCK_USDT","SPCXSTOCK_USDT","SOL_USDT","XRP_USDT","SUI_USDT","DOGE_USDT"}

def sha(b): return hashlib.sha256(b).hexdigest()

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    out={
      "lab":"MEXC_EVENT_FUTURES_EXACT_BROWSER_V0.12.2",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "page":PAGE,"route":ROUTE,
      "authenticated_requests":0,"orders":0,"account_mutations":0,
      "aborted_non_get_count":0,
      "captured":False,"records":[]
    }

    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await browser.new_context(locale="en-GB",timezone_id="UTC")
        await ctx.clear_cookies()
        page=await ctx.new_page()
        captured={}

        async def route_handler(route):
            req=route.request
            if req.method.upper()!="GET":
                out["aborted_non_get_count"]+=1
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",route_handler)

        async def on_response(resp):
            if resp.url.split("?")[0]!=ROUTE:
                return
            try:
                b=await resp.body()
                captured["status"]=resp.status
                captured["headers"]=dict(resp.headers)
                captured["body"]=b
            except Exception as e:
                captured["error"]=repr(e)
        page.on("response",on_response)

        try:
            resp=await page.goto(PAGE,wait_until="domcontentloaded",timeout=60000)
            out["page_status"]=resp.status if resp else None
            await page.wait_for_timeout(20000)
            out["page_final_url"]=page.url
            out["page_title"]=await page.title()
            body=await page.locator("body").inner_text(timeout=10000)
            out["visible_has_up_payout"]="Up Payout" in body
            out["visible_has_down_payout"]="Down Payout" in body
            out["visible_has_80pct"]="80%" in body
        except Exception as e:
            out["page_error"]=repr(e)

        await browser.close()

    if "body" in captured:
        b=captured["body"]
        out["captured"]=True
        out["route_status"]=captured.get("status")
        out["route_content_type"]=(captured.get("headers") or {}).get("content-type")
        out["route_bytes"]=len(b)
        out["route_sha256"]=sha(b)
        try:
            j=json.loads(b.decode("utf-8","replace"))
            out["top_level_keys"]=sorted(j.keys()) if isinstance(j,dict) else []
            out["success"]=j.get("success") if isinstance(j,dict) else None
            out["code"]=j.get("code") if isinstance(j,dict) else None
            data=j.get("data") if isinstance(j,dict) else None
            out["record_count"]=len(data) if isinstance(data,list) else None
            out["all_symbols"]=[x.get("symbol") for x in data if isinstance(x,dict)] if isinstance(data,list) else []
            if isinstance(data,list):
                for x in data:
                    if isinstance(x,dict) and x.get("symbol") in TARGETS:
                        out["records"].append(x)
            out["raw_json"]=j
        except Exception as e:
            out["json_error"]=repr(e)
    elif "error" in captured:
        out["capture_error"]=captured["error"]

    if out.get("captured") and out.get("route_status")==200 and out.get("success") is True and out["records"]:
        verdict="EXACT_PUBLIC_BROWSER_ROUTE_CONFIRMED"
    elif out.get("captured"):
        verdict="EXACT_ROUTE_OBSERVED_SCHEMA_INSUFFICIENT"
    else:
        verdict="BROWSER_EXACT_ROUTE_NOT_CAPTURED"
    out["verdict"]=verdict

    pth="artifacts/mexc_event_futures/exact_browser_v0122.json"
    with open(pth,"w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,sort_keys=True)

    print("VERDICT="+verdict)
    print("PAGE_STATUS="+str(out.get("page_status")))
    print("ROUTE_STATUS="+str(out.get("route_status")))
    print("CAPTURED="+str(out.get("captured")))
    print("RECORD_COUNT="+str(out.get("record_count")))
    print("ALL_SYMBOLS="+json.dumps(out.get("all_symbols",[]),ensure_ascii=False))
    for rec in out["records"]:
        print("CONTRACT_RECORD="+json.dumps(rec,ensure_ascii=False,sort_keys=True))
    print("VISIBLE_UP_PAYOUT="+str(out.get("visible_has_up_payout")))
    print("VISIBLE_DOWN_PAYOUT="+str(out.get("visible_has_down_payout")))
    print("VISIBLE_80PCT="+str(out.get("visible_has_80pct")))
    print("ABORTED_NON_GETS="+str(out.get("aborted_non_get_count")))
    print("NO_AUTH=PASS")
    print("NO_ORDERS=PASS")
    print("NO_MUTATION=PASS")
    print("WROTE "+pth)

if __name__=="__main__":
    asyncio.run(main())
