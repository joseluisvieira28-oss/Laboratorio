#!/usr/bin/env python3
import json,re,urllib.parse,urllib.request
from datetime import datetime,timezone

URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
def get(page):
    q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":48})
    r=urllib.request.Request(URL+"?"+q,headers={"User-Agent":"Mozilla/5.0 CryptoLabPre2024Census/1.0","Accept":"application/json"})
    with urllib.request.urlopen(r,timeout=30) as x:return json.load(x)
def yr(v):
    try:
        v=int(v); return datetime.fromtimestamp(v/1000 if v>10**12 else v,tz=timezone.utc).year
    except:return None

rows=[]; seen_target=False
for page in range(1,121):
    j=get(page); arts=[]
    for cat in ((j.get("data") or {}).get("catalogs") or []): arts += cat.get("articles") or []
    if not arts: break
    ys=[]
    for a in arts:
        r={"title":a.get("title",""),"code":a.get("code") or a.get("id"),"release":a.get("releaseDate")}
        rows.append(r); y=yr(r["release"]); ys.append(y)
        if y in (2022,2023): seen_target=True
    print(json.dumps({"page":page,"n":len(arts),"years":sorted(set(y for y in ys if y))}))
    if seen_target and ys and min(y for y in ys if y)<2022: break

cand=[]
for r in rows:
    y=yr(r["release"]); t=r["title"].strip()
    low=t.lower()
    # Public listing announcements, not pair-additions for already-listed assets.
    if y in (2022,2023) and (
        low.startswith("binance will list ") or
        low.startswith("binance will open trading for ") or
        "and will open trading for" in low
    ):
        tickers=re.findall(r"\(([A-Z0-9]{2,20})\)",t)
        cand.append({**r,"year":y,"tickers":tickers})
cand.sort(key=lambda x:int(x["release"]))
print("PRE2024_CENSUS_BEGIN")
print(json.dumps({"raw_count":len(rows),"announcement_count":len(cand),
                  "asset_mentions":sum(len(x["tickers"]) for x in cand),"candidates":cand},indent=2,ensure_ascii=False))
print("PRE2024_CENSUS_END")
