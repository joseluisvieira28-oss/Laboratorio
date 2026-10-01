#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re,sys
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

PARENT=Path("Dream-Account-OS-v2.3-PARTIAL/research/exchange_delisting_shock_001")
sys.path.insert(0,str(PARENT))
import source_gate_v02 as v2
import source_gate_v03 as v3

LAB_ID="DELISTING-PERP-SHOCK-001"
CENSUS=PARENT/"source_evidence/EDS_SOURCE_DATA_GATE_V03.json"
OUT=Path("labs/DELISTING_PERP_SHOCK_001/source_output")
SPOT_DV="https://data.binance.vision/data/spot/daily/klines"
FUT_DV="https://data.binance.vision/data/futures/um/daily/klines"
QUOTE_FIREWALL={"USDT","USDC","FDUSD","BUSD","BTC","ETH","BNB","EUR","TRY","BRL","AUD","GBP","DAI","TUSD"}

def checksum(url):
    try:
        b=v2.get(url,attempts=1).decode("utf-8","replace").strip().split()
        dg=b[0].lower() if b else ""
        ok=len(dg)==64 and all(c in "0123456789abcdef" for c in dg)
        return {"ok":ok,"sha256":dg if ok else None,"url":url,"status":200}
    except Exception as e:
        return {"ok":False,"sha256":None,"url":url,"status":"ERROR:"+type(e).__name__}

def spot_checksum(sym,day):
    p=sym+"USDT";d=day.isoformat()
    return checksum(f"{SPOT_DV}/{p}/1m/{p}-1m-{d}.zip.CHECKSUM")

def fut_checksum(sym,day):
    p=sym+"USDT";d=day.isoformat()
    return checksum(f"{FUT_DV}/{p}/1m/{p}-1m-{d}.zip.CHECKSUM")

def title_symbols(title):
    m=re.match(r"(?i)^Binance Will Delist\s+(.+?)\s+on\s+20\d{2}-\d{2}-\d{2}\s*$",title.strip())
    if not m:return []
    s=re.sub(r"\s+(?:AND|&)\s+",",",m.group(1).upper())
    out=[]
    for x in s.split(","):
        x=re.sub(r"[^A-Z0-9]","",x)
        if 2<=len(x)<=15 and x not in QUOTE_FIREWALL:out.append(x)
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    parent=json.loads(CENSUS.read_text())
    assert parent["receipt"]["classification"]=="INSUFFICIENT_SOURCE_SAMPLE"
    assert parent["receipt"]["market_price_values_opened"] is False
    # Immutable parent census: articles that already reached exact full-token parsing
    # but failed only because Name(SYMBOL) identity could not be resolved.
    by_article={}
    for x in parent["rejected"]:
        if x.get("reason")!="TOKEN_NAME_NOT_EXACTLY_RESOLVED":continue
        code=x["article_code"];title=x["title"]
        by_article.setdefault(code,title)

    raw_events=[];rejected=[];detail_failures={}
    for n,(code,title0) in enumerate(sorted(by_article.items()),1):
        try:
            raw,j=v2.get_json(v2.DETAIL,{"articleCode":code})
            d=v2.find_detail(j)
            if not d:raise RuntimeError("detail body absent")
            pub=v2.parse_release(d.get("releaseDate"))
            title=str(d.get("title") or title0)
            body=str(d.get("body") or "")
            txt=v2.textify(body)
            stop=v3.delist_ts(txt)
            if pub is None:
                rejected.append({"article_code":code,"title":title,"reason":"NO_EXACT_PUBLICATION_TIMESTAMP"});continue
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
            print(f"article {n}/{len(by_article)} {title} -> {len(syms)} title tickers",flush=True)
        except Exception as e:
            detail_failures[code]=type(e).__name__+":"+str(e)

    raw_events.sort(key=lambda x:(x["publication_timestamp_utc"],x["article_code"],x["token_symbol"]))
    events=[];seen=set()
    for e in raw_events:
        if e["token_symbol"] in seen:
            rejected.append({"article_code":e["article_code"],"symbol":e["token_symbol"],"reason":"LATER_REPEAT_ANNOUNCEMENT"});continue
        seen.add(e["token_symbol"]);events.append(e)

    route=[]
    for i,e in enumerate(events,1):
        pub=datetime.fromisoformat(e["publication_timestamp_utc"].replace("Z","+00:00"))
        stop=datetime.fromisoformat(e["all_pairs_cessation_timestamp_utc"].replace("Z","+00:00"))
        sym=e["token_symbol"];prev=pub.date()-timedelta(days=1);pd=pub.date();nd=pd+timedelta(days=1)
        sp=spot_checksum(sym,prev);fp=fut_checksum(sym,pd)
        nr=datetime.combine(nd,datetime.min.time(),tzinfo=timezone.utc)<stop
        fn=fut_checksum(sym,nd) if nr else None
        ok=sp["ok"] and fp["ok"] and ((not nr) or fn["ok"])
        route.append({**e,
          "spot_prepublication_day":prev.isoformat(),"spot_prepublication_checksum":sp,
          "futures_publication_day_checksum":fp,"futures_next_day_required":nr,
          "futures_next_day_checksum":fn,"route_qualified":bool(ok)})
        print(f"route {i}/{len(events)} {sym}: {ok}",flush=True)

    rq=[x for x in route if x["route_qualified"]]
    years=Counter(x["publication_timestamp_utc"][:4] for x in rq);tickers={x["token_symbol"] for x in rq}
    passed=len(rq)>=20 and len(tickers)>=12 and years["2023"]>=5 and years["2024"]>=5
    if detail_failures and not route:cl="SOURCE_TECHNICAL_FAILURE"
    elif passed:cl="SOURCE_DATA_PASS"
    else:cl="INSUFFICIENT_SOURCE_SAMPLE"
    rec={"lab_id":LAB_ID,"classification":cl,
      "parent_v03_census_sha_context":"IMMUTABLE_PARENT_REJECTED_TITLE_EVENTS_ONLY",
      "parent_candidate_articles_used":len(by_article),
      "title_authoritative_events":len(events),"route_qualified_events":len(rq),
      "distinct_route_tickers":len(tickers),"route_year_counts":dict(sorted(years.items())),
      "detail_failure_count":len(detail_failures),
      "rejected_reason_counts":dict(Counter(x["reason"] for x in rejected)),
      "market_price_values_opened":False,"returns_computed":False,"pnl_computed":False,
      "access_2025":False,"access_2026":False,"trading_authority":"NONE"}
    (OUT/"SOURCE_GATE_RESULT.json").write_text(json.dumps({"receipt":rec,"route_checks":route,"rejected":rejected,"detail_failures":detail_failures},indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":main()
