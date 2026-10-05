#!/usr/bin/env python3
# SOURCE-ONLY event-timestamp + archive-sidecar coverage probe.
# No market values are opened.
import json, urllib.parse, urllib.request, re, html, time
from datetime import datetime, timezone

UA={"User-Agent":"Mozilla/5.0 CryptoLabForcedDelistCoverage/1.0","Accept":"application/json,text/plain,*/*"}
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
KNOWN_CODE="cfe97d52a8c840d3ba631835b637e9e7"
CATALOG_ID=161

def get_json(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status, json.load(r)

def get_text(url,n=512):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.status, r.read(n).decode("utf-8","replace")

def year(v):
    try:
        n=int(v)
        return datetime.fromtimestamp(n/(1000 if n>10**12 else 1),tz=timezone.utc).year
    except Exception:
        return None

def normalize_article_body(j):
    data=(j or {}).get("data") or {}
    raw=data.get("body") or data.get("content") or data.get("articleBody") or ""
    if not isinstance(raw,str):
        raw=json.dumps(raw,ensure_ascii=False)
    txt=html.unescape(raw)
    txt=re.sub(r"<[^>]+>"," ",txt)
    txt=txt.replace("\u00a0"," ")
    return re.sub(r"\s+"," ",txt).strip()

def page_articles(params):
    st,j=get_json(LIST+"?"+urllib.parse.urlencode(params))
    arts=[]
    for cat in ((j.get("data") or {}).get("catalogs") or []):
        arts.extend(cat.get("articles") or [])
    return arts

# Build candidate metadata from Futures catalog plus broad CMS route.
cand={}
for route,base_params,max_pages in [
    ("catalog",{"type":1,"pageSize":50,"catalogId":CATALOG_ID},120),
    ("broad",{"type":1,"pageSize":50},180)
]:
    seen_target=False
    for page in range(1,max_pages+1):
        params=dict(base_params); params["pageNo"]=page
        try: arts=page_articles(params)
        except Exception: break
        if not arts: break
        ys=[]
        for a in arts:
            y=year(a.get("releaseDate")); ys.append(y)
            title=(a.get("title") or "").strip()
            low=title.lower()
            if y in (2024,2025) and any(k in low for k in ("delist","rebrand","token swap","migration")):
                code=a.get("code") or a.get("id")
                if code:
                    old=cand.get(str(code),{})
                    cand[str(code)]={**old,"code":str(code),"title":title,"releaseDate":a.get("releaseDate"),"year":y,"routes":sorted(set((old.get("routes") or [])+[route]))}
                    seen_target=True
        yy=[x for x in ys if x is not None]
        if seen_target and yy and min(yy)<2024: break

# Source-only mechanical classifier + settlement timestamp parser.
# Timestamp regexes cover common Binance notice wording.
dt_patterns=[
    re.compile(r"(20\d{2}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*\(UTC\)",re.I),
    re.compile(r"(20\d{2}/\d{2}/\d{2})\s+(\d{1,2}:\d{2})\s*\(UTC\)",re.I),
]
mech=[]
for idx,(code,r) in enumerate(cand.items()):
    try:
        st,j=get_json(DETAIL+"?"+urllib.parse.urlencode({"articleCode":code}))
        body=normalize_article_body(j)
    except Exception:
        continue
    low=body.lower()
    if not ("close all positions" in low and ("automatic settlement" in low or "automatically settle" in low)):
        continue
    syms=sorted(set(re.findall(r"\b([A-Z0-9]{2,24}USDT)\b",body)))
    if not syms:
        continue

    # Gather all exact UTC date-times stated in the official article body.
    dts=[]
    for pat in dt_patterns:
        for m in pat.finditer(body):
            ds=m.group(1).replace("/","-"); ts=m.group(2)
            try:
                dt=datetime.strptime(ds+" "+ts,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                dts.append({"iso":dt.isoformat().replace("+00:00","Z"),"date":ds,"pos":m.start()})
            except Exception:
                pass
    # Deduplicate timestamps.
    seen=set(); dts2=[]
    for x in dts:
        if x["iso"] not in seen:
            seen.add(x["iso"]); dts2.append(x)
    dts=dts2

    # Map timestamps to symbols from local context around each automatic-settlement phrase.
    mappings=[]
    for sm in re.finditer(r"automatic settlement|automatically settle",body,re.I):
        lo=max(0,sm.start()-900); hi=min(len(body),sm.end()+900)
        ctx=body[lo:hi]
        ctx_syms=sorted(set(re.findall(r"\b([A-Z0-9]{2,24}USDT)\b",ctx)))
        ctx_dts=[]
        for pat in dt_patterns:
            for m in pat.finditer(ctx):
                ds=m.group(1).replace("/","-"); ts=m.group(2)
                try:
                    dt=datetime.strptime(ds+" "+ts,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    ctx_dts.append(dt.isoformat().replace("+00:00","Z"))
                except Exception:
                    pass
        ctx_dts=sorted(set(ctx_dts))
        if len(ctx_dts)==1 and ctx_syms:
            for s in ctx_syms:
                mappings.append((s,ctx_dts[0]))

    # If one exact UTC timestamp exists in whole article, safely apply to all evidenced USD-M symbols.
    if len(dts)==1:
        mappings=[(s,dts[0]["iso"]) for s in syms]

    mp={}
    for s,dt in mappings:
        mp.setdefault(s,set()).add(dt)

    mapped=[]
    ambiguous=[]
    for s in syms:
        vals=sorted(mp.get(s,set()))
        if len(vals)==1:
            mapped.append({"symbol":s,"settlement_utc":vals[0]})
        else:
            ambiguous.append({"symbol":s,"candidate_times":vals or [x["iso"] for x in dts]})

    mech.append({**r,"symbols":syms,"exact_times":[x["iso"] for x in dts],"mapped":mapped,"ambiguous":ambiguous})
    if idx and idx%25==0: time.sleep(0.05)

# Resolve duplicate symbol observations by article release order but preserve all event identities.
events=[]
for a in mech:
    for m in a["mapped"]:
        events.append({
          "article_code":a["code"],"article_title":a["title"],"releaseDate":a["releaseDate"],
          "year":a["year"],"symbol":m["symbol"],"settlement_utc":m["settlement_utc"]
        })

# Archive sidecar coverage only; no ZIP content opened.
base="https://data.binance.vision/data/futures/um/daily"
def checksum_present(url):
    try:
        st,txt=get_text(url)
        return st==200 and bool(re.match(r"^[0-9a-fA-F]{64}\s+",txt.strip()))
    except Exception:
        return False

for i,e in enumerate(events):
    day=e["settlement_utc"][:10]
    s=e["symbol"]
    urls={
      "perp":f"{base}/klines/{s}/1m/{s}-1m-{day}.zip.CHECKSUM",
      "mark":f"{base}/markPriceKlines/{s}/1m/{s}-1m-{day}.zip.CHECKSUM",
      "index":f"{base}/indexPriceKlines/{s}/1m/{s}-1m-{day}.zip.CHECKSUM",
      "metrics":f"{base}/metrics/{s}/{s}-metrics-{day}.zip.CHECKSUM",
    }
    e["archive"]={k:checksum_present(v) for k,v in urls.items()}
    e["core_archive_ok"]=all(e["archive"][k] for k in ("perp","mark","index"))
    e["metrics_ok"]=e["archive"]["metrics"]
    if i and i%15==0: time.sleep(0.05)

n=len(events)
core=sum(1 for e in events if e["core_archive_ok"])
metrics=sum(1 for e in events if e["metrics_ok"])
res={
 "candidate_articles":len(cand),
 "mechanical_articles":len(mech),
 "exact_mapped_contract_observations":n,
 "ambiguous_contract_observations":sum(len(a["ambiguous"]) for a in mech),
 "core_archive_ok_count":core,
 "core_archive_coverage":(core/n if n else 0),
 "metrics_ok_count":metrics,
 "metrics_coverage":(metrics/n if n else 0),
 "sample_ge_12":n>=12,
 "core_archive_ge_80pct":(n>0 and core/n>=0.80),
 "metrics_source_proven":metrics>0,
 "market_values_opened":False,
 "events":events,
 "ambiguous":[{"article_code":a["code"],"title":a["title"],"items":a["ambiguous"]} for a in mech if a["ambiguous"]],
}
res["source_gate_pass_candidate"]=(
  res["sample_ge_12"] and res["core_archive_ge_80pct"] and res["metrics_source_proven"]
)
print("FORCED_DELIST_EVENT_COVERAGE_BEGIN")
print(json.dumps(res,indent=2,ensure_ascii=False,sort_keys=True))
print("FORCED_DELIST_EVENT_COVERAGE_END")
if not res["source_gate_pass_candidate"]:
    raise SystemExit(2)
