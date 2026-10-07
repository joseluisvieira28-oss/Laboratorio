#!/usr/bin/env python3
import hashlib, json, os, re, urllib.request, urllib.error
from datetime import datetime, timezone
from urllib.parse import urljoin

OUT="research/pos_unbonding_completion_001_v0_4_index_free/KAVA_VALOPERS_SOURCEB_PROBE_V04.json"
UA="CryptoLab-Kava-Valopers-SourceB/1.0"
PAGE="https://kava.valopers.com/blocks/9500000"
CANON_HASH="A37031A071F215F108C485A46D5E59E0C382E416B4FAD07FD3BB852F2B79D591"
CANON_TIME="2024-04-20T05:02:33.015922027Z"

def fetch(url, timeout=20):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/json,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read()
            return {"status":getattr(r,"status",200),"url":r.geturl(),"raw":raw,
                    "content_type":r.headers.get("content-type","")}
    except urllib.error.HTTPError as e:
        raw=e.read()
        return {"status":e.code,"url":url,"raw":raw,"content_type":e.headers.get("content-type",""),"error":"HTTPError"}
    except Exception as e:
        return {"url":url,"error":type(e).__name__+": "+str(e),"raw":b""}

def summarize(resp):
    raw=resp.pop("raw",b"")
    text=raw.decode("utf-8","replace")
    resp["bytes"]=len(raw)
    resp["sha256"]=hashlib.sha256(raw).hexdigest()
    resp["contains_height"]="9500000" in text or "9,500,000" in text or "9 500 000" in text
    resp["contains_canonical_hash"]=CANON_HASH.lower() in text.lower()
    resp["contains_canonical_time"]=CANON_TIME in text
    resp["sample"]=text[:1000]
    return resp,text

def main():
    receipt={"generated_utc":datetime.now(timezone.utc).isoformat(),
             "scope":"source-only KAVA frozen fifth-chain candidate; no market data/outcomes",
             "canonical_anchor":{"height":9500000,"hash":CANON_HASH,"time":CANON_TIME},
             "page":{},"scripts":[],"candidate_api":[]}
    r=fetch(PAGE)
    s,html=summarize(r)
    receipt["page"]=s

    srcs=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I)
    # Also preserve direct API host references embedded in HTML.
    receipt["html_api_urls"]=sorted(set(re.findall(r'https?://[^"\'<> ]*api\.valopers\.com[^"\'<> ]*',html)))[:50]

    api_hints=set()
    for src in srcs[:30]:
        url=urljoin(PAGE,src)
        rr=fetch(url,15)
        ss,txt=summarize(rr)
        ss["script_url"]=url
        hints=sorted(set(re.findall(r'https?://[^"\' )]+|/api/[A-Za-z0-9_?=&/{}.-]+',txt)))
        val=[h for h in hints if "valopers" in h.lower() or "/api/" in h.lower()]
        ss["api_hints"]=val[:80]
        for h in val:
            api_hints.add(h)
        # keep receipt compact
        ss.pop("sample",None)
        receipt["scripts"].append(ss)

    candidates=[
      "https://api.valopers.com/kava/blocks/9500000",
      "https://api.valopers.com/api/kava/blocks/9500000",
      "https://api.valopers.com/blocks/kava/9500000",
      "https://api.valopers.com/blocks/9500000?chain=kava",
      "https://api.valopers.com/api/blocks/9500000?chain=kava",
      "https://api.valopers.com/kava/block/9500000",
      "https://api.valopers.com/api/kava/block/9500000"
    ]
    for url in candidates:
        rr=fetch(url,15)
        ss,txt=summarize(rr)
        ss["contains_blockish_fields"]=any(k in txt.lower() for k in ["block_hash","blockhash","height","app_hash","apphash","proposer"])
        receipt["candidate_api"].append(ss)

    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
