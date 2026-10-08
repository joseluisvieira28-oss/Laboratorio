import ccxt, requests, bs4, re, json, os, time, hashlib
from datetime import datetime, timezone

OUT="artifacts/mexc_launchpool_reward_token_sellpressure_v01_source"
os.makedirs(OUT,exist_ok=True)
ex=ccxt.mexc({"enableRateLimit":True})
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (CryptoLabResearch/1.0)"})

START=datetime(2025,1,1,tzinfo=timezone.utc)
END=datetime(2026,10,1,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000)
END_MS=int(END.timestamp()*1000)

page_cache={}
def fetch_page(page):
    if page in page_cache:return page_cache[page]
    last=None
    for delay in [0,2,4,8,16,24]:
        if delay: time.sleep(delay)
        try:
            resp=ex.spot_public_get_announcements({"page":page})
            raw=resp.get("data") if isinstance(resp,dict) else resp
            if isinstance(raw,list) and raw and isinstance(raw[0],dict): box=raw[0]
            elif isinstance(raw,dict): box=raw
            elif isinstance(resp,dict): box=resp
            else: raise RuntimeError("UNSUPPORTED_SCHEMA")
            details=box.get("details") or []
            total=int(box.get("totalPage") or page)
            rows=[]
            for r in details:
                if r.get("postTime") is None: continue
                rr=dict(r); rr["postTime"]=int(rr["postTime"])
                rr["postTime_iso"]=datetime.fromtimestamp(rr["postTime"]/1000,tz=timezone.utc).isoformat()
                rows.append(rr)
            rec={"page":page,"totalPage":total,"rows":rows}; page_cache[page]=rec
            time.sleep(.8); return rec
        except Exception as e:
            last=e
    raise RuntimeError(f"PAGE_FETCH_FAILED:{page}:{repr(last)}")

p1=fetch_page(1); TOTAL=p1["totalPage"]

def bounds(page):
    r=fetch_page(page); ts=[x["postTime"] for x in r["rows"]]
    return (min(ts),max(ts)) if ts else (None,None)

def locate(target):
    lo,hi=1,TOTAL; best=1
    while lo<=hi:
        mid=(lo+hi)//2; oldest,newest=bounds(mid)
        if oldest is None: lo=mid+1; continue
        best=mid
        if oldest<=target<=newest:return mid
        if target>newest:hi=mid-1
        else:lo=mid+1
    return max(1,min(TOTAL,best))

p_end=locate(END_MS-1); p_start=locate(START_MS)
scan_lo=max(1,min(p_end,p_start)-3); scan_hi=min(TOTAL,max(p_end,p_start)+3)

rows=[]
pages=[]
for p in range(scan_lo,scan_hi+1):
    rec=fetch_page(p)
    pages.append({"page":p,"n":len(rec["rows"])})
    rows += [r for r in rec["rows"] if START_MS<=r["postTime"]<END_MS]
dedup={}
for r in rows: dedup[(r.get("url"),r.get("title"),r.get("postTime"))]=r
rows=sorted(dedup.values(),key=lambda x:x["postTime"])
launch=[r for r in rows if "launchpool" in str(r.get("title","")).lower()]

def norm(s): return re.sub(r"\s+"," ",s or "").strip()

def parse_symbol(title,text):
    # prioritize explicit token ticker in title
    pats=[
      r'\[Initial Listing\][^\n]{0,100}?\(([A-Z0-9]{2,15})\)',
      r'Initial Listing[^\n]{0,100}?\(([A-Z0-9]{2,15})\)',
      r'Launchpool[^\n]{0,100}?\(([A-Z0-9]{2,15})\)',
      r'\b([A-Z0-9]{2,15})\s+Launchpool\b'
    ]
    for s in [title,text[:1000]]:
        for pat in pats:
            m=re.search(pat,s,re.I)
            if m:return m.group(1).upper()
    return None

MONTHS="Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
def parse_listing_times(text):
    found=[]
    labels=[
      r'(?:Spot\s+)?Trading(?:\s+Starts?|\s+Start|\s+Opens?)?',
      r'Listing(?:\s+Time)?',
      r'Open(?:ing)?\s+Time',
      r'Trading\s+Time'
    ]
    datepat=rf'({MONTHS})\s+(\d{{1,2}}),?\s+(20\d{{2}})[,\s]+(\d{{1,2}}):(\d{{2}})'
    numpat=r'(20\d{2})[-/](\d{1,2})[-/](\d{1,2})[ T]+(\d{1,2}):(\d{2})'
    for lab in labels:
        for m in re.finditer(lab+r'[^.\n]{0,180}?'+datepat,text,re.I):
            raw=m.group(0)
            try:
                datepart=re.search(datepat,raw,re.I)
                dt=datetime.strptime(" ".join(datepart.groups()),"%b %d %Y %H %M").replace(tzinfo=timezone.utc)
                found.append(dt)
            except: 
                try:
                    g=datepart.groups()
                    dt=datetime.strptime(" ".join(g),"%B %d %Y %H %M").replace(tzinfo=timezone.utc); found.append(dt)
                except: pass
        for m in re.finditer(lab+r'[^.\n]{0,180}?'+numpat,text,re.I):
            g=re.search(numpat,m.group(0),re.I).groups()
            try: found.append(datetime(int(g[0]),int(g[1]),int(g[2]),int(g[3]),int(g[4]),tzinfo=timezone.utc))
            except: pass
    # dedup plausible times
    out=[]
    for x in found:
        if START <= x < datetime(2027,1,1,tzinfo=timezone.utc) and x not in out: out.append(x)
    return sorted(out)

articles=[]
for r in launch:
    rec={"title":r.get("title"),"url":r.get("url"),"postTime":r.get("postTime"),"postTime_iso":r.get("postTime_iso")}
    try:
        rr=None
        for delay in [0,1,2,4,8]:
            if delay:time.sleep(delay)
            rr=S.get(rec["url"],timeout=30)
            if rr.status_code==429:continue
            rr.raise_for_status();break
        if rr is None or rr.status_code!=200:raise RuntimeError("ARTICLE_FETCH_FAIL")
        html=rr.text; soup=bs4.BeautifulSoup(html,"html.parser"); text=norm(soup.get_text(" "))
        title=norm(r.get("title") or "")
        rec["body_sha256"]=hashlib.sha256(html.encode()).hexdigest()
        rec["symbol"]=parse_symbol(title,text)
        rec["initial_listing"]=bool(re.search(r'\bInitial Listing\b|\binitially list(?:ed|ing)\b|\bnew listing\b',title+" "+text[:2500],re.I))
        lts=parse_listing_times(text)
        rec["listing_time_candidates"]=[x.isoformat() for x in lts]
        rec["exact_listing_t0"]=lts[0].isoformat() if len(lts)==1 else None
        rec["listing_time_unambiguous"]=len(lts)==1
        rec["text_sample"]=text[:6000]
    except Exception as e:rec["error"]=repr(e)
    articles.append(rec);time.sleep(.15)

# source eligibility excludes market availability; that is checked before outcomes in activation step
eligible=[a for a in articles if not a.get("error") and a.get("initial_listing") and a.get("symbol") and a.get("listing_time_unambiguous")]
# one initial listing per reward token
by={}
for a in eligible:
    by.setdefault(a["symbol"],a)
eligible=sorted(by.values(),key=lambda x:x["exact_listing_t0"])
years=sorted({x["exact_listing_t0"][:4] for x in eligible})
gate={
 "events_ge_10":len(eligible)>=10,
 "unique_symbols_ge_10":len({x["symbol"] for x in eligible})>=10,
 "years_ge_2":len(years)>=2,
 "exact_listing_t0_complete":all(x.get("exact_listing_t0") for x in eligible)
}
summary={
 "source_route":"MEXC public announcements endpoint + official article bodies",
 "authenticated":False,"reward_token_market_outcomes_opened":False,"btc_outcomes_opened":False,
 "calendar":["2025-01-01","2026-09-30"],"total_pages":TOTAL,
 "scan_pages":[scan_lo,scan_hi],"in_window_announcements":len(rows),
 "launchpool_title_rows":len(launch),"article_bodies":len(articles),
 "eligible_initial_listing_events":len(eligible),"unique_symbols":len({x["symbol"] for x in eligible}),
 "years":years,"gate":gate,
 "classification":"SOURCE_GATE_PASS" if all(gate.values()) else "SOURCE_INSUFFICIENT_SAMPLE"
}
for name,obj in [("pages.json",pages),("launchpool_articles.json",articles),("eligible_events.json",eligible),("summary.json",summary)]:
    with open(f"{OUT}/{name}","w",encoding="utf-8") as f:json.dump(obj,f,ensure_ascii=False,indent=2)
print(json.dumps(summary,indent=2))
