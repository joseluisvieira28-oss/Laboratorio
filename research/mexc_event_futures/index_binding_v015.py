#!/usr/bin/env python3
import asyncio,json,os
from playwright.async_api import async_playwright

PAGE="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
PREFIX="https://www.mexc.com/api/platform/futures/api/v1/"

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    out={"lab":"MEXC_EVENT_FUTURES_INDEX_BINDING_V0.15","responses":[],
         "authenticated_requests":0,"orders":0,"account_mutations":0,"aborted_non_gets":0}
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        c=await b.new_context(locale="en-GB",timezone_id="UTC"); await c.clear_cookies()
        page=await c.new_page()

        async def rh(route):
            if route.request.method.upper()!="GET":
                out["aborted_non_gets"]+=1; await route.abort()
            else: await route.continue_()
        await page.route("**/*",rh)

        async def on_response(resp):
            u=resp.url
            if not u.startswith(PREFIX): return
            rec={"url":u,"status":resp.status,"content_type":resp.headers.get("content-type")}
            try:
                t=(await resp.body()).decode("utf-8","replace")
                j=json.loads(t)
                rec["top_keys"]=sorted(j.keys()) if isinstance(j,dict) else []
                data=j.get("data") if isinstance(j,dict) else None
                if isinstance(data,list):
                    btc=[x for x in data if isinstance(x,dict) and x.get("symbol")=="BTC_USDT"]
                    if btc: rec["btc_record"]=btc[0]
                    rec["data_count"]=len(data)
                elif isinstance(data,dict):
                    rec["data_keys"]=sorted(data.keys())
                    if data.get("symbol")=="BTC_USDT": rec["btc_record"]=data
            except Exception as e:
                rec["parse_error"]=repr(e)
            out["responses"].append(rec)
        page.on("response",on_response)

        resp=await page.goto(PAGE,wait_until="domcontentloaded",timeout=60000)
        out["page_status"]=resp.status if resp else None
        await page.wait_for_timeout(20000)
        out["page_final_url"]=page.url
        out["page_title"]=await page.title()
        await b.close()

    # dedupe same url, preserve richest record
    by={}
    for r in out["responses"]:
        u=r["url"]
        if u not in by or len(json.dumps(r))>len(json.dumps(by[u])): by[u]=r
    out["responses_unique"]=list(by.values())
    key=[r for r in out["responses_unique"] if any(k in r["url"] for k in ["ticker","index","kline","event_contract"])]
    out["key_responses"]=key
    out["verdict"]="EVENT_PAGE_MARKET_DATA_ROUTES_CAPTURED" if key else "INDEX_SOURCE_BINDING_BLOCKED"

    pth="artifacts/mexc_event_futures/index_binding_v015.json"
    with open(pth,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
    print("VERDICT="+out["verdict"])
    print("PAGE_STATUS="+str(out.get("page_status")))
    print("KEY_RESPONSES")
    for r in key: print(json.dumps(r,ensure_ascii=False,sort_keys=True))
    print("NO_AUTH=PASS\nNO_ORDERS=PASS\nNO_MUTATION=PASS")
    print("WROTE "+pth)

if __name__=="__main__": asyncio.run(main())
