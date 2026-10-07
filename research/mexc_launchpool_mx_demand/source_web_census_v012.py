import requests, re, json, os, time, hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

BASE="https://www.mexc.com"
TAG=BASE+"/announcements/tag/launchpool-28?page={}"
OUT="artifacts/mexc_launchpool_mx_demand_v012_source"
os.makedirs(OUT,exist_ok=True)
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; CryptoLabResearch/1.0)"})

def get(url):
    r=S.get(url,timeout=30)
    r.raise_for_status()
    return r

def norm_article_url(href):
    if not href: return None
    u=urljoin(BASE,href)
    p=urlparse(u)
    if p.netloc not in {"www.mexc.com","mexc.com"}: return None
    if "/announcements/article/" in p.path or "/support/articles/" in p.path:
        return "https://www.mexc.com"+p.path
    return None

pages=[]
article_urls=[]
seen=set()
consecutive_no_new=0
for page in range(1,81):
    try:
        r=get(TAG.format(page))
        soup=BeautifulSoup(r.text,"html.parser")
        urls=[]
        for a in soup.find_all("a",href=True):
            u=norm_article_url(a.get("href"))
            if u: urls.append(u)
        new=[u for u in urls if u not in seen]
        for u in new:
            seen.add(u); article_urls.append(u)
        pages.append({"page":page,"http":r.status_code,"links":len(urls),"new_links":len(new),
                      "sha256":hashlib.sha256(r.content).hexdigest()})
        consecutive_no_new = consecutive_no_new+1 if len(new)==0 else 0
        if page>=6 and consecutive_no_new>=3:
            break
        time.sleep(0.12)
    except Exception as e:
        pages.append({"page":page,"error":repr(e)})
        consecutive_no_new+=1
        if page>=6 and consecutive_no_new>=3: break

def extract_date(soup, html):
    # Prefer explicit structured datePublished
    for node in soup.find_all("script"):
        txt=node.string or node.get_text(" ",strip=True)
        if "datePublished" in txt:
            m=re.search(r'"datePublished"\s*:\s*"([^"]+)"',txt)
            if m: return m.group(1),"datePublished"
    # Common meta tags
    for key in ["article:published_time","date","datePublished","publish_date"]:
        tag=soup.find("meta",attrs={"property":key}) or soup.find("meta",attrs={"name":key})
        if tag and tag.get("content"): return tag["content"],"meta:"+key
    # ISO datetimes anywhere in source
    m=re.search(r'(20(?:24|25|26)-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)',html)
    if m: return m.group(1),"iso_source"
    # date-only fallback is recorded but NOT sufficient for timestamp gate
    text=soup.get_text(" ",strip=True)
    m=re.search(r'\b(20(?:24|25|26)-\d{2}-\d{2})\b',text)
    if m: return m.group(1),"date_only"
    m=re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+20(?:24|25|26)\b',text,re.I)
    if m: return m.group(0),"date_only_text"
    return None,None

articles=[]
for i,u in enumerate(article_urls,1):
    try:
        r=get(u)
        soup=BeautifulSoup(r.text,"html.parser")
        title=(soup.find("h1").get_text(" ",strip=True) if soup.find("h1") else (soup.title.get_text(" ",strip=True) if soup.title else ""))
        text=soup.get_text(" ",strip=True)
        pub,pub_source=extract_date(soup,r.text)
        launch=("launchpool" in (title+" "+text).lower())
        mx_eligible=bool(re.search(r'(stake|staking|commit|committed)[^\n]{0,120}\bMX\b|\bMX\b[^\n]{0,120}(stake|staking|pool|commit)',text,re.I))
        articles.append({
            "url":u,"title":title,"publication":pub,"publication_source":pub_source,
            "launchpool":launch,"mx_eligible_text":mx_eligible,
            "text_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "text_excerpt":text[:1200]
        })
        time.sleep(0.10)
    except Exception as e:
        articles.append({"url":u,"error":repr(e)})

eligible=[]
for a in articles:
    if a.get("launchpool") and a.get("mx_eligible_text") and a.get("publication"):
        eligible.append(a)

def year_of(x):
    p=x.get("publication") or ""
    m=re.search(r'20\d{2}',p)
    return int(m.group()) if m else None

years=sorted({year_of(x) for x in eligible if year_of(x)})
exact=[x for x in eligible if x.get("publication_source") not in {"date_only","date_only_text"}]

# Cluster by publication time only where exact ISO timestamp exists. For source gate,
# no fabricated timestamps are permitted.
def parse_dt(s):
    try:
        if s.endswith("Z"): return datetime.fromisoformat(s.replace("Z","+00:00"))
        return datetime.fromisoformat(s)
    except: return None

dts=sorted([(parse_dt(x["publication"]),x) for x in exact if parse_dt(x["publication"])],key=lambda z:z[0])
clusters=[]
for dt,x in dts:
    if not clusters or (dt-clusters[-1]["last"]).total_seconds()>3600:
        clusters.append({"first":dt,"last":dt,"urls":[x["url"]]})
    else:
        clusters[-1]["last"]=dt; clusters[-1]["urls"].append(x["url"])

summary={
 "source":"MEXC official Launchpool announcement tag + official article pages",
 "authenticated":False,
 "market_prices_opened":False,
 "archive_pages_fetched":len(pages),
 "article_urls_discovered":len(article_urls),
 "articles_fetched":sum(1 for x in articles if not x.get("error")),
 "eligible_mx_launchpool_articles":len(eligible),
 "eligible_with_exact_publication_timestamp":len(exact),
 "years":years,
 "exact_timestamp_clusters_60m":len(clusters),
 "source_gate_checks":{
   "eligible_events_ge_20":len(eligible)>=20,
   "exact_timestamp_all":len(eligible)>=20 and len(exact)==len(eligible),
   "clusters_ge_12":len(clusters)>=12,
   "years_ge_2":len(years)>=2,
   "public_read_only":True,
   "market_outcomes_unopened":True
 }
}
summary["verdict"]="SOURCE_GATE_PASS" if all(summary["source_gate_checks"].values()) else "SOURCE_GATE_INCOMPLETE_OR_BLOCKED"

for name,obj in [
 ("pages.json",pages),
 ("article_urls.json",article_urls),
 ("articles.json",articles),
 ("eligible.json",eligible),
 ("clusters.json",[{"first":c["first"].isoformat(),"last":c["last"].isoformat(),"urls":c["urls"]} for c in clusters]),
 ("source_gate_summary.json",summary)
]:
    with open(f"{OUT}/{name}","w",encoding="utf-8") as f: json.dump(obj,f,ensure_ascii=False,indent=2,default=str)
print(json.dumps(summary,indent=2))
