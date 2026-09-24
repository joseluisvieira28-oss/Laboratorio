#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import requests
from bs4 import BeautifulSoup

ROOT=Path("Dream-Account-OS-v2.3-PARTIAL")
MANIFEST=ROOT/"research/BINANCE_COLLATERAL_HAIRCUT_001_MANIFEST_V0.1B.json"
OUT=ROOT/"runtime/binance_collateral_haircut_001/source_manifest_receipt_v01b.json"
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
REFERER="https://www.binance.com/en/support/announcement"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab","clienttype":"web","Accept-Language":"en-US,en;q=0.9"})

def get(code):
    last=None
    for i in range(7):
        try:
            r=S.get(DETAIL,params={"articleCode":code},headers={"Referer":REFERER},timeout=45)
            if r.status_code==429 or r.status_code>=500: raise RuntimeError(f"retryable HTTP {r.status_code}")
            r.raise_for_status(); return r
        except Exception as e:
            last=e
            if i<6: time.sleep(min(20,1.5*(2**i)))
    raise RuntimeError(str(last))

def iter_dicts(x:Any)->Iterable[dict]:
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from iter_dicts(v)
    elif isinstance(x,list):
        for v in x: yield from iter_dicts(v)

def strings(x):
    o=[]
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,str) and k.lower() not in {"url","link","shareurl","image","icon"}: o.append(v)
            elif isinstance(v,(dict,list)): o.extend(strings(v))
    elif isinstance(x,list):
        for v in x:o.extend(strings(v))
    return o

def norm(s):
    s=re.sub(r"<script[^>]*>.*?</script>"," ",str(s),flags=re.I|re.S)
    s=re.sub(r"<style[^>]*>.*?</style>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<[^>]+>"," ",s)
    return re.sub(r"\s+"," ",html.unescape(s)).strip()

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

def release_ms(obj):
    vals=[]
    for d in iter_dicts(obj):
        for k,v in d.items():
            if k.lower() in {"releasedate","releasetime","publishtime","publishdate","publishedat","publishedtime"}:
                z=parse_ts(v)
                if z:vals.append(z)
    return min(vals) if vals else None

def title_of(obj):
    for d in iter_dicts(obj):
        v=d.get("title")
        if isinstance(v,str) and v.strip():return norm(v)
    return ""

def pct(s):
    m=re.search(r"(-?\d+(?:\.\d+)?)\s*%",s)
    return float(m.group(1)) if m else None

def parse_tables(ss):
    out=[];seen=set()
    for raw in ss:
        if "<table" not in raw.lower():continue
        soup=BeautifulSoup(raw,"html.parser")
        for ti,t in enumerate(soup.find_all("table")):
            rows=[]
            for tr in t.find_all("tr"):
                cells=[norm(c.get_text(" ",strip=True)) for c in tr.find_all(["th","td"])]
                if cells:rows.append(cells)
            hdr=None
            for i,row in enumerate(rows[:6]):
                low=[x.lower() for x in row]
                ai=next((j for j,x in enumerate(low) if x in ("asset","assets") or x.startswith("assets ")),None)
                bi=next((j for j,x in enumerate(low) if "collateral ratio" in x and "before" in x),None)
                ci=next((j for j,x in enumerate(low) if "collateral ratio" in x and "after" in x),None)
                if ai is not None and bi is not None and ci is not None:
                    hdr=(i,ai,bi,ci);break
            if hdr is None:continue
            hi,ai,bi,ci=hdr
            for row in rows[hi+1:]:
                if max(ai,bi,ci)>=len(row):continue
                asset=re.sub(r"[^A-Z0-9]","",row[ai].upper())
                before=pct(row[bi]); after=pct(row[ci])
                if asset and before is not None and after is not None and 0<=before<=100 and 0<=after<=100 and before!=after:
                    k=(asset,before,after)
                    if k not in seen:
                        seen.add(k);out.append({"asset":asset,"before_pct":before,"after_pct":after,"delta_pp":after-before,"table_index":ti})
    return out

def body_has_effective(text,iso):
    d=datetime.fromisoformat(iso.replace("Z","+00:00"))
    date=d.strftime("%Y-%m-%d"); hh=d.strftime("%H:%M")
    return date in text and hh in text and "UTC" in text

def main():
    manifest=json.loads(MANIFEST.read_text())
    arts=[];events=[]
    try:
        if manifest.get("expected_article_count")!=5 or manifest.get("expected_asset_event_count")!=36:
            raise RuntimeError("manifest invariant mismatch")
        for m in manifest["articles"]:
            r=get(m["code"]); obj=r.json(); data=obj.get("data",obj); ss=strings(data)
            text=norm(" ".join(ss)); title=title_of(obj); rel=release_ms(obj)
            body_code=False
            for d in iter_dicts(obj):
                for k in ("code","articleCode","articlecode"):
                    if str(d.get(k,"")).lower()==m["code"].lower():body_code=True
            rows=parse_tables(ss)
            eff_ms=int(datetime.fromisoformat(m["effective_utc"].replace("Z","+00:00")).timestamp()*1000)
            structural=("collateral ratio" in text.lower() and "portfolio margin" in text.lower())
            rec={
              "code":m["code"],"official_title":title,"release_ms":rel,"effective_utc":m["effective_utc"],"effective_ms":eff_ms,
              "payload_code_match":body_code,"body_effective_timestamp_match":body_has_effective(text,m["effective_utc"]),
              "structural":structural,"table_event_count":len(rows),"response_sha256":hashlib.sha256(r.content).hexdigest()
            }
            arts.append(rec)
            if not (body_code and structural and rec["body_effective_timestamp_match"] and rel is not None and rel<eff_ms):
                raise RuntimeError("canonical validation failed for "+m["code"])
            for row in rows:
                events.append({"article_code":m["code"],"official_title":title,"release_ms":rel,"effective_utc":m["effective_utc"],"effective_ms":eff_ms,**row})
            time.sleep(.6)

        if len(events)!=36: raise RuntimeError(f"expected exactly 36 parsed asset-events, got {len(events)}")
        clusters={(e["article_code"],e["effective_ms"]) for e in events}
        assets={e["asset"] for e in events}
        tight=sum(e["delta_pp"]<0 for e in events); loose=sum(e["delta_pp"]>0 for e in events)
        passed=(len(clusters)==5 and len(assets)>=15 and tight>=5 and loose>=5)
        receipt={
          "lab_id":"BINANCE-COLLATERAL-HAIRCUT-001",
          "classification":"BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" if passed else "SOURCE_INSUFFICIENT",
          "manifest_version":"V0.1B","independent_clusters":len(clusters),"asset_events":len(events),
          "unique_assets":len(assets),"tightening_events":tight,"loosening_events":loose,
          "articles":arts,"events":events,
          "safety":{"market_prices_opened":False,"btc_prices_opened":False,"returns_opened":False,"pnl_opened":False,"protected_2025_2026_opened":False,"authenticated_api":False,"mutation":False}
        }
    except Exception as e:
        receipt={"lab_id":"BINANCE-COLLATERAL-HAIRCUT-001","classification":"PROVENANCE_FAILURE","failure":f"{type(e).__name__}: {e}","articles":arts,"events_parsed_before_failure":len(events),"safety":{"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"protected_2025_2026_opened":False,"mutation":False}}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:receipt.get(k) for k in ["classification","independent_clusters","asset_events","unique_assets","tightening_events","loosening_events","failure"]},indent=2))
    return 0 if receipt["classification"]=="BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" else 2

if __name__=="__main__":raise SystemExit(main())
