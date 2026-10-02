from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PAGE="https://www.mexc.com/futures/event-futures/BTC_USDT"
UA="crypto-edge-radar/mexc-event-futures-public-base-extract-v04"
SCRIPT_RE=re.compile(r'<script[^>]+src=["\']([^"\']+)["\']',re.I)
URL_RE=re.compile(r'https?://[^"\'\x60\\\s]{5,300}')

def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/javascript,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read()

def ctx(text:str,needle:str,window:int=6000)->str|None:
    i=text.find(needle)
    if i<0: return None
    return text[max(0,i-window):min(len(text),i+len(needle)+window)].replace("\n"," ")

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
            if "NEW_SWAP_API" not in text and "853411" not in text:
                continue
            contexts=[]
            for needle in ("853411,e=>","NEW_SWAP_API","PUBLIC_CONTRACT_DEPLOY"):
                x=ctx(text,needle)
                if x: contexts.append({"needle":needle,"text":x})
            urls=[]
            for m in URL_RE.finditer(text):
                v=m.group(0)
                if any(k in v.lower() for k in ("mexc","contract","future","api")) and v not in urls:
                    urls.append(v)
                if len(urls)>=200: break
            findings.append({"script":u,"bytes":len(raw),"contexts":contexts,"candidate_urls":urls})
        except Exception as e:
            findings.append({"script":u,"error":f"{type(e).__name__}:{e}"})

    receipt={
      "probe_id":"MEXC_EVENT_FUTURES_PUBLIC_BASE_EXTRACT_V0.4",
      "created_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "findings":findings,
      "authenticated_api_used":False,
      "private_endpoint_called":False,
      "orders_created":False,
    }
    with open("mexc_event_futures_public_base_extract_v04.json","w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps({"probe_id":receipt["probe_id"],"finding_count":len(findings)},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
