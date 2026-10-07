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

print("=== NEXT/API DIAG ===")
r=s.get("https://miniapp.gate.com/announcements/fee",timeout=30)
html=r.text
for pat in [
    r'https?://[^"\\s]+',
    r"[^\\\"'\\s]{0,100}(?:announcement|article|category|pageSize|currentPage|list)[^\\\"'\\s]{0,160}",
]:
    vals=[]
    for m in re.finditer(pat,html,re.I):
        v=m.group(0)
        if any(k in v.lower() for k in ("api","announcement","page","category")):
            vals.append(v[:320])
    seen=[]
    for v in vals:
        if v not in seen: seen.append(v)
    print("PATTERN",pat)
    print(json.dumps(seen[:120],ensure_ascii=False))

print("=== CATEGORY CHUNK DIAG ===")
soup=BeautifulSoup(html,"html.parser")
srcs=[x.get("src") for x in soup.find_all("script",src=True) if "announcements" in x.get("src","") and "category" in x.get("src","")]
print("CATEGORY_SCRIPTS",json.dumps(srcs))
for src in srcs:
    u=src if src.startswith("http") else "https://miniapp.gate.com"+src
    rr=s.get(u,timeout=30)
    print("CHUNK",u,rr.status_code,len(rr.text))
    vals=[]
    for m in re.finditer(r'.{0,140}(?:api|announcement|article|category|pageSize|page_size|limit|offset).{0,220}',rr.text,re.I):
        v=m.group(0)
        if any(k in v.lower() for k in ("announcement","article","api/","category")):
            vals.append(v)
    seen=[]
    for v in vals:
        if v not in seen: seen.append(v)
    print("CHUNK_HINTS",json.dumps(seen[:160],ensure_ascii=False))

print("=== ALL SCRIPT API DIAG ===")
all_srcs=[x.get("src") for x in soup.find_all("script",src=True)]
for src in all_srcs[:80]:
    u=src if src.startswith("http") else "https://miniapp.gate.com"+src
    try:
        rr=s.get(u,timeout=20)
    except Exception:
        continue
    txt=rr.text
    if "75418:" in txt or ("announcement" in txt.lower() and ("/api/" in txt.lower() or "article" in txt.lower())):
        hints=[]
        for m in re.finditer(r'.{0,180}(?:75418:|/api/|announcement|article).{0,280}',txt,re.I):
            hints.append(m.group(0))
        print("SCRIPT_HIT",u,"LEN",len(txt),"MODULE75418",("75418:" in txt))
        print("SCRIPT_HINTS",json.dumps(hints[:80],ensure_ascii=False))

print("=== NEXT DATA ===")
nd=soup.find("script",id="__NEXT_DATA__")
if nd and nd.string:
    obj=json.loads(nd.string)
    pp=(obj.get("props") or {}).get("pageProps") or {}
    print("PAGEPROPS_KEYS",json.dumps(sorted(pp.keys())))
    cats=pp.get("categories")
    ld=pp.get("listData")
    print("CATEGORIES",json.dumps(cats,ensure_ascii=False)[:12000])
    print("LISTDATA",json.dumps(ld,ensure_ascii=False)[:12000])

print("=== LIST ENDPOINT PROBE ===")
ep="https://miniapp.gate.com/api/web/v1/portal/announcement/list_article"
payloads=[
 {"cate":"fee","page":2,"page_size":15,"cate_level":1},
 {"cate":"fees-precision","page":2,"page_size":15,"cate_level":1},
 {"category":"fee","page":2,"page_size":15,"cate_level":1},
 {"cate":"fee","page":2,"pageSize":15,"cate_level":1},
 {"cate":"fee","page":2,"page_size":15,"cate_level":2},
]
for p in payloads:
    for mode in ("json","form","get"):
        try:
            if mode=="json": rr=s.post(ep,json=p,timeout=20)
            elif mode=="form": rr=s.post(ep,data=p,timeout=20)
            else: rr=s.get(ep,params=p,timeout=20)
            sample=rr.text[:600].replace("\n"," ")
            ids=re.findall(r'"id"\s*:\s*(\d+)',rr.text)
            print("EP_PROBE",mode,json.dumps(p,sort_keys=True),"STATUS",rr.status_code,"IDS",ids[:5],"SAMPLE",sample)
        except Exception as e:
            print("EP_ERR",mode,json.dumps(p,sort_keys=True),type(e).__name__,str(e))

print("=== CATEGORY ID + PAYLOAD PROBE ===")
matches=[]
def walkcats(xs):
    for x in xs or []:
        if "fee" in str(x.get("cate","")).lower() or "fee" in str(x.get("name","")).lower() or int(x.get("id",0) or 0) in (54,55):
            matches.append(x)
        walkcats(x.get("children") or [])
walkcats(cats)
print("FEE_CATEGORY_MATCHES",json.dumps(matches,ensure_ascii=False))
for p in [
 {"cate_id":55,"page":2,"page_size":15,"cate_level":1},
 {"category_id":55,"page":2,"page_size":15,"cate_level":1},
 {"cate":55,"page":2,"page_size":15,"cate_level":1},
 {"id":55,"page":2,"page_size":15,"cate_level":1},
 {"cate_id":54,"page":2,"page_size":15,"cate_level":1},
]:
    try:
        rr=s.post(ep,json=p,timeout=20)
        j=rr.json()
        d=j.get("data") or {}
        rows=d.get("list") or []
        print("CATID_PROBE",json.dumps(p,sort_keys=True),"CODE",j.get("code"),"TOTAL",d.get("total"),"IDS",[x.get("id") for x in rows[:6]],"CATES",[x.get("cate_id") for x in rows[:6]])
    except Exception as e:
        print("CATID_ERR",json.dumps(p,sort_keys=True),type(e).__name__,str(e))

print("=== STORE MODULE 80922 ===")
for src in all_srcs[:80]:
    u=src if src.startswith("http") else "https://miniapp.gate.com"+src
    try:
        rr=s.get(u,timeout=20)
    except Exception:
        continue
    txt=rr.text
    pos=txt.find("80922:function")
    if pos>=0:
        print("STORE_SCRIPT",u,"POS",pos,"LEN",len(txt))
        print("STORE_SNIP",txt[pos:pos+12000])

print("=== EXACT STORE PAYLOAD ===")
p={"cate_name":"fee","page":2,"size":15,"tags":"","timer":"","cate_level":2}
rr=s.post(ep,json=p,timeout=20)
j=rr.json(); d=j.get("data") or {}; rows=d.get("list") or []
print("EXACT_PAYLOAD_RESULT","CODE",j.get("code"),"TOTAL",d.get("total"),
      "IDS",[x.get("id") for x in rows],
      "CATES",[x.get("cate_id") for x in rows],
      "DATES",[x.get("release_time") for x in rows])
