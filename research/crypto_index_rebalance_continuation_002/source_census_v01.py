#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, html, json, re, urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

LAB_ID="CRYPTO-INDEX-REBALANCE-CONTINUATION-002"
BASE="https://bitwiseinvestments.com/indexes/rebalance-results/bitwise-crypto-asset-indexes"
UA="CryptoLab-CIRC002-SourceCensus/0.1 research-only"
OUT=Path("artifacts/crypto_index_rebalance_continuation_002")

MONTHS=["january","february","march","april","may","june","july","august","september","october","november","december"]
EXPECTED=[]
for y in (2025,2026):
    max_m=12 if y==2025 else 9
    for m in range(1,max_m+1):
        EXPECTED.append((y,m,f"{BASE}/{MONTHS[m-1]}-{y}"))

# Frozen from the NYSE Business Day calendar before market outcomes are opened.
# Standard Bitwise implementation = 16:00 America/New_York on the last Business Day of month.
IMPLEMENTATION_DATES={
"2025-01":"2025-01-31","2025-02":"2025-02-28","2025-03":"2025-03-31","2025-04":"2025-04-30",
"2025-05":"2025-05-30","2025-06":"2025-06-30","2025-07":"2025-07-31","2025-08":"2025-08-29",
"2025-09":"2025-09-30","2025-10":"2025-10-31","2025-11":"2025-11-28","2025-12":"2025-12-31",
"2026-01":"2026-01-30","2026-02":"2026-02-27","2026-03":"2026-03-31","2026-04":"2026-04-30",
"2026-05":"2026-05-29","2026-06":"2026-06-30","2026-07":"2026-07-31","2026-08":"2026-08-31",
"2026-09":"2026-09-30"
}

class TextParser(HTMLParser):
    blocks={"p","div","section","article","h1","h2","h3","h4","li","tr","td","th","br"}
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in self.blocks:self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in self.blocks:self.parts.append("\n")
    def handle_data(self,data):self.parts.append(data)
    def text(self):
        raw=html.unescape("".join(self.parts))
        lines=[re.sub(r"\s+"," ",x).strip() for x in raw.splitlines()]
        return "\n".join(x for x in lines if x)

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
        return raw,{"url":url,"http_status":int(r.status),"bytes":len(raw),
                    "content_type":r.headers.get("content-type",""),
                    "raw_sha256":hashlib.sha256(raw).hexdigest()}

def visible(raw):
    p=TextParser();p.feed(raw.decode("utf-8","replace"));return p.text()

def published_meta(raw):
    s=raw.decode("utf-8","replace")
    pats=[
      r'"datePublished"\s*:\s*"([^"]+)"',
      r'property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)',
      r'name=["\']datePublished["\'][^>]*content=["\']([^"\']+)'
    ]
    for pat in pats:
        m=re.search(pat,s,re.I)
        if m:return m.group(1)
    return None

def implementation_ts(month_key):
    local=dt.datetime.fromisoformat(IMPLEMENTATION_DATES[month_key]+"T16:00:00").replace(tzinfo=ZoneInfo("America/New_York"))
    return local.astimezone(dt.timezone.utc).isoformat().replace("+00:00","Z")

def parse_clause(clause):
    c=clause.strip().strip(".")
    if not c or c.lower() in {"no changes","none","no change"}:return []
    m=re.fullmatch(r"(.+?)\s+(re-entered|reentered|re-enters|reenter|entered|enters|enter|exited|exits|exit|removed|removes|remove)",c,re.I)
    if not m:return None
    phrase,verb=m.group(1),m.group(2).lower()
    ticks=[x.upper() for x in re.findall(r"\(([A-Za-z0-9]+)\)",phrase)]
    if not ticks:return None
    direction="ADD" if verb in {"re-entered","reentered","re-enters","reenter","entered","enters","enter"} else "REMOVE"
    return [(t,direction) for t in ticks]

def parse_changes(text):
    if text.lower().strip() in {"no changes","none","no change"}:return [],None
    out=[]
    for clause in text.split(";"):
        x=parse_clause(clause)
        if x is None:return None,clause.strip()
        out.extend(x)
    return out,None

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pages=[]; rawlegs=[]; quarantined=[]
    for year,month,url in EXPECTED:
        key=f"{year:04d}-{month:02d}"
        raw,meta=get(url); txt=visible(raw)
        dm=re.search(r"\bDate:\s*([A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2})",txt)
        tm=re.search(r"\bTime:\s*As of\s*(\d{1,2}:\d{2}\s*(?:am|pm)\s*ET)",txt,re.I)
        changes=[]
        for line in txt.splitlines():
            if line.lower().startswith("changes:"):
                changes.append(line.split(":",1)[1].strip())
        page={**meta,"month_key":key,"official_date":dm.group(1) if dm else None,
              "official_time":tm.group(1) if tm else None,
              "machine_date_published":published_meta(raw),
              "implementation_date":IMPLEMENTATION_DATES[key],
              "implementation_timestamp_utc":implementation_ts(key),
              "changes_fields":changes}
        pages.append(page)
        for source_text in changes:
            if source_text.lower() in {"no changes","no change","none"}:continue
            legs,bad=parse_changes(source_text)
            if legs is None:
                quarantined.append({"month_key":key,"source_text":source_text,"unparsed_clause":bad})
                continue
            for ticker,direction in legs:
                rawlegs.append({"month_key":key,"ticker":ticker,"direction":direction,
                    "source_text":source_text,"result_page_date":page["official_date"],
                    "result_page_time":page["official_time"],
                    "machine_date_published":page["machine_date_published"],
                    "implementation_timestamp_utc":page["implementation_timestamp_utc"]})
    grouped={}
    for leg in rawlegs:
        k=(leg["month_key"],leg["ticker"],leg["direction"])
        grouped.setdefault(k,[]).append(leg)
    by_mt={}
    for m,t,d in grouped:by_mt.setdefault((m,t),set()).add(d)
    contradictions=[{"month_key":m,"ticker":t,"directions":sorted(ds)} for (m,t),ds in by_mt.items() if len(ds)>1]
    events=[]
    for (m,t,d),xs in sorted(grouped.items()):
        x=xs[0]
        events.append({"month_key":m,"ticker":t,"direction":d,
          "result_page_date":x["result_page_date"],"result_page_time":x["result_page_time"],
          "machine_date_published":x["machine_date_published"],
          "implementation_timestamp_utc":x["implementation_timestamp_utc"],
          "duplicate_section_records_collapsed":len(xs)-1,
          "source_texts":sorted(set(z["source_text"] for z in xs))})
    change_months=sorted({x["month_key"] for x in events})
    dirs=Counter(x["direction"] for x in events)
    years=sorted({int(x["month_key"][:4]) for x in events})
    missing_date_time=[x["month_key"] for x in pages if not x["official_date"] or not x["official_time"]]
    publication_meta_count=sum(bool(x["machine_date_published"]) for x in pages)
    gates={
      "pages_21_of_21":len(pages)==21,
      "zero_missing_official_date_time":not missing_date_time,
      "zero_unparsed_change_strings":not quarantined,
      "zero_direction_contradictions":not contradictions,
      "both_2025_2026":years==[2025,2026],
      "min_12_event_legs":len(events)>=12,
      "min_4_change_months":len(change_months)>=4,
      "both_add_remove":dirs["ADD"]>0 and dirs["REMOVE"]>0
    }
    result={
      "lab_id":LAB_ID,"schema":"CIRC002_SOURCE_CENSUS_V0.1",
      "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "classification":"SOURCE_CENSUS_PASS" if all(gates.values()) else "SOURCE_CENSUS_BLOCKED",
      "pages":pages,"events":events,"quarantined":quarantined,"contradictions":contradictions,
      "expected_pages":21,"recovered_pages":len(pages),
      "unique_event_legs":len(events),"distinct_change_months":len(change_months),
      "change_months":change_months,"direction_counts":dict(dirs),"years":years,
      "machine_publication_timestamp_pages":publication_meta_count,
      "gates":gates,
      "market_prices_read":False,"returns_computed":False,"pnl_computed":False,
      "trading_authority":"NONE"
    }
    stable={"events":events,"pages":[{k:p[k] for k in ["month_key","url","raw_sha256","official_date","official_time","machine_date_published","implementation_timestamp_utc"]} for p in pages]}
    result["source_identity_sha256"]=hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    (OUT/"SOURCE_CENSUS_V0.1.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["classification","recovered_pages","unique_event_legs","distinct_change_months","change_months","direction_counts","years","machine_publication_timestamp_pages","gates","source_identity_sha256"]},indent=2,sort_keys=True))
    return 0 if result["classification"]=="SOURCE_CENSUS_PASS" else 2
if __name__=="__main__":raise SystemExit(main())
