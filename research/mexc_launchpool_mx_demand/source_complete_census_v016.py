import ccxt, requests, bs4, re, json, os, time, hashlib
from datetime import datetime, timezone

OUT="artifacts/mexc_launchpool_mx_demand_v016_complete_source"
os.makedirs(OUT,exist_ok=True)
ex=ccxt.mexc({"enableRateLimit":True})
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0"})

START=datetime(2024,10,18,tzinfo=timezone.utc)
END=datetime(2026,10,1,tzinfo=timezone.utc)

def iso_ms(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc)

def norm(s):
    return re.sub(r"\s+"," ",s or "").strip()

all_rows=[]
launch_rows=[]
pages=[]
page=1
while True:
    resp=ex.spot_public_get_announcements({"page":page})
    box=resp.get("data") or resp
    details=box.get("details") or []
    total_page=int(box.get("totalPage") or page)
    parsed=[]
    for r in details:
        ms=r.get("postTime")
        if ms is None: continue
        dt=iso_ms(int(ms))
        rr=dict(r)
        rr["postTime_iso"]=dt.isoformat()
        parsed.append(rr)
        if START <= dt < END:
            all_rows.append(rr)
            if "launchpool" in str(r.get("title","")).lower():
                launch_rows.append(rr)
    pages.append({
      "page":page,
      "n":len(details),
      "oldest":min((x["postTime_iso"] for x in parsed),default=None),
      "newest":max((x["postTime_iso"] for x in parsed),default=None),
    })
    if parsed and max(iso_ms(int(x["postTime"])) for x in details if x.get("postTime") is not None) < START:
        break
    if page>=total_page:
        break
    page+=1

article_records=[]
for r in launch_rows:
    url=r.get("url")
    rec={
      "title":r.get("title"),
      "url":url,
      "postTime":r.get("postTime"),
      "postTime_iso":r.get("postTime_iso"),
      "language":r.get("language"),
    }
    try:
        html=S.get(url,timeout=30).text
        soup=bs4.BeautifulSoup(html,"html.parser")
        text=norm(soup.get_text(" "))
        rec["body_sha256"]=hashlib.sha256(html.encode()).hexdigest()
        rec["body_text_sample"]=text[:6000]
        rec["explicit_mx_eligibility"]=bool(
          re.search(r"\bMX\s+Staking\s+Pool\b",text,re.I)
          or re.search(r"Stake[^.]{0,120}\bMX\b",text,re.I)
          or re.search(r"Supported Sessions\s*:\s*MX",text,re.I)
          or re.search(r"commit\s+MX",text,re.I)
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
    time.sleep(0.03)

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
 "source_route":"MEXC public announcements endpoint paginated with page + official article bodies",
 "authenticated":False,
 "market_prices_opened":False,
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
