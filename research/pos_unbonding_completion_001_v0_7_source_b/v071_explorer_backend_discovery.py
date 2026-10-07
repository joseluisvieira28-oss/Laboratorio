#!/usr/bin/env python3
import json,re,urllib.request,urllib.parse,hashlib,os
from datetime import datetime,timezone
OUT="research/pos_unbonding_completion_001_v0_7_source_b/TX_EXPLORER_BACKEND_DISCOVERY_V071.json"
BASE="https://explorer.tx.org/tx"
UA="CryptoLab-Unbonding-V071/1.0"

def get(url,t=25):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/javascript,*/*"})
    with urllib.request.urlopen(req,timeout=t) as r:
        return r.geturl(),r.read()

def main():
    rec={"generated_utc":datetime.now(timezone.utc).isoformat(),"event_counts_opened":False,"base":BASE,"scripts":[],"candidates":[]}
    try:
        final,html=get(BASE)
        rec["final_url"]=final
        rec["html_sha256"]=hashlib.sha256(html).hexdigest()
        txt=html.decode("utf-8","replace")
        srcs=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',txt,re.I)
        for src in srcs[:100]:
            url=urllib.parse.urljoin(final,src)
            ent={"url":url}
            try:
                _,raw=get(url,20)
                ent["sha256"]=hashlib.sha256(raw).hexdigest()
                ent["bytes"]=len(raw)
                s=raw.decode("utf-8","replace")
                found=set()
                for m in re.findall(r'https?://[^"\'\\\s<>]+',s):
                    ml=m.lower()
                    if any(k in ml for k in ("graphql","gql","forbole","rpc.","api.","tx.org","coreum")):
                        found.add(m[:500])
                ent["endpoint_strings"]=sorted(found)[:100]
                rec["candidates"].extend(ent["endpoint_strings"])
            except Exception as e:
                ent["error"]=type(e).__name__+": "+str(e)[:500]
            rec["scripts"].append(ent)
        rec["candidates"]=sorted(set(rec["candidates"]))
    except Exception as e:
        rec["fatal_error"]=type(e).__name__+": "+str(e)
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with open(OUT,"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(rec,indent=2))
if __name__=="__main__":main()
