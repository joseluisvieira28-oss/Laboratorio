#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import requests
from bs4 import BeautifulSoup

LAB="BINANCE-PERP-MARGIN-TIER-FORCED-DELEVERAGING-001"
START=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000); END_MS=int(END.timestamp()*1000)
LIST_ENDPOINTS=[
 "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query",
 "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
]
DETAIL_ENDPOINTS=[
 "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query",
 "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/detail/query",
]
REFERER="https://www.binance.com/en/support/announcement"
HEADERS={"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-SourceGate/0.1","Accept-Language":"en-US,en;q=0.9","lang":"en"}
MAX_PAGES=160
PAGE_SIZE=100
OUT=Path("bpmtfd_v01_source_gate_report.json")
SESSION=requests.Session()
SESSION.headers.update({**HEADERS,"Referer":REFERER})

def req(url, params=None, method="GET", attempts=8):
    last=None
    for i in range(attempts):
        try:
            r=SESSION.request(method,url,params=params,timeout=40,allow_redirects=True)
            if r.status_code==429:
                ra=r.headers.get("retry-after")
                try: wait=max(3,min(75,int(float(ra)))) if ra else min(75,5*(2**i))
                except: wait=min(75,5*(2**i))
                last=RuntimeError("HTTP 429")
                if i+1<attempts:
                    print(f"SOURCE_RATE_LIMIT wait={wait}s attempt={i+1}/{attempts}")
                    time.sleep(wait); continue
            if r.status_code>=500:
                last=RuntimeError(f"HTTP {r.status_code}")
                if i+1<attempts: time.sleep(min(30,2*(2**i))); continue
            return r
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(30,2*(2**i)))
    raise RuntimeError(str(last))

def iter_dicts(x:Any)->Iterable[dict]:
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from iter_dicts(v)
    elif isinstance(x,list):
        for v in x: yield from iter_dicts(v)

def norm(s:str)->str:
    return re.sub(r"\s+"," ",html.unescape(s or "")).strip()

def parse_ts(v):
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
        except: pass
    return None

def article_meta_from_list(obj):
    out=[]
    for d in iter_dicts(obj):
        code=d.get("code")
        title=d.get("title")
        rel=d.get("releaseDate") or d.get("releaseTime") or d.get("publishTime")
        z=parse_ts(rel)
        if isinstance(code,str) and re.fullmatch(r"[0-9a-fA-F]{32}",code) and isinstance(title,str) and z:
            out.append({"code":code.lower(),"title":norm(title),"release_ms":z})
    # dedupe by code
    dd={}
    for x in out: dd.setdefault(x["code"],x)
    return list(dd.values())

def list_universe():
    endpoint=None; pages=[]; articles={}; crossed=False
    for p in range(1,MAX_PAGES+1):
        r=None
        for ep in ([endpoint] if endpoint else []) + [x for x in LIST_ENDPOINTS if x!=endpoint]:
            if not ep: continue
            rr=req(ep,{"type":"1","catalogId":"49","pageNo":p,"pageSize":20})
            try: obj=rr.json()
            except: continue
            rows=article_meta_from_list(obj)
            if rr.status_code==200 and rows:
                endpoint=ep; r=rr; break
        if r is None:
            pages.append({"page":p,"ok":False}); break
        rows=article_meta_from_list(r.json())
        dates=[x["release_ms"] for x in rows]
        pages.append({"page":p,"catalogId":49,"count":len(rows),"min_release_ms":min(dates),"max_release_ms":max(dates),
                      "sha256":hashlib.sha256(r.content).hexdigest()})
        for x in rows:
            if START_MS<=x["release_ms"]<=END_MS:
                articles[x["code"]]=x
        if min(dates)<START_MS:
            crossed=True; break
        time.sleep(0.35)
        if p % 40 == 0: time.sleep(4)
    return endpoint,list(articles.values()),pages,crossed

def detail(code):
    last=None
    for ep in DETAIL_ENDPOINTS:
        r=req(ep,{"articleCode":code})
        last=r
        try:
            obj=r.json()
            if r.status_code==200 and obj:
                return ep,r,obj
        except: pass
    raise RuntimeError(f"detail failed {code} http={getattr(last,'status_code',None)}")

def strings(x):
    out=[]
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,str) and k.lower() not in {"url","link","shareurl","image","icon"}: out.append(v)
            elif isinstance(v,(dict,list)): out.extend(strings(v))
    elif isinstance(x,list):
        for v in x: out.extend(strings(v))
    return out

def extract_release(obj, fallback):
    keys={"releasedate","releasetime","publishtime","publishdate","publishedat","publishedtime"}
    vals=[]
    for d in iter_dicts(obj):
        for k,v in d.items():
            if k.lower() in keys:
                z=parse_ts(v)
                if z: vals.append(z)
    inwin=[z for z in vals if START_MS<=z<=END_MS]
    return min(inwin) if inwin else fallback

def extract_title(obj,fallback):
    for d in iter_dicts(obj):
        v=d.get("title")
        if isinstance(v,str) and v.strip(): return norm(v)
    return fallback

DATE_RE=re.compile(r"(202[3-5])[-/](\d{1,2})[-/](\d{1,2})[^0-9]{0,20}(\d{1,2}):(\d{2})\s*(?:\(UTC\)|UTC)",re.I)
DATE_RE2=re.compile(r"(202[3-5])[-/](\d{1,2})[-/](\d{1,2})[^0-9]{0,30}at\s+(\d{1,2}):(\d{2})\s*(?:\(UTC\)|UTC)",re.I)

def times_in_text(txt):
    out=[]
    for rx in (DATE_RE,DATE_RE2):
        for m in rx.finditer(txt):
            try:
                d=datetime(int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5)),tzinfo=timezone.utc)
                if START<=d<=END: out.append(d)
            except: pass
    return sorted({d.isoformat():d for d in out}.values())

def max_lev(s):
    if re.search(r"\bN/?A\b|\bNA\b",s,re.I): return None
    nums=[float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*x",s,re.I)]
    return max(nums) if nums else None

def pct(s):
    m=re.search(r"(\d+(?:\.\d+)?)\s*%",s)
    return float(m.group(1)) if m else None

def table_symbols(table,title):
    tags=table.find_all_previous(["h1","h2","h3","h4","h5","li","p","strong","div"],limit=18)
    for tag in tags:
        syms=re.findall(r"\b([A-Z0-9]{2,20}USDT)\b",tag.get_text(" ",strip=True).upper())
        if syms: return sorted(set(syms))
    syms=re.findall(r"\b([A-Z0-9]{2,20}USDT)\b",title.upper())
    return sorted(set(syms))

def table_time(table,all_times):
    tags=table.find_all_previous(["h1","h2","h3","h4","h5","li","p","strong","div"],limit=18)
    for tag in tags:
        ts=times_in_text(tag.get_text(" ",strip=True))
        if ts: return ts[-1]
    if len(all_times)==1: return all_times[0]
    return None

def parse_tightening_tables(raw_html,title,all_times):
    soup=BeautifulSoup(raw_html,"html.parser")
    ev=[]; tables=[]
    for ti,table in enumerate(soup.find_all("table")):
        syms=table_symbols(table,title)
        t=table_time(table,all_times)
        tight_rows=[]; rowcount=0
        for tr in table.find_all("tr"):
            cells=[norm(c.get_text(" ",strip=True)) for c in tr.find_all(["th","td"])]
            if len(cells)<4: continue
            rowcount+=1
            # Standard Binance tables place before leverage at 0, before MMR at 2,
            # after leverage at 3, after MMR at 5 when six columns exist.
            if len(cells)>=6:
                bl=max_lev(cells[0]); bm=pct(cells[2]); al=max_lev(cells[3]); am=pct(cells[5])
                lev_tight = bl is not None and (al is None or al < bl)
                mmr_tight = bm is not None and am is not None and am > bm + 1e-12
                if lev_tight or mmr_tight:
                    tight_rows.append({"before_lev":bl,"after_lev":al,"before_mmr":bm,"after_mmr":am})
        tables.append({"table_index":ti,"symbols":syms,"effective_utc":t.isoformat().replace("+00:00","Z") if t else None,
                       "row_count":rowcount,"tightening_rows":len(tight_rows)})
        if t and tight_rows:
            for sym in syms:
                ev.append({"symbol":sym,"effective_utc":t.isoformat().replace("+00:00","Z"),
                           "table_index":ti,"tightening_rows":len(tight_rows)})
    # de-dupe symbol/effective
    dd={}
    for x in ev: dd[(x["symbol"],x["effective_utc"])]=x
    return list(dd.values()),tables

def data_capability(symbol,effective_utc):
    d=datetime.fromisoformat(effective_utc.replace("Z","+00:00"))
    ym=d.strftime("%Y-%m")
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1m/{symbol}-1m-{ym}.zip"
    try:
        r=req(url,method="HEAD",attempts=3)
        if r.status_code not in (200,206):
            # GET range fallback; do not decode payload/outcomes.
            r=requests.get(url,headers={**HEADERS,"Range":"bytes=0-0"},timeout=25,stream=True)
        return {"url":url,"http":r.status_code,"content_length":r.headers.get("content-length"),
                "pass":r.status_code in (200,206)}
    except Exception as e:
        return {"url":url,"http":None,"pass":False,"error":type(e).__name__}

def main():
    endpoint,universe,pages,crossed=list_universe()
    print("LIST_ENUM_PAGES="+str(len(pages)))
    print("LIST_ENUM_CROSSED_PRE2023="+str(crossed))
    print("LIST_ENUM_UNIVERSE="+str(len(universe)))
    time.sleep(12)
    candidates=[]
    for x in universe:
        lo=x["title"].lower()
        if ("margin tier" in lo or "margin tiers" in lo) and ("leverage" in lo or "maintenance margin" in lo):
            candidates.append(x)
    print("LIST_ENUM_CANDIDATES="+str(len(candidates)))
    inspected=[]; eligible=[]
    for i,meta in enumerate(sorted(candidates,key=lambda x:x["release_ms"])):
        ep,r,obj=detail(meta["code"])
        ss=strings(obj)
        htmls=[s for s in ss if "<table" in s.lower()]
        joined=norm(" ".join(BeautifulSoup(s,"html.parser").get_text(" ",strip=True) if "<" in s else s for s in ss))
        title=extract_title(obj,meta["title"])
        rel=extract_release(obj,meta["release_ms"])
        lo=(title+" "+joined).lower()
        affected=bool(re.search(r"existing positions.{0,90}will be affected",lo,re.S) or "avoid any potential liquidation" in lo)
        not_affected=bool(re.search(r"existing positions.{0,90}will not be affected",lo,re.S))
        delist=("delist" in lo or "automatic settlement" in lo)
        funding=("funding rate settlement frequency" in lo or "capped funding rate multiplier" in lo)
        all_times=times_in_text(joined)
        parsed=[]; tables=[]
        for h in htmls:
            e,tb=parse_tightening_tables(h,title,all_times); parsed.extend(e); tables.extend(tb)
        dd={}
        for e in parsed: dd[(e["symbol"],e["effective_utc"])]=e
        parsed=list(dd.values())
        reasons=[]
        if not affected: reasons.append("existing_positions_affected_not_proven")
        if not_affected: reasons.append("existing_positions_explicitly_not_affected")
        if delist: reasons.append("delisting_or_auto_settlement_confound")
        if funding: reasons.append("funding_parameter_confound")
        if not parsed: reasons.append("no_unambiguous_tightening_table_event")
        valid_events=[]
        if not reasons:
            for e in parsed:
                eff=datetime.fromisoformat(e["effective_utc"].replace("Z","+00:00"))
                if not (START<=eff<=END): continue
                if rel>=int(eff.timestamp()*1000): continue
                cap=data_capability(e["symbol"],e["effective_utc"])
                ee={**e,"article_code":meta["code"],"official_title":title,"release_ms":rel,"data_capability":cap}
                if cap["pass"]: valid_events.append(ee)
        rec={"code":meta["code"],"title":title,"release_ms":rel,"detail_endpoint":ep,
             "source_sha256":hashlib.sha256(r.content).hexdigest(),"affected":affected,"not_affected":not_affected,
             "delist_confound":delist,"funding_confound":funding,"effective_times":[d.isoformat().replace("+00:00","Z") for d in all_times],
             "tightening_table_events":len(parsed),"eligible_events":len(valid_events),
             "reject":";".join(reasons) if reasons else None,"tables":tables}
        inspected.append(rec); eligible.extend(valid_events)
        print(f"DETAIL_PROGRESS={i+1}/{len(candidates)} code={meta['code']} eligible={len(valid_events)} reject={rec['reject']}")
        time.sleep(1.1)

    # de-dupe exact asset-event
    dd={}
    for e in eligible: dd[(e["article_code"],e["effective_utc"],e["symbol"])]=e
    eligible=list(dd.values())
    clusters={}
    for e in eligible:
        k=e["article_code"]+"@"+e["effective_utc"]
        clusters.setdefault(k,[]).append(e)
    assets=sorted({e["symbol"] for e in eligible})
    years=sorted({datetime.fromisoformat(e["effective_utc"].replace("Z","+00:00")).year for e in eligible})
    n=len(eligible); max_cluster=max((len(v) for v in clusters.values()),default=0)
    conc=(max_cluster/n if n else 1.0)
    complete=crossed
    gate=(complete and len(clusters)>=12 and n>=20 and len(assets)>=8 and conc<=0.35 and len(years)>=2)
    if gate: verdict="SOURCE_GATE_PASS"
    elif complete: verdict="INSUFFICIENT_SAMPLE"
    else: verdict="SOURCE_BLOCKED"
    report={
      "family":LAB,"verdict":verdict,"outcome_access":"NONE","calendar":"2023-2025; 2026 EXCLUDED",
      "list_endpoint":endpoint,"archive_crossed_pre2023":crossed,"list_pages":pages,
      "official_articles_in_window":len(universe),"candidate_articles":len(candidates),"inspected_articles":len(inspected),
      "eligible_asset_events":n,"independent_clusters":len(clusters),"unique_contracts":len(assets),
      "years":years,"max_cluster_concentration":conc,
      "sample_gates":{"clusters_ge_12":len(clusters)>=12,"asset_events_ge_20":n>=20,
                      "unique_contracts_ge_8":len(assets)>=8,"max_cluster_le_35pct":conc<=0.35,
                      "years_ge_2":len(years)>=2},
      "eligible_events":sorted(eligible,key=lambda e:(e["effective_utc"],e["symbol"])),
      "inspected_articles":inspected,
      "safety":{"market_values_opened":False,"prices_opened":False,"returns_opened":False,
                "volatility_opened":False,"volume_opened":False,"funding_values_opened":False,
                "liquidation_values_opened":False,"pnl_opened":False,"authenticated_api":False,"mutation":False}
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BPMTFD_SOURCE_GATE_RESULT="+verdict)
    print("OFFICIAL_ARTICLES_IN_WINDOW="+str(len(universe)))
    print("CANDIDATE_ARTICLES="+str(len(candidates)))
    print("ELIGIBLE_ASSET_EVENTS="+str(n))
    print("INDEPENDENT_CLUSTERS="+str(len(clusters)))
    print("UNIQUE_CONTRACTS="+str(len(assets)))
    print("YEARS="+json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION="+str(conc))
    print("SAFETY: no market values/outcomes opened")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
