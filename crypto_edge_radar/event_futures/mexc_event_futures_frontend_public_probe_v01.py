from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PAGE="https://www.mexc.com/futures/event-futures/BTC_USDT"
UA="crypto-edge-radar/mexc-event-futures-frontend-public-probe-v01"
KEYWORDS=("eventfutures","event-futures","predictionfutures","prediction-futures","uppayout","downpayout","payout")
URLISH=re.compile(r'(?:"|\')((?:https?:)?//[^"\']+|/api/[^"\']+|/api/v\d+/[^"\']+)(?:"|\')')
SCRIPT_RE=re.compile(r'<script[^>]+src=["\']([^"\']+)["\']',re.I)


def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/javascript,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read()


def contexts(text:str,needle:str,window:int=180)->list[str]:
    low=text.lower()
    out=[]
    start=0
    while len(out)<12:
        i=low.find(needle,start)
        if i<0: break
        s=max(0,i-window); e=min(len(text),i+len(needle)+window)
        frag=text[s:e].replace("\n"," ")
        out.append(frag)
        start=i+len(needle)
    return out


def main()->int:
    html=fetch(PAGE).decode("utf-8",errors="replace")
    srcs=[]
    for src in SCRIPT_RE.findall(html):
        full=urllib.parse.urljoin(PAGE,src)
        if full not in srcs:
            srcs.append(full)

    findings=[]
    scanned=0
    for url in srcs[:40]:
        try:
            raw=fetch(url)
            if len(raw)>8_000_000:
                continue
            text=raw.decode("utf-8",errors="replace")
            scanned+=1
            low=text.lower()
            hits=[k for k in KEYWORDS if k in low]
            if not hits:
                continue
            candidates=[]
            for m in URLISH.finditer(text):
                val=m.group(1)
                lv=val.lower()
                if any(k in lv for k in ("event","prediction","payout")):
                    if val not in candidates:
                        candidates.append(val[:500])
                if len(candidates)>=30:
                    break
            ctx={}
            for k in hits:
                ctx[k]=contexts(text,k,120)[:4]
            findings.append({
                "script":url,
                "bytes":len(raw),
                "keywords":hits,
                "candidate_url_strings":candidates,
                "contexts":ctx,
            })
        except Exception as e:
            findings.append({"script":url,"error":f"{type(e).__name__}:{e}"})

    receipt={
      "probe_id":"MEXC_EVENT_FUTURES_FRONTEND_PUBLIC_PROBE_V0.1",
      "created_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "page":PAGE,
      "page_bytes":len(html.encode("utf-8")),
      "external_script_count":len(srcs),
      "scripts_scanned":scanned,
      "findings":findings,
      "authenticated_api_used":False,
      "orders_created":False,
      "private_endpoint_used":False,
    }
    with open("mexc_event_futures_frontend_public_probe_v01.json","w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps({
      "probe_id":receipt["probe_id"],
      "external_script_count":receipt["external_script_count"],
      "scripts_scanned":receipt["scripts_scanned"],
      "finding_count":len(receipt["findings"]),
      "authenticated_api_used":False,
      "orders_created":False,
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
