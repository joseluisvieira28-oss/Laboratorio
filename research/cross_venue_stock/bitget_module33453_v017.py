#!/usr/bin/env python3
import requests,re,json,hashlib
from urllib.parse import urljoin
from pathlib import Path
BASE="https://www.bitget.com/data-download"
UA="CryptoLab-Bitget-Module33453/0.1.7"
r=requests.get(BASE,headers={"User-Agent":UA},timeout=60);r.raise_for_status()
scripts=[urljoin(BASE,x) for x in re.findall(r'''<script[^>]+src=["']([^"']+)["']''',r.text,re.I)]
hits=[]
for u in scripts:
    try:q=requests.get(u,headers={"User-Agent":UA},timeout=40)
    except Exception:continue
    if q.status_code!=200 or len(q.content)>15_000_000:continue
    text=q.text
    for pat in ("33453(e","33453(",":33453"):
        pos=0
        while True:
            i=text.find(pat,pos)
            if i<0:break
            hits.append({"url":u,"pattern":pat,"position":i,
              "sha256":hashlib.sha256(q.content).hexdigest(),
              "context":text[max(0,i-10000):min(len(text),i+22000)]})
            pos=i+len(pat)
p=Path("artifacts/cross_venue_stock/bitget_module33453_v017");p.mkdir(parents=True,exist_ok=True)
(p/"BITGET_MODULE33453_V017.json").write_text(json.dumps({"hits":hits},indent=2))
print("HITS",len(hits))
for h in hits:
    print("\n=== MODULE33453",h["url"],"===\n",h["context"])
