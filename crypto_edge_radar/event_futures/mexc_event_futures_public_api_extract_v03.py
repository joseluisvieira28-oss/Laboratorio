from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PAGE="https://www.mexc.com/futures/event-futures/BTC_USDT"
UA="crypto-edge-radar/mexc-event-futures-public-api-extract-v03"
SCRIPT_RE=re.compile(r'<script[^>]+src=["\']([^"\']+)["\']',re.I)
PATH_RE=re.compile(r'NEW_SWAP_API\}\s*/?([^\x60\'"]{0,220}event_contract[^\x60\'"]{0,220})',re.I)
LITERAL_RE=re.compile(r'["\']([^"\']*(?:event_contract|event-contract)[^"\']*)["\']',re.I)

def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/javascript,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read()

def contexts(text:str,needle:str,window:int=2500,limit:int=20)->list[str]:
    low=text.lower(); q=needle.lower(); out=[]; pos=0
    while len(out)<limit:
        i=low.find(q,pos)
        if i<0: break
        out.append(text[max(0,i-window):min(len(text),i+len(q)+window)].replace("\n"," "))
        pos=i+len(q)
    return out

def main()->int:
    html=fetch(PAGE).decode("utf-8",errors="replace")
    srcs=[]
    for src in SCRIPT_RE.findall(html):
        u=urllib.parse.urljoin(PAGE,src)
        if u not in srcs: srcs.append(u)

    findings=[]
    for u in srcs:
        try:
            raw=fetch(u)
            if len(raw)>12_000_000: continue
            text=raw.decode("utf-8",errors="replace")
            low=text.lower()
            if "event_contract" not in low and "getproductlistapi" not in low:
                continue
            lits=[]
            for m in LITERAL_RE.finditer(text):
                v=m.group(1)
                if v not in lits:
                    lits.append(v)
            module_ctx=[]
            for needle in ("946846,e=>","getProductListApi","NEW_SWAP_API","event_contract"):
                module_ctx.extend(contexts(text,needle,2000,8))
            findings.append({
                "script":u,
                "bytes":len(raw),
                "string_literals":lits[:200],
                "contexts":module_ctx[:40],
            })
        except Exception as e:
            findings.append({"script":u,"error":f"{type(e).__name__}:{e}"})

    receipt={
      "probe_id":"MEXC_EVENT_FUTURES_PUBLIC_API_EXTRACT_V0.3",
      "created_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "page":PAGE,
      "findings":findings,
      "public_calls_made":[] ,
      "authenticated_api_used":False,
      "private_endpoint_called":False,
      "orders_created":False,
    }
    with open("mexc_event_futures_public_api_extract_v03.json","w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps({
      "probe_id":receipt["probe_id"],
      "finding_count":len(findings),
      "authenticated_api_used":False,
      "private_endpoint_called":False,
      "orders_created":False,
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
