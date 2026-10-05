#!/usr/bin/env python3
import json,urllib.parse,urllib.request
from datetime import datetime,timezone
URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
def get(page):
 q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":48})
 req=urllib.request.Request(URL+"?"+q,headers={"User-Agent":"Mozilla/5.0 CryptoLabCensus/3.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def year_of(x):
 try:
  v=int(x);return datetime.fromtimestamp(v/1000 if v>10**12 else v,tz=timezone.utc).year
 except:return None
rows=[];found=False
for page in range(1,120):
 j=get(page); cats=(j.get("data") or {}).get("catalogs") or []; arts=[]
 for c in cats: arts.extend(c.get("articles") or [])
 if not arts: break
 years=[]
 for a in arts:
  r={"title":a.get("title",""),"code":a.get("code") or a.get("id"),"release":a.get("releaseDate")}
  rows.append(r);y=year_of(r["release"]);years.append(y)
  if y==2025:found=True
 print(json.dumps({"page":page,"n":len(arts),"years":sorted(set(y for y in years if y))}))
 if found and years and min(y for y in years if y)<2025:break
cand=[r for r in rows if year_of(r["release"])==2025 and r["title"].strip().lower().startswith("binance will list ")]
cand.sort(key=lambda x:int(x["release"]))
print("CENSUS_2025_JSON_BEGIN")
print(json.dumps({"candidate_2025_count":len(cand),"candidates":cand},ensure_ascii=False,indent=2))
print("CENSUS_2025_JSON_END")
