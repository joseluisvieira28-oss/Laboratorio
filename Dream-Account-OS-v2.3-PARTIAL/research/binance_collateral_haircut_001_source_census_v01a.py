#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import requests
from bs4 import BeautifulSoup

LAB="BINANCE-COLLATERAL-HAIRCUT-001"
START=datetime(2024,1,1,tzinfo=timezone.utc); END=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000); END_MS=int(END.timestamp()*1000)
LIST="https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
REFERER="https://www.binance.com/en/support/announcement"
CONTROLS={"0806a835368b409e8d5ebd84d9fdc4ed","3f0978bcf69643aeb29424d45c9b810c","b9fad723c9c64240801d0e11dd77faa8","51bb9a7a59d2472cbd0c2b3ff38fe9bd"}
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab","clienttype":"web","Accept-Language":"en-US,en;q=0.9"})

def get(url,params=None,attempts=6):
    last=None
    for i in range(attempts):
        try:
            r=S.get(url,params=params,headers={"Referer":REFERER},timeout=45)
            if r.status_code==429 or r.status_code>=500: raise RuntimeError(f"retryable HTTP {r.status_code}")
            r.raise_for_status(); return r
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(20,1.5*(2**i)))
    raise RuntimeError(str(last))

def iter_dicts(x:Any)->Iterable[dict]:
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from iter_dicts(v)
    elif isinstance(x,list):
        for v in x: yield from iter_dicts(v)

def norm(s):
    s=re.sub(r"<script[^>]*>.*?</script>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<style[^>]*>.*?</style>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<[^>]+>"," ",s)
    return re.sub(r"\s+"," ",html.unescape(str(s))).strip()

def parse_ts(v):
    if isinstance(v,(int,float)):
        z=int(v); return z*1000 if z<10_000_000_000 else z
    if isinstance(v,str):
        q=v.strip()
        if re.fullmatch(r"\d{10,16}",q):
            z=int(q); return z*1000 if z<10_000_000_000 else z
        try:
            d=datetime.fromisoformat(q.replace("Z","+00:00"))
            if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
            return int(d.astimezone(timezone.utc).timestamp()*1000)
        except:return None
    return None

def article_meta_records(obj):
    out={}
    for d in iter_dicts(obj):
        code=None
        for k in ("code","articleCode","articlecode"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"[0-9a-fA-F]{32}",v.strip()):
                code=v.lower(); break
        title=d.get("title")
        if not code or not isinstance(title,str) or not title.strip(): continue
        ts=None
        for k,v in d.items():
            if k.lower() in {"releasedate","releasetime","publishtime","publishdate","publishedat","publishedtime"}:
                ts=parse_ts(v)
                if ts: break
        old=out.get(code)
        rec={"code":code,"title":norm(title),"release_ms":ts}
        if old is None or (old.get("release_ms") is None and ts is not None): out[code]=rec
    return list(out.values())

def strings(x):
    o=[]
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,str) and k.lower() not in {"url","link","shareurl","image","icon"}:o.append(v)
            elif isinstance(v,(dict,list)):o.extend(strings(v))
    elif isinstance(x,list):
        for v in x:o.extend(strings(v))
    return o

def detail_release(obj):
    vals=[]
    for d in iter_dicts(obj):
        for k,v in d.items():
            if k.lower() in {"releasedate","releasetime","publishtime","publishdate","publishedat","publishedtime"}:
                z=parse_ts(v)
                if z:vals.append(z)
    inside=[z for z in vals if START_MS<=z<=END_MS]
    return min(inside) if inside else (min(vals) if vals else None)

def detail_title(obj):
    for d in iter_dicts(obj):
        v=d.get("title")
        if isinstance(v,str) and v.strip():return norm(v)
    return ""

def effective_times(text):
    found=[]
    pats=[
      r"(?:will\s+update|update|adjust)[^.]{0,700}?(?:from|on|at)\s+(2024-\d{1,2}-\d{1,2})\s+(\d{2}:\d{2})\s*\(UTC\)",
      r"(?:from|on|at)\s+(2024-\d{1,2}-\d{1,2})\s+(\d{2}:\d{2})\s*\(UTC\)"
    ]
    for p in pats:
        for m in re.finditer(p,text,flags=re.I):
            try:
                d=datetime.strptime(m.group(1)+" "+m.group(2),"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                if START<=d<=END:found.append(d)
            except:pass
        if found:break
    return sorted({x.isoformat():x for x in found}.values())

def pct(s):
    m=re.search(r"(-?\d+(?:\.\d+)?)\s*%",s)
    return float(m.group(1)) if m else None

def parse_tables(ss):
    out=[]; seen=set()
    for raw in ss:
        if "<table" not in raw.lower():continue
        soup=BeautifulSoup(raw,"html.parser")
        for ti,t in enumerate(soup.find_all("table")):
            rows=[]
            for tr in t.find_all("tr"):
                cells=[norm(c.get_text(" ",strip=True)) for c in tr.find_all(["th","td"])]
                if cells:rows.append(cells)
            hdr=None
            for i,row in enumerate(rows[:5]):
                low=[x.lower() for x in row]
                ai=next((j for j,x in enumerate(low) if x=="asset" or x=="assets" or x.startswith("assets ")),None)
                bi=next((j for j,x in enumerate(low) if "collateral ratio" in x and "before" in x),None)
                ci=next((j for j,x in enumerate(low) if "collateral ratio" in x and "after" in x),None)
                if ai is not None and bi is not None and ci is not None:
                    hdr=(i,ai,bi,ci);break
            if hdr is None:continue
            hi,ai,bi,ci=hdr
            for row in rows[hi+1:]:
                if max(ai,bi,ci)>=len(row):continue
                asset=re.sub(r"[^A-Z0-9]","",row[ai].upper())
                before=pct(row[bi]);after=pct(row[ci])
                if asset and before is not None and after is not None and 0<=before<=100 and 0<=after<=100 and before!=after:
                    key=(asset,before,after)
                    if key not in seen:
                        seen.add(key);out.append({"asset":asset,"before_pct":before,"after_pct":after,"delta_pp":after-before,"table_index":ti})
    return out

def main():
    root=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/binance_collateral_haircut_001")
    root.mkdir(parents=True,exist_ok=True)
    pages=[]; seen={}; reached_2024=False; crossed_before=False; last_codes=None
    try:
        for page in range(1,151):
            r=get(LIST,{"type":1,"pageNo":page,"pageSize":50})
            obj=r.json(); recs=article_meta_records(obj)
            codes=sorted({x["code"] for x in recs})
            if not codes: raise RuntimeError(f"CMS page {page} contains no parseable article metadata")
            if last_codes==codes: raise RuntimeError(f"CMS pagination stalled at page {page}")
            last_codes=codes
            times=[x["release_ms"] for x in recs if x["release_ms"]]
            pages.append({"page":page,"http_status":r.status_code,"sha256":hashlib.sha256(r.content).hexdigest(),"article_records":len(recs),"min_release_ms":min(times) if times else None,"max_release_ms":max(times) if times else None})
            for x in recs:
                if x["release_ms"] and START_MS<=x["release_ms"]<=END_MS:
                    reached_2024=True
                    seen[x["code"]]=x
            if reached_2024 and times and min(times)<START_MS:
                crossed_before=True;break
            time.sleep(.35)
        if not reached_2024 or not crossed_before: raise RuntimeError("official CMS index did not fully traverse frozen 2024 interval")

        # 2024-only title population; controls are included even if title wording differs
        cands={code:x for code,x in seen.items() if ("collateral ratio" in x["title"].lower() and "margin" in x["title"].lower()) or code in CONTROLS}
        missing=sorted(CONTROLS-set(cands))
        if missing: raise RuntimeError("positive controls absent from official CMS 2024 index: "+",".join(missing))

        articles=[];events=[]
        for code,meta in sorted(cands.items()):
            r=get(DETAIL,{"articleCode":code}); obj=r.json(); data=obj.get("data",obj); ss=strings(data)
            text=norm(" ".join(ss)); title=detail_title(obj); rel=detail_release(obj)
            structural=("collateral ratio" in text.lower() and "portfolio margin" in text.lower())
            ets=effective_times(text); rows=parse_tables(ss)
            art={**meta,"official_title":title,"detail_release_ms":rel,"response_sha256":hashlib.sha256(r.content).hexdigest(),"structural":structural,"effective_times":[x.isoformat() for x in ets],"table_event_count":len(rows)}
            articles.append(art)
            if structural and len(ets)==1 and rel is not None and START_MS<=rel<=END_MS and rel<int(ets[0].timestamp()*1000):
                for row in rows:
                    events.append({"article_code":code,"official_title":title,"release_ms":rel,"effective_ms":int(ets[0].timestamp()*1000),"effective_utc":ets[0].isoformat(),**row})
            time.sleep(.7)

        clusters=sorted({(e["article_code"],e["effective_ms"]) for e in events})
        assets=sorted({e["asset"] for e in events})
        tight=sum(e["delta_pp"]<0 for e in events);loose=sum(e["delta_pp"]>0 for e in events)
        controls={c:any(a["code"]==c and a["structural"] and len(a["effective_times"])==1 and a["table_event_count"]>0 for a in articles) for c in sorted(CONTROLS)}
        passed=len(clusters)>=4 and len(events)>=20 and len(assets)>=15 and tight>=5 and loose>=5 and all(controls.values())
        receipt={
          "lab_id":LAB,"classification":"BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" if passed else "SOURCE_INSUFFICIENT",
          "enumeration_transport":"official Binance CMS article-list index V0.1A",
          "cms_pages":pages,"indexed_2024_articles":len(seen),"candidate_articles":len(cands),
          "independent_clusters":len(clusters),"asset_events":len(events),"unique_assets":len(assets),
          "tightening_events":tight,"loosening_events":loose,"positive_controls":controls,
          "articles":articles,"events":events,
          "safety":{"only_2024_article_bodies_hydrated":True,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"authenticated_api":False,"mutation":False}
        }
    except Exception as e:
        receipt={"lab_id":LAB,"classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE","failure":f"{type(e).__name__}: {e}","cms_pages":pages,"safety":{"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"mutation":False}}
    (root/"source_census_receipt_v01a.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:receipt.get(k) for k in ["classification","indexed_2024_articles","candidate_articles","independent_clusters","asset_events","unique_assets","tightening_events","loosening_events","positive_controls","failure"]},indent=2))
    return 0 if receipt["classification"]=="BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" else 2

if __name__=="__main__":raise SystemExit(main())
