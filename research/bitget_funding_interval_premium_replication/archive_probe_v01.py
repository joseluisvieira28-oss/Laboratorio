#!/usr/bin/env python3
import json,re,time,hashlib
from datetime import datetime,timezone
import requests
from bs4 import BeautifulSoup

BASE="https://www.bitget.com"
SECTION="/support/sections/12508313445234"
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/140 CryptoLab-BGFIPR/0.1","Accept-Language":"en-US,en;q=0.9"})

DATE_RE=re.compile(r"(20\d{2})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})")
ARTICLE_RE=re.compile(r"/support/articles/(\d+)")

def parse_page(html):
    soup=BeautifulSoup(html,"html.parser")
    rows={}
    for a in soup.find_all("a",href=True):
        href=a.get("href","")
        m=ARTICLE_RE.search(href)
        if not m: continue
        aid=m.group(1)
        # Walk a few ancestors to capture title + nearby date.
        card=a
        best=""
        for _ in range(5):
            txt=" ".join(card.get_text(" ",strip=True).split())
            if len(txt)>len(best): best=txt
            if DATE_RE.search(txt): break
            if card.parent is None: break
            card=card.parent
        txt=best or " ".join(a.get_text(" ",strip=True).split())
        dm=DATE_RE.search(txt)
        dt=None
        if dm:
            dt=datetime(int(dm.group(1)),int(dm.group(2)),int(dm.group(3)),int(dm.group(4)),int(dm.group(5)),tzinfo=timezone.utc)
        title=" ".join(a.get_text(" ",strip=True).split())
        rows[aid]={"id":aid,"url":BASE+href if href.startswith("/") else href,"title":title,"card_text":txt,"listed_utc":dt.isoformat().replace("+00:00","Z") if dt else None}
    return list(rows.values())

def main():
    allrows={}
    pages=[]
    crossed=False
    for p in range(1,121):
        u=f"{BASE}{SECTION}/{p}"
        r=S.get(u,timeout=40)
        print("PAGE",p,"HTTP",r.status_code,"LEN",len(r.content))
        if r.status_code!=200:
            break
        rows=parse_page(r.text)
        dates=[datetime.fromisoformat(x["listed_utc"].replace("Z","+00:00")) for x in rows if x["listed_utc"]]
        pages.append({"page":p,"count":len(rows),"ids":[x["id"] for x in rows],
                      "min_date":min(dates).isoformat() if dates else None,
                      "max_date":max(dates).isoformat() if dates else None,
                      "sha256":hashlib.sha256(r.content).hexdigest()})
        for x in rows: allrows[x["id"]]=x
        print("PAGE_ROWS",p,len(rows),"MIN",min(dates).isoformat() if dates else None,"MAX",max(dates).isoformat() if dates else None)
        if dates and min(dates)<datetime(2024,1,1,tzinfo=timezone.utc):
            crossed=True
            break
        if not rows:
            break
        time.sleep(0.15)
    win=[x for x in allrows.values() if x["listed_utc"] and datetime(2024,1,1,tzinfo=timezone.utc)<=datetime.fromisoformat(x["listed_utc"].replace("Z","+00:00"))<=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)]
    def cand(x):
        z=(x["title"]+" "+x["card_text"]).lower()
        return "funding" in z and ("interval" in z or "frequency" in z) and "perpetual" in z
    c=[x for x in win if cand(x)]
    print("ENUMERATED_UNIQUE="+str(len(allrows)))
    print("CROSSED_PRE2024="+str(crossed))
    print("IN_WINDOW="+str(len(win)))
    print("CANDIDATES="+str(len(c)))
    print("CANDIDATE_YEARS="+json.dumps(sorted({int(x["listed_utc"][:4]) for x in c})))
    print("CANDIDATE_ROWS="+json.dumps(sorted(c,key=lambda x:x["listed_utc"]),ensure_ascii=False))
    open("bgfipr_archive_probe.json","w",encoding="utf-8").write(json.dumps({"pages":pages,"crossed_pre2024":crossed,"rows":list(allrows.values()),"candidates":c},indent=2,sort_keys=True))
if __name__=="__main__":
    main()
