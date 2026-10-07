#!/usr/bin/env python3
import json, re, hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

EVENTS=[
("US_CPI_2021-02-10","2021-02-10","2021-02-10T13:30:00Z"),
("US_CPI_2021-04-13","2021-04-13","2021-04-13T12:30:00Z"),
("US_CPI_2021-05-12","2021-05-12","2021-05-12T12:30:00Z"),
("US_CPI_2021-07-13","2021-07-13","2021-07-13T12:30:00Z"),
("US_CPI_2021-10-13","2021-10-13","2021-10-13T12:30:00Z"),
]
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; CryptoLabSourceAudit/1.0)"}
LOCALES=["uk","vi","sr","en"]
PRIMARY_COMPLETE=7
GATE_MIN_CPI=10

def get(url, timeout=6):
    return requests.get(url,headers=HEADERS,timeout=timeout,allow_redirects=True)

def sha(b): return hashlib.sha256(b).hexdigest()

def parse_iso(s):
    if not s: return None
    try:
        if s.endswith("Z"): return datetime.fromisoformat(s[:-1]+"+00:00")
        return datetime.fromisoformat(s)
    except: return None

def extract_published(soup,text):
    vals=[]
    for key in [("property","article:published_time"),("name","article:published_time"),("itemprop","datePublished")]:
        el=soup.find(attrs={key[0]:key[1]})
        if el:
            v=el.get("content") or el.get_text(" ",strip=True)
            if v: vals.append(v)
    for sc in soup.find_all("script",attrs={"type":"application/ld+json"}):
        try:
            obj=json.loads(sc.string or sc.get_text())
            objs=obj if isinstance(obj,list) else [obj]
            for o in objs:
                if isinstance(o,dict) and o.get("datePublished"): vals.append(str(o["datePublished"]))
        except: pass
    m=re.search(r"(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2})",text)
    if m: vals.append(m.group(1)+" "+m.group(2))
    return list(dict.fromkeys(vals))

def published_pre_t0(cands,t0):
    t=parse_iso(t0)
    good=[]
    for s in cands or []:
        d=parse_iso(s)
        if d is None:
            m=re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})",s.strip())
            if m:
                d=datetime(int(m.group(3)),int(m.group(2)),int(m.group(1)),int(m.group(4)),int(m.group(5)),tzinfo=timezone.utc)
        if d and d.tzinfo:
            d=d.astimezone(timezone.utc)
            if d<t: good.append((s,d))
    return good[-1] if good else None

def discover_article(date):
    token=datetime.fromisoformat(date).strftime("%d-%m-%Y")
    attempts=[]; candidates=[]
    for loc in LOCALES:
        u=f"https://www.teletrade.org/{loc}/analytics/market-analysis/market-news/date-{token}"
        try:
            r=get(u); attempts.append({"url":u,"status":r.status_code,"bytes":len(r.content)})
            if r.status_code!=200: continue
            soup=BeautifulSoup(r.text,"html.parser")
            for a in soup.find_all("a",href=True):
                href=a["href"]
                if not re.search(r"/analytics/market-analysis/market-news/\d+$",href): continue
                label=" ".join(a.get_text(" ",strip=True).split())
                parent=" ".join((a.parent.get_text(" ",strip=True) if a.parent else "").split())
                if "schedule for today" in (label+" "+parent).lower():
                    candidates.append(urljoin(r.url,href))
        except Exception as e:
            attempts.append({"url":u,"error":repr(e)})
    candidates=list(dict.fromkeys(candidates))
    best=None
    for u in candidates[:12]:
        try:
            r=get(u)
            if r.status_code!=200: continue
            soup=BeautifulSoup(r.text,"html.parser")
            title=" ".join((soup.find("h1").get_text(" ",strip=True) if soup.find("h1") else "").split())
            text=" ".join(soup.get_text(" ",strip=True).split())
            if "schedule for today" not in (title+" "+text[:600]).lower(): continue
            fields={}; relevant=[]
            for tr in soup.find_all("tr"):
                cells=[" ".join(x.get_text(" ",strip=True).split()) for x in tr.find_all(["td","th"])]
                if len(cells)<4: continue
                row=" | ".join(cells); low=row.lower()
                if not ("u.s." in low or "| us " in low or "united states" in low): continue
                forecast=cells[-1].strip()
                if "cpi excluding food and energy" in low and ("y/y" in low or "yoy" in low):
                    fields["core_yoy"]={"forecast":forecast,"row":row}
                elif "cpi excluding food and energy" in low and ("m/m" in low or "mom" in low):
                    fields["core_mom"]={"forecast":forecast,"row":row}
                elif re.search(r"\bcpi\b",low) and ("y/y" in low or "yoy" in low):
                    fields["headline_yoy"]={"forecast":forecast,"row":row}
                elif re.search(r"\bcpi\b",low) and ("m/m" in low or "mom" in low):
                    fields["headline_mom"]={"forecast":forecast,"row":row}
                if "cpi" in low: relevant.append(row)
            rec={"url":r.url,"sha256":sha(r.content),"title":title,"published_candidates":extract_published(soup,text),
                 "fields":fields,"relevant_rows":relevant[:20]}
            if best is None or len(fields)>len(best["fields"]): best=rec
            if len(fields)>=4: break
        except Exception as e:
            attempts.append({"url":u,"error":repr(e)})
    return best,attempts,candidates

results=[]
for eid,date,t0 in EVENTS:
    art,attempts,cands=discover_article(date)
    pre=published_pre_t0(art.get("published_candidates",[]) if art else [],t0)
    vals={k:(art.get("fields",{}).get(k,{}).get("forecast") if art else None) for k in ["headline_mom","headline_yoy","core_mom","core_yoy"]}
    complete=bool(art and pre and all(v not in [None,"","--","—"] for v in vals.values()))
    results.append({"event_id":eid,"date":date,"t0_utc":t0,"article":art,"pre_t0":str(pre) if pre else None,
                    "values":vals,"fallback_complete":complete,"archive_attempts":attempts,"article_candidates":cands})
    print(eid,"COMPLETE" if complete else "INCOMPLETE",vals)

fallback_complete=sum(1 for r in results if r["fallback_complete"])
total_complete=PRIMARY_COMPLETE+fallback_complete
verdict="DANSKE_TELETRADE_CPI_SOURCE_CENSUS_PASS" if total_complete>=GATE_MIN_CPI else "DANSKE_TELETRADE_CPI_COVERAGE_BLOCKED"
out={"probe_id":"NEWS-SHOCK-V03-DANSKE-TELETRADE-CPI-2021-001","generated_at_utc":datetime.now(timezone.utc).isoformat(),
     "scope":"SOURCE_ONLY","primary_complete":PRIMARY_COMPLETE,"fallback_complete":fallback_complete,
     "total_complete_cpi":total_complete,"gate_minimum":GATE_MIN_CPI,"verdict":verdict,"results":results,"outcomes_opened":False}
open("teletrade_cpi_fallback_2021_probe.json","w",encoding="utf-8").write(json.dumps(out,indent=2,ensure_ascii=False))
with open("teletrade_cpi_fallback_2021_probe.md","w",encoding="utf-8") as f:
    f.write(f"# Danske-TeleTrade CPI 2021 census\n\n**Verdict:** {verdict}\n\n")
    f.write(f"Primary Danske complete: **{PRIMARY_COMPLETE}/12**. TeleTrade fallback complete among 5 missing: **{fallback_complete}/5**. Total: **{total_complete}/12** (gate >=10).\n\n")
    for r in results:
        f.write(f"## {r['event_id']} — {'COMPLETE' if r['fallback_complete'] else 'INCOMPLETE'}\n")
        f.write(f"- Values: `{json.dumps(r['values'],ensure_ascii=False)}`\n")
        if r['article']:
            f.write(f"- TeleTrade: {r['article']['url']}\n- Published: {r['article']['published_candidates']}\n- Pre-T0: {r['pre_t0']}\n\n")
print(json.dumps({"verdict":verdict,"fallback_complete":fallback_complete,"total_complete_cpi":total_complete},indent=2))
