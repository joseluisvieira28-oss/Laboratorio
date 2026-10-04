#!/usr/bin/env python3
import requests,re,json,hashlib
from urllib.parse import urljoin
from pathlib import Path
BASE="https://www.bitget.com/data-download"
UA="CryptoLab-Bitget-Wrapper55167/0.1.6"
r=requests.get(BASE,headers={"User-Agent":UA},timeout=60);r.raise_for_status()
scripts=[urljoin(BASE,x) for x in re.findall(r'''<script[^>]+src=["']([^"']+)["']''',r.text,re.I)]
hits=[]
for u in scripts:
    try:q=requests.get(u,headers={"User-Agent":UA},timeout=40)
    except Exception:continue
    if q.status_code!=200 or len(q.content)>15_000_000:continue
    text=q.text
    for pat in ("55167(e","55167(",'"55167"',":55167"):
        pos=0
        while True:
            i=text.find(pat,pos)
            if i<0:break
            hits.append({"url":u,"pattern":pat,"position":i,
                         "sha256":hashlib.sha256(q.content).hexdigest(),
                         "context":text[max(0,i-8000):min(len(text),i+12000)]})
            pos=i+len(pat)
out={"script_count":len(scripts),"hits":hits}
p=Path("artifacts/cross_venue_stock/bitget_wrapper_v016");p.mkdir(parents=True,exist_ok=True)
(p/"BITGET_WRAPPER_55167_V016.json").write_text(json.dumps(out,indent=2))
print("SCRIPTS",len(scripts),"HITS",len(hits))
for h in hits:
    print("\n=== WRAPPER HIT",h["url"],h["pattern"],"===\n")
    print(h["context"])
