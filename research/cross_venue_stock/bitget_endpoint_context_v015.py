#!/usr/bin/env python3
import requests, hashlib, json
from pathlib import Path
URL="https://www.bitget.com/landing-static/client/js/pages-data-download-index-page.fee91d1d274130313d4c.chunk.js"
r=requests.get(URL,headers={"User-Agent":"CryptoLab-Bitget-EndpointContext/0.1.5"},timeout=60);r.raise_for_status()
text=r.text
keys=["/statistics/public/download/getPublicDataV2","/statistics/public/download/getSymbolList"]
out={"url":URL,"sha256":hashlib.sha256(r.content).hexdigest(),"contexts":[]}
for key in keys:
    pos=0
    while True:
        i=text.find(key,pos)
        if i<0:break
        ctx=text[max(0,i-5000):min(len(text),i+5000)]
        out["contexts"].append({"key":key,"position":i,"context":ctx})
        print("\n===",key,"===\n",ctx)
        pos=i+len(key)
p=Path("artifacts/cross_venue_stock/bitget_endpoint_context_v015");p.mkdir(parents=True,exist_ok=True)
(p/"BITGET_ENDPOINT_CONTEXT_V015.json").write_text(json.dumps(out,indent=2))
