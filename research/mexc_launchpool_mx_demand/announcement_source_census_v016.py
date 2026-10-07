import ccxt, requests, re, json, os, time, hashlib
from datetime import datetime, timezone

OUT="artifacts/mlmxd_v016_source_census"
os.makedirs(OUT,exist_ok=True)
ex=ccxt.mexc({"enableRateLimit":True})
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (CryptoLabResearch/1.0)"})

START=int(datetime(2024,10,18,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,9,30,23,59,59,tzinfo=timezone.utc).timestamp()*1000)

def page_rows(page):
    x=ex.spot_public_get_announcements({"page":page})
    box=x["data"][0]
    return box.get("details",[]), int(box.get("totalPage",0))

def bounds(page):
    rows,total=page_rows(page)
    ts=[int(r["postTime"]) for r in rows if r.get("postTime")]
    return (max(ts) if ts else None,min(ts) if ts else None,total,rows)

# Find first page whose content reaches END or earlier.
# Pages are newest -> oldest.
p=1
hi=None
_,lo,total,_=bounds(1)
# Exponential search until oldest timestamp <= END
step=1
while True:
    newest,oldest,total,rows=bounds(p)
    if oldest is not None and oldest<=END:
        hi=p; break
    p+=step; step*=2
    if p>total: hi=total; break
# Binary search earliest page with oldest<=END
l=1; r=hi
while l<r:
    m=(l+r)//2
    newest,oldest,total,_=bounds(m)
    if oldest is not None and oldest<=END: r=m
    else: l=m+1
first=l

# Find last page whose newest timestamp >= START
l=first; r=total
last=first
while l<=r:
    m=(l+r)//2
    newest,oldest,total,_=bounds(m)
    if newest is not None and newest>=START:
        last=m; l=m+1
    else:
        r=m-1

raw=[]
for page in range(first,last+1):
    rows,total=page_rows(page)
    for x in rows:
        ts=int(x.get("postTime") or 0)
        if START<=ts<=END:
            raw.append({
                "title":x.get("title",""),
                "url":x.get("url",""),
                "postTime":ts,
                "page":page
            })

# Deduplicate by URL+postTime
seen=set(); uniq=[]
for r0 in raw:
    k=(r0["url"],r0["postTime"])
    if k not in seen:
        seen.add(k); uniq.append(r0)

launch=[r for r in uniq if "launchpool" in r["title"].lower()]

mx_patterns=[
 re.compile(r"\bMX\s+Staking\s+Pool\b",re.I),
 re.compile(r"\bStake\s+MX\b",re.I),
 re.compile(r"\bstake[^.]{0,160}\bMX\b",re.I),
 re.compile(r"\bMX\b[^.]{0,120}\bstaking\b",re.I)
]
exclude_title=re.compile(r"FAQ|Upgrade|Renamed|Early Conclusion|Help|Guide",re.I)

eligible=[]
body_fail=[]
for i,a in enumerate(launch,1):
    try:
        url=a["url"]
        if url.startswith("/"): url="https://www.mexc.com"+url
        h=S.get(url,timeout=30).text
        text=re.sub(r"<script[\s\S]*?</script>"," ",h,flags=re.I)
        text=re.sub(r"<style[\s\S]*?</style>"," ",text,flags=re.I)
        text=re.sub(r"<[^>]+>"," ",text)
        text=re.sub(r"\s+"," ",text)
        explicit=any(p.search(text) for p in mx_patterns)
        generic=bool(exclude_title.search(a["title"]))
        rec=dict(a); rec.update({"resolved_url":url,"explicit_mx":explicit,"generic":generic})
        if explicit and not generic:
            eligible.append(rec)
        time.sleep(0.02)
    except Exception as e:
        body_fail.append({"article":a,"error":repr(e)})

# Collapse duplicate/same-information announcements by <=60m.
eligible=sorted(eligible,key=lambda x:x["postTime"])
clusters=[]
for e in eligible:
    if not clusters or e["postTime"]-clusters[-1]["last_postTime"]>60*60*1000:
        clusters.append({"cluster_id":len(clusters)+1,"first_postTime":e["postTime"],"last_postTime":e["postTime"],"events":[e]})
    else:
        clusters[-1]["events"].append(e)
        clusters[-1]["last_postTime"]=e["postTime"]

years=sorted(set(datetime.fromtimestamp(e["postTime"]/1000,timezone.utc).year for e in eligible))
summary={
 "authenticated":False,
 "market_prices_opened":False,
 "first_page":first,
 "last_page":last,
 "pages_scanned":last-first+1,
 "announcements_in_window":len(uniq),
 "launchpool_title_articles":len(launch),
 "eligible_mx_events":len(eligible),
 "independent_clusters":len(clusters),
 "calendar_years":years,
 "body_fetch_failures":len(body_fail),
 "all_eligible_have_postTime":all(bool(e["postTime"]) for e in eligible),
}
summary["source_gate_pass"]=(
    summary["eligible_mx_events"]>=20 and
    summary["independent_clusters"]>=12 and
    len(years)>=2 and
    summary["all_eligible_have_postTime"] and
    summary["body_fetch_failures"]==0
)
summary["classification"]="SOURCE_GATE_PASS" if summary["source_gate_pass"] else "SOURCE_INSUFFICIENT_OR_INCOMPLETE"

for name,obj in [
 ("summary.json",summary),
 ("eligible_events.json",eligible),
 ("clusters.json",clusters),
 ("launchpool_articles.json",launch),
 ("body_failures.json",body_fail),
]:
    with open(f"{OUT}/{name}","w",encoding="utf-8") as f: json.dump(obj,f,ensure_ascii=False,indent=2)
print(json.dumps(summary,indent=2))
for e in eligible:
    print(datetime.fromtimestamp(e["postTime"]/1000,timezone.utc).isoformat(),e["title"])
