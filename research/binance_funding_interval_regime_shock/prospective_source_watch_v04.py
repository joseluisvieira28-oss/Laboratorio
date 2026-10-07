#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import requests
from bs4 import BeautifulSoup

LAB="BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001"
START=datetime(2026,10,7,4,44,37,tzinfo=timezone.utc)
END=datetime.now(timezone.utc)
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
HEADERS={"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-BFIRS/0.1","Accept-Language":"en-US,en;q=0.9","lang":"en"}
MAX_PAGES=180
OUT=Path("bfirs_v04_prospective_source_report.json")
SESSION=requests.Session(); SESSION.headers.update({**HEADERS,"Referer":REFERER})

def req(url, params=None, method="GET", attempts=8):
    last=None
    for i in range(attempts):
        try:
            r=SESSION.request(method,url,params=params,timeout=45,allow_redirects=True)
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
        code=d.get("code"); title=d.get("title")
        rel=d.get("releaseDate") or d.get("releaseTime") or d.get("publishTime")
        z=parse_ts(rel)
        if isinstance(code,str) and re.fullmatch(r"[0-9a-fA-F]{32}",code) and isinstance(title,str) and z:
            out.append({"code":code.lower(),"title":norm(title),"release_ms":z})
    dd={}
    for x in out: dd.setdefault(x["code"],x)
    return list(dd.values())

def list_universe():
    endpoint=None; pages=[]; articles={}; crossed=False
    for p in range(1,MAX_PAGES+1):
        chosen=None; rows=[]
        for ep in ([endpoint] if endpoint else []) + [x for x in LIST_ENDPOINTS if x!=endpoint]:
            if not ep: continue
            rr=req(ep,{"type":"1","catalogId":"49","pageNo":p,"pageSize":20})
            try: obj=rr.json()
            except: continue
            rrrows=article_meta_from_list(obj)
            if rr.status_code==200 and rrrows:
                endpoint=ep; chosen=rr; rows=rrrows; break
        if chosen is None:
            pages.append({"page":p,"ok":False}); break
        dates=[x["release_ms"] for x in rows]
        pages.append({"page":p,"count":len(rows),"min_release_ms":min(dates),"max_release_ms":max(dates),
                      "sha256":hashlib.sha256(chosen.content).hexdigest()})
        for x in rows:
            if START_MS<x["release_ms"]<=END_MS: articles[x["code"]]=x
        if min(dates)<START_MS:
            crossed=True; break
        time.sleep(0.25)
        if p%35==0: time.sleep(3)
    return endpoint,list(articles.values()),pages,crossed

def detail(code):
    last=None
    for ep in DETAIL_ENDPOINTS:
        r=req(ep,{"articleCode":code})
        last=r
        try:
            obj=r.json()
            if r.status_code==200 and obj: return ep,r,obj
        except: pass
    raise RuntimeError(f"detail failed {code} http={getattr(last,'status_code',None)}")

def render_body_json(raw):
    if not isinstance(raw,str) or not raw.strip(): return ""
    try: root=json.loads(raw)
    except Exception: return raw if "<" in raw else html.escape(raw)
    def rec(x):
        if isinstance(x,list): return "".join(rec(v) for v in x)
        if not isinstance(x,dict): return ""
        if x.get("node")=="text": return html.escape(str(x.get("text","")))
        tag=x.get("tag"); inner=rec(x.get("child",[]))
        if isinstance(tag,str) and re.fullmatch(r"[A-Za-z0-9]+",tag):
            return f"<{tag}>{inner}</{tag}>"
        return inner
    return rec(root)

def body_plain(raw):
    return BeautifulSoup(render_body_json(raw),"html.parser").get_text(" ",strip=True)

DATE_PATTERNS=[
 re.compile(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\s+(?:at\s+)?(\d{1,2}):(\d{2})\s*(?:\(UTC\)|UTC)",re.I),
 re.compile(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})[^0-9]{0,20}(\d{1,2}):(\d{2})\s*(?:\(UTC\)|UTC)",re.I),
]
def times_in_text(txt):
    out=[]
    for rx in DATE_PATTERNS:
        for m in rx.finditer(txt):
            try:
                d=datetime(int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5)),tzinfo=timezone.utc)
                if START<=d<=END: out.append((m.start(),d))
            except: pass
    dd={}
    for pos,d in out: dd[(pos,d.isoformat())]=(pos,d)
    return sorted(dd.values(),key=lambda x:x[0])

HOUR_WORDS={"one":1,"two":2,"three":3,"four":4,"six":6,"eight":8,"twelve":12,"twenty-four":24}
HOUR_RX=r"(one|two|three|four|six|eight|twelve|twenty-four|\d{1,2})"
TRANS_RE=re.compile(
    rf"(?:funding(?:\s+rate)?\s+(?:settlement\s+)?frequency|funding\s+interval)"
    rf".{{0,240}}?from\s+every\s+{HOUR_RX}\s+hours?"
    rf".{{0,120}}?to\s+every\s+{HOUR_RX}\s+hours?",
    re.I|re.S
)
ALT_TRANS_RE=re.compile(
    rf"from\s+every\s+{HOUR_RX}\s+hours?"
    rf".{{0,120}}?to\s+every\s+{HOUR_RX}\s+hours?",
    re.I|re.S
)

def hour_num(s):
    s=s.lower()
    return HOUR_WORDS.get(s,int(s) if s.isdigit() else None)

def extract_transitions(text):
    found=[]
    for rx in (TRANS_RE,ALT_TRANS_RE):
        for m in rx.finditer(text):
            groups=m.groups()
            old=hour_num(groups[-2]); new=hour_num(groups[-1])
            if old and new:
                found.append({"start":m.start(),"end":m.end(),"old_hours":old,"new_hours":new,"match":norm(m.group(0))[:500]})
    dd={}
    for x in found: dd[(x["start"],x["old_hours"],x["new_hours"])]=x
    return sorted(dd.values(),key=lambda x:x["start"])

def nearest_effective(text, tr, pub_ms):
    ts=times_in_text(text)
    pub=datetime.fromtimestamp(pub_ms/1000,tz=timezone.utc)
    # Prefer timestamps after transition phrase, within 6000 chars, and after publication.
    after=[(pos,d) for pos,d in ts if pos>=tr["start"] and pos<=tr["end"]+6000 and d>pub]
    if after: return after[0][1]
    # fallback first post-publication timestamp in article
    cand=[d for _,d in ts if d>pub]
    return cand[0] if cand else None

def extract_symbols(text,title):
    syms=sorted(set(re.findall(r"\b([A-Z0-9]{2,25}USDT)\b",(title+" "+text).upper())))
    # Remove generic references if present only in educational/example language later;
    # eligibility is conservative: candidate article must itself be about a frequency change.
    return syms

def source_capability(symbol, eff):
    ym=eff.strftime("%Y-%m")
    urls={
      "premium_index_1m":f"https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{symbol}/1m/{symbol}-1m-{ym}.zip",
      "funding_rate":f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip",
    }
    out={}
    for k,u in urls.items():
        try:
            r=req(u,method="HEAD",attempts=3)
            if r.status_code not in (200,206):
                # Metadata-only range request fallback; payload is not decoded.
                r=SESSION.get(u,headers={**HEADERS,"Range":"bytes=0-0"},timeout=25,stream=True)
            out[k]={"url":u,"http":r.status_code,"content_length":r.headers.get("content-length"),"pass":r.status_code in (200,206)}
        except Exception as e:
            out[k]={"url":u,"http":None,"pass":False,"error":type(e).__name__}
    out["pass"]=all(v["pass"] for k,v in out.items() if k!="pass")
    return out

def main():
    endpoint,universe,pages,crossed=list_universe()
    print("LIST_ENUM_PAGES="+str(len(pages)))
    print("LIST_ENUM_CROSSED_PRE_BOUNDARY="+str(crossed))
    print("LIST_ENUM_UNIVERSE="+str(len(universe)))
    candidates=[x for x in universe if "funding" in x["title"].lower()]
    print("TITLE_FUNDING_CANDIDATES="+str(len(candidates)))
    time.sleep(8)

    inspected=[]; eligible=[]
    for i,meta in enumerate(sorted(candidates,key=lambda x:x["release_ms"])):
        ep,r,obj=detail(meta["code"])
        data=obj.get("data",{}) if isinstance(obj,dict) else {}
        title=norm(data.get("title") or meta["title"]) if isinstance(data,dict) else meta["title"]
        raw=data.get("body","") if isinstance(data,dict) else ""
        text=norm(title+" "+body_plain(raw))
        lo=text.lower()
        launch=bool(re.search(r"\bwill launch\b|\blaunch time\b|at the time of launch",lo))
        delist=("delist" in lo or "automatic settlement" in lo)
        generic_rule=bool("if the funding rate" in lo and ("consecutive cycles" in lo or "previous funding rate settlement" in lo))
        transitions=extract_transitions(text)
        syms=extract_symbols(text,title)
        article_events=[]
        reject_reasons=[]

        if launch: reject_reasons.append("listing_launch_specification")
        if delist: reject_reasons.append("delisting_or_auto_settlement")
        if generic_rule and not transitions: reject_reasons.append("generic_dynamic_rule_no_fixed_transition")
        if not transitions: reject_reasons.append("no_explicit_interval_transition")
        if not syms: reject_reasons.append("no_usdt_contract")

        if not reject_reasons:
            for tr in transitions:
                if tr["new_hours"] >= tr["old_hours"]:
                    continue
                eff=nearest_effective(text,tr,meta["release_ms"])
                if not eff: continue
                if meta["release_ms"] >= int(eff.timestamp()*1000): continue
                # All explicitly named USDT contracts in a dedicated interval-change article
                # inherit the same article-level transition/effective timestamp.
                for sym in syms:
                    cap=source_capability(sym,eff)
                    if cap["pass"]:
                        article_events.append({
                          "article_code":meta["code"],"official_title":title,
                          "release_ms":meta["release_ms"],
                          "effective_utc":eff.isoformat().replace("+00:00","Z"),
                          "symbol":sym,"old_interval_hours":tr["old_hours"],"new_interval_hours":tr["new_hours"],
                          "capability":cap
                        })
                # One fixed shorter-interval transition per article is enough; avoid
                # duplicating the same symbols from repeated explanatory phrasing.
                if article_events: break

        dd={}
        for e in article_events:
            dd[(e["article_code"],e["effective_utc"],e["symbol"],e["old_interval_hours"],e["new_interval_hours"])]=e
        article_events=list(dd.values())
        eligible.extend(article_events)
        rec={
          "code":meta["code"],"title":title,"release_ms":meta["release_ms"],
          "detail_endpoint":ep,"source_sha256":hashlib.sha256(r.content).hexdigest(),
          "launch":launch,"delist":delist,"generic_rule":generic_rule,
          "transitions":transitions,"symbols":syms,
          "eligible_events":len(article_events),
          "reject":";".join(reject_reasons) if reject_reasons else None
        }
        inspected.append(rec)
        print(f"DETAIL_PROGRESS={i+1}/{len(candidates)} code={meta['code']} transitions={len(transitions)} symbols={len(syms)} eligible={len(article_events)} reject={rec['reject']}")
        time.sleep(0.8)

    dd={}
    for e in eligible:
        dd[(e["article_code"],e["effective_utc"],e["symbol"],e["old_interval_hours"],e["new_interval_hours"])]=e
    eligible=list(dd.values())
    clusters={}
    for e in eligible:
        k=f"{e['article_code']}@{e['effective_utc']}@{e['old_interval_hours']}to{e['new_interval_hours']}"
        clusters.setdefault(k,[]).append(e)
    assets=sorted({e["symbol"] for e in eligible})
    years=sorted({datetime.fromisoformat(e["effective_utc"].replace("Z","+00:00")).year for e in eligible})
    n=len(eligible); max_cluster=max((len(v) for v in clusters.values()),default=0)
    conc=max_cluster/n if n else 1.0
    complete=crossed
    gates={
      "clusters_ge_12":len(clusters)>=12,
      "asset_events_ge_20":n>=20,
      "unique_contracts_ge_8":len(assets)>=8,
      "max_cluster_le_35pct":conc<=0.35,
      "all_capabilities_pass":all(e["capability"]["pass"] for e in eligible) if eligible else True,
    }
    if complete and all(gates.values()): verdict="PROSPECTIVE_SOURCE_READY"
    elif complete: verdict="PROSPECTIVE_ACCUMULATING"
    else: verdict="PROSPECTIVE_SOURCE_BLOCKED"

    report={
      "family":LAB,"verdict":verdict,"outcome_access":"NONE",
      "calendar":"strictly after 2026-10-07T04:44:37Z; prospective only","list_endpoint":endpoint,
      "archive_crossed_pre_boundary":crossed,"list_pages":pages,
      "official_articles_in_window":len(universe),"funding_title_candidates":len(candidates),
      "eligible_asset_events":n,"independent_clusters":len(clusters),"unique_contracts":len(assets),
      "years":years,"max_cluster_concentration":conc,"sample_gates":gates,
      "eligible_events":sorted(eligible,key=lambda e:(e["effective_utc"],e["symbol"])),
      "inspected_articles":inspected,
      "safety":{
        "premium_values_opened":False,"funding_values_opened":False,"prices_opened":False,
        "returns_opened":False,"volume_opened":False,"volatility_opened":False,
        "liquidation_values_opened":False,"oi_opened":False,"pnl_opened":False,
        "authenticated_api":False,"mutation":False
      }
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BFIRS_V04_PROSPECTIVE_SOURCE_RESULT="+verdict)
    print("OFFICIAL_ARTICLES_IN_WINDOW="+str(len(universe)))
    print("FUNDING_TITLE_CANDIDATES="+str(len(candidates)))
    print("ELIGIBLE_ASSET_EVENTS="+str(n))
    print("INDEPENDENT_CLUSTERS="+str(len(clusters)))
    print("UNIQUE_CONTRACTS="+str(len(assets)))
    print("YEARS="+json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION="+str(conc))
    print("SAMPLE_GATES="+json.dumps(gates,sort_keys=True))
    print("SAFETY: no premium/funding/price/return/volume/volatility/OI/liquidation/PnL values opened")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
