#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

PARENT=Path("Dream-Account-OS-v2.3-PARTIAL/research/exchange_delisting_shock_001")
sys.path.insert(0,str(PARENT))
import source_gate_v02 as v2
import source_gate_v03 as v3

LAB_ID="DELISTING-PERP-SHOCK-001"
OUT=Path("labs/DELISTING_PERP_SHOCK_001/source_output")
START=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)
SPOT_DV="https://data.binance.vision/data/spot/daily/klines"
FUT_DV="https://data.binance.vision/data/futures/um/daily/klines"
QUOTE_FIREWALL={"USDT","USDC","FDUSD","BUSD","BTC","ETH","BNB","EUR","TRY","BRL","AUD","GBP","DAI","TUSD"}

def checksum(url):
    try:
        b=v2.get(url, attempts=1).decode("utf-8","replace").strip().split()
        dg=b[0].lower() if b else ""
        ok=len(dg)==64 and all(c in "0123456789abcdef" for c in dg)
        return {"ok":ok,"sha256":dg if ok else None,"url":url,"status":200}
    except Exception as e:
        return {"ok":False,"sha256":None,"url":url,"status":"ERROR:"+type(e).__name__}

def spot_checksum(sym,day):
    pair=sym+"USDT"; ds=day.isoformat()
    return checksum(f"{SPOT_DV}/{pair}/1m/{pair}-1m-{ds}.zip.CHECKSUM")

def fut_checksum(sym,day):
    pair=sym+"USDT"; ds=day.isoformat()
    return checksum(f"{FUT_DV}/{pair}/1m/{pair}-1m-{ds}.zip.CHECKSUM")

def title_symbols(title):
    m=re.match(r"(?i)^Binance Will Delist\s+(.+?)\s+on\s+20\d{2}-\d{2}-\d{2}\s*$",title.strip())
    if not m:
        return []
    s=m.group(1).upper()
    s=re.sub(r"\s+(?:AND|&)\s+",",",s)
    s=s.replace(" & ",",")
    parts=[re.sub(r"[^A-Z0-9]","",x) for x in s.split(",")]
    return [x for x in parts if 2<=len(x)<=15 and x not in QUOTE_FIREWALL]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    candidates={};list_pages=0;list_error=None
    try:
        for p in range(1,201):
            raw,j=v2.get_json(v2.LIST,{"type":1,"catalogId":161,"pageNo":p,"pageSize":50})
            arts=v2.find_articles(j);list_pages=p
            if not arts:break
            for a in arts:
                title=str(a.get("title",""))
                code=str(a.get("code") or a.get("articleCode") or "")
                if code and re.search(r"^Binance Will Delist\b",title,re.I):
                    candidates[code]=a
    except Exception as e:
        list_error=type(e).__name__+":"+str(e)

    raw_events=[];rejected=[];detail_failures={}
    for code,a in sorted(candidates.items()):
        try:
            raw,j=v2.get_json(v2.DETAIL,{"articleCode":code})
            d=v2.find_detail(j)
            if not d:raise RuntimeError("detail body absent")
            pub=v2.parse_release(d.get("releaseDate") or a.get("releaseDate"))
            if pub is None or not (START<=pub<=END):continue
            title=str(d.get("title") or a.get("title") or "")
            body=str(d.get("body") or "")
            txt=v2.textify(body)
            stop=v3.delist_ts(txt)
            if stop is None:
                rejected.append({"article_code":code,"title":title,"reason":"NO_EXACT_CESSATION_TIMESTAMP"});continue
            syms=title_symbols(title)
            if not syms:
                rejected.append({"article_code":code,"title":title,"reason":"NO_TITLE_TICKERS"});continue
            digest=hashlib.sha256(raw).hexdigest()
            for sym in syms:
                raw_events.append({
                    "article_code":code,
                    "official_url":f"https://www.binance.com/en/support/announcement/detail/{code}",
                    "title":title,
                    "publication_timestamp_utc":pub.isoformat().replace("+00:00","Z"),
                    "token_symbol":sym,
                    "identity_source":"OFFICIAL_ANNOUNCEMENT_TITLE",
                    "all_pairs_cessation_timestamp_utc":stop.isoformat().replace("+00:00","Z"),
                    "article_response_sha256":digest
                })
        except Exception as e:
            detail_failures[code]=type(e).__name__+":"+str(e)

    raw_events.sort(key=lambda x:(x["publication_timestamp_utc"],x["article_code"],x["token_symbol"]))
    events=[];seen=set()
    for e in raw_events:
        if e["token_symbol"] in seen:
            rejected.append({"article_code":e["article_code"],"symbol":e["token_symbol"],"reason":"LATER_REPEAT_ANNOUNCEMENT"})
            continue
        seen.add(e["token_symbol"]);events.append(e)

    route=[]
    for i,e in enumerate(events,1):
        pub=datetime.fromisoformat(e["publication_timestamp_utc"].replace("Z","+00:00"))
        stop=datetime.fromisoformat(e["all_pairs_cessation_timestamp_utc"].replace("Z","+00:00"))
        sym=e["token_symbol"]
        prev_day=pub.date()-timedelta(days=1)
        pub_day=pub.date()
        next_day=pub_day+timedelta(days=1)
        spot_pre=spot_checksum(sym,prev_day)
        fut_pub=fut_checksum(sym,pub_day)
        fut_next=None
        next_required=(datetime.combine(next_day,datetime.min.time(),tzinfo=timezone.utc)<stop)
        if next_required:fut_next=fut_checksum(sym,next_day)
        q=spot_pre["ok"] and fut_pub["ok"] and ((not next_required) or fut_next["ok"])
        route.append({
            **e,
            "spot_prepublication_day":prev_day.isoformat(),
            "spot_prepublication_checksum":spot_pre,
            "futures_publication_day_checksum":fut_pub,
            "futures_next_day_required":next_required,
            "futures_next_day_checksum":fut_next,
            "route_qualified":bool(q)
        })
        print(f"{i}/{len(events)} {sym} {e['publication_timestamp_utc']} route={q}",flush=True)

    rq=[x for x in route if x["route_qualified"]]
    years=Counter(x["publication_timestamp_utc"][:4] for x in rq)
    tickers={x["token_symbol"] for x in rq}
    passed=len(rq)>=20 and len(tickers)>=12 and years["2023"]>=5 and years["2024"]>=5
    if list_error and not candidates:cl="SOURCE_ACCESS_BLOCKED"
    elif detail_failures and not route:cl="SOURCE_TECHNICAL_FAILURE"
    elif passed:cl="SOURCE_DATA_PASS"
    else:cl="INSUFFICIENT_SOURCE_SAMPLE"
    receipt={
        "lab_id":LAB_ID,"classification":cl,
        "candidate_articles":len(candidates),
        "title_authoritative_events":len(events),
        "route_qualified_events":len(rq),
        "distinct_route_tickers":len(tickers),
        "route_year_counts":dict(sorted(years.items())),
        "list_pages_requested":list_pages,"list_error":list_error,
        "detail_failure_count":len(detail_failures),
        "rejected_reason_counts":dict(Counter(x["reason"] for x in rejected)),
        "market_price_values_opened":False,"returns_computed":False,"pnl_computed":False,
        "access_2025":False,"access_2026":False,"trading_authority":"NONE"
    }
    doc={"receipt":receipt,"route_checks":route,"rejected":rejected,"detail_failures":detail_failures}
    (OUT/"SOURCE_GATE_RESULT.json").write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":main()
