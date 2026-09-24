#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import requests
from bs4 import BeautifulSoup

LAB="BINANCE-COLLATERAL-HAIRCUT-001"
START=datetime(2024,1,1,tzinfo=timezone.utc)
END=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000); END_MS=int(END.timestamp()*1000)
END_FLOOR_MS=int(datetime(2024,12,31,tzinfo=timezone.utc).timestamp()*1000)
TELEGRAM="https://t.me/s/binance_announcements"
DETAIL="https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
REFERER="https://www.binance.com/en/support/announcement"
UPPER_CURSOR=6899
MAX_PAGES=300
CONTROLS={
 "0806a835368b409e8d5ebd84d9fdc4ed",
 "3f0978bcf69643aeb29424d45c9b810c",
 "b9fad723c9c64240801d0e11dd77faa8",
 "51bb9a7a59d2472cbd0c2b3ff38fe9bd",
}
CODE_RE=re.compile(r"([0-9a-fA-F]{32})")
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab","Accept-Language":"en-US,en;q=0.9"})

def req(url, params=None, attempts=6):
    last=None
    for i in range(attempts):
        try:
            r=SESSION.get(url,params=params,headers={"Referer":REFERER},timeout=45)
            if r.status_code==429 or r.status_code>=500: raise RuntimeError(f"retryable HTTP {r.status_code}")
            r.raise_for_status(); return r
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(20,1.5*(2**i)))
    raise RuntimeError(str(last))

def norm(s):
    s=re.sub(r"<script[^>]*>.*?</script>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<style[^>]*>.*?</style>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<[^>]+>"," ",s)
    return re.sub(r"\s+"," ",html.unescape(s)).strip()

def iter_dicts(x:Any)->Iterable[dict]:
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from iter_dicts(v)
    elif isinstance(x,list):
        for v in x: yield from iter_dicts(v)

def strings(x):
    out=[]
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,str) and k.lower() not in {"url","link","shareurl","image","icon"}: out.append(v)
            elif isinstance(v,(dict,list)): out.extend(strings(v))
    elif isinstance(x,list):
        for v in x: out.extend(strings(v))
    return out

def parse_telegram(raw):
    soup=BeautifulSoup(raw,"html.parser"); out=[]
    for m in soup.select("div.tgme_widget_message[data-post]"):
        dp=m.get("data-post","")
        if not dp.startswith("binance_announcements/"): continue
        try: mid=int(dp.rsplit("/",1)[1])
        except: continue
        tt=m.select_one("time[datetime]")
        if not tt: continue
        dt=datetime.fromisoformat(tt.get("datetime").replace("Z","+00:00")).astimezone(timezone.utc)
        txt=m.select_one("div.tgme_widget_message_text")
        text=txt.get_text("\n",strip=True) if txt else ""
        title=next((z.strip() for z in text.splitlines() if z.strip()),"")
        codes=set()
        for a in m.select("a[href]"):
            href=a.get("href","")
            if "binance.com/" in href and "/support/announcement/" in href:
                mm=CODE_RE.search(href)
                if mm: codes.add(mm.group(1).lower())
        out.append({"message_id":mid,"ts_ms":int(dt.timestamp()*1000),"title":title,"codes":sorted(codes)})
    return out

def parse_ts_value(v):
    if isinstance(v,(int,float)):
        z=int(v); return z*1000 if z<10_000_000_000 else z
    if isinstance(v,str):
        s=v.strip()
        if re.fullmatch(r"\d{10,16}",s):
            z=int(s); return z*1000 if z<10_000_000_000 else z
        try:
            d=datetime.fromisoformat(s.replace("Z","+00:00"))
            if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
            return int(d.astimezone(timezone.utc).timestamp()*1000)
        except: return None
    return None

def release_ms(obj):
    keys={"releasedate","releasetime","publishtime","publishdate","publishedat","publishedtime"}
    cand=[]
    for d in iter_dicts(obj):
        for k,v in d.items():
            if k.lower() in keys:
                z=parse_ts_value(v)
                if z: cand.append(z)
    inside=[z for z in cand if START_MS<=z<=END_MS]
    return min(inside) if inside else (min(cand) if cand else None)

def title_of(obj):
    for d in iter_dicts(obj):
        v=d.get("title")
        if isinstance(v,str) and v.strip(): return norm(v)
    return ""

def effective_times(text):
    pats=[
      r"(?:will\s+update|update|adjust)[^.]{0,500}?(?:from|on|at)\s+(2024-\d{1,2}-\d{1,2})\s+(\d{2}:\d{2})\s*\(UTC\)",
      r"(?:from|on|at)\s+(2024-\d{1,2}-\d{1,2})\s+(\d{2}:\d{2})\s*\(UTC\)"
    ]
    found=[]
    for pat in pats:
        for m in re.finditer(pat,text,flags=re.I):
            try:
                dt=datetime.strptime(m.group(1)+" "+m.group(2),"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                if START<=dt<=END: found.append(dt)
            except: pass
        if found: break
    uniq=sorted({d.isoformat():d for d in found}.values())
    return uniq

def pct(s):
    m=re.search(r"(-?\d+(?:\.\d+)?)\s*%",s)
    return float(m.group(1)) if m else None

def parse_tables(raw_strings):
    rows=[]
    for raw in raw_strings:
        if "<table" not in raw.lower(): continue
        soup=BeautifulSoup(raw,"html.parser")
        for ti,table in enumerate(soup.find_all("table")):
            rr=[]
            for tr in table.find_all("tr"):
                cells=[norm(c.get_text(" ",strip=True)) for c in tr.find_all(["th","td"])]
                if cells: rr.append(cells)
            if not rr: continue
            header_i=None; ai=bi=ci=None
            for i,row in enumerate(rr[:4]):
                low=[x.lower() for x in row]
                asset_idx=next((j for j,x in enumerate(low) if x=="assets" or x=="asset" or x.startswith("assets ")),None)
                before_idx=next((j for j,x in enumerate(low) if "collateral ratio" in x and "before" in x),None)
                after_idx=next((j for j,x in enumerate(low) if "collateral ratio" in x and "after" in x),None)
                if asset_idx is not None and before_idx is not None and after_idx is not None:
                    header_i=i; ai=asset_idx; bi=before_idx; ci=after_idx; break
            if header_i is None: continue
            for row in rr[header_i+1:]:
                if max(ai,bi,ci)>=len(row): continue
                asset=re.sub(r"[^A-Z0-9]","",row[ai].upper())
                before=pct(row[bi]); after=pct(row[ci])
                if asset and before is not None and after is not None and 0<=before<=100 and 0<=after<=100 and before!=after:
                    rows.append({"asset":asset,"before_pct":before,"after_pct":after,"delta_pp":after-before,"table_index":ti})
    # de-dupe exact
    out=[]; seen=set()
    for x in rows:
        k=(x["asset"],x["before_pct"],x["after_pct"])
        if k not in seen: seen.add(k); out.append(x)
    return out

def main():
    outdir=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/binance_collateral_haircut_001")
    outdir.mkdir(parents=True,exist_ok=True)
    cursor=UPPER_CURSOR; pages=[]; candidates={}; reached=False; protected=False
    try:
        for page_no in range(1,MAX_PAGES+1):
            r=req(TELEGRAM,{"before":str(cursor)}); raw=r.content
            page=parse_telegram(raw)
            if not page: raise RuntimeError(f"no parseable Telegram messages page {page_no}")
            ids=sorted({x["message_id"] for x in page}); nxt=min(ids)
            pmin=min(x["ts_ms"] for x in page); pmax=max(x["ts_ms"] for x in page)
            if page_no==1 and pmax>END_MS:
                protected=True; raise RuntimeError("protected period seen at upper boundary")
            if page_no==1 and pmax<END_FLOOR_MS: raise RuntimeError("upper cursor does not cover 2024-12-31")
            if pmax>END_MS: protected=True; raise RuntimeError("protected 2025/2026 page encountered")
            for rec in page:
                if not START_MS<=rec["ts_ms"]<=END_MS: continue
                low=rec["title"].lower()
                match=("collateral ratio" in low and ("portfolio margin" in low or "margin" in low))
                for code in rec["codes"]:
                    if match or code in CONTROLS:
                        old=candidates.get(code)
                        z={"code":code,"telegram_message_id":rec["message_id"],"telegram_ts_ms":rec["ts_ms"],"telegram_title":rec["title"],"title_match":match}
                        if old is None or z["telegram_message_id"]<old["telegram_message_id"]: candidates[code]=z
            pages.append({"page":page_no,"sha256":hashlib.sha256(raw).hexdigest(),"min_ts":pmin,"max_ts":pmax,"min_id":min(ids),"max_id":max(ids)})
            if pmin<START_MS: reached=True; break
            if nxt>=cursor: raise RuntimeError("non-descending cursor")
            cursor=nxt
        if not reached: raise RuntimeError("did not cross lower 2024 boundary")
        missing_controls_index=sorted(CONTROLS-set(candidates))
        (outdir/"enumeration_diagnostic.json").write_text(json.dumps({
          "candidate_count":len(candidates),
          "candidates":sorted(candidates.values(),key=lambda x:x["telegram_message_id"]),
          "missing_controls_from_index":missing_controls_index,
          "pages":pages,
          "market_prices_opened":False,
          "returns_opened":False,
          "pnl_opened":False
        },indent=2,sort_keys=True)+"\\n")
        if missing_controls_index: raise RuntimeError("positive controls missing from immutable index: "+",".join(missing_controls_index))

        articles=[]; events=[]
        for code,meta in sorted(candidates.items()):
            r=req(DETAIL,{"articleCode":code}); obj=r.json()
            data=obj.get("data",obj)
            ss=strings(data)
            text=norm(" ".join(ss))
            title=title_of(obj)
            rel=release_ms(obj)
            structural=("collateral ratio" in text.lower() and "portfolio margin" in text.lower())
            if not structural and code not in CONTROLS: continue
            ets=effective_times(text)
            table_rows=parse_tables(ss)
            article={
              **meta,"http_status":r.status_code,"response_sha256":hashlib.sha256(r.content).hexdigest(),
              "official_title":title,"release_ms":rel,"effective_times":[x.isoformat() for x in ets],
              "table_event_count":len(table_rows),"structural":structural
            }
            articles.append(article)
            if len(ets)==1 and rel is not None and rel<int(ets[0].timestamp()*1000):
                for row in table_rows:
                    events.append({
                      "article_code":code,"official_title":title,"release_ms":rel,
                      "effective_ms":int(ets[0].timestamp()*1000),"effective_utc":ets[0].isoformat(),**row
                    })
            time.sleep(1.0)

        # retain only rows whose article has exactly one effective time and publication precedes it
        clusters=sorted({(e["article_code"],e["effective_ms"]) for e in events})
        unique_assets=sorted({e["asset"] for e in events})
        tight=sum(e["delta_pp"]<0 for e in events); loose=sum(e["delta_pp"]>0 for e in events)
        controls_recovered={c:any(a["code"]==c and a["structural"] and a["table_event_count"]>0 and len(a["effective_times"])==1 for a in articles) for c in sorted(CONTROLS)}
        pass_all=(len(clusters)>=4 and len(events)>=20 and len(unique_assets)>=15 and tight>=5 and loose>=5 and all(controls_recovered.values()))
        classification="BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" if pass_all else "SOURCE_INSUFFICIENT"
        receipt={
          "lab_id":LAB,"classification":classification,"frozen_window":["2024-01-01","2024-12-31"],
          "telegram_upper_cursor":UPPER_CURSOR,"pages":pages,"candidate_article_count":len(candidates),
          "hydrated_structural_articles":len([a for a in articles if a["structural"]]),
          "independent_clusters":len(clusters),"asset_events":len(events),"unique_assets":len(unique_assets),
          "tightening_events":tight,"loosening_events":loose,"positive_controls":controls_recovered,
          "articles":articles,"events":events,
          "safety":{"market_prices_opened":False,"btc_prices_opened":False,"returns_opened":False,"pnl_opened":False,"protected_2025_2026_seen":False,"authenticated_api":False,"mutation":False}
        }
    except Exception as e:
        classification="PROVENANCE_FAILURE" if protected else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt={"lab_id":LAB,"classification":classification,"failure":f"{type(e).__name__}: {e}","pages":pages,"safety":{"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"protected_2025_2026_seen":protected,"mutation":False}}
    path=outdir/"source_census_receipt.json"
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:receipt.get(k) for k in ["classification","candidate_article_count","hydrated_structural_articles","independent_clusters","asset_events","unique_assets","tightening_events","loosening_events","positive_controls","failure"]},indent=2))
    return 0 if receipt["classification"]=="BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
