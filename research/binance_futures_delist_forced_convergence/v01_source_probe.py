#!/usr/bin/env python3
# SOURCE-ONLY probe. Does not open market values.
import json, urllib.parse, urllib.request, re, time
from datetime import datetime, timezone

UA={"User-Agent":"Mozilla/5.0 CryptoLabForcedDelistSource/1.1","Accept":"application/json,text/plain,*/*"}
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
KNOWN_CODE="cfe97d52a8c840d3ba631835b637e9e7"

def get_json(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status, json.load(r)

def get_text(url,n=4096):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status, r.read(n).decode("utf-8","replace")

def walk(obj,path=""):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            p=f"{path}.{k}" if path else k
            out.append((p,k,v)); out.extend(walk(v,p))
    elif isinstance(obj,list):
        for i,v in enumerate(obj): out.extend(walk(v,f"{path}[{i}]"))
    return out

def year(v):
    try:
        n=int(v)
        return datetime.fromtimestamp(n/(1000 if n>10**12 else 1),tz=timezone.utc).year
    except Exception: return None

def flatten_strings(obj):
    vals=[]
    if isinstance(obj,str): vals.append(obj)
    elif isinstance(obj,dict):
        for v in obj.values(): vals.extend(flatten_strings(v))
    elif isinstance(obj,list):
        for v in obj: vals.extend(flatten_strings(v))
    return "\n".join(vals)

# Known article proves detail route and may reveal category metadata.
detail_status,detail=get_json(DETAIL+"?"+urllib.parse.urlencode({"articleCode":KNOWN_CODE}))
walked=walk(detail)
catalog_candidates=[]
for p,k,v in walked:
    if ("catalog" in k.lower() or "category" in k.lower()) and isinstance(v,(int,str)):
        s=str(v)
        if s.isdigit(): catalog_candidates.append(int(s))
catalog_candidates=sorted(set(catalog_candidates))
title_fields=[{"path":p,"value":v} for p,k,v in walked if k.lower()=="title" and isinstance(v,str)]
release_fields=[{"path":p,"value":v} for p,k,v in walked if k.lower() in ("releasedate","publishtime","publishtimestamp")]

# Archive capability probe: checksum sidecars only; no market values.
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
        st,txt=get_text(url,512)
        archive[name]={"http_status":st,"checksum_present":bool(re.match(r"^[0-9a-fA-F]{64}\s+",txt.strip()))}
    except Exception as e:
        archive[name]={"error":type(e).__name__,"checksum_present":False}

# Route A: any catalog IDs embedded in a known Futures delisting article.
catalog_rows=[]
catalog_probe=[]
for cid in catalog_candidates:
    rows=[]
    seen_target=False
    for page in range(1,121):
        q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":cid})
        try: st,j=get_json(LIST+"?"+q)
        except Exception: break
        arts=[]
        for cat in ((j.get("data") or {}).get("catalogs") or []): arts.extend(cat.get("articles") or [])
        if not arts: break
        ys=[]
        for a in arts:
            y=year(a.get("releaseDate")); ys.append(y)
            t=(a.get("title") or "").strip(); low=t.lower()
            if y in (2024,2025) and ("delist" in low or "rebrand" in low or "swap" in low or "migration" in low):
                rows.append({"title":t,"code":a.get("code") or a.get("id"),"releaseDate":a.get("releaseDate"),"year":y,"route":"catalog"})
                seen_target=True
        yy=[x for x in ys if x is not None]
        if seen_target and yy and min(yy)<2024: break
    if rows:
        catalog_probe.append({"catalog_id":cid,"candidate_metadata":len(rows)})
        catalog_rows.extend(rows)

# Route B fallback/independent: broad public CMS feed without a catalogId.
# We collect only metadata first, then inspect details of mechanically plausible titles.
broad=[]
seen_target=False
for page in range(1,181):
    q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50})
    try: st,j=get_json(LIST+"?"+q)
    except Exception: break
    arts=[]
    for cat in ((j.get("data") or {}).get("catalogs") or []): arts.extend(cat.get("articles") or [])
    if not arts: break
    ys=[]
    for a in arts:
        y=year(a.get("releaseDate")); ys.append(y)
        t=(a.get("title") or "").strip(); low=t.lower()
        if y in (2024,2025) and any(k in low for k in ("delist","rebrand","token swap","migration")):
            broad.append({"title":t,"code":a.get("code") or a.get("id"),"releaseDate":a.get("releaseDate"),"year":y,"route":"broad"})
            seen_target=True
    yy=[x for x in ys if x is not None]
    if seen_target and yy and min(yy)<2024: break

# Dedupe candidate articles before reading detail. Still SOURCE metadata only.
cand={}
for r in catalog_rows+broad:
    if r.get("code"): cand[str(r["code"])]=r

mechanical=[]
for i,(code,r) in enumerate(cand.items()):
    try:
        st,j=get_json(DETAIL+"?"+urllib.parse.urlencode({"articleCode":code}))
        body=flatten_strings(j)
    except Exception:
        continue
    low=body.lower()
    phrase=("close all positions and conduct an automatic settlement" in low or
            "close all positions and perform automatic settlement" in low or
            "conduct automatic settlements" in low)
    if not phrase: continue
    syms=sorted(set(re.findall(r"\b([A-Z0-9]{2,24}USDT)\b",body)))
    # Keep only USD-M style contracts evidenced in article body.
    if syms:
        mechanical.append({**r,"symbols":syms,"contract_observations":len(syms)})
    if i and i%30==0: time.sleep(0.1)

# Dedupe mechanical articles.
mech={str(r["code"]):r for r in mechanical}
mechanical=sorted(mech.values(),key=lambda x:int(x.get("releaseDate") or 0))
n_contracts=sum(r["contract_observations"] for r in mechanical)

res={
 "detail_http_status":detail_status,
 "detail_title_fields":title_fields[:5],
 "detail_release_fields":release_fields[:5],
 "catalog_candidates":catalog_candidates,
 "catalog_probe":catalog_probe,
 "broad_candidate_articles":len(broad),
 "mechanical_articles_2024_2025":len(mechanical),
 "mechanical_contract_observations_lower_bound":n_contracts,
 "mechanical_sample":mechanical[:40],
 "archive_checksum_coverage":archive,
 "archive_core_pass":all(archive[k].get("checksum_present") for k in ("perp_klines","mark_klines","index_klines")),
 "metrics_checksum_pass":archive["metrics"].get("checksum_present",False),
 "sample_ge_12":n_contracts>=12,
 "market_values_opened":False,
}
print("FORCED_DELIST_SOURCE_PROBE_BEGIN")
print(json.dumps(res,indent=2,ensure_ascii=False,sort_keys=True))
print("FORCED_DELIST_SOURCE_PROBE_END")
if detail_status!=200 or not res["archive_core_pass"] or not res["sample_ge_12"]:
    raise SystemExit(2)

# trigger hardened V0.1.1 source probe after workflow registration
