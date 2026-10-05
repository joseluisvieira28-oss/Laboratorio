#!/usr/bin/env python3
# Source-only Binance CMS catalog discovery for DUAL PRECURSOR V0.1.
# Finds catalog IDs that expose Alpha/Futures/Spot-relevant 2025 announcement titles.
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone

URL="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
UA={"User-Agent":"Mozilla/5.0 CryptoLabDualPrecursorCatalog/1.0","Accept":"application/json"}

def get(cid):
    q=urllib.parse.urlencode({"type":1,"pageNo":1,"pageSize":50,"catalogId":cid})
    r=urllib.request.Request(URL+"?"+q,headers=UA)
    try:
        with urllib.request.urlopen(r,timeout=15) as x:
            return json.load(x)
    except Exception:
        return None

def yr(v):
    try:
        v=int(v)
        return datetime.fromtimestamp(v/1000 if v>10**12 else v,tz=timezone.utc).year
    except Exception:
        return None

hits=[]
for cid in range(1,251):
    j=get(cid)
    arts=[]
    if j:
        for cat in ((j.get("data") or {}).get("catalogs") or []):
            arts += cat.get("articles") or []
    titles=[]
    for a in arts:
        if yr(a.get("releaseDate"))!=2025:
            continue
        t=(a.get("title") or "").strip()
        low=t.lower()
        if (
            "binance futures will launch" in low
            or "binance alpha" in low
            or low.startswith("binance will list ")
            or "hodler airdrops" in low
        ):
            titles.append(t)
    if titles:
        hits.append({"catalog_id":cid,"matching_titles":titles[:8],"matching_count":len(titles)})
    time.sleep(0.03)

print("DUAL_PRECURSOR_CATALOG_DISCOVERY_BEGIN")
print(json.dumps({"catalog_hits":hits,"hit_count":len(hits)},indent=2,ensure_ascii=False))
print("DUAL_PRECURSOR_CATALOG_DISCOVERY_END")
if not hits:
    raise SystemExit(2)
