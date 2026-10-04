#!/usr/bin/env python3
import json,re,requests,hashlib
from pathlib import Path
URL="https://www.bitget.com/landing-static/client/js/pages-data-download-index-page.fee91d1d274130313d4c.chunk.js"
OUT=Path("artifacts/cross_venue_stock/bitget_download_helper_v014")
OUT.mkdir(parents=True,exist_ok=True)
r=requests.get(URL,headers={"User-Agent":"CryptoLab-Bitget-DownloadHelper/0.1.4"},timeout=60)
r.raise_for_status()
text=r.text
keys=["getDownloadFiles","fileUrl","downloadAllFiles","fileName"]
contexts=[]
for key in keys:
    pos=0
    while True:
        i=text.find(key,pos)
        if i<0:break
        ctx=text[max(0,i-9000):min(len(text),i+5000)]
        contexts.append({"key":key,"position":i,"context":ctx})
        pos=i+len(key)
# Extract request-like paths and URLs across the full page chunk.
paths=sorted(set(re.findall(r'''["']((?:/|https?://)[^"']{3,300})["']''',text)))
interesting=[x for x in paths if any(k in x.lower() for k in ("download","history","historical","market","data","file"))]
# Minified module/import references around getDownloadFiles.
refs=[]
for c in contexts:
    if c["key"]=="getDownloadFiles":
        refs.extend(re.findall(r'''\b(?:n|o|a|t|e)\((\d{2,7})\)''',c["context"]))
report={
 "url":URL,"http":r.status_code,"bytes":len(r.content),
 "sha256":hashlib.sha256(r.content).hexdigest(),
 "contexts":contexts,
 "nearby_module_refs":sorted(set(refs)),
 "interesting_paths":interesting[:500]
}
(OUT/"BITGET_DOWNLOAD_HELPER_V014.json").write_text(json.dumps(report,indent=2))
print("HTTP",r.status_code,"bytes",len(r.content),"contexts",len(contexts))
print("MODULE_REFS",sorted(set(refs)))
print("INTERESTING_PATHS",json.dumps(interesting[:100],indent=2))
for c in contexts:
    if c["key"]=="getDownloadFiles":
        print("\n=== GETDOWNLOADFILES CONTEXT ===\n")
        print(c["context"])
