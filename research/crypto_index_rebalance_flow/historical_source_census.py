#!/usr/bin/env python3
"""Official Bitwise rebalance-results source census, 2022-2025.

Source-only: no crypto market data, prices, returns, volume or PnL.
"""

from __future__ import annotations
import datetime as dt
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

BASE="https://bitwiseinvestments.com"
INDEX=BASE+"/indexes/rebalance-results/bitwise-crypto-asset-indexes"
YEARS={2022,2023,2024,2025}
MONTHS=["january","february","march","april","may","june","july","august","september","october","november","december"]
EXPECTED={(m,y) for y in YEARS for m in MONTHS}
UA="CryptoLab-Bitwise-SourceCensus/0.1 research-only"
OUT=Path("artifacts/crypto_index_rebalance_flow")

class TextParser(HTMLParser):
    blocks={"p","div","section","article","h1","h2","h3","h4","li","tr","td","th","br"}
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in self.blocks:
            self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in self.blocks:
            self.parts.append("\n")
    def handle_data(self,data):
        self.parts.append(data)
    def text(self):
        raw=html.unescape("".join(self.parts))
        lines=[re.sub(r"\s+"," ",x).strip() for x in raw.splitlines()]
        return "\n".join(x for x in lines if x)

def get(url:str)->tuple[bytes,dict[str,Any]]:
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
        return raw,{
            "url":url,
            "http_status":int(r.status),
            "content_type":r.headers.get("content-type",""),
            "bytes":len(raw),
            "raw_sha256":hashlib.sha256(raw).hexdigest(),
        }

def visible(raw:bytes)->str:
    p=TextParser()
    p.feed(raw.decode("utf-8","replace"))
    return p.text()

def links(raw:bytes)->set[str]:
    s=raw.decode("utf-8","replace")
    out=set()
    for href in re.findall(r'href=["\']([^"\']+)["\']',s,re.I):
        u=urllib.parse.urljoin(BASE,html.unescape(href))
        if "/indexes/rebalance-results/bitwise-crypto-asset-indexes/" in u:
            out.add(u.split("#")[0].split("?")[0].rstrip("/"))
    return out

def month_id(url:str):
    slug=url.rstrip("/").split("/")[-1].lower()
    m=re.fullmatch(r"([a-z]+)-(20\d{2})",slug)
    if not m:
        return None
    mon,year=m.group(1),int(m.group(2))
    if mon not in MONTHS or year not in YEARS:
        return None
    return mon,year

def parse_page(url:str,raw:bytes,meta:dict[str,Any])->dict[str,Any]:
    txt=visible(raw)
    date_match=re.search(r"\bDate:\s*([A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2})",txt)
    time_match=re.search(r"\bTime:\s*As of\s*(\d{1,2}:\d{2}\s*(?:am|pm)\s*ET)",txt,re.I)
    changes=[]
    for line in txt.splitlines():
        if line.lower().startswith("changes:"):
            val=line.split(":",1)[1].strip()
            changes.append(val)
    non_no=[x for x in changes if x.lower() not in {"no changes","none","no change"}]
    return {
        **meta,
        "month_identity":month_id(url),
        "official_date":date_match.group(1) if date_match else None,
        "official_time":time_match.group(1) if time_match else None,
        "changes_fields":changes,
        "non_no_change_fields":non_no,
        "visible_text_sha256":hashlib.sha256(txt.encode()).hexdigest(),
    }

def main()->int:
    OUT.mkdir(parents=True,exist_ok=True)
    idx_raw,idx_meta=get(INDEX)
    discovered={month_id(u):u for u in links(idx_raw) if month_id(u) is not None}

    # Never silently invent missing URLs during the first pass. The completeness
    # result reports exactly what the official index page exposes.
    rows=[]
    for key in sorted(discovered,key=lambda x:(x[1],MONTHS.index(x[0]))):
        raw,meta=get(discovered[key])
        rows.append(parse_page(discovered[key],raw,meta))

    got={tuple(x["month_identity"]) for x in rows if x.get("month_identity")}
    missing=sorted(EXPECTED-got,key=lambda x:(x[1],MONTHS.index(x[0])))
    unique_dates=[x["official_date"] for x in rows if x.get("official_date")]
    change_months=sum(bool(x["non_no_change_fields"]) for x in rows)
    by_year={str(y):sum(1 for x in rows if x["month_identity"][1]==y and x["non_no_change_fields"]) for y in sorted(YEARS)}
    complete=(
        len(got)==48
        and not missing
        and len(unique_dates)==48
        and len(set(unique_dates))==48
        and all(x.get("official_time") for x in rows)
    )
    classification="SOURCE_CORPUS_COMPLETE" if complete else "SOURCE_CORPUS_INCOMPLETE"
    receipt={
        "schema":"BITWISE_REBALANCE_HISTORICAL_SOURCE_CENSUS_V0.1",
        "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_index":idx_meta,
        "period":"2022-01..2025-12",
        "expected_months":48,
        "recovered_months":len(got),
        "missing_months":[{"month":m,"year":y} for m,y in missing],
        "months_with_non_no_changes":change_months,
        "non_no_change_section_records":sum(len(x["non_no_change_fields"]) for x in rows),
        "distinct_non_no_change_strings":len({s for x in rows for s in x["non_no_change_fields"]}),
        "change_months_by_year":by_year,
        "pages":rows,
        "classification":classification,
        "market_prices_read":False,
        "returns_computed":False,
        "pnl_computed":False,
        "2026_result_pages_fetched":False,
    }
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
    path=OUT/"historical_source_census_v0.1.json"
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
        "classification":classification,
        "recovered_months":len(got),
        "missing_months":len(missing),
        "months_with_non_no_changes":change_months,
        "non_no_change_section_records":receipt["non_no_change_section_records"],
        "change_months_by_year":by_year,
        "market_prices_read":False,
    },indent=2,sort_keys=True))
    return 0 if complete else 2

if __name__=="__main__":
    raise SystemExit(main())
