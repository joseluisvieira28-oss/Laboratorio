#!/usr/bin/env python3
import json,urllib.parse,urllib.request
from datetime import datetime,timezone

URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
def get(params):
  q=urllib.parse.urlencode(params)
  req=urllib.request.Request(URL+"?"+q,headers={"User-Agent":"Mozilla/5.0 CryptoLabCensus/1.0","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

rows=[]
for page in range(1,15):
  try:
    j=get({"type":1,"pageNo":page,"pageSize":50,"catalogId":48})
  except Exception as e:
    print(json.dumps({"page":page,"error":repr(e)}));break
  data=j.get("data") or {}
  arts=data.get("articles") or data.get("catalogs") or []
  if not arts: break
  for a in arts:
    title=a.get("title","")
    code=a.get("code") or a.get("id")
    release=a.get("releaseDate") or a.get("publishDate") or a.get("publishedAt")
    rows.append({"title":title,"code":code,"release":release})
  if len(arts)<50: break

def year_of(x):
  if x is None:return None
  try:
    v=int(x)
    if v>10**12:return datetime.fromtimestamp(v/1000,tz=timezone.utc).year
    if v>10**9:return datetime.fromtimestamp(v,tz=timezone.utc).year
  except:pass
  try:return datetime.fromisoformat(str(x).replace("Z","+00:00")).year
  except:return None

cand=[]
for r in rows:
  y=year_of(r["release"])
  t=r["title"].lower()
  if y==2024 and ("will list" in t or "new spot trading pairs" in t or "listing" in t):
    cand.append(r)
print(json.dumps({"raw_count":len(rows),"candidate_2024_count":len(cand),"candidates":cand},ensure_ascii=False,indent=2))

# trigger after workflow registration
