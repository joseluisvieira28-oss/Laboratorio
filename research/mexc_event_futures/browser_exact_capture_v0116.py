#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ENTRY="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
BASE_PATH="/api/platform/futures/api/v1"
SYMBOLS=["BTC_USDT","ETH_USDT","NVIDIA_USDT","MUSTOCK_USDT","SPCXSTOCK_USDT"]
PUBLIC_ACTIVE_PATHS=[
    "/event_contract/trade_date_time",
    "/event_contract/last_trade_date_time",
]
SENSITIVE_URL_TERMS=[
    "/private/","/account","/balance","/wallet","/positions","/position/",
    "/order","/orders","/user/","/api_key","/apikey"
]
STATIC_TERMS=[
    "event_contract","EventContractPositionChange","payout","profitRate","profit_rate",
    "winRate","upPayout","downPayout","cycleAmount","timeUnit","priceLimit",
    "minAmount","maxAmount","settle","settlement","indexPrice","index_price"
]
MAX_BODY=2*1024*1024
MAX_JS=100
MAX_JS_BYTES=10*1024*1024
MAX_WS_FRAMES=120

def sha(b): return hashlib.sha256(b).hexdigest()

def allowed_host(url):
    h=(urlparse(url).hostname or "").lower()
    return h=="mexc.com" or h.endswith(".mexc.com") or h.endswith(".mocortech.com")

def sensitive_url(url):
    low=url.lower()
    return any(x in low for x in SENSITIVE_URL_TERMS)

def redact(obj):
    if isinstance(obj,dict):
        out={}
        for k,v in obj.items():
            lk=str(k).lower()
            if any(s in lk for s in ["token","secret","password","cookie","authorization","api_key","apikey"]):
                out[k]="<REDACTED>"
            else:
                out[k]=redact(v)
        return out
    if isinstance(obj,list):
        return [redact(x) for x in obj[:500]]
    return obj

def parse_body(raw, content_type):
    if len(raw)>MAX_BODY:
        return {"bytes":len(raw),"sha256":sha(raw),"too_large":True}
    rec={"bytes":len(raw),"sha256":sha(raw)}
    txt=raw.decode("utf-8","replace")
    if "json" in (content_type or "").lower():
        try:
            rec["json"]=redact(json.loads(txt))
            return rec
        except Exception:
            pass
    rec["preview"]=txt[:12000]
    return rec

def static_snips(text,url):
    low=text.lower()
    out=[]
    for term in STATIC_TERMS:
        pos=0
        count=0
        needle=term.lower()
        while count<12:
            i=low.find(needle,pos)
            if i<0: break
            out.append({
                "term":term,"url":url,"offset":i,
                "snippet":text[max(0,i-700):min(len(text),i+len(term)+1300)]
            })
            pos=i+len(term); count+=1
    return out

def contains_payout_signal(obj):
    try:
        low=json.dumps(obj,ensure_ascii=False).lower()
    except Exception:
        low=str(obj).lower()
    keys=["payout","profitrate","profit_rate","uppayout","downpayout","winrate","rewardrate","yieldrate"]
    return any(k in low for k in keys)

def contains_product_signal(obj):
    try:
        low=json.dumps(obj,ensure_ascii=False).lower()
    except Exception:
        low=str(obj).lower()
    return "event_contract" in low or any(k in low for k in [
        "cycleamount","timeunit","pricelimit","minamount","maxamount","settlement","indexprice"
    ])

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    ev={
      "lab":"MEXC_EVENT_FUTURES_BROWSER_EXACT_CAPTURE_V0.11.6",
      "entry":ENTRY,
      "authenticated_requests":0,
      "orders":0,
      "account_mutations":0,
      "private_routes_called":0,
      "transmitted_non_gets":0,
      "browser_gets":[],
      "event_responses":[],
      "blocked_non_gets":[],
      "blocked_sensitive_gets":[],
      "public_fetches":[],
      "websockets":[],
      "ws_frames_received":[],
      "js_assets":[],
      "static_snippets":[],
      "page":{},
    }

    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await browser.new_context(
            locale="en-GB",timezone_id="UTC",
            extra_http_headers={"Accept-Language":"en-GB,en;q=0.9"}
        )
        await ctx.clear_cookies()
        page=await ctx.new_page()

        async def route_handler(route):
            req=route.request
            method=req.method.upper()
            url=req.url
            if method!="GET":
                if len(ev["blocked_non_gets"])<300:
                    ev["blocked_non_gets"].append({"method":method,"url":url})
                await route.abort()
                return
            if sensitive_url(url):
                if len(ev["blocked_sensitive_gets"])<300:
                    ev["blocked_sensitive_gets"].append({"method":method,"url":url})
                await route.abort()
                return
            if ("event_contract" in url.lower() or "event-futures" in url.lower()) and len(ev["browser_gets"])<500:
                ev["browser_gets"].append({"method":method,"url":url})
            await route.continue_()

        await ctx.route("**/*",route_handler)

        async def on_response(resp):
            u=resp.url
            low=u.lower()
            if "event_contract" not in low and "event-futures" not in low:
                return
            rec={
                "url":u,
                "status":resp.status,
                "content_type":resp.headers.get("content-type"),
            }
            try:
                b=await resp.body()
                rec.update(parse_body(b,rec["content_type"]))
            except Exception as e:
                rec["body_error"]=repr(e)
            if len(ev["event_responses"])<300:
                ev["event_responses"].append(rec)

        page.on("response",on_response)

        def on_ws(ws):
            item={"url":ws.url,"received_frames":0}
            ev["websockets"].append(item)
            def recv(payload):
                if len(ev["ws_frames_received"])>=MAX_WS_FRAMES:
                    return
                txt=payload if isinstance(payload,str) else repr(payload)
                low=txt.lower()
                if any(k.lower() in low for k in STATIC_TERMS):
                    ev["ws_frames_received"].append({
                        "url":ws.url,
                        "sha256":hashlib.sha256(txt.encode("utf-8","replace")).hexdigest(),
                        "preview":txt[:12000]
                    })
                    item["received_frames"]+=1
            ws.on("framereceived",recv)

        page.on("websocket",on_ws)

        try:
            nav=await page.goto(ENTRY,wait_until="domcontentloaded",timeout=75000)
            await page.wait_for_timeout(25000)
            body=await page.locator("body").inner_text(timeout=15000)
            ev["page"]={
                "status":nav.status if nav else None,
                "final_url":page.url,
                "title":await page.title(),
                "body_chars":len(body),
                "body_sha256":sha(body.encode()),
                "visible_payout_label":"payout" in body.lower(),
                "visible_event_futures":"event futures" in body.lower(),
            }
        except Exception as e:
            ev["page"]={"error":repr(e),"final_url":page.url}

        # Active probes are restricted to bundle-proven public GET routes.
        for sym in SYMBOLS:
            for path in PUBLIC_ACTIVE_PATHS:
                rel=f"{BASE_PATH}{path}?symbol={sym}"
                try:
                    result=await page.evaluate("""async (u) => {
                      try {
                        const r=await fetch(u,{method:'GET',credentials:'same-origin',headers:{'accept':'application/json,text/plain,*/*'}});
                        const t=await r.text();
                        return {ok:r.ok,status:r.status,url:r.url,contentType:r.headers.get('content-type'),body:t.slice(0,200000)};
                      } catch(e) {
                        return {error:String(e)};
                      }
                    }""",rel)
                    rec={"symbol":sym,"path":path,**result}
                    b=(rec.pop("body","") or "").encode("utf-8","replace")
                    if b:
                        rec.update(parse_body(b,rec.get("contentType")))
                    ev["public_fetches"].append(rec)
                except Exception as e:
                    ev["public_fetches"].append({"symbol":sym,"path":path,"error":repr(e)})

        # Static bundle mapping, GET only.
        try:
            scripts=await page.locator("script[src]").evaluate_all("(els)=>Array.from(new Set(els.map(e=>e.src)))")
        except Exception:
            scripts=[]
        for u in scripts[:MAX_JS]:
            if not allowed_host(u) or sensitive_url(u):
                continue
            try:
                r=await ctx.request.get(u,timeout=30000)
                if not r.ok:
                    ev["js_assets"].append({"url":u,"status":r.status})
                    continue
                b=await r.body()
                if len(b)>MAX_JS_BYTES:
                    ev["js_assets"].append({"url":u,"status":r.status,"bytes":len(b),"too_large":True})
                    continue
                t=b.decode("utf-8","replace")
                sn=static_snips(t,u)
                ev["js_assets"].append({"url":u,"status":r.status,"bytes":len(b),"sha256":sha(b),"snippet_count":len(sn)})
                ev["static_snippets"].extend(sn)
            except Exception as e:
                ev["js_assets"].append({"url":u,"error":repr(e)})

        await browser.close()

    # Safety counters are semantic: blocked attempts were not transmitted.
    ev["authenticated_requests"]=0
    ev["orders"]=0
    ev["account_mutations"]=0
    ev["private_routes_called"]=0
    ev["transmitted_non_gets"]=0

    runtime_records=ev["event_responses"]+ev["public_fetches"]
    payout_runtime=any(
        (r.get("status")==200 or r.get("ok") is True) and contains_payout_signal(r.get("json",r.get("preview","")))
        for r in runtime_records
    )
    product_runtime=any(
        (r.get("status")==200 or r.get("ok") is True) and contains_product_signal(r.get("json",r.get("preview","")))
        for r in runtime_records
    )
    schedule_ok=any(
        r.get("status")==200 and isinstance(r.get("json"),(dict,list))
        for r in ev["public_fetches"]
    )
    static_mapping=any(
        x.get("term") in ["payout","profitRate","profit_rate","upPayout","downPayout","cycleAmount","timeUnit","priceLimit","EventContractPositionChange"]
        for x in ev["static_snippets"]
    )
    event_blocked=any(r.get("status") in (401,403,429) for r in ev["event_responses"]+ev["public_fetches"])

    if payout_runtime:
        verdict="EXACT_PAYOUT_FIELDS_FOUND"
    elif product_runtime:
        verdict="EXACT_PRODUCT_SCHEMA_FOUND"
    elif schedule_ok:
        verdict="PUBLIC_SCHEDULE_SCHEMA_FOUND_PAYOUT_UNRESOLVED"
    elif static_mapping:
        verdict="STATIC_PRODUCT_MAPPING_FOUND_RUNTIME_SOURCE_BLOCKED"
    elif event_blocked:
        verdict="BROWSER_EVENT_CONTRACT_ACCESS_BLOCKED"
    else:
        verdict="SOURCE_BLOCKED"

    ev["verdict"]=verdict
    ev["counters"]={
        "browser_gets":len(ev["browser_gets"]),
        "event_responses":len(ev["event_responses"]),
        "blocked_non_gets":len(ev["blocked_non_gets"]),
        "blocked_sensitive_gets":len(ev["blocked_sensitive_gets"]),
        "public_fetches":len(ev["public_fetches"]),
        "public_fetch_200_json":sum(1 for r in ev["public_fetches"] if r.get("status")==200 and isinstance(r.get("json"),(dict,list))),
        "websockets":len(ev["websockets"]),
        "ws_frames_received":len(ev["ws_frames_received"]),
        "js_assets":len(ev["js_assets"]),
        "static_snippets":len(ev["static_snippets"]),
    }

    path="artifacts/mexc_event_futures/browser_exact_capture_v0116.json"
    with open(path,"w",encoding="utf-8") as f:
        json.dump(ev,f,indent=2,sort_keys=True,ensure_ascii=False)

    print(json.dumps({
        "verdict":verdict,
        **ev["counters"],
        "page":ev["page"],
        "safety":{
          "authenticated_requests":0,"orders":0,"account_mutations":0,
          "private_routes_called":0,"transmitted_non_gets":0
        },
        "public_fetch_statuses":[
          {"symbol":r.get("symbol"),"path":r.get("path"),"status":r.get("status"),"contentType":r.get("contentType")}
          for r in ev["public_fetches"]
        ],
        "event_response_statuses":[
          {"url":r.get("url"),"status":r.get("status"),"content_type":r.get("content_type")}
          for r in ev["event_responses"][:80]
        ]
    },indent=2,sort_keys=True,ensure_ascii=False))
    print("STATIC_TOPICS="+json.dumps(sorted(set(x.get("term") for x in ev["static_snippets"] if x.get("term"))),ensure_ascii=False))
    print("WROTE",path)

if __name__=="__main__":
    asyncio.run(main())
