#!/usr/bin/env python3
# SOURCE-ONLY: construct 2025 Alpha + first Binance Futures perpetual source universe.
# Does not query Binance Spot listing outcomes or market prices.
import json, re, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone

UA={"User-Agent":"Mozilla/5.0 CryptoLabDualPrecursorSourceCensus/1.0","Accept":"application/json,text/plain,*/*"}
ALPHA="https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
CMS_LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
FUTURES_CATALOG=161

def get_json(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status,json.load(r)

def epoch_ms(v):
    try:
        n=int(v)
        if n<10**11: n*=1000
        return n
    except Exception:
        return None

def year_ms(v):
    n=epoch_ms(v)
    if n is None: return None
    return datetime.fromtimestamp(n/1000,tz=timezone.utc).year

# Alpha snapshot.
st,obj=get_json(ALPHA)
data=obj.get("data",obj) if isinstance(obj,dict) else obj
if isinstance(data,dict):
    lists=[v for v in data.values() if isinstance(v,list)]
    rows=lists[0] if lists else []
elif isinstance(data,list):
    rows=data
else:
    rows=[]

alpha=[]
for x in rows:
    if not isinstance(x,dict): continue
    lt=epoch_ms(x.get("listingTime"))
    if lt is None or year_ms(lt)!=2025: continue
    sym=str(x.get("symbol") or "").strip().upper()
    if not sym: continue
    alpha.append({
      "alphaId":x.get("alphaId"),
      "tokenId":x.get("tokenId"),
      "symbol":sym,
      "name":x.get("name"),
      "chainId":x.get("chainId"),
      "chainName":x.get("chainName"),
      "contractAddress":x.get("contractAddress"),
      "listingTime":lt,
      "listingTimeUtc":datetime.fromtimestamp(lt/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "fullyDelisted":x.get("fullyDelisted"),
      "offline":x.get("offline")
    })

sym_counts=Counter(x["symbol"] for x in alpha)
ambiguous_symbols=sorted([s for s,n in sym_counts.items() if n>1])
alpha_unique={x["symbol"]:x for x in alpha if sym_counts[x["symbol"]]==1}

# Futures catalog: scan back through historical launch announcements and keep earliest per symbol.
fut_rows=[]
seen_any=False
for page in range(1,161):
    q=urllib.parse.urlencode({"type":1,"pageNo":page,"pageSize":50,"catalogId":FUTURES_CATALOG})
    try:
        _,j=get_json(CMS_LIST+"?"+q)
    except Exception:
        break
    arts=[]
    for cat in ((j.get("data") or {}).get("catalogs") or []):
        arts.extend(cat.get("articles") or [])
    if not arts: break
    years=[]
    for a in arts:
        y=year_ms(a.get("releaseDate")); years.append(y)
        if y is None or y>2025: continue
        title=(a.get("title") or "").strip()
        low=title.lower()
        # Source classifier: official futures launch + perpetual contract.
        if "futures will launch" not in low: continue
        if "perpetual" not in low: continue
        syms=sorted(set(re.findall(r"\b([A-Z0-9]{2,40})USDT\b",title.upper())))
        if not syms:
            continue
        seen_any=True
        for sym in syms:
            fut_rows.append({
              "symbol":sym,
              "pair":sym+"USDT",
              "article_code":a.get("code") or a.get("id"),
              "title":title,
              "releaseDate":epoch_ms(a.get("releaseDate")),
              "releaseUtc":datetime.fromtimestamp(epoch_ms(a.get("releaseDate"))/1000,tz=timezone.utc).isoformat().replace("+00:00","Z") if epoch_ms(a.get("releaseDate")) else None,
              "year":y
            })
    yy=[y for y in years if y is not None]
    if seen_any and yy and min(yy)<=2020:
        break
    time.sleep(0.03)

first_fut={}
for r in fut_rows:
    s=r["symbol"]
    if s not in first_fut or r["releaseDate"]<first_fut[s]["releaseDate"]:
        first_fut[s]=r

joined=[]
for sym,a in alpha_unique.items():
    f=first_fut.get(sym)
    if not f: continue
    tdual=max(a["listingTime"],f["releaseDate"])
    joined.append({
      "symbol":sym,
      "alpha":a,
      "first_futures":f,
      "t_dual_source_ms":tdual,
      "t_dual_source_utc":datetime.fromtimestamp(tdual/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
      "t_dual_year":year_ms(tdual)
    })
joined.sort(key=lambda x:x["t_dual_source_ms"])
joined_2025=[x for x in joined if x["t_dual_year"]==2025]

res={
 "alpha_http_status":st,
 "alpha_endpoint_total_rows":len(rows),
 "alpha_2025_identity_rows":len(alpha),
 "alpha_2025_unique_symbols":len(alpha_unique),
 "alpha_2025_ambiguous_symbol_count":len(ambiguous_symbols),
 "alpha_2025_ambiguous_symbols":ambiguous_symbols,
 "futures_launch_rows_through_2025":len(fut_rows),
 "futures_unique_symbols_through_2025":len(first_fut),
 "exact_alpha_futures_joins":len(joined),
 "exact_dual_candidates_tdual_in_2025":len(joined_2025),
 "sample_ge_12":len(joined_2025)>=12,
 "spot_outcomes_opened":False,
 "market_prices_opened":False,
 "dual_source_candidates_2025":joined_2025,
}
print("DUAL_PRECURSOR_ALPHA_FUTURES_CENSUS_BEGIN")
print(json.dumps(res,indent=2,ensure_ascii=False,sort_keys=True))
print("DUAL_PRECURSOR_ALPHA_FUTURES_CENSUS_END")
if not res["sample_ge_12"]:
    raise SystemExit(2)
