#!/usr/bin/env python3
from __future__ import annotations
import json, re, time, hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

LAB="OKX-FUNDING-INTERVAL-BASIS-REPLICATION-001"
BASE="https://www.okx.com"
ARCHIVE_ORIGIN="https://www.okx.com/en-gb"
ARCHIVE="/help/section/announcements-trading-updates"
START=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)
OUT=Path("okxfibr_v01_source_gate_report.json")
S=requests.Session()
S.headers.update({
    "User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-OKXFIBR/0.1",
    "Accept-Language":"en-US,en;q=0.9",
})
MONTHS={m:i for i,m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],1
)}
MONTHS.update({m:i for i,m in enumerate(
    ["January","February","March","April","May","June","July","August","September","October","November","December"],1
)})
HOUR_WORDS={"one":1,"two":2,"three":3,"four":4,"six":6,"eight":8,"twelve":12,"twenty-four":24}
INTERVAL_RE=re.compile(r"(?:every\s+)?(one|two|three|four|six|eight|twelve|twenty-four|\d{1,2})\s*hours?",re.I)
DATE_TEXT_RE=re.compile(
    r"(?:Published\s+on\s+)?([A-Z][a-z]{2,8})\s+(\d{1,2}),?\s+(20\d{2})"
    r"|(?:Published\s+on\s+)?(\d{1,2})\s+([A-Z][a-z]{2,8})\s+(20\d{2})",
    re.I
)
ISO_RE=re.compile(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")

def req(url,attempts=7):
    last=None
    for i in range(attempts):
        try:
            r=S.get(url,timeout=45,allow_redirects=True)
            if r.status_code==429:
                wait=min(45,2**(i+1)); print(f"RATE_LIMIT wait={wait}s"); time.sleep(wait); last=RuntimeError("429"); continue
            if r.status_code>=500:
                last=RuntimeError(f"http_{r.status_code}"); time.sleep(min(20,2**i)); continue
            r.raise_for_status()
            return r
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(20,2**i))
    raise RuntimeError(str(last))

def parse_date_text(txt):
    m=DATE_TEXT_RE.search(txt or "")
    if not m: return None
    try:
        if m.group(1):
            mon=MONTHS[m.group(1).title()[:3]] if len(m.group(1))<=3 else MONTHS[m.group(1).title()]
            day=int(m.group(2)); year=int(m.group(3))
        else:
            day=int(m.group(4))
            name=m.group(5).title()
            mon=MONTHS[name[:3]] if len(name)<=3 else MONTHS[name]
            year=int(m.group(6))
        return datetime(year,mon,day,tzinfo=timezone.utc)
    except: return None

def article_links_from_listing(html):
    soup=BeautifulSoup(html,"html.parser")
    out={}
    for a in soup.find_all("a",href=True):
        href=a.get("href","").strip()
        title=" ".join(a.get_text(" ",strip=True).split())
        if not title or len(title)<12: continue
        if "/help/" not in href: continue
        if "/help/section/" in href or "/help/category/" in href: continue
        url=urljoin(BASE,href)
        # Canonicalize locale-prefixed OKX links to global /help when possible.
        p=urlparse(url)
        path=p.path
        m=re.search(r"/help/([^/?#]+)$",path)
        if not m: continue
        slug=m.group(1)
        if slug in {"section","category"}: continue
        canon=f"{BASE}/help/{slug}"
        # Pull nearby card text to recover listing date.
        card=a
        for _ in range(4):
            if card.parent is None: break
            card=card.parent
            t=" ".join(card.get_text(" ",strip=True).split())
            if "Published" in t and len(t)<1200: break
        nearby=" ".join(card.get_text(" ",strip=True).split()) if card else title
        d=parse_date_text(nearby)
        prev=out.get(canon)
        if prev is None or len(title)>len(prev["title"]):
            out[canon]={"url":canon,"title":title,"listing_date":d.isoformat() if d else None}
    return list(out.values())

def enumerate_archive():
    articles={}; pages=[]; crossed=False; empty_streak=0
    for page in range(1,81):
        url=ARCHIVE_ORIGIN+ARCHIVE if page==1 else f"{ARCHIVE_ORIGIN}{ARCHIVE}/page/{page}"
        r=req(url)
        rows=article_links_from_listing(r.text)
        dates=[datetime.fromisoformat(x["listing_date"]) for x in rows if x["listing_date"]]
        pages.append({
            "page":page,"url":url,"links":len(rows),
            "min_listing_date":min(dates).isoformat() if dates else None,
            "max_listing_date":max(dates).isoformat() if dates else None,
            "sha256":hashlib.sha256(r.content).hexdigest()
        })
        for x in rows: articles.setdefault(x["url"],x)
        if dates and min(dates)<START:
            crossed=True; break
        if not rows: empty_streak+=1
        else: empty_streak=0
        if empty_streak>=2: break
        time.sleep(0.25)
    return list(articles.values()),pages,crossed

def exact_publish(obj,soup,listing_date):
    # JSON-LD / embedded ISO timestamps only; date-only text is insufficient for T0.
    for sc in soup.find_all("script"):
        txt=sc.string or sc.get_text(" ",strip=True)
        if not txt: continue
        if "datePublished" in txt or "publish" in txt.lower():
            for m in ISO_RE.finditer(txt):
                try:
                    d=datetime.fromisoformat(m.group(0).replace("Z","+00:00"))
                    if START-timedelta(days=30)<=d<=END+timedelta(days=30):
                        return d.astimezone(timezone.utc)
                except: pass
    for tag in soup.find_all(["meta","time"]):
        vals=[tag.get("content"),tag.get("datetime")]
        for v in vals:
            if not v or not isinstance(v,str): continue
            mm=ISO_RE.search(v)
            if mm:
                try: return datetime.fromisoformat(mm.group(0).replace("Z","+00:00")).astimezone(timezone.utc)
                except: pass
    return None

# avoid dependency above in exact_publish branch
from datetime import timedelta

def hnum(s):
    s=s.strip().lower()
    return HOUR_WORDS.get(s,int(s) if s.isdigit() else None)

def parse_rows_for_events(soup,title):
    events=[]
    # Prefer structured tables.
    for table in soup.find_all("table"):
        rows=[]
        for tr in table.find_all("tr"):
            cells=[" ".join(c.get_text(" ",strip=True).split()) for c in tr.find_all(["th","td"])]
            if cells: rows.append(cells)
        if len(rows)<2: continue
        header=" | ".join(rows[0]).lower()
        if "funding" not in header or "interval" not in header: continue
        for row in rows[1:]:
            txt=" | ".join(row)
            syms=sorted(set(re.findall(r"\b([A-Z0-9]{2,30})USDT\b",txt.upper())))
            ints=[hnum(m.group(1)) for m in INTERVAL_RE.finditer(txt)]
            ints=[x for x in ints if x]
            if not syms or len(ints)<2: continue
            old,new=ints[0],ints[1]
            if new>=old: continue
            # Date + UTC time may be in this row or inherited from nearby section text.
            row_date=parse_date_text(txt)
            tm=re.search(r"(\d{1,2}):(\d{2})\s*(?:am|pm)?\s*(?:\(UTC\)|UTC)",txt,re.I)
            hour=minute=None
            if tm:
                hour=int(tm.group(1)); minute=int(tm.group(2))
                if re.search(r"pm",tm.group(0),re.I) and hour<12: hour+=12
                if re.search(r"am",tm.group(0),re.I) and hour==12: hour=0
            events.append({"symbols":syms,"old_hours":old,"new_hours":new,
                           "row_text":txt,"row_date":row_date,"hour":hour,"minute":minute})
    return events

def article_detail(meta):
    r=req(meta["url"])
    soup=BeautifulSoup(r.text,"html.parser")
    title=(soup.find("h1").get_text(" ",strip=True) if soup.find("h1") else meta["title"])
    full=" ".join(soup.get_text(" ",strip=True).split())
    pub=exact_publish(r.text,soup,meta.get("listing_date"))
    events=parse_rows_for_events(soup,title)

    # Fallback for the known common prose/table pattern where dates are section headings
    # and the row itself carries contract + before/after + adjustment time.
    if events:
        # Gather article-level date candidates in order.
        date_candidates=[]
        for m in DATE_TEXT_RE.finditer(full):
            d=parse_date_text(m.group(0))
            if d and START<=d<=END: date_candidates.append((m.start(),d))
        for e in events:
            if e["row_date"] is None:
                # We cannot safely map a table row to a date without structure.
                # Leave unresolved; provenance gate will reject.
                pass

    return r,soup,title,full,pub,events

def candidate_title(title):
    x=(title or "").lower()
    return "funding" in x and ("interval" in x or "settlement" in x) and ("adjust" in x or "change" in x)

def main():
    universe,pages,crossed=enumerate_archive()
    print("ARCHIVE_PAGES="+str(len(pages)))
    print("ARCHIVE_CROSSED_PRE2023="+str(crossed))
    print("ARCHIVE_ARTICLES="+str(len(universe)))
    candidates=[x for x in universe if candidate_title(x["title"])]
    print("CANDIDATE_ARTICLES="+str(len(candidates)))

    inspected=[]; eligible=[]
    for i,meta in enumerate(sorted(candidates,key=lambda x:x.get("listing_date") or "")):
        try:
            r,soup,title,full,pub,parsed=article_detail(meta)
        except Exception as e:
            inspected.append({**meta,"error":f"{type(e).__name__}:{e}"})
            continue
        launch=bool(re.search(r"\bto list\b|\bwill list\b|\blaunch\b",title,re.I))
        delist=bool(re.search(r"delist|automatic settlement",title+" "+full,re.I))
        rec={**meta,"title":title,"source_sha256":hashlib.sha256(r.content).hexdigest(),
             "exact_publish_utc":pub.isoformat().replace("+00:00","Z") if pub else None,
             "launch":launch,"delist":delist,"parsed_rows":len(parsed),"eligible_events":0}
        if not launch and not delist and pub and START<=pub<=END:
            for e in parsed:
                # Exact effective date+time is mandatory; unresolved rows are excluded.
                if e["row_date"] is None or e["hour"] is None: continue
                eff=e["row_date"].replace(hour=e["hour"],minute=e["minute"] or 0)
                if eff<=pub: continue
                for base in e["symbols"]:
                    sym=base+"USDT"
                    eligible.append({
                        "article_url":meta["url"],"official_title":title,
                        "publish_utc":pub.isoformat().replace("+00:00","Z"),
                        "effective_utc":eff.isoformat().replace("+00:00","Z"),
                        "symbol":sym,"old_interval_hours":e["old_hours"],"new_interval_hours":e["new_hours"]
                    })
                    rec["eligible_events"]+=1
        inspected.append(rec)
        print(f"DETAIL_PROGRESS={i+1}/{len(candidates)} parsed={len(parsed)} eligible={rec['eligible_events']} pub={rec['exact_publish_utc']} title={title[:100]}")
        time.sleep(0.4)

    dd={}
    for e in eligible:
        dd[(e["article_url"],e["effective_utc"],e["symbol"],e["old_interval_hours"],e["new_interval_hours"])]=e
    eligible=list(dd.values())
    clusters=defaultdict(list)
    for e in eligible:
        k=f"{e['article_url']}@{e['effective_utc']}@{e['old_interval_hours']}to{e['new_interval_hours']}"
        clusters[k].append(e)
    assets=sorted({e["symbol"] for e in eligible})
    years=sorted({datetime.fromisoformat(e["effective_utc"].replace("Z","+00:00")).year for e in eligible})
    n=len(eligible)
    maxcl=max((len(v) for v in clusters.values()),default=0)
    conc=maxcl/n if n else 1.0
    gates={
        "clusters_ge_12":len(clusters)>=12,
        "asset_events_ge_20":n>=20,
        "unique_contracts_ge_8":len(assets)>=8,
        "years_ge_2":len(years)>=2,
        "max_cluster_le_35pct":conc<=0.35,
        "canonical_provenance_resolved":all(e["article_url"].startswith("https://www.okx.com/help/") for e in eligible) if eligible else False,
    }
    if crossed and all(gates.values()): verdict="EXTERNAL_SOURCE_PASS"
    elif crossed: verdict="EXTERNAL_INSUFFICIENT_SAMPLE"
    else: verdict="EXTERNAL_SOURCE_BLOCKED"
    report={
        "family":LAB,"verdict":verdict,"outcome_access":"NONE",
        "calendar":"2023-2025","archive_pages":pages,"archive_crossed_pre2023":crossed,
        "archive_articles":len(universe),"candidate_articles":len(candidates),
        "eligible_asset_events":n,"independent_clusters":len(clusters),"unique_contracts":len(assets),
        "years":years,"max_cluster_concentration":conc,"sample_gates":gates,
        "eligible_events":sorted(eligible,key=lambda e:(e["effective_utc"],e["symbol"])),
        "inspected_articles":inspected,
        "safety":{"mark_values_opened":False,"index_values_opened":False,"funding_values_opened":False,
                  "returns_opened":False,"pnl_opened":False,"authenticated_api":False,"mutation":False}
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("OKXFIBR_SOURCE_RESULT="+verdict)
    print("ELIGIBLE_ASSET_EVENTS="+str(n))
    print("INDEPENDENT_CLUSTERS="+str(len(clusters)))
    print("UNIQUE_CONTRACTS="+str(len(assets)))
    print("YEARS="+json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION="+str(conc))
    print("SAMPLE_GATES="+json.dumps(gates,sort_keys=True))
    print("SAFETY: no mark/index/funding/return/PnL values opened")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
