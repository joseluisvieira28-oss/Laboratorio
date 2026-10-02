from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PAGE="https://www.mexc.com/futures/event-futures/BTC_USDT"
UA="crypto-edge-radar/mexc-event-futures-frontend-deep-probe-v02"
SCRIPT_RE=re.compile(r'<script[^>]+src=["\']([^"\']+)["\']',re.I)
QUOTED=re.compile(r'["\']([^"\']{1,500})["\']')
NEEDLES=(
    "currentPayout","setCurrentPayout","eventContract","event.contract",
    "event/contract","event-contract","productList","contract.position",
    "prediction-futures","event-futures","payout"
)

def fetch(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/javascript,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read()

def ctx(text:str,needle:str,window:int=900,limit:int=5)->list[str]:
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
            if len(raw)>10_000_000: continue
            text=raw.decode("utf-8",errors="replace")
            low=text.lower()
            hits=[n for n in NEEDLES if n.lower() in low]
            if not hits: continue
            literals=[]
            for m in QUOTED.finditer(text):
                v=m.group(1)
                lv=v.lower()
                if any(k in lv for k in ("event","payout","prediction")):
                    if v not in literals:
                        literals.append(v)
                if len(literals)>=160: break
            contexts={n:ctx(text,n) for n in hits[:8]}
            findings.append({
                "script":u,
                "bytes":len(raw),
                "hits":hits,
                "matching_string_literals":literals,
                "contexts":contexts,
            })
        except Exception as e:
            findings.append({"script":u,"error":f"{type(e).__name__}:{e}"})
    receipt={
      "probe_id":"MEXC_EVENT_FUTURES_FRONTEND_DEEP_PROBE_V0.2",
      "created_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "page":PAGE,
      "scripts_total":len(srcs),
      "findings":findings,
      "authenticated_api_used":False,
      "private_endpoint_called":False,
      "orders_created":False,
    }
    with open("mexc_event_futures_frontend_deep_probe_v02.json","w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps({
      "probe_id":receipt["probe_id"],
      "scripts_total":receipt["scripts_total"],
      "finding_count":len(findings),
      "authenticated_api_used":False,
      "private_endpoint_called":False,
      "orders_created":False,
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
