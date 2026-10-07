#!/usr/bin/env python3
import json,re,requests
from bs4 import BeautifulSoup
from datetime import datetime,timezone
BASE="https://www.mexc.com"
PAGES=[1,2,5,10,25,50,100,200,400,800,1199]
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-MFIBR/0.1","Accept-Language":"en-US,en;q=0.9"})
MONTHS={m:i for i,m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],1)}
DATE_RE=re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(20\d{2})\b")
for p in PAGES:
    u=f"{BASE}/announcements/tag/19?page={p}"
    try:
        r=S.get(u,timeout=35,allow_redirects=True)
        print("PAGE_HTTP",p,r.status_code,"LEN",len(r.content),"FINAL",r.url)
        soup=BeautifulSoup(r.text,"html.parser")
        links=[]
        for a in soup.find_all("a",href=True):
            href=a.get("href","")
            if "/announcements/article/" not in href and "/support/articles/" not in href: continue
            title=" ".join(a.get_text(" ",strip=True).split())
            card=a
            txt=title
            for _ in range(5):
                if card.parent is None: break
                card=card.parent
                z=" ".join(card.get_text(" ",strip=True).split())
                if len(z)>len(txt): txt=z
                if DATE_RE.search(z): break
            m=DATE_RE.search(txt)
            dt=None
            if m:
                dt=datetime(int(m.group(3)),MONTHS[m.group(1)],int(m.group(2)),tzinfo=timezone.utc)
            links.append({"href":href,"title":title[:180],"date":dt.isoformat() if dt else None})
        dd={x["href"]:x for x in links}
        vals=list(dd.values())
        dates=[datetime.fromisoformat(x["date"]) for x in vals if x["date"]]
        print("PAGE_META",p,"ARTICLES",len(vals),
              "MIN",min(dates).isoformat() if dates else None,
              "MAX",max(dates).isoformat() if dates else None)
        print("PAGE_ROWS",p,json.dumps(vals[:12],ensure_ascii=False))
    except Exception as e:
        print("PAGE_ERR",p,type(e).__name__,str(e))
