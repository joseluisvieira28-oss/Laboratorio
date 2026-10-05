#!/usr/bin/env python3
import json,urllib.parse,urllib.request
from datetime import datetime,timezone

URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
def get(page):
  q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":48})
  req=urllib.request.Request(URL+"?"+q,headers={"User-Agent":"Mozilla/5.0 CryptoLabCensus/1.1","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

def year_of(x):
  try:
    v=int(x)
    return datetime.fromtimestamp(v/1000 if v>10**12 else v,tz=timezone.utc).year
  except:return None

rows=[]; found2025=False
for page in range(1,101):
  j=get(page)
  catalogs=(j.get("data") or {}).get("catalogs") or []
  arts=[]
  for cat in catalogs:
    arts.extend(cat.get("articles") or [])
  if not arts: break
  years=[]
  for a in arts:
    r={"title":a.get("title",""),"code":a.get("code") or a.get("id"),"release":a.get("releaseDate")}
    rows.append(r)
    y=year_of(r["release"]); years.append(y)
    if y==2025: found2025=True
  print(json.dumps({"page":page,"n":len(arts),"years":sorted(set(y for y in years if y))}))
  if found2025 and years and min(y for y in years if y)<2025: break

cand=[]
for r in rows:
  y=year_of(r["release"])
  title=r["title"].strip()
  if y==2025 and title.lower().startswith("binance will list "):
    cand.append(r)
cand.sort(key=lambda x:int(x["release"]))
print("V04_2025_CENSUS_BEGIN")
print(json.dumps({"raw_count":len(rows),"candidate_2025_count":len(cand),"candidates":cand},ensure_ascii=False,indent=2))
print("V04_2025_CENSUS_END")
