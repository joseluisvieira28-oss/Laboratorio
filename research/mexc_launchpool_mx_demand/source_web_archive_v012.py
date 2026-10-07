import requests, bs4, re, json, os, time, hashlib
from urllib.parse import urljoin
from datetime import datetime, timezone

BASE="https://www.mexc.com"
OUT="artifacts/mexc_launchpool_mx_demand_v012_web_source"
os.makedirs(OUT,exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0"})

def get(url):
    r=S.get(url,timeout=30)
    r.raise_for_status()
    return r.text

def norm(s):
    return re.sub(r"\s+"," ",s or "").strip()

article_urls=[]
page_receipts=[]
for page in range(1,11):
    url=f"{BASE}/announcements/tag/launchpool-28?page={page}"
    try:
        html=get(url)
        h=hashlib.sha256(html.encode()).hexdigest()
        soup=bs4.BeautifulSoup(html,"html.parser")
        links=[]
        for a in soup.find_all("a",href=True):
            href=a["href"]
            if "/announcements/article/" in href:
                full=urljoin(BASE,href.split("?")[0])
                links.append(full)
        links=sorted(set(links))
        page_receipts.append({"page":page,"url":url,"sha256":h,"article_links":len(links)})
        article_urls.extend(links)
        if not links and page>4:
            break
    except Exception as e:
        page_receipts.append({"page":page,"url":url,"error":repr(e)})
        break
article_urls=sorted(set(article_urls))

articles=[]
for i,url in enumerate(article_urls):
    try:
        html=get(url)
        soup=bs4.BeautifulSoup(html,"html.parser")
        text=norm(soup.get_text(" "))
        title=norm((soup.title.get_text(" ") if soup.title else ""))[:500]
        # look for canonical English-style publication date in rendered article text
        dm=re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+20\d{2}\b",text)
        date_txt=dm.group(0) if dm else None
        dt=None
        if date_txt:
            dt=datetime.strptime(date_txt,"%b %d, %Y").replace(tzinfo=timezone.utc)
        is_launch="launchpool" in text.lower()
        has_mx=bool(re.search(r"\bMX\b",text,re.I))
        explicit_mx_pool=bool(re.search(r"MX\s+(Staking\s+Pool|staking|pool|or\s+USDT|,\s*USDT|or\s+[A-Z0-9]+)",text,re.I))
        articles.append({
            "url":url,
            "title":title,
            "date":date_txt,
            "date_iso":dt.isoformat() if dt else None,
            "is_launchpool":is_launch,
            "has_mx":has_mx,
            "explicit_mx_eligibility":explicit_mx_pool,
            "sha256":hashlib.sha256(html.encode()).hexdigest(),
            "text_sample":text[:2500],
        })
    except Exception as e:
        articles.append({"url":url,"error":repr(e)})
    time.sleep(0.05)

start=datetime(2024,10,18,tzinfo=timezone.utc)
end=datetime(2026,10,1,tzinfo=timezone.utc)
eligible=[]
for a in articles:
    if a.get("error") or not a.get("date_iso"): continue
    dt=datetime.fromisoformat(a["date_iso"])
    if not (start <= dt < end): continue
    if not a.get("is_launchpool") or not a.get("explicit_mx_eligibility"): continue
    # exclude obvious FAQ/product-update/general docs, keep event-like titles/text
    low=(a.get("title") or "").lower()
    if any(x in low for x in ["faq","what is launchpool","upgrade","renamed","rename"]): continue
    eligible.append(a)

# collapse exact duplicate URL only; cluster by calendar hour conservatively
eligible=sorted(eligible,key=lambda x:x["date_iso"])
years=sorted(set(datetime.fromisoformat(x["date_iso"]).year for x in eligible))
clusters=[]
for a in eligible:
    dt=datetime.fromisoformat(a["date_iso"])
    if not clusters or (dt-datetime.fromisoformat(clusters[-1]["last"])).total_seconds()>3600:
        clusters.append({"first":a["date_iso"],"last":a["date_iso"],"urls":[a["url"]]})
    else:
        clusters[-1]["last"]=a["date_iso"]; clusters[-1]["urls"].append(a["url"])

summary={
 "source":"MEXC official public Launchpool tag/archive + article pages",
 "authenticated":False,
 "market_prices_opened":False,
 "pages_attempted":len(page_receipts),
 "article_urls":len(article_urls),
 "articles_parsed":sum(1 for x in articles if not x.get("error")),
 "eligible_events":len(eligible),
 "independent_clusters":len(clusters),
 "years":years,
 "source_gate":{
   "events_ge_20":len(eligible)>=20,
   "clusters_ge_12":len(clusters)>=12,
   "years_ge_2":len(years)>=2,
   "timestamps_complete":all(x.get("date_iso") for x in eligible),
 },
}
summary["classification"]="SOURCE_GATE_PASS" if all(summary["source_gate"].values()) else "SOURCE_INSUFFICIENT_SAMPLE"

for name,obj in [
 ("page_receipts.json",page_receipts),
 ("article_index.json",articles),
 ("eligible_events.json",eligible),
 ("clusters.json",clusters),
 ("source_summary.json",summary),
]:
    with open(f"{OUT}/{name}","w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
print(json.dumps(summary,indent=2))
