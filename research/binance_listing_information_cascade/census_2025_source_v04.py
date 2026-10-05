#!/usr/bin/env python3
import json,re,urllib.parse,urllib.request
from datetime import datetime,timezone

URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
def get(page):
  q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":48})
  r=urllib.request.Request(URL+"?"+q,headers={"User-Agent":"Mozilla/5.0 CryptoLab2025Census/1.0","Accept":"application/json"})
  with urllib.request.urlopen(r,timeout=30) as x:return json.load(x)
def yr(v):
  try:
    v=int(v);return datetime.fromtimestamp(v/1000 if v>10**12 else v,tz=timezone.utc).year
  except:return None
def tickers(title):
  xs=re.findall(r"\(([A-Z0-9]{2,20})\)",title)
  if xs:return list(dict.fromkeys(xs))
  # Launchpad/open-trading titles sometimes omit parentheses.
  m=re.search(r"(?:Trading for|trading for)\s+([A-Z0-9]{2,20})(?:\s|,|$)",title)
  return [m.group(1)] if m else []

rows=[]; seen=False
for page in range(1,80):
  j=get(page);arts=[]
  for cat in ((j.get("data") or {}).get("catalogs") or []):arts+=cat.get("articles") or []
  if not arts:break
  ys=[]
  for a in arts:
    r={"title":a.get("title",""),"code":a.get("code") or a.get("id"),"release":a.get("releaseDate")}
    rows.append(r);y=yr(r["release"]);ys.append(y)
    if y==2025:seen=True
  print(json.dumps({"page":page,"n":len(arts),"years":sorted(set(y for y in ys if y))}))
  if seen and ys and min(y for y in ys if y)<2025:break

cand=[]
for r in rows:
  if yr(r["release"])!=2025:continue
  lo=r["title"].lower()
  if lo.startswith("binance will list ") or lo.startswith("binance will open trading for ") or "and will open trading for" in lo:
    cand.append({**r,"tickers":tickers(r["title"])})
cand.sort(key=lambda x:int(x["release"]))
print("CENSUS_2025_BEGIN")
print(json.dumps({"announcement_count":len(cand),"asset_mentions":sum(len(x["tickers"]) for x in cand),"candidates":cand},indent=2,ensure_ascii=False))
print("CENSUS_2025_END")
