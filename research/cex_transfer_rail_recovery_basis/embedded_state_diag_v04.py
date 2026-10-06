#!/usr/bin/env python3
import json,re,requests,html as htmllib
S=requests.Session(); S.headers.update({"User-Agent":"CryptoLab-EmbeddedStateDiag/0.4"})
pages=[4,10,16,19]
out=[]
for p in pages:
    u=f"https://status.exchange.coinbase.com/history?page={p}"
    x={"page":p,"url":u}
    try:
        r=S.get(u,timeout=15)
        raw=r.text
        x["http"]=r.status_code;x["bytes"]=len(r.content)
        needles=["incident-container","pagination-container","page_number","incident_history","incidents","start_date","created_at","page_id"]
        ctx={}
        for needle in needles:
            pos=[m.start() for m in re.finditer(re.escape(needle),raw,re.I)]
            ctx[needle]=[raw[max(0,i-450):min(len(raw),i+900)] for i in pos[:8]]
        # Extract script tags that look like embedded app/page JSON.
        scripts=re.findall(r'<script[^>]*>(.*?)</script>',raw,re.I|re.S)
        candidates=[]
        for s in scripts:
            if any(k in s.lower() for k in ["incident","history","page_id","pagination"]):
                candidates.append(s[:12000])
        x["contexts"]=ctx
        x["candidate_scripts"]=candidates[:10]
        # hidden/input/data attrs potentially encode page range
        x["data_attrs"]=re.findall(r'\b(data-[a-z0-9_-]+)=["\']([^"\']{0,500})',raw,re.I)[:200]
        # Form/action/query fragments around page/filter
        x["page_fragments"]=re.findall(r'[^"\'<>\s]{0,100}(?:history\?page|page=|pagination)[^"\'<>\s]{0,200}',raw,re.I)[:100]
    except Exception as e:x["error"]=type(e).__name__+":"+str(e)[:150]
    out.append(x)
json.dump(out,open("ctrrb_embedded_state_diag.json","w"),indent=2)
for x in out:
    print("EMBED_META="+json.dumps({k:x.get(k) for k in ["page","http","bytes","error"]}))
    for needle,vals in x.get("contexts",{}).items():
        for v in vals[:2]: print("EMBED_CTX="+json.dumps({"page":x["page"],"needle":needle,"context":v}))
    for s in x.get("candidate_scripts",[])[:3]: print("EMBED_SCRIPT="+json.dumps({"page":x["page"],"text":s[:5000]}))
    print("PAGE_FRAGMENTS="+json.dumps({"page":x["page"],"items":x.get("page_fragments",[])[:30]}))
print("EMBED_DIAG_SAFETY=OFFICIAL_SOURCE_STRUCTURE_ONLY")
