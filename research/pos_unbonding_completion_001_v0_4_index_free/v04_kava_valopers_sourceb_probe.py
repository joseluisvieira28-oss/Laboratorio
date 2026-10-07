#!/usr/bin/env python3
import hashlib, json, os, re, urllib.request, urllib.error
from datetime import datetime, timezone
from urllib.parse import urljoin

OUT="research/pos_unbonding_completion_001_v0_4_index_free/KAVA_VALOPERS_SOURCEB_PROBE_V04.json"
UA="CryptoLab-Kava-Valopers-SourceB/2.0"
PAGE="https://kava.valopers.com/blocks/9500000"
API="https://api.kava.valopers.com"
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

def summarize(resp, keep_sample=True):
    raw=resp.pop("raw",b"")
    text=raw.decode("utf-8","replace")
    resp["bytes"]=len(raw)
    resp["sha256"]=hashlib.sha256(raw).hexdigest()
    low=text.lower()
    resp["contains_height"]="9500000" in text or "9,500,000" in text or "9 500 000" in text
    resp["contains_canonical_hash"]=CANON_HASH.lower() in low
    resp["contains_canonical_time"]=CANON_TIME in text
    resp["contains_blockish_fields"]=any(k in low for k in ["block_hash","blockhash","height","app_hash","apphash","proposer","txs","transactions"])
    if keep_sample:
        resp["sample"]=text[:1600]
    return resp,text

def main():
    receipt={"generated_utc":datetime.now(timezone.utc).isoformat(),
             "scope":"source-only KAVA frozen fifth-chain candidate; no market data/outcomes",
             "canonical_anchor":{"height":9500000,"hash":CANON_HASH,"time":CANON_TIME},
             "page":{},"route_hints":[],"candidate_api":[]}

    rp=fetch(PAGE); sp,html=summarize(rp); receipt["page"]=sp
    srcs=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I)

    route_hints=set()
    target_chunks=[]
    for src in srcs:
        if "blocks" in src or "6267-" in src:
            target_chunks.append(urljoin(PAGE,src))
    for url in target_chunks:
        rr=fetch(url,20); ss,txt=summarize(rr,False)
        contexts=[]
        for pat in ["api.kava.valopers.com","/blocks","block/","transactions","graphql","axios","fetch("]:
            pos=0
            while True:
                i=txt.find(pat,pos)
                if i<0: break
                contexts.append(txt[max(0,i-240):min(len(txt),i+500)])
                pos=i+1
        literals=re.findall(r'["\']([^"\']{1,160})["\']',txt)
        for lit in literals:
            if any(k in lit.lower() for k in ["block","transaction","tx","height","api"]):
                route_hints.add(lit)
        receipt["route_hints"].append({"script":url,"status":ss.get("status"),"sha256":ss.get("sha256"),
                                       "contexts":contexts[:30],"literals":sorted(route_hints)[:300]})

    # Probe docs/root plus plausible REST patterns on the chain-specific API host.
    candidates=[
      API+"/",
      API+"/health",
      API+"/openapi.json",
      API+"/swagger.json",
      API+"/docs",
      API+"/blocks/9500000",
      API+"/block/9500000",
      API+"/api/blocks/9500000",
      API+"/api/block/9500000",
      API+"/v1/blocks/9500000",
      API+"/v1/block/9500000",
      API+"/api/v1/blocks/9500000",
      API+"/api/v1/block/9500000",
      API+"/blocks?height=9500000",
      API+"/block?height=9500000",
      API+"/transactions?height=9500000",
      API+"/txs?height=9500000"
    ]
    for url in candidates:
        rr=fetch(url,15); ss,txt=summarize(rr)
        receipt["candidate_api"].append(ss)

    receipt["all_route_hints"]=sorted(route_hints)[:500]
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
