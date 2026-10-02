#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from datetime import datetime, timezone
from playwright.async_api import async_playwright

ASSETS={
 "BTCUSDT":"BTC_USDT",
 "ETHUSDT":"ETH_USDT",
 "NVDAUSDT":"NVIDIA_USDT",
 "MUUSDT":"MUSTOCK_USDT",
 "SPCXUSDT":"SPCXSTOCK_USDT",
}
BASE="https://www.mexc.com/futures/event-futures/"

def h(s):
    return hashlib.sha256(s.encode("utf-8","ignore")).hexdigest()

async def inspect_asset(browser,display,symbol):
    ctx=await browser.new_context()
    page=await ctx.new_page()
    rec={
      "display":display,"symbol":symbol,
      "observed_at_utc":datetime.now(timezone.utc).isoformat(),
      "responses":[],"websocket_frames":[],"dom":{}
    }

    async def route_handler(route,request):
        if request.method.upper()!="GET":
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*",route_handler)

    async def response_handler(resp):
        try:
            req=resp.request
            typ=req.resource_type
            url=resp.url
            if typ not in ("xhr","fetch") and not any(k in url.lower() for k in ("event","prediction","payout")):
                return
            ctype=(resp.headers.get("content-type") or "").lower()
            if "json" not in ctype and "text" not in ctype and "javascript" not in ctype:
                return
            body=await resp.text()
            if len(body)>300000: body=body[:300000]
            low=body.lower()
            if not any(k in low or k in url.lower() for k in ("event","prediction","payout","up","down","timeunit")):
                return
            rec["responses"].append({
              "url":url,"status":resp.status,"resource_type":typ,
              "body_sha256":h(body),"body_excerpt":body[:12000]
            })
        except Exception:
            pass
    page.on("response",response_handler)

    def ws_handler(ws):
        def frame_recv(payload):
            try:
                s=payload if isinstance(payload,str) else str(payload)
                low=s.lower()
                if any(k in low for k in ("event","prediction","payout","up","down","timeunit",symbol.lower())):
                    rec["websocket_frames"].append({
                      "url":ws.url,"payload_sha256":h(s),"payload_excerpt":s[:12000]
                    })
            except Exception:
                pass
        ws.on("framereceived",frame_recv)
    page.on("websocket",ws_handler)

    url=BASE+symbol
    try:
        await page.goto(url,wait_until="domcontentloaded",timeout=90000)
        await page.wait_for_timeout(12000)
        body=await page.locator("body").inner_text()
        rec["dom"]["url"]=page.url
        rec["dom"]["text_sha256"]=h(body)
        rec["dom"]["text_excerpt"]=body[:30000]
        # Flexible payout extraction from rendered text.
        vals=re.findall(r'(?i)(?:Up\s*Payout|Payout\s*Up)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)
        vals2=re.findall(r'(?i)(?:Down\s*Payout|Payout\s*Down)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)
        rec["dom"]["up_payout_candidates"]=vals[:10]
        rec["dom"]["down_payout_candidates"]=vals2[:10]
        rec["dom"]["percent_values"]=re.findall(r'(\d{1,3}(?:\.\d+)?)\s*%',body)[:100]
    except Exception as e:
        rec["error"]=repr(e)

    await ctx.close()
    return rec

async def main():
    out={"lab":"MEXC_EVENT_FUTURES_PAYOUT_BROWSER_PROBE_V0.6","assets":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for display,symbol in ASSETS.items():
            out["assets"].append(await inspect_asset(browser,display,symbol))
        await browser.close()

    exact=[]
    for x in out["assets"]:
        ups=x.get("dom",{}).get("up_payout_candidates") or []
        dns=x.get("dom",{}).get("down_payout_candidates") or []
        if ups and dns:
            exact.append({"asset":x["display"],"up":ups[0],"down":dns[0],"source":"DOM"})
    out["exact_dom_payouts"]=exact
    if len(exact)==len(ASSETS):
        out["source_gate"]="PASS_EXACT_CURRENT_PAYOUT"
    elif exact or any(x.get("responses") or x.get("websocket_frames") for x in out["assets"]):
        out["source_gate"]="PARTIAL"
    else:
        out["source_gate"]="BLOCKED"

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    pth="artifacts/mexc_event_futures/payout_browser_probe_v06.json"
    with open(pth,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({
      "source_gate":out["source_gate"],
      "exact_dom_payouts":exact,
      "asset_summaries":[{
        "asset":x["display"],
        "responses":len(x.get("responses",[])),
        "ws_frames":len(x.get("websocket_frames",[])),
        "percents":x.get("dom",{}).get("percent_values",[])[:20]
      } for x in out["assets"]]
    },indent=2))
    print("WROTE",pth)

if __name__=="__main__":
    asyncio.run(main())
