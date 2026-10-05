#!/usr/bin/env python3
import json,urllib.parse,urllib.request
from datetime import datetime,timezone
URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
START=1672531200000
END=1704067199999
def get(page):
 q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":48})
 r=urllib.request.Request(URL+"?"+q,headers={"User-Agent":"Mozilla/5.0 CryptoLabCensusV07/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=30) as x:return json.load(x)
rows=[];found=False
for page in range(1,160):
 j=get(page);cats=(j.get("data") or {}).get("catalogs") or [];arts=[]
 for c in cats:arts.extend(c.get("articles") or [])
 if not arts:break
 vals=[]
 for a in arts:
  try:v=int(a.get("releaseDate"))
  except:continue
  rows.append({"title":a.get("title",""),"code":a.get("code") or a.get("id"),"release":v});vals.append(v)
  if START<=v<=END:found=True
 if found and vals and min(vals)<START:break
cand=[r for r in rows if START<=r["release"]<=END and r["title"].strip().lower().startswith("binance will list ")]
cand.sort(key=lambda x:x["release"])
print("V07_CENSUS_BEGIN")
print(json.dumps({"count":len(cand),"candidates":cand},ensure_ascii=False,indent=2))
print("V07_CENSUS_END")
