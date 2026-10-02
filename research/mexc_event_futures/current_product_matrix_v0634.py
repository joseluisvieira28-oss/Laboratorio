#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from datetime import datetime, timezone
import requests
from playwright.async_api import async_playwright

ASSETS={
 "BTCUSDT":"BTC_USDT",
 "ETHUSDT":"ETH_USDT",
 "NVDAUSDT":"NVIDIA_USDT",
 "MUUSDT":"MUSTOCK_USDT",
 "SPCXUSDT":"SPCXSTOCK_USDT",
}
BASE="https://www.mexc.com/futures/event-futures/"
INDEX_BASE="https://contract.mexc.com/api/v1/contract/index_price/"

def sha(s):
    return hashlib.sha256(s.encode("utf-8","ignore")).hexdigest()

def parse_payouts(body):
    up=re.findall(r'(?i)(?:Up\s*Payout|Payout\s*Up)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)
    dn=re.findall(r'(?i)(?:Down\s*Payout|Payout\s*Down)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)
    return (float(up[0]) if up else None, float(dn[0]) if dn else None)

def public_proxy_index(symbol):
    try:
        r=requests.get(INDEX_BASE+symbol,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
        j=r.json()
        d=(j or {}).get("data") or {}
        return {
          "source_kind":"PROXY_INDEX",
          "url":r.url,
          "status_code":r.status_code,
          "success":bool((j or {}).get("success") is True),
          "index_price":d.get("indexPrice") if "indexPrice" in d else d.get("price"),
          "timestamp":d.get("timestamp"),
          "payload_sha256":sha(json.dumps(j,sort_keys=True,ensure_ascii=False))
        }
    except Exception as e:
        return {"source_kind":"PROXY_INDEX","error":repr(e)}

async def group_info(page):
    return await page.evaluate("""
    () => {
      const isVisibleLeaf=(el,txt)=>{
        if((el.innerText||'').trim()!==txt) return false;
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) return false;
        return ![...el.children].some(ch=>(ch.innerText||'').trim()===txt);
      };
      const anchors=[...document.querySelectorAll('span,button,[role="button"],div')].filter(el=>isVisibleLeaf(el,'10m'));
      if(anchors.length!==1) return {ok:false,reason:'ANCHOR_10M_NOT_UNIQUE',count:anchors.length};
      const group=anchors[0].parentElement && anchors[0].parentElement.parentElement;
      if(!group) return {ok:false,reason:'GROUP_MISSING'};
      const all=[...group.querySelectorAll('span,button,[role="button"],div')];
      const labels=[];
      for(const el of all){
        const t=(el.innerText||'').trim();
        if(!/^\d+\s*[mMhHdD]$/.test(t)) continue;
        if(!isVisibleLeaf(el,t)) continue;
        if(!labels.includes(t)) labels.push(t);
      }
      return {
        ok: labels.length===4 && labels.includes('10m') && labels.includes('30m'),
        labels,
        text:(group.innerText||'').trim().slice(0,500)
      };
    }
    """)

async def click_in_group(page,label):
    return await page.evaluate("""
    (label) => {
      const isVisibleLeaf=(el,txt)=>{
        if((el.innerText||'').trim()!==txt) return false;
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) return false;
        return ![...el.children].some(ch=>(ch.innerText||'').trim()===txt);
      };
      const anchors=[...document.querySelectorAll('span,button,[role="button"],div')].filter(el=>isVisibleLeaf(el,'10m'));
      if(anchors.length!==1) return {clicked:false,reason:'ANCHOR_10M_NOT_UNIQUE',count:anchors.length};
      const group=anchors[0].parentElement && anchors[0].parentElement.parentElement;
      if(!group) return {clicked:false,reason:'GROUP_MISSING'};
      const candidates=[...group.querySelectorAll('span,button,[role="button"],div')].filter(el=>isVisibleLeaf(el,label));
      if(candidates.length!==1) return {clicked:false,reason:'TARGET_NOT_UNIQUE',count:candidates.length};
      candidates[0].click();
      return {clicked:true,group_text:(group.innerText||'').trim().slice(0,500)};
    }
    """,label)

async def event_index_context(page):
    return await page.evaluate("""
    () => {
      const out=[];
      for(const el of [...document.querySelectorAll('div,span')]){
        const t=(el.innerText||'').trim();
        if(t!=='Index' && t!=='Index Price') continue;
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) continue;
        out.push({
          label:t,
          parent_text:((el.parentElement&&el.parentElement.innerText)||'').trim().slice(0,500),
          grandparent_text:((el.parentElement&&el.parentElement.parentElement&&el.parentElement.parentElement.innerText)||'').trim().slice(0,1000)
        });
      }
      return out.slice(0,20);
    }
    """)

async def inspect(browser,display,symbol):
    ctx=await browser.new_context()
    page=await ctx.new_page()
    async def guard(route,request):
        if request.method.upper()!="GET":
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*",guard)
    a={"asset":display,"symbol":symbol,"page":BASE+symbol,"records":[]}
    try:
        await page.goto(BASE+symbol,wait_until="domcontentloaded",timeout=90000)
        await page.wait_for_timeout(9000)
        gi=await group_info(page)
        a["horizon_group"]=gi
        if not gi.get("ok"):
            a["error"]="HORIZON_GROUP_INVALID"
            await ctx.close()
            return a
        for h in gi["labels"]:
            ck=await click_in_group(page,h)
            if not ck.get("clicked"):
                a["records"].append({"asset":display,"symbol":symbol,"horizon":h,"status":"SELECTOR_FAIL","selector":ck})
                continue
            await page.wait_for_timeout(1700)
            body=await page.locator("body").inner_text()
            up,dn=parse_payouts(body)
            a["records"].append({
              "asset":display,"symbol":symbol,"horizon":h,
              "status":"PASS" if up is not None and dn is not None else "PAYOUT_NOT_FOUND",
              "observed_at_utc":datetime.now(timezone.utc).isoformat(),
              "up_payout_pct":up,"down_payout_pct":dn,
              "source_kind":"EXACT_CURRENT_PAYOUT",
              "source_url":page.url,
              "dom_sha256":sha(body),
              "selector":ck,
              "event_dom_index_context":await event_index_context(page),
              "proxy_index":public_proxy_index(symbol)
            })
    except Exception as e:
        a["error"]=repr(e)
    await ctx.close()
    return a

async def main():
    out={"lab":"MEXC_EVENT_FUTURES_CURRENT_PRODUCT_MATRIX_V0.6.3.4",
         "started_at_utc":datetime.now(timezone.utc).isoformat(),"assets":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for display,symbol in ASSETS.items():
            out["assets"].append(await inspect(browser,display,symbol))
        await browser.close()

    all_records=[r for a in out["assets"] for r in a.get("records",[])]
    good=[r for r in all_records if r.get("status")=="PASS"]
    groups_ok=all(a.get("horizon_group",{}).get("ok") and len(a["horizon_group"].get("labels",[]))==4 for a in out["assets"])
    out["current_horizon_matrix"]={a["asset"]:a.get("horizon_group",{}).get("labels",[]) for a in out["assets"]}
    out["records"]=good
    out["pass_count"]=len(good)
    out["source_gate"]="PASS_CURRENT_PRODUCT_MATRIX" if groups_ok and len(good)==20 else ("PARTIAL" if good else "BLOCKED")
    out["finished_at_utc"]=datetime.now(timezone.utc).isoformat()

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    path="artifacts/mexc_event_futures/current_product_matrix_v0634.json"
    jl="artifacts/mexc_event_futures/current_product_matrix_v0634.jsonl"
    with open(path,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
    with open(jl,"w",encoding="utf-8") as f:
        for r in good: f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n")

    print(json.dumps({
      "source_gate":out["source_gate"],"pass_count":out["pass_count"],
      "current_horizon_matrix":out["current_horizon_matrix"],
      "payout_matrix":[{
        "asset":r["asset"],"horizon":r["horizon"],
        "up":r["up_payout_pct"],"down":r["down_payout_pct"],
        "proxy_index":r.get("proxy_index",{}).get("index_price")
      } for r in good],
      "asset_errors":{a["asset"]:a.get("error") for a in out["assets"] if a.get("error")}
    },indent=2,ensure_ascii=False))
    print("WROTE",path); print("WROTE",jl)

if __name__=="__main__":
    asyncio.run(main())
