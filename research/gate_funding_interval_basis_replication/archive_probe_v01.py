#!/usr/bin/env python3
import json,re,requests
from bs4 import BeautifulSoup
URLS=[
 "https://www.gate.com/announcements/fee",
 "https://www.gate.com/announcements/fee?page=2",
 "https://www.gate.com/announcements/fee/2",
 "https://miniapp.gate.com/announcements/fee",
 "https://miniapp.gate.com/announcements/fee?page=2",
]
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-GFIBR/0.1","Accept-Language":"en-US,en;q=0.9"})
for u in URLS:
    try:
        r=s.get(u,timeout=30,allow_redirects=True)
        print("URL",u,"STATUS",r.status_code,"FINAL",r.url,"LEN",len(r.text))
        soup=BeautifulSoup(r.text,"html.parser")
        links=[]
        for a in soup.find_all("a",href=True):
            href=a["href"]
            txt=" ".join(a.get_text(" ",strip=True).split())
            if "/announcements/article/" in href:
                links.append((href,txt[:140]))
        print("ARTICLE_LINKS",len(links))
        print(json.dumps(links[:20],ensure_ascii=False))
        print("PAGE_HINTS",json.dumps(sorted(set(re.findall(r'page[^\"\']{0,25}',r.text,re.I)))[:40]))
    except Exception as e:
        print("ERR",u,type(e).__name__,str(e))
