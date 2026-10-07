#!/usr/bin/env python3
from __future__ import annotations
import json,re,time,hashlib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone,timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup

LAB="BITGET-FUNDING-INTERVAL-PREMIUM-REPLICATION-001"
BASE="https://www.bitget.com"
SECTION="/support/sections/12508313445234"
START=datetime(2024,1,1,tzinfo=timezone.utc)
END=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)
OUT=Path("bgfipr_v01_source_gate_report.json")
DATE_RE=re.compile(r"(20\d{2})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})")
ARTICLE_RE=re.compile(r"/support/articles/(\d+)")
INTERVAL_RE=re.compile(
    r"(?:funding(?:\s+rate)?\s*(?:interval|frequency)|funding\s+rate).{0,220}?"
    r"(?:adjusted\s+)?from\s+every\s+(1|2|4|8|12|24)\s*hour\(s\)|"
    r"(?:funding(?:\s+rate)?\s*(?:interval|frequency)|funding\s+rate).{0,220}?"
    r"(?:adjusted\s+)?from\s+every\s+(1|2|4|8|12|24)\s*hours?",
    re.I|re.S
)
FROM_TO_RE=re.compile(
    r"from\s+every\s+(1|2|4|8|12|24)\s*hour(?:\(s\)|s?)\s+to\s+every\s+"
    r"(1|2|4|8|12|24)\s*hour(?:\(s\)|s?)",re.I
)
AFFECTED_RE=re.compile(r"affected\s+trading\s+pair\s*:\s*([A-Z0-9_,/\- ]+)",re.I)
USDT_RE=re.compile(r"\b([A-Z0-9]{1,30}USDT)\b")
ISO_EFF_RE=re.compile(
    r"(20\d{2})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s*[（(]?UTC\s*([+-])\s*(\d{1,2})[）)]?",
    re.I
)
MONTHS={m:i for i,m in enumerate(
    ["January","February","March","April","May","June","July","August","September","October","November","December"],1
)}
TEXT_EFF_RE=re.compile(
    r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(20\d{2}).{0,30}?"
    r"(\d{1,2}):(\d{2})\s*[（(]?UTC\s*([+-])\s*(\d{1,2})[）)]?",re.I
)

HEADERS={"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-BGFIPR/0.1","Accept-Language":"en-US,en;q=0.9"}

def get(url,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=requests.get(url,headers=HEADERS,timeout=35)
            if r.status_code==429:
                last=RuntimeError("429"); time.sleep(min(15,2**i)); continue
            if r.status_code>=500:
                last=RuntimeError(f"http_{r.status_code}"); time.sleep(min(10,2**i)); continue
            r.raise_for_status(); return r
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(8,2**i))
    raise RuntimeError(str(last))

def parse_page(html):
    soup=BeautifulSoup(html,"html.parser")
    rows={}
    for a in soup.find_all("a",href=True):
        href=a.get("href","")
        m=ARTICLE_RE.search(href)
        if not m: continue
        aid=m.group(1)
        card=a; best=""
        for _ in range(5):
            txt=" ".join(card.get_text(" ",strip=True).split())
            if len(txt)>len(best): best=txt
            if DATE_RE.search(txt): break
            if card.parent is None: break
            card=card.parent
        dm=DATE_RE.search(best)
        dt=None
        if dm:
            dt=datetime(int(dm.group(1)),int(dm.group(2)),int(dm.group(3)),int(dm.group(4)),int(dm.group(5)),tzinfo=timezone.utc)
        title=" ".join(a.get_text(" ",strip=True).split())
        rows[aid]={"id":aid,"url":BASE+href if href.startswith("/") else href,
                   "title":title,"listed_utc":dt.isoformat().replace("+00:00","Z") if dt else None}
    return list(rows.values())

def enumerate_archive():
    allrows={}; pages=[]; crossed=False
    for p in range(1,121):
        u=f"{BASE}{SECTION}/{p}"
        r=get(u)
        rows=parse_page(r.text)
        dates=[datetime.fromisoformat(x["listed_utc"].replace("Z","+00:00")) for x in rows if x["listed_utc"]]
        pages.append({"page":p,"count":len(rows),"ids":[x["id"] for x in rows],
                      "min_date":min(dates).isoformat() if dates else None,
                      "max_date":max(dates).isoformat() if dates else None,
                      "sha256":hashlib.sha256(r.content).hexdigest()})
        for x in rows: allrows[x["id"]]=x
        print(f"ARCHIVE_PAGE={p} rows={len(rows)} min={min(dates).isoformat() if dates else None} max={max(dates).isoformat() if dates else None}")
        if dates and min(dates)<START:
            crossed=True; break
        if not rows: break
        time.sleep(0.08)
    return list(allrows.values()),pages,crossed

def candidate_text(txt):
    z=txt.lower()
    return (
        "funding" in z and
        ("interval" in z or "frequency" in z) and
        ("adjust" in z or "adjustment" in z) and
        "perpetual" in z
    )

def parse_effective(txt):
    vals=[]
    # Primary modern format: explicit Adjustment time field.
    rx_adj=re.compile(
        r"Adjustment\s+time\s*:\s*(20\\d{2})-(\\d{2})-(\\d{2})\\s+(\\d{1,2}):(\\d{2})\\s*[（(]?UTC\\s*([+-])\\s*(\\d{1,2})[）)]?",
        re.I
    )
    for m in rx_adj.finditer(txt):
        y,mo,d,h,mi=int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5))
        off=int(m.group(7)); off=off if m.group(6)=="+" else -off
        try:
            vals.append(datetime(y,mo,d,h,mi,tzinfo=timezone(timedelta(hours=off))).astimezone(timezone.utc))
        except: pass
    if vals:
        return sorted({x.isoformat():x for x in vals}.values())

    # Older prose format: "... adjust ... on April 29, 2025, at 20:00 (UTC+8)".
    rx_old=re.compile(
        r"adjust.{0,220}?on\\s+([A-Z][a-z]+)\\s+(\\d{1,2}),?\\s+(20\\d{2}).{0,45}?"
        r"(\\d{1,2}):(\\d{2})\\s*[（(]?UTC\\s*([+-])\\s*(\\d{1,2})[）)]?",
        re.I|re.S
    )
    for m in rx_old.finditer(txt):
        mon=MONTHS.get(m.group(1).title())
        if not mon: continue
        d,y,h,mi=int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5))
        off=int(m.group(7)); off=off if m.group(6)=="+" else -off
        try:
            vals.append(datetime(y,mon,d,h,mi,tzinfo=timezone(timedelta(hours=off))).astimezone(timezone.utc))
        except: pass
    return sorted({x.isoformat():x for x in vals}.values())

def parse_intervals(txt):
    return sorted({(int(m.group(1)),int(m.group(2))) for m in FROM_TO_RE.finditer(txt)})

def parse_symbols(txt,title):
    vals=set(USDT_RE.findall((title+" "+txt).upper()))
    # remove obvious non-pair references if any
    return sorted(vals)

def article_body_text(soup,title):
    h1=soup.find("h1")
    if not h1:
        return ""
    parts=[]
    # Consume visible text after the article heading until related-content/footer.
    for node in h1.find_all_next(string=True):
        z=" ".join(str(node).split())
        if not z: continue
        if z in {"Related articles","About Bitget"}:
            break
        parts.append(z)
    body=" ".join(parts)
    # The first title may be repeated; harmless for parsing.
    return body

def fetch_article(meta):
    r=get(meta["url"])
    soup=BeautifulSoup(r.text,"html.parser")
    h1=soup.find("h1")
    title=" ".join(h1.get_text(" ",strip=True).split()) if h1 else meta["title"]
    body=article_body_text(soup,title)
    pub=datetime.fromisoformat(meta["listed_utc"].replace("Z","+00:00")) if meta.get("listed_utc") else None
    cand=candidate_text(title+" "+body)
    launch=bool(re.search(r"\\b(listing|will list|launch)\\b",title,re.I))
    delist=bool(re.search(r"delist|automatic settlement",title+" "+body,re.I))
    effs=parse_effective(body)
    trans=parse_intervals(body)
    syms=parse_symbols(body,title)
    return {
      **meta,"title":title,"source_sha256":hashlib.sha256(r.content).hexdigest(),
      "candidate":cand,"launch":launch,"delist":delist,
      "effective_candidates":[x.isoformat().replace("+00:00","Z") for x in effs],
      "interval_transitions":[list(x) for x in trans],
      "symbols":syms,
      "text_sample":body[:1600],
      "_pub":pub
    }

def main():
    universe,pages,crossed=enumerate_archive()
    inwin=[x for x in universe if x.get("listed_utc") and START<=datetime.fromisoformat(x["listed_utc"].replace("Z","+00:00"))<=END]
    print("ENUMERATED="+str(len(universe)))
    print("ARCHIVE_CROSSED_PRE2024="+str(crossed))
    print("IN_WINDOW="+str(len(inwin)))

    inspected=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(fetch_article,x):x for x in inwin}
        done=0
        for fut in as_completed(futs):
            done+=1
            try: rec=fut.result()
            except Exception as e:
                x=futs[fut]; rec={**x,"error":f"{type(e).__name__}:{e}","candidate":False}
            inspected.append(rec)
            if done%25==0 or done==len(futs):
                print(f"ARTICLE_PROGRESS={done}/{len(futs)}")
    inspected.sort(key=lambda x:x.get("listed_utc") or "")

    candidates=[x for x in inspected if x.get("candidate")]
    eligible=[]
    for x in candidates:
        pub=x.get("_pub")
        effs=[datetime.fromisoformat(z.replace("Z","+00:00")) for z in x.get("effective_candidates",[])]
        trans=[tuple(z) for z in x.get("interval_transitions",[])]
        if x.get("launch") or x.get("delist") or not pub: continue
        # Conservative: exactly one explicit shortening transition and at least one exact post-publication effective timestamp.
        short=sorted({z for z in trans if z[1]<z[0]})
        if len(short)!=1: continue
        old,new=short[0]
        post=[z for z in effs if z>pub and START<=z<=END]
        if len(post)!=1: continue
        eff=post[0]
        syms=[s for s in x.get("symbols",[]) if s.endswith("USDT")]
        if not syms: continue
        for sym in syms:
            eligible.append({
              "article_id":x["id"],"official_title":x["title"],"url":x["url"],
              "publish_utc":pub.isoformat().replace("+00:00","Z"),
              "effective_utc":eff.isoformat().replace("+00:00","Z"),
              "symbol":sym,"old_interval_hours":old,"new_interval_hours":new
            })

    dd={}
    for e in eligible:
        dd[(e["article_id"],e["effective_utc"],e["symbol"],e["old_interval_hours"],e["new_interval_hours"])]=e
    eligible=list(dd.values())
    clusters=defaultdict(list)
    for e in eligible:
        k=f"{e['article_id']}@{e['effective_utc']}@{e['old_interval_hours']}to{e['new_interval_hours']}"
        clusters[k].append(e)
    n=len(eligible); assets=sorted({e["symbol"] for e in eligible})
    years=sorted({datetime.fromisoformat(e["publish_utc"].replace("Z","+00:00")).year for e in eligible})
    maxcl=max((len(v) for v in clusters.values()),default=0)
    conc=maxcl/n if n else 1.0
    gates={
      "clusters_ge_12":len(clusters)>=12,
      "asset_events_ge_20":n>=20,
      "unique_contracts_ge_8":len(assets)>=8,
      "years_ge_2":len(years)>=2,
      "max_cluster_le_35pct":conc<=0.35,
      "archive_crossed_pre2024":crossed,
      "canonical_provenance_resolved":all(e["url"].startswith("https://www.bitget.com/support/articles/") for e in eligible) if eligible else False,
    }
    if crossed and all(gates.values()): verdict="EXTERNAL_SOURCE_PASS"
    elif crossed: verdict="EXTERNAL_INSUFFICIENT_SAMPLE"
    else: verdict="EXTERNAL_SOURCE_BLOCKED"

    for x in inspected:
        x.pop("_pub",None)
    report={
      "family":LAB,"verdict":verdict,"outcome_access":"NONE","calendar":"2024-2025",
      "archive_pages":pages,"archive_crossed_pre2024":crossed,
      "enumerated_articles":len(universe),"articles_in_window":len(inwin),
      "candidate_articles":len(candidates),
      "candidate_years":sorted({int(x["listed_utc"][:4]) for x in candidates if x.get("listed_utc")}),
      "eligible_asset_events":n,"independent_clusters":len(clusters),"unique_contracts":len(assets),
      "years":years,"max_cluster_concentration":conc,"sample_gates":gates,
      "eligible_events":sorted(eligible,key=lambda e:(e["publish_utc"],e["symbol"])),
      "inspected_articles":inspected,
      "safety":{"premium_values_opened":False,"funding_values_opened":False,"mark_values_opened":False,
                "index_values_opened":False,"returns_opened":False,"pnl_opened":False,
                "authenticated_api":False,"mutation":False}
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BGFIPR_SOURCE_RESULT="+verdict)
    print("CANDIDATE_ARTICLES="+str(len(candidates)))
    print("CANDIDATE_YEARS="+json.dumps(report["candidate_years"]))
    print("ELIGIBLE_ASSET_EVENTS="+str(n))
    print("INDEPENDENT_CLUSTERS="+str(len(clusters)))
    print("UNIQUE_CONTRACTS="+str(len(assets)))
    print("YEARS="+json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION="+str(conc))
    print("SAMPLE_GATES="+json.dumps(gates,sort_keys=True))
    print("SAFETY: no premium/funding/mark/index/return/PnL values opened")
if __name__=="__main__":
    main()
