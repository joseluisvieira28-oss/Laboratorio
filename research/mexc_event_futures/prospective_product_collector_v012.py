#!/usr/bin/env python3
import asyncio, csv, hashlib, json, os
from datetime import datetime, timezone
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ENTRY="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
DETAIL_PATH="/api/platform/futures/api/v1/event_contract/detail"
BASE_PATH="/api/platform/futures/api/v1"
PUBLIC_SCHEDULE_PATHS=[
    "/event_contract/trade_date_time",
    "/event_contract/last_trade_date_time",
]
SENSITIVE_TERMS=[
    "/private/","/account","/balance","/wallet","/positions","/position/",
    "/order","/orders","/user/","/api_key","/apikey"
]
MAX_BODY=4*1024*1024

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def sensitive(url):
    low=url.lower()
    return any(x in low for x in SENSITIVE_TERMS)

def allowed_mexc(url):
    h=(urlparse(url).hostname or "").lower()
    return h=="mexc.com" or h.endswith(".mexc.com")

def be_prob(q):
    try:
        q=float(q)
        if q<0: return None
        return 1.0/(1.0+q)
    except Exception:
        return None

async def main():
    os.makedirs("artifacts/mexc_event_futures/v012",exist_ok=True)
    observed_at=now_utc()
    safety={
        "authenticated_requests":0,
        "orders":0,
        "account_mutations":0,
        "private_routes_called":0,
        "transmitted_non_gets":0,
    }
    ev={
        "lab":"MEXC_EVENT_FUTURES_PROSPECTIVE_PRODUCT_V0.12",
        "observed_at_utc":observed_at,
        "entry":ENTRY,
        "safety":safety,
        "blocked_non_gets":[],
        "blocked_sensitive_gets":[],
        "detail_capture":None,
        "detail_candidates":[],
        "schedule_responses":[],
        "rows":[],
        "page":{},
    }

    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await browser.new_context(
            locale="en-GB",
            timezone_id="UTC",
            service_workers="block",
            extra_http_headers={"Accept-Language":"en-GB,en;q=0.9"},
        )
        await ctx.clear_cookies()
        page=await ctx.new_page()

        async def route_handler(route):
            req=route.request
            method=req.method.upper()
            url=req.url
            if method!="GET":
                if len(ev["blocked_non_gets"])<500:
                    ev["blocked_non_gets"].append({"method":method,"url":url})
                await route.abort()
                return
            if sensitive(url):
                if len(ev["blocked_sensitive_gets"])<500:
                    ev["blocked_sensitive_gets"].append({"method":method,"url":url})
                await route.abort()
                return
            await route.continue_()

        await ctx.route("**/*",route_handler)

        detail_event=asyncio.Event()

        async def on_response(resp):
            if DETAIL_PATH not in resp.url:
                return
            if ev["detail_capture"] is not None:
                return
            rec={
                "received_at_utc":now_utc(),
                "url":resp.url,
                "status":resp.status,
                "content_type":resp.headers.get("content-type"),
            }
            try:
                b=await resp.body()
                rec["bytes"]=len(b)
                rec["sha256"]=sha256(b)
                if len(b)>MAX_BODY:
                    rec["error"]="DETAIL_BODY_TOO_LARGE"
                else:
                    rec["json"]=json.loads(b.decode("utf-8","replace"))
            except Exception as e:
                rec["error"]=repr(e)

            j=rec.get("json")
            valid=(
                rec.get("status")==200
                and isinstance(j,dict)
                and j.get("success") is True
                and isinstance(j.get("data"),list)
                and len(j.get("data"))>0
            )
            ev["detail_candidates"].append({
                "received_at_utc":rec.get("received_at_utc"),
                "url":rec.get("url"),
                "status":rec.get("status"),
                "content_type":rec.get("content_type"),
                "bytes":rec.get("bytes"),
                "sha256":rec.get("sha256"),
                "valid":valid,
                "error":rec.get("error"),
            })
            if valid:
                ev["detail_capture"]=rec
                detail_event.set()

        page.on("response",on_response)

        try:
            nav=await page.goto(ENTRY,wait_until="domcontentloaded",timeout=75000)
            try:
                await asyncio.wait_for(detail_event.wait(),timeout=35)
            except asyncio.TimeoutError:
                pass
            body=await page.locator("body").inner_text(timeout=15000)
            ev["page"]={
                "status":nav.status if nav else None,
                "final_url":page.url,
                "title":await page.title(),
                "body_sha256":sha256(body.encode("utf-8","replace")),
                "body_chars":len(body),
            }
        except Exception as e:
            ev["page"]={"error":repr(e),"final_url":page.url}

        dc=ev.get("detail_capture") or {}
        data=(dc.get("json") or {}).get("data")
        if isinstance(data,list):
            for product in data:
                symbol=product.get("symbol")
                if not symbol:
                    continue
                # Optional public schedule data, exact GET-only routes.
                if allowed_mexc(page.url):
                    for path in PUBLIC_SCHEDULE_PATHS:
                        rel=f"{BASE_PATH}{path}?symbol={symbol}"
                        try:
                            res=await page.evaluate("""async (u) => {
                              try {
                                const r=await fetch(u,{method:'GET',credentials:'same-origin',headers:{'accept':'application/json,text/plain,*/*'}});
                                const t=await r.text();
                                return {status:r.status,ok:r.ok,url:r.url,contentType:r.headers.get('content-type'),body:t.slice(0,300000)};
                              } catch(e) { return {error:String(e)}; }
                            }""",rel)
                            raw=(res.pop("body","") or "").encode("utf-8","replace")
                            rec={"symbol":symbol,"path":path,**res}
                            if raw:
                                rec["sha256"]=sha256(raw)
                                try: rec["json"]=json.loads(raw.decode("utf-8","replace"))
                                except Exception: rec["preview"]=raw.decode("utf-8","replace")[:5000]
                            ev["schedule_responses"].append(rec)
                        except Exception as e:
                            ev["schedule_responses"].append({"symbol":symbol,"path":path,"error":repr(e)})

            source_url=dc.get("url")
            source_hash=dc.get("sha256")
            recv_at=dc.get("received_at_utc")
            for product in data:
                cmap=product.get("cycleConfigMap") or {}
                for unit,configs in cmap.items():
                    if not isinstance(configs,list):
                        continue
                    for cfg in configs:
                        up=cfg.get("upPayRate")
                        down=cfg.get("downPayRate")
                        ev["rows"].append({
                            "observation_id":f"{observed_at}|{source_hash}",
                            "observed_at_utc":observed_at,
                            "source_response_received_at_utc":recv_at,
                            "source_url":source_url,
                            "source_sha256":source_hash,
                            "symbol":product.get("symbol"),
                            "contract_id":product.get("contractId"),
                            "product_state":product.get("state"),
                            "cycle_unit":unit,
                            "cycle_value":cfg.get("val"),
                            "up_pay_rate":up,
                            "down_pay_rate":down,
                            "up_break_even_probability":be_prob(up),
                            "down_break_even_probability":be_prob(down),
                            "invest_min_amount":product.get("investMinAmount"),
                            "invest_max_amount":product.get("investMaxAmount"),
                            "index_price_scale":product.get("indexPriceScale"),
                            "pay_rate_scale":product.get("payRateScale"),
                            "settle_coin":product.get("settleCoin"),
                        })

        await browser.close()

    # Fail-closed validation.
    dc=ev.get("detail_capture")
    if not dc:
        verdict="BLOCKED_NO_DETAIL_CAPTURE"
    elif dc.get("status")!=200:
        verdict="BLOCKED_DETAIL_HTTP"
    elif not isinstance(dc.get("json"),dict) or dc["json"].get("success") is not True:
        verdict="BLOCKED_DETAIL_SCHEMA"
    elif not isinstance(dc["json"].get("data"),list) or not dc["json"]["data"]:
        verdict="BLOCKED_EMPTY_PRODUCT_LIST"
    elif not ev["rows"]:
        verdict="BLOCKED_NO_PRODUCT_CYCLE_ROWS"
    else:
        verdict="PROSPECTIVE_SNAPSHOT_PASS"

    ev["verdict"]=verdict
    ev["counters"]={
        "products":len((dc.get("json") or {}).get("data",[])) if isinstance(dc,dict) else 0,
        "rows":len(ev["rows"]),
        "schedule_responses":len(ev["schedule_responses"]),
        "schedule_200_json":sum(1 for r in ev["schedule_responses"] if r.get("status")==200 and isinstance(r.get("json"),(dict,list))),
        "blocked_non_gets":len(ev["blocked_non_gets"]),
        "blocked_sensitive_gets":len(ev["blocked_sensitive_gets"]),
    }

    json_path="artifacts/mexc_event_futures/v012/prospective_snapshot_v012.json"
    with open(json_path,"w",encoding="utf-8") as f:
        json.dump(ev,f,indent=2,sort_keys=True,ensure_ascii=False)

    csv_path="artifacts/mexc_event_futures/v012/prospective_product_cycles_v012.csv"
    fields=[
        "observation_id","observed_at_utc","source_response_received_at_utc","source_url","source_sha256",
        "symbol","contract_id","product_state","cycle_unit","cycle_value","up_pay_rate","down_pay_rate",
        "up_break_even_probability","down_break_even_probability","invest_min_amount","invest_max_amount",
        "index_price_scale","pay_rate_scale","settle_coin"
    ]
    with open(csv_path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(ev["rows"])

    print(json.dumps({
        "verdict":verdict,
        "observed_at_utc":observed_at,
        "detail_status":dc.get("status") if isinstance(dc,dict) else None,
        "detail_sha256":dc.get("sha256") if isinstance(dc,dict) else None,
        "counters":ev["counters"],
        "safety":safety,
        "sample_rows":ev["rows"][:12],
    },indent=2,sort_keys=True,ensure_ascii=False))

    if verdict!="PROSPECTIVE_SNAPSHOT_PASS":
        raise SystemExit(2)

if __name__=="__main__":
    asyncio.run(main())
