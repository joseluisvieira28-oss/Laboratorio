#!/usr/bin/env python3
import html,json,requests
from bs4 import BeautifulSoup

S=requests.Session(); S.headers.update({"User-Agent":"CryptoLab-HistoryProps/0.5"})
pages=[4,7,10,13,16,19]
out=[]
def summarize(v,depth=0):
    if depth>4: return type(v).__name__
    if isinstance(v,dict):
        return {k:summarize(val,depth+1) for k,val in list(v.items())[:80]}
    if isinstance(v,list):
        return {"__type__":"list","len":len(v),"sample":[summarize(x,depth+1) for x in v[:2]]}
    return type(v).__name__

def collect_incidentish(v,path="$",hits=None):
    if hits is None:hits=[]
    if isinstance(v,dict):
        keys=set(v)
        if ("incident_updates" in keys or ("name" in keys and "status" in keys and ("created_at" in keys or "resolved_at" in keys))):
            safe={k:v.get(k) for k in ("id","name","status","created_at","updated_at","resolved_at","scheduled_for","scheduled_until","impact","shortlink") if k in v}
            if "incident_updates" in v and isinstance(v["incident_updates"],list):
                safe["updates"]=[{k:u.get(k) for k in ("id","status","created_at","updated_at","display_at","body") if k in u} for u in v["incident_updates"][:20] if isinstance(u,dict)]
            hits.append({"path":path,"safe":safe})
        for k,val in v.items(): collect_incidentish(val,path+"."+str(k),hits)
    elif isinstance(v,list):
        for i,val in enumerate(v): collect_incidentish(val,path+f"[{i}]",hits)
    return hits

for p in pages:
    u=f"https://status.exchange.coinbase.com/history?page={p}"
    row={"page":p,"url":u}
    try:
        r=S.get(u,timeout=20)
        soup=BeautifulSoup(r.text,"html.parser")
        node=soup.find(attrs={"data-react-class":"HistoryIndex"})
        if not node:
            row["error"]="HistoryIndex_not_found";out.append(row);continue
        raw=node.get("data-react-props","")
        props=json.loads(html.unescape(raw))
        hits=collect_incidentish(props)
        row["http"]=r.status_code
        row["props_keys"]=list(props.keys())
        row["shape"]=summarize(props)
        row["incidentish_count"]=len(hits)
        row["incidentish"]=hits[:300]
        # exact page-specific props hash is unnecessary; HTML source is official and event metadata retained.
    except Exception as e: row["error"]=type(e).__name__+":"+str(e)[:200]
    out.append(row)

json.dump(out,open("ctrrb_history_props_diag.json","w"),indent=2,sort_keys=True)
for r in out:
    print("PROPS_META="+json.dumps({k:r.get(k) for k in ("page","http","props_keys","incidentish_count","error")},sort_keys=True))
    print("PROPS_SHAPE="+json.dumps({"page":r["page"],"shape":r.get("shape")},sort_keys=True)[:12000])
    for h in r.get("incidentish",[])[:20]:
        print("PROPS_INCIDENT="+json.dumps({"page":r["page"],**h},sort_keys=True))
print("PROPS_DIAG_SAFETY=OFFICIAL_INCIDENT_METADATA_ONLY_NO_MARKET_DATA")
