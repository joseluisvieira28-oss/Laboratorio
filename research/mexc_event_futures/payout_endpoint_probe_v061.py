#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from datetime import datetime, timezone
from playwright.async_api import async_playwright

URL="https://www.mexc.com/futures/event-futures/BTC_USDT"

def sha(s):
    return hashlib.sha256(s.encode("utf-8","ignore")).hexdigest()

def payoutish(obj):
    s=json.dumps(obj,ensure_ascii=False) if not isinstance(obj,str) else obj
    low=s.lower()
    return any(k in low for k in (
        "payout","predict/market","prediction","event","timeunit","time_unit",
        "up_rate","down_rate","up_rate","downrate","uprate"
    ))

async def main():
    out={
      "lab":"MEXC_EVENT_FUTURES_PAYOUT_ENDPOINT_DERIVATION_V0.6.1",
      "observed_at_utc":datetime.now(timezone.utc).isoformat(),
      "page":URL,"responses":[],"ws_frames":[],"dom":{}
    }
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context()
        page=await ctx.new_page()

        async def route_handler(route,request):
            if request.method.upper()!="GET":
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",route_handler)

        async def on_response(resp):
            try:
                req=resp.request
                url=resp.url
                if req.resource_type not in ("xhr","fetch") and "prediction" not in url.lower():
                    return
                ctype=(resp.headers.get("content-type") or "").lower()
                if "json" not in ctype and "text" not in ctype:
                    return
                body=await resp.text()
                if len(body)>600000: body=body[:600000]
                if payoutish(body) or "prediction" in url.lower() or "/predict/" in url.lower():
                    out["responses"].append({
                      "url":url,"status":resp.status,"resource_type":req.resource_type,
                      "sha256":sha(body),"body_excerpt":body[:50000]
                    })
            except Exception:
                pass
        page.on("response",on_response)

        def on_ws(ws):
            def recv(payload):
                try:
                    s=payload if isinstance(payload,str) else str(payload)
                    if payoutish(s):
                        out["ws_frames"].append({
                          "url":ws.url,"sha256":sha(s),"payload_excerpt":s[:50000]
                        })
                except Exception:
                    pass
            ws.on("framereceived",recv)
        page.on("websocket",on_ws)

        await page.goto(URL,wait_until="domcontentloaded",timeout=90000)
        await page.wait_for_timeout(15000)
        body=await page.locator("body").inner_text()
        out["dom"]["text_sha256"]=sha(body)
        out["dom"]["excerpt"]=body[:40000]
        out["dom"]["up"]=re.findall(r'(?i)(?:Up\s*Payout|Payout\s*Up)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)[:5]
        out["dom"]["down"]=re.findall(r'(?i)(?:Down\s*Payout|Payout\s*Down)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)[:5]
        await ctx.close(); await browser.close()

    # Surface candidate exact endpoints and payout-like key/value fragments.
    candidates=[]
    for r in out["responses"]:
        body=r["body_excerpt"]
        fields=[]
        for pat in [
          r'"([^"]*payout[^"]*)"\s*:\s*([^,}\]]+)',
          r'"([^"]*(?:up|down)[^"]*(?:rate|ratio|pay)[^"]*)"\s*:\s*([^,}\]]+)',
          r'"([^"]*(?:time.?unit|period|expire|duration)[^"]*)"\s*:\s*([^,}\]]+)',
        ]:
            fields.extend(re.findall(pat,body,re.I)[:30])
        candidates.append({"url":r["url"],"status":r["status"],"fields":fields[:60],"excerpt":body[:6000]})

    out["candidate_endpoint_evidence"]=candidates
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    path="artifacts/mexc_event_futures/payout_endpoint_probe_v061.json"
    with open(path,"w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,sort_keys=True)

    print(json.dumps({
      "dom_up":out["dom"]["up"],
      "dom_down":out["dom"]["down"],
      "response_count":len(out["responses"]),
      "ws_count":len(out["ws_frames"]),
      "candidate_endpoints":[{
        "url":x["url"],"status":x["status"],"fields":x["fields"][:20]
      } for x in candidates[:80]],
      "ws_urls":sorted(set(x["url"] for x in out["ws_frames"]))[:50]
    },indent=2,ensure_ascii=False))
    print("WROTE",path)

if __name__=="__main__":
    asyncio.run(main())
