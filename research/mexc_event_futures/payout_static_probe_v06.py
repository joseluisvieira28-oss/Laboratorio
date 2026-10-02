#!/usr/bin/env python3
import hashlib, json, os, re, sys, time
from urllib.parse import urljoin, urlparse
import requests

PAGE="https://www.mexc.com/futures/event-futures/BTC_USDT"
KEYWORDS=("event-futures","prediction-futures","payout","upPayout","downPayout","timeUnit","prediction","eventFutures")
SAFE_PATH_HINTS=("event","prediction","payout","future")
MAX_SCRIPTS=80
MAX_BYTES=5_000_000

def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8","ignore")).hexdigest()

def get(url):
    r=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0"})
    return r.status_code,r.url,r.text[:MAX_BYTES],dict(r.headers)

def main():
    out={"page":PAGE,"static_hits":[],"scripts":[],"candidate_strings":[]}
    sc,final,html,headers=get(PAGE)
    out["page_status"]=sc; out["page_final_url"]=final; out["page_sha256"]=sha256_text(html)

    srcs=[]
    for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I):
        srcs.append(urljoin(final,m.group(1)))
    seen=set()
    for u in srcs:
        if u in seen or len(seen)>=MAX_SCRIPTS: continue
        seen.add(u)
        try:
            sc2,fu,txt,h=get(u)
        except Exception as e:
            out["scripts"].append({"url":u,"error":repr(e)}); continue
        low=txt.lower()
        hits=[k for k in KEYWORDS if k.lower() in low]
        rec={"url":fu,"status":sc2,"bytes":len(txt),"sha256":sha256_text(txt),"keywords":hits}
        out["scripts"].append(rec)
        if not hits: continue

        # Extract bounded string literals containing relevant terms/API fragments.
        pats=[
          r'["\']([^"\']{0,220}(?:event-futures|prediction-futures|payout|timeUnit|eventFutures|prediction)[^"\']{0,220})["\']',
          r'["\']([^"\']{0,220}/api/[^"\']{0,220})["\']'
        ]
        for pat in pats:
            for mm in re.finditer(pat,txt,re.I):
                s=mm.group(1)
                if any(h in s.lower() for h in ("event","prediction","payout")):
                    out["candidate_strings"].append({"script":fu,"value":s[:500]})
        time.sleep(0.05)

    # Deduplicate.
    uniq=[]; keys=set()
    for x in out["candidate_strings"]:
        key=(x["script"],x["value"])
        if key in keys: continue
        keys.add(key); uniq.append(x)
    out["candidate_strings"]=uniq[:1000]
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    p="artifacts/mexc_event_futures/payout_static_probe_v06.json"
    with open(p,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({
      "page_status":out["page_status"],
      "scripts_scanned":len(out["scripts"]),
      "scripts_with_keywords":sum(bool(x.get("keywords")) for x in out["scripts"]),
      "candidate_strings":len(out["candidate_strings"]),
      "sample":out["candidate_strings"][:40]
    },indent=2))
    print("WROTE",p)

if __name__=="__main__":
    main()
