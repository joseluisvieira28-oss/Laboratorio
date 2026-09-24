#!/usr/bin/env python3
import json, requests
from pathlib import Path

URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/binance_collateral_haircut_001/cms_catalog_probe.json")
r=requests.get(URL,params={"type":1,"pageNo":1,"pageSize":50},headers={"User-Agent":"Mozilla/5.0","clienttype":"web"},timeout=45)
r.raise_for_status()
obj=r.json()
cats=[]

def walk(x,path="root"):
    if isinstance(x,dict):
        # capture any dict that looks like a catalog and contains articles
        has_articles=isinstance(x.get("articles"),list)
        if has_articles:
            cats.append({
              "path":path,
              "catalogId":x.get("catalogId") or x.get("id"),
              "catalogName":x.get("catalogName") or x.get("name") or x.get("title"),
              "article_count":len(x.get("articles") or []),
              "sample_titles":[a.get("title") for a in (x.get("articles") or [])[:5] if isinstance(a,dict)]
            })
        for k,v in x.items(): walk(v,path+"."+str(k))
    elif isinstance(x,list):
        for i,v in enumerate(x): walk(v,path+f"[{i}]")
walk(obj)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"http_status":r.status_code,"catalog_like_nodes":cats,"top_keys":list(obj.keys()) if isinstance(obj,dict) else None},indent=2,sort_keys=True)+"\n")
print(json.dumps({"catalog_nodes":len(cats),"catalogs":cats},indent=2))
