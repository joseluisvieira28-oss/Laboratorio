import ccxt, requests, bs4, re, json, os, time, hashlib
from datetime import datetime, timezone

OUT="artifacts/mexc_launchpool_mx_demand_v017_complete_source"
os.makedirs(OUT,exist_ok=True)
ex=ccxt.mexc({"enableRateLimit":True})
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (CryptoLabResearch/1.0)"})

START=datetime(2024,10,18,tzinfo=timezone.utc)
END=datetime(2026,10,1,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000)
END_MS=int(END.timestamp()*1000)

page_cache={}
def fetch_page(page):
    if page in page_cache:
        return page_cache[page]
    last=None
    for attempt,delay in enumerate([0,2,4,8,16,24],1):
        if delay: time.sleep(delay)
        try:
            resp=ex.spot_public_get_announcements({"page":page})
            raw=resp.get("data") if isinstance(resp,dict) else resp
            if isinstance(raw,list) and raw and isinstance(raw[0],dict):
                box=raw[0]
            elif isinstance(raw,dict):
                box=raw
            elif isinstance(resp,dict):
                box=resp
            else:
                raise RuntimeError("UNSUPPORTED_SCHEMA")
            details=box.get("details") or []
            total=int(box.get("totalPage") or page)
            rows=[]
            for r in details:
                if r.get("postTime") is None: continue
                rr=dict(r)
                rr["postTime"]=int(rr["postTime"])
                rr["postTime_iso"]=datetime.fromtimestamp(rr["postTime"]/1000,tz=timezone.utc).isoformat()
                rows.append(rr)
            rec={"page":page,"totalPage":total,"rows":rows}
            page_cache[page]=rec
            time.sleep(0.8)
            return rec
        except Exception as e:
            last=e
            if "429" not in repr(e) and "RateLimit" not in type(e).__name__ and attempt>=2:
                break
    raise RuntimeError(f"PAGE_FETCH_FAILED:{page}:{repr(last)}")

p1=fetch_page(1)
TOTAL=p1["totalPage"]

def bounds(page):
    rec=fetch_page(page)
    ts=[x["postTime"] for x in rec["rows"]]
    if not ts:
        return None,None
    return min(ts),max(ts)

# Pages are newest -> oldest. Return a page at/around target time.
def locate(target_ms):
    lo,hi=1,TOTAL
    best=None
    while lo<=hi:
        mid=(lo+hi)//2
        oldest,newest=bounds(mid)
        if oldest is None:
            lo=mid+1
            continue
        best=mid
        if oldest <= target_ms <= newest:
            return mid
        if target_ms > newest:
            hi=mid-1
        else: # target older than this page
            lo=mid+1
    return max(1,min(TOTAL,best or lo))

p_end=locate(END_MS-1)
p_start=locate(START_MS)
scan_lo=max(1,min(p_end,p_start)-3)
scan_hi=min(TOTAL,max(p_end,p_start)+3)

pages=[]
all_rows=[]
for page in range(scan_lo,scan_hi+1):
    rec=fetch_page(page)
    rows=rec["rows"]
    pages.append({
        "page":page,
        "n":len(rows),
        "oldest":min((x["postTime_iso"] for x in rows),default=None),
        "newest":max((x["postTime_iso"] for x in rows),default=None)
    })
    for rr in rows:
        if START_MS <= rr["postTime"] < END_MS:
            all_rows.append(rr)

# exact row de-dup by stable URL/title/postTime
dedup={}
for r in all_rows:
    k=(r.get("url"),r.get("title"),r.get("postTime"))
    dedup[k]=r
all_rows=sorted(dedup.values(),key=lambda x:x["postTime"])

launch_rows=[r for r in all_rows if "launchpool" in str(r.get("title","")).lower()]

def norm(s): return re.sub(r"\s+"," ",s or "").strip()

article_records=[]
for i,r in enumerate(launch_rows,1):
    url=r.get("url")
    rec={
      "title":r.get("title"),"url":url,"postTime":r.get("postTime"),
      "postTime_iso":r.get("postTime_iso"),"language":r.get("language")
    }
    try:
        rr=None
        for attempt,delay in enumerate([0,1,2,4,8],1):
            if delay: time.sleep(delay)
            rr=S.get(url,timeout=30)
            if rr.status_code==429:
                continue
            rr.raise_for_status()
            break
        if rr is None or rr.status_code!=200:
            raise RuntimeError(f"ARTICLE_HTTP_{None if rr is None else rr.status_code}")
        html=rr.text
        soup=bs4.BeautifulSoup(html,"html.parser")
        text=norm(soup.get_text(" "))
        rec["body_sha256"]=hashlib.sha256(html.encode()).hexdigest()
        rec["body_text_sample"]=text[:8000]
        rec["explicit_mx_eligibility"]=bool(
          re.search(r"\bMX\s+Staking\s+Pool\b",text,re.I)
          or re.search(r"Stake[^.]{0,160}\bMX\b",text,re.I)
          or re.search(r"Supported Sessions\s*:\s*MX",text,re.I)
          or re.search(r"commit\s+(?:your\s+)?MX",text,re.I)
          or re.search(r"\bMX\b[^.]{0,160}(?:staking|stake|commit|pool)",text,re.I)
        )
        low=text.lower()
        rec["excluded_generic"]=any(x in low for x in [
          "what is the mexc launchpool event",
          "launchpad event will officially be renamed launchpool",
          "launchpool will undergo a major upgrade"
        ])
    except Exception as e:
        rec["error"]=repr(e)
        rec["explicit_mx_eligibility"]=False
        rec["excluded_generic"]=False
    article_records.append(rec)
    time.sleep(0.15)

eligible=[x for x in article_records
          if x.get("explicit_mx_eligibility")
          and not x.get("excluded_generic")
          and not x.get("error")]
eligible.sort(key=lambda x:x["postTime"])

clusters=[]
for e in eligible:
    dt=datetime.fromisoformat(e["postTime_iso"])
    if not clusters:
        clusters.append({"first":e["postTime_iso"],"last":e["postTime_iso"],"events":[e["url"]]})
    else:
        last=datetime.fromisoformat(clusters[-1]["last"])
        if (dt-last).total_seconds()<=3600:
            clusters[-1]["last"]=e["postTime_iso"]
            clusters[-1]["events"].append(e["url"])
        else:
            clusters.append({"first":e["postTime_iso"],"last":e["postTime_iso"],"events":[e["url"]]})

years=sorted(set(datetime.fromisoformat(x["postTime_iso"]).year for x in eligible))
gate={
 "events_ge_20":len(eligible)>=20,
 "clusters_ge_12":len(clusters)>=12,
 "years_ge_2":len(years)>=2,
 "timestamps_complete":all(x.get("postTime") is not None for x in eligible),
 "article_body_complete":all(not x.get("error") for x in article_records),
}
classification="SOURCE_GATE_PASS" if all(gate.values()) else "SOURCE_INSUFFICIENT_SAMPLE"

summary={
 "source_route":"MEXC public announcements endpoint, rate-limit-safe bounded census + official article bodies",
 "authenticated":False,
 "additional_market_outcomes_opened":False,
 "total_pages_reported":TOTAL,
 "located_end_page":p_end,
 "located_start_page":p_start,
 "scanned_page_range":[scan_lo,scan_hi],
 "pages_scanned":len(pages),
 "in_window_announcements":len(all_rows),
 "launchpool_title_rows":len(launch_rows),
 "launchpool_article_bodies":len(article_records),
 "eligible_mx_launchpool_events":len(eligible),
 "independent_clusters":len(clusters),
 "years":years,
 "gate":gate,
 "classification":classification,
}
for name,obj in [
 ("pages.json",pages),
 ("in_window_announcements.json",all_rows),
 ("launchpool_rows.json",launch_rows),
 ("launchpool_articles.json",article_records),
 ("eligible_events.json",eligible),
 ("clusters.json",clusters),
 ("summary.json",summary),
]:
    with open(f"{OUT}/{name}","w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
print(json.dumps(summary,indent=2))
