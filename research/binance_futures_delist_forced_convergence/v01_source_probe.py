#!/usr/bin/env python3
# SOURCE-ONLY probe. Does not open market values.
import json, urllib.parse, urllib.request, re
from datetime import datetime, timezone

UA={"User-Agent":"Mozilla/5.0 CryptoLabForcedDelistSource/1.0","Accept":"application/json,text/plain,*/*"}
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
KNOWN_CODE="cfe97d52a8c840d3ba631835b637e9e7"  # 2024 XEM/ORBS/LOOM futures-delisting notice

def get_json(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status, json.load(r)

def get_text(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status, r.read(2048).decode("utf-8","replace")

def walk(obj,path=""):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            p=f"{path}.{k}" if path else k
            out.append((p,k,v))
            out.extend(walk(v,p))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            out.extend(walk(v,f"{path}[{i}]"))
    return out

def year(v):
    try:
        n=int(v)
        return datetime.fromtimestamp(n/(1000 if n>10**12 else 1),tz=timezone.utc).year
    except Exception:
        return None

detail_url=DETAIL+"?"+urllib.parse.urlencode({"articleCode":KNOWN_CODE})
detail_status,detail=get_json(detail_url)
walked=walk(detail)
catalog_candidates=[]
for p,k,v in walked:
    kl=k.lower()
    if ("catalog" in kl or "category" in kl) and isinstance(v,(int,str)):
        s=str(v)
        if s.isdigit():
            catalog_candidates.append(int(s))
catalog_candidates=sorted(set(catalog_candidates))

title_fields=[{"path":p,"value":v} for p,k,v in walked if k.lower()=="title" and isinstance(v,str)]
release_fields=[{"path":p,"value":v} for p,k,v in walked if k.lower() in ("releasedate","publishtime","publishtimestamp")]

# Check archive existence using checksum sidecars only; never parse market values.
base="https://data.binance.vision/data/futures/um/daily"
checks={
 "perp_klines":f"{base}/klines/XEMUSDT/1m/XEMUSDT-1m-2024-12-09.zip.CHECKSUM",
 "mark_klines":f"{base}/markPriceKlines/XEMUSDT/1m/XEMUSDT-1m-2024-12-09.zip.CHECKSUM",
 "index_klines":f"{base}/indexPriceKlines/XEMUSDT/1m/XEMUSDT-1m-2024-12-09.zip.CHECKSUM",
 "metrics":f"{base}/metrics/XEMUSDT/XEMUSDT-metrics-2024-12-09.zip.CHECKSUM",
}
archive={}
for name,url in checks.items():
    try:
        st,txt=get_text(url)
        archive[name]={"http_status":st,"checksum_present":bool(re.match(r"^[0-9a-fA-F]{64}\s+",txt.strip()))}
    except Exception as e:
        archive[name]={"error":type(e).__name__,"checksum_present":False}

# If detail gives catalog IDs, enumerate only announcement metadata/titles for 2024-2025.
census=[]
catalog_probe=[]
for cid in catalog_candidates:
    seen_target=False
    rows=[]
    for page in range(1,81):
        q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":cid})
        try:
            st,j=get_json(LIST+"?"+q)
        except Exception:
            break
        arts=[]
        for cat in ((j.get("data") or {}).get("catalogs") or []):
            arts.extend(cat.get("articles") or [])
        if not arts: break
        ys=[]
        for a in arts:
            y=year(a.get("releaseDate")); ys.append(y)
            t=(a.get("title") or "").strip()
            low=t.lower()
            if y in (2024,2025) and "futures" in low and "delist" in low and "perpetual" in low:
                rows.append({"title":t,"code":a.get("code") or a.get("id"),"releaseDate":a.get("releaseDate"),"year":y})
                seen_target=True
        if ys and min(x for x in ys if x is not None)<2024:
            break
    if rows:
        catalog_probe.append({"catalog_id":cid,"matching_announcements":len(rows)})
        census.extend(rows)

# Dedupe article metadata.
uniq={}
for r in census:
    uniq[str(r["code"])]=r
census=sorted(uniq.values(),key=lambda x:int(x["releaseDate"] or 0))

res={
 "detail_http_status":detail_status,
 "detail_title_fields":title_fields[:5],
 "detail_release_fields":release_fields[:5],
 "catalog_candidates":catalog_candidates,
 "catalog_probe":catalog_probe,
 "announcement_metadata_count_2024_2025":len(census),
 "announcement_metadata_sample":census[:20],
 "archive_checksum_coverage":archive,
 "archive_core_pass":all(archive[k].get("checksum_present") for k in ("perp_klines","mark_klines","index_klines")),
 "metrics_checksum_pass":archive["metrics"].get("checksum_present",False),
 "market_values_opened":False,
}
print("FORCED_DELIST_SOURCE_PROBE_BEGIN")
print(json.dumps(res,indent=2,ensure_ascii=False,sort_keys=True))
print("FORCED_DELIST_SOURCE_PROBE_END")
if detail_status!=200 or not res["archive_core_pass"]:
    raise SystemExit(2)
