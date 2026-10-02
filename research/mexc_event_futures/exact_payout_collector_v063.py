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
HORIZONS=["10m","30m","1H","1D"]
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

async def get_horizon_group(page):
    return await page.evaluate("""
    () => {
      const labels=['10m','30m','1H','1D'];
      const nodes=[...document.querySelectorAll('div,section,aside,header,main')];
      const candidates=[];
      for(const el of nodes){
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) continue;
        const txt=(el.innerText||'').trim().split(/\n+/).map(x=>x.trim()).filter(Boolean);
        const found=labels.every(x=>txt.includes(x));
        if(!found) continue;
        const extra=txt.filter(x=>/^\d+\s*[mMhHdD]$/.test(x));
        const score=extra.length;
        candidates.push({
          score, text:txt.slice(0,20), x:r.x,y:r.y,w:r.width,h:r.height,
          tag:el.tagName,className:String(el.className||'')
        });
      }
      candidates.sort((a,b)=>a.score-b.score || a.w*b.h-b.w*b.h);
      return candidates.slice(0,20);
    }
    """)

async def click_horizon_in_group(page,label):
    return await page.evaluate("""
    (label) => {
      const visibleLeaf=(txt)=>[...document.querySelectorAll('span,button,[role="button"],div')].filter(el=>{
        if((el.innerText||'').trim()!==txt) return false;
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) return false;
        return ![...el.children].some(ch=>(ch.innerText||'').trim()===txt);
      });

      const anchors=visibleLeaf('10m');
      if(anchors.length!==1) return {clicked:false,reason:'ANCHOR_10M_NOT_UNIQUE',count:anchors.length};

      const group=anchors[0].parentElement && anchors[0].parentElement.parentElement;
      if(!group) return {clicked:false,reason:'GROUP_GRANDPARENT_MISSING'};

      const short=(group.innerText||'').trim().split(/\n+/).map(x=>x.trim()).filter(x=>/^\d+\s*[mMhHdD]$/.test(x));
      const normalized=[...new Set(short)];
      const required=['10m','30m','1H','1D'];
      if(normalized.length!==4 || !required.every(x=>normalized.includes(x))){
        return {clicked:false,reason:'GROUP_VALIDATION_FAILED',short_labels:normalized,text:(group.innerText||'').trim().slice(0,500)};
      }

      const candidates=[...group.querySelectorAll('span,button,[role="button"],div')].filter(el=>{
        if((el.innerText||'').trim()!==label) return false;
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) return false;
        return ![...el.children].some(ch=>(ch.innerText||'').trim()===label);
      });
      if(candidates.length!==1) return {clicked:false,reason:'TARGET_NOT_UNIQUE_IN_VALIDATED_GROUP',count:candidates.length};

      const target=candidates[0];
      target.click();
      const r=target.getBoundingClientRect();
      return {
        clicked:true,count:1,tag:target.tagName,className:String(target.className||''),
        x:r.x,y:r.y,group_text:(group.innerText||'').trim().slice(0,500)
      };
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
          grandparent_text:((el.parentElement&&el.parentElement.parentElement&&el.parentElement.parentElement.innerText)||'').trim().slice(0,1000),
          x:r.x,y:r.y
        });
      }
      return out.slice(0,30);
    }
    """)

async def inspect(browser,display,symbol):
    ctx=await browser.new_context()
    page=await ctx.new_page()
    async def route_handler(route,request):
        if request.method.upper()!="GET":
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*",route_handler)
    asset={"asset":display,"symbol":symbol,"page":BASE+symbol,"records":[]}
    try:
        await page.goto(BASE+symbol,wait_until="domcontentloaded",timeout=90000)
        await page.wait_for_timeout(9000)
        asset["group_candidates"]=await get_horizon_group(page)
        asset["initial_index_context"]=await event_index_context(page)
        for horizon in HORIZONS:
            click=await click_horizon_in_group(page,horizon)
            if not click.get("clicked"):
                asset["records"].append({
                  "asset":display,"symbol":symbol,"horizon":horizon,
                  "status":"SELECTOR_FAIL","selector":click
                })
                continue
            await page.wait_for_timeout(1800)
            body=await page.locator("body").inner_text()
            up,dn=parse_payouts(body)
            rec={
              "asset":display,"symbol":symbol,"horizon":horizon,
              "status":"PASS" if up is not None and dn is not None else "PAYOUT_NOT_FOUND",
              "observed_at_utc":datetime.now(timezone.utc).isoformat(),
              "up_payout_pct":up,"down_payout_pct":dn,
              "source_kind":"EXACT_CURRENT_PAYOUT",
              "source_url":page.url,
              "dom_sha256":sha(body),
              "selector":click,
              "event_dom_index_context":await event_index_context(page),
              "proxy_index":public_proxy_index(symbol)
            }
            asset["records"].append(rec)
    except Exception as e:
        asset["error"]=repr(e)
    await ctx.close()
    return asset

async def main():
    out={
      "lab":"MEXC_EVENT_FUTURES_EXACT_PAYOUT_COLLECTOR_V0.6.3.2",
      "run_started_at_utc":datetime.now(timezone.utc).isoformat(),
      "assets":[]
    }
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for display,symbol in ASSETS.items():
            out["assets"].append(await inspect(browser,display,symbol))
        await browser.close()

    records=[r for a in out["assets"] for r in a.get("records",[]) if r.get("status")=="PASS"]
    out["records"]=records
    out["pass_count"]=len(records)
    out["source_gate"]="PASS_20_OF_20" if len(records)==20 else ("PARTIAL" if records else "BLOCKED")
    out["run_finished_at_utc"]=datetime.now(timezone.utc).isoformat()

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    jp="artifacts/mexc_event_futures/exact_payout_snapshot_v063.json"
    jl="artifacts/mexc_event_futures/exact_payout_snapshot_v063.jsonl"
    with open(jp,"w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,sort_keys=True)
    with open(jl,"w",encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n")

    print(json.dumps({
      "source_gate":out["source_gate"],
      "pass_count":out["pass_count"],
      "records":[{
        "asset":r["asset"],"horizon":r["horizon"],
        "up":r["up_payout_pct"],"down":r["down_payout_pct"],
        "observed_at_utc":r["observed_at_utc"],
        "proxy_index":r.get("proxy_index",{}).get("index_price"),
        "index_context":r.get("event_dom_index_context",[])[:3]
      } for r in records],
      "all_statuses":[{
        "asset":a["asset"],
        "error":a.get("error"),
        "records":a.get("records",[])
      } for a in out["assets"]]
    },indent=2,ensure_ascii=False))
    print("WROTE",jp)
    print("WROTE",jl)

if __name__=="__main__":
    asyncio.run(main())
