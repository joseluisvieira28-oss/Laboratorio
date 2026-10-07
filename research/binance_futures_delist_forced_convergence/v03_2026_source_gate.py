#!/usr/bin/env python3
import json, urllib.parse, urllib.request, re, html, time
from datetime import datetime, timezone

UA={"User-Agent":"Mozilla/5.0 CryptoLabForcedDelistV03/1.0","Accept":"application/json,text/plain,*/*"}
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
CATALOG_ID=161
START=datetime(2026,1,1,tzinfo=timezone.utc)
END=datetime(2026,10,1,tzinfo=timezone.utc)

def get_json(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status,json.load(r)

def get_text(url,n=256):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.status,r.read(n).decode("utf-8","replace")

def release_dt(v):
    try:
        n=int(v); return datetime.fromtimestamp(n/(1000 if n>10**12 else 1),tz=timezone.utc)
    except: return None

def body_text(j):
    d=(j or {}).get("data") or {}
    raw=d.get("body") or d.get("content") or d.get("articleBody") or ""
    if not isinstance(raw,str): raw=json.dumps(raw,ensure_ascii=False)
    txt=html.unescape(raw); txt=re.sub(r"<[^>]+>"," ",txt); txt=txt.replace("\u00a0"," ")
    return re.sub(r"\s+"," ",txt).strip()

def page_articles(params):
    _,j=get_json(LIST+"?"+urllib.parse.urlencode(params))
    out=[]
    for cat in ((j.get("data") or {}).get("catalogs") or []): out.extend(cat.get("articles") or [])
    return out

cand={}
for route,base,max_pages in [
  ("catalog",{"type":1,"pageSize":50,"catalogId":CATALOG_ID},120),
  ("broad",{"type":1,"pageSize":50},180)
]:
    crossed=False
    for page in range(1,max_pages+1):
        p=dict(base); p["pageNo"]=page
        try: arts=page_articles(p)
        except Exception: break
        if not arts: break
        years=[]
        for a in arts:
            rd=release_dt(a.get("releaseDate"))
            if rd: years.append(rd.year)
            title=(a.get("title") or "").strip(); low=title.lower()
            if rd and rd.year==2026 and any(k in low for k in ("delist","rebrand","token swap","migration")):
                code=str(a.get("code") or a.get("id") or "")
                if code:
                    old=cand.get(code,{})
                    cand[code]={**old,"code":code,"title":title,"releaseDate":a.get("releaseDate"),"release_utc":rd.isoformat().replace("+00:00","Z"),"routes":sorted(set((old.get("routes") or [])+[route]))}
        if years and min(years)<2026:
            crossed=True; break
    if not crossed:
        raise SystemExit("SOURCE_BLOCKED:archive_did_not_cross_2026")

pat=[
 re.compile(r"(20\d{2}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*\(UTC\)",re.I),
 re.compile(r"(20\d{2}/\d{2}/\d{2})\s+(\d{1,2}:\d{2})\s*\(UTC\)",re.I),
]

events=[]; ambiguous=[]
for code,a in cand.items():
    try:
        _,j=get_json(DETAIL+"?"+urllib.parse.urlencode({"articleCode":code}))
        body=body_text(j)
    except Exception:
        continue
    low=body.lower()
    if not ("close all positions" in low and ("automatic settlement" in low or "automatically settle" in low)):
        continue
    syms=sorted(set(re.findall(r"\b([A-Z0-9]{2,24}USDT)\b",body)))
    if not syms: continue
    dts=[]
    for p in pat:
        for m in p.finditer(body):
            try:
                d=datetime.strptime(m.group(1).replace("/","-")+" "+m.group(2),"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                dts.append((d,m.start()))
            except: pass
    uniq=[]
    seen=set()
    for d,pos in dts:
        if d not in seen: seen.add(d); uniq.append((d,pos))
    mappings=[]
    for sm in re.finditer(r"automatic settlement|automatically settle",body,re.I):
        lo=max(0,sm.start()-900); hi=min(len(body),sm.end()+900); ctx=body[lo:hi]
        ss=sorted(set(re.findall(r"\b([A-Z0-9]{2,24}USDT)\b",ctx)))
        tt=[]
        for p in pat:
            for m in p.finditer(ctx):
                try: tt.append(datetime.strptime(m.group(1).replace("/","-")+" "+m.group(2),"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))
                except: pass
        tt=sorted(set(tt))
        if len(tt)==1:
            mappings.extend((s,tt[0]) for s in ss)
    if len(uniq)==1:
        mappings=[(s,uniq[0][0]) for s in syms]
    mp={}
    for s,d in mappings: mp.setdefault(s,set()).add(d)
    rd=release_dt(a.get("releaseDate"))
    for s in syms:
        vals=sorted(mp.get(s,set()))
        if len(vals)!=1:
            ambiguous.append({"article_code":code,"symbol":s,"candidate_times":[x.isoformat().replace("+00:00","Z") for x,_ in uniq]})
            continue
        T=vals[0]
        if not (START<=T<END): continue
        if rd is None or rd>=T: continue
        events.append({"article_code":code,"article_title":a["title"],"release_utc":rd.isoformat().replace("+00:00","Z"),"symbol":s,"settlement_utc":T.isoformat().replace("+00:00","Z")})

# de-duplicate exact identity
uniq={}
for e in events: uniq[(e["article_code"],e["symbol"],e["settlement_utc"])]=e
events=list(uniq.values())

BASE="https://data.binance.vision/data/futures/um/daily"
def sidecar(url):
    try:
        st,txt=get_text(url)
        return st==200 and bool(re.match(r"^[0-9a-fA-F]{64}\s+",txt.strip()))
    except: return False

for i,e in enumerate(events):
    day=e["settlement_utc"][:10]; s=e["symbol"]
    urls={
      "mark":f"{BASE}/markPriceKlines/{s}/1m/{s}-1m-{day}.zip.CHECKSUM",
      "index":f"{BASE}/indexPriceKlines/{s}/1m/{s}-1m-{day}.zip.CHECKSUM",
      "metrics":f"{BASE}/metrics/{s}/{s}-metrics-{day}.zip.CHECKSUM"
    }
    e["archive"]={k:sidecar(v) for k,v in urls.items()}
    e["archive_ok"]=all(e["archive"].values())
    if i and i%20==0: time.sleep(.05)

eligible=[e for e in events if e["archive_ok"]]
clusters=len(set(e["article_code"] for e in eligible))
verdict="SOURCE_PASS" if len(eligible)>=12 and clusters>=10 else "INSUFFICIENT_SAMPLE_2026"
res={"candidate_articles":len(cand),"exact_events":len(events),"eligible_events":len(eligible),"distinct_article_clusters":clusters,
     "ambiguous_count":len(ambiguous),"market_values_opened":False,"events":eligible,"ambiguous":ambiguous,"verdict":verdict}
print("V03_SOURCE_BEGIN"); print(json.dumps(res,indent=2,sort_keys=True)); print("V03_SOURCE_END")
if verdict!="SOURCE_PASS": raise SystemExit(3)
