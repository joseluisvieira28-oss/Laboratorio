import requests,re,json
from urllib.parse import urljoin

PAGES=[
 "https://www.mexc.com/market-data-download/BTC",
 "https://www.mexc.com/market-data-download/MX",
]
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0"})
scripts=set()
for u in PAGES:
    t=S.get(u,timeout=30).text
    for m in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',t,re.I):
        scripts.add(urljoin(u,m))

found=[]
for s in sorted(scripts):
    try:
        t=S.get(s,timeout=30).text
    except Exception:
        continue
    low=t.lower()
    if not ("market-data-download" in low or ("kline" in low and "download" in low)):
        continue
    vals=set()
    for q in re.findall(r'["\']([^"\']{3,400})["\']',t):
        l=q.lower()
        if any(k in l for k in ["market-data","download","kline","history"]):
            if "/api/" in l or "http" in l or "download" in l or "kline" in l:
                vals.add(q)
    vals.update(re.findall(r'/api/[A-Za-z0-9_./?=&:\-]+',t))
    if vals:
        found.append({"script":s,"strings":sorted(vals)[:400]})

print(json.dumps(found,ensure_ascii=False,indent=2))
