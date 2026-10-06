#!/usr/bin/env python3
import json,re,time,urllib.parse,urllib.request
from collections import Counter
from datetime import datetime,timezone

UA={"User-Agent":"Mozilla/5.0 CryptoLabDualPrecursorSourceCensus/1.2","Accept":"application/json,text/plain,*/*"}
ALPHA="https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
KNOWN="52c6f34173e44f898764fb45e9dbb4ca"

def get(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status,json.load(r)

def ems(v):
    try:
        n=int(v)
        if n<10**11:n*=1000
        return n
    except:return None

def yr(v):
    n=ems(v)
    return datetime.fromtimestamp(n/1000,tz=timezone.utc).year if n else None

_,ao=get(ALPHA)
data=ao.get("data",ao) if isinstance(ao,dict) else ao
if isinstance(data,dict):
    vals=[v for v in data.values() if isinstance(v,list)]
    rows=vals[0] if vals else []
else:
    rows=data if isinstance(data,list) else []

alpha=[]
for x in rows:
    if not isinstance(x,dict) or yr(x.get("listingTime"))!=2025: continue
    s=str(x.get("symbol") or "").strip().upper()
    if not s: continue
    alpha.append({
      "symbol":s,"alphaId":x.get("alphaId"),"tokenId":x.get("tokenId"),
      "name":x.get("name"),"chainId":x.get("chainId"),"chainName":x.get("chainName"),
      "contractAddress":x.get("contractAddress"),"listingTime":ems(x.get("listingTime"))
    })
cnt=Counter(x["symbol"] for x in alpha)
unique={x["symbol"]:x for x in alpha if cnt[x["symbol"]]==1}
amb=sorted(s for s,n in cnt.items() if n>1)

_,d=get(DETAIL+"?"+urllib.parse.urlencode({"articleCode":KNOWN}))
cids=set()
def walk(o):
    if isinstance(o,dict):
        for k,v in o.items():
            if ("catalog" in k.lower() or "category" in k.lower()) and isinstance(v,(str,int)) and str(v).isdigit():
                cids.add(int(v))
            walk(v)
    elif isinstance(o,list):
        for v in o:walk(v)
walk(d)
cids=sorted(cids)

fr=[]
for cid in cids:
    hit=False
    for page in range(1,181):
        try:
            _,j=get(LIST+"?"+urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":cid}))
        except: break
        arts=[]
        for cat in ((j.get("data") or {}).get("catalogs") or []): arts+=cat.get("articles") or []
        if not arts:break
        ys=[]
        for a in arts:
            y=yr(a.get("releaseDate"));ys.append(y)
            if y is None or y>2025:continue
            t=(a.get("title") or "").strip()
            lo=t.lower()
            if "futures will launch" not in lo or "perpetual" not in lo:continue
            syms=sorted(set(re.findall(r"\b([A-Z0-9]{1,40})USDT\b",t.upper())))
            for s in syms:
                hit=True
                fr.append({"symbol":s,"article_code":a.get("code") or a.get("id"),
                  "title":t,"releaseDate":ems(a.get("releaseDate")),"catalog_id":cid})
        yy=[x for x in ys if x]
        if hit and yy and min(yy)<=2020:break
        time.sleep(.02)

first={}
for r in fr:
    if r["symbol"] not in first or r["releaseDate"]<first[r["symbol"]]["releaseDate"]:
        first[r["symbol"]]=r

joins=[]
for s,a in unique.items():
    if s not in first:continue
    f=first[s]
    td=max(a["listingTime"],f["releaseDate"])
    if yr(td)!=2025:continue
    joins.append({"symbol":s,"alpha":a,"first_futures":f,
      "t_dual_source_ms":td,
      "t_dual_source_utc":datetime.fromtimestamp(td/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")})
joins.sort(key=lambda x:x["t_dual_source_ms"])

res={
 "alpha_endpoint_total_rows":len(rows),
 "alpha_2025_identity_rows":len(alpha),
 "alpha_2025_unique_symbols":len(unique),
 "alpha_2025_ambiguous_symbols":amb,
 "alpha_unique_2025":sorted(unique.values(),key=lambda x:(x["listingTime"],x["symbol"])),
 "futures_catalog_candidates":cids,
 "futures_launch_rows_through_2025":len(fr),
 "futures_unique_symbols_through_2025":len(first),
 "exact_dual_candidates_tdual_in_2025":len(joins),
 "sample_ge_12":len(joins)>=12,
 "spot_outcomes_opened":False,
 "market_prices_opened":False,
 "dual_source_candidates_2025":joins
}
print("DUAL_PRECURSOR_V012_SOURCE_BEGIN")
print(json.dumps(res,indent=2,ensure_ascii=False,sort_keys=True))
print("DUAL_PRECURSOR_V012_SOURCE_END")
if not res["sample_ge_12"]:raise SystemExit(2)

# trigger registered V0.1.2 workflow
