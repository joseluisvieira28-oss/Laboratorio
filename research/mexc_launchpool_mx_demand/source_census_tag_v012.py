import requests, re, json, os, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse

OUT="artifacts/mexc_launchpool_mx_demand_v012_source"
os.makedirs(OUT,exist_ok=True)
BASE="https://www.mexc.com"
TAG="https://www.mexc.com/en-GB/announcements/tag/launchpool-28"
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; CryptoLabResearch/1.0)"})

def norm(u):
    u=urljoin(BASE,u)
    p=urlparse(u)
    return urlunparse((p.scheme,p.netloc,p.path,"","",""))

def get(url):
    r=S.get(url,timeout=30)
    r.raise_for_status()
    return r.text

archive_pages=[]
links=[]
seen=set()
empty_streak=0
for page in range(1,31):
    url=TAG if page==1 else TAG+f"?page={page}"
    html=get(url)
    soup=BeautifulSoup(html,"html.parser")
    page_links=[]
    for a in soup.find_all("a",href=True):
        href=norm(a["href"])
        if "/announcements/article/" in href:
            txt=" ".join(a.get_text(" ",strip=True).split())
            if href not in seen:
                seen.add(href)
                links.append({"url":href,"anchor_text":txt,"archive_page":page})
                page_links.append(href)
    archive_pages.append({"page":page,"url":url,"new_article_links":len(page_links)})
    if not page_links:
        empty_streak+=1
        if empty_streak>=2: break
    else:
        empty_streak=0
    time.sleep(0.05)

date_re=re.compile(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b")
epoch_patterns=[
 re.compile(r'(?i)"(?:publishTime|publish_time|releaseTime|release_time|createdAt|created_at|publishDate|publish_date)"\s*:\s*"?([0-9]{10,13})"?'),
 re.compile(r'(?i)(?:publishTime|releaseTime|createdAt)[^0-9]{0,30}([0-9]{13})')
]
mx_patterns=[
 re.compile(r"\bMX\s+Staking\s+Pool\b",re.I),
 re.compile(r"\bStake(?:\s+Eligible\s+Tokens)?[^.]{0,160}\bMX\b",re.I),
 re.compile(r"\bstake\s+(?:USDT\s*,?\s*)?MX\b",re.I),
 re.compile(r"\bstake\s+MX\b",re.I),
]
rows=[]
for i,item in enumerate(links,1):
    html=get(item["url"])
    soup=BeautifulSoup(html,"html.parser")
    og=soup.find("meta",attrs={"property":"og:title"})
    h1=soup.find("h1")
    title=(og.get("content","") if og else "") or (h1.get_text(" ",strip=True) if h1 else "") or item["anchor_text"]
    text=" ".join(soup.get_text(" ",strip=True).split())
    low=(title+" "+text).lower()
    dates=sorted(set("-".join(m.groups()) for m in date_re.finditer(text[:5000])))
    epochs=[]
    for pat in epoch_patterns:
        epochs += pat.findall(html)
    epochs=sorted(set(epochs))
    explicit_mx=any(p.search(text) for p in mx_patterns)
    generic_doc=bool(re.search(r"FAQ|Upgrade|Renamed|Early Conclusion|Help",title,re.I))
    is_launch="launchpool" in low
    eligible=is_launch and explicit_mx and not generic_doc
    rows.append({
      "url":item["url"],
      "archive_page":item["archive_page"],
      "title":title,
      "date_candidates":dates[:10],
      "epoch_candidates":epochs[:20],
      "explicit_mx_staking":explicit_mx,
      "generic_or_non_event":generic_doc,
      "eligible_event_candidate":eligible,
      "text_sample":text[:1600],
    })
    time.sleep(0.05)

eligible=[r for r in rows if r["eligible_event_candidate"]]
years={}
for r in eligible:
    year=None
    if r["date_candidates"]: year=int(r["date_candidates"][0][:4])
    years[str(year)]=years.get(str(year),0)+1

timestamp_complete=sum(1 for r in eligible if r["epoch_candidates"])
summary={
 "source_route":"official MEXC Launchpool tag archive + linked official articles",
 "authenticated":False,
 "market_prices_opened":False,
 "archive_pages_scanned":len(archive_pages),
 "unique_article_links":len(links),
 "eligible_mx_launchpool_candidates":len(eligible),
 "eligible_by_year":years,
 "eligible_with_epoch_timestamp_candidate":timestamp_complete,
 "all_eligible_have_epoch_timestamp_candidate": timestamp_complete==len(eligible) and len(eligible)>0,
}

for name,obj in [
 ("summary.json",summary),
 ("archive_pages.json",archive_pages),
 ("all_articles.json",rows),
 ("eligible_mx_launchpool_candidates.json",eligible),
]:
    with open(f"{OUT}/{name}","w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)

print(json.dumps(summary,indent=2))
