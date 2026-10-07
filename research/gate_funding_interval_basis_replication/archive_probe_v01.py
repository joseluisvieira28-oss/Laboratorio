#!/usr/bin/env python3
import json,re,requests,datetime
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

print("=== DEEP MINIAPP DIAG ===")
for u in ["https://miniapp.gate.com/announcements/fee","https://miniapp.gate.com/announcements/fee?page=2"]:
    r=s.get(u,timeout=30,allow_redirects=True)
    soup=BeautifulSoup(r.text,"html.parser")
    rows=[]
    for a in soup.find_all("a",href=True):
        href=a.get("href","")
        if "/announcements/article/" in href:
            rows.append((href," ".join(a.get_text(" ",strip=True).split())[:120]))
    print("DEEP_URL",u)
    print("DEEP_LINKS",json.dumps(rows,ensure_ascii=False))
    nd=soup.find("script",id="__NEXT_DATA__")
    if nd:
        txt=nd.string or nd.get_text()
        print("NEXT_DATA_LEN",len(txt))
        print("NEXT_DATA_HEAD",txt[:1200])
        for pat in ["announcements","category","fee","pageSize","pageNum","total","list"]:
            if pat.lower() in txt.lower():
                print("NEXT_HAS",pat)
        # print compact snippets around likely API/path markers
        for m in re.finditer(r'(?i)(api[^"\\]{0,180}|announcement[^"\\]{0,220}|pageSize[^,}]{0,80}|pageNum[^,}]{0,80})',txt):
            z=m.group(0)
            if len(z)>20:
                print("NEXT_SNIP",z[:260])
    for sc in soup.find_all("script",src=True):
        src=sc.get("src","")
        if "announcements" in src or "_next/static/chunks/pages/announcements" in src:
            print("SCRIPT_SRC",src)

print("=== LIGHTWEIGHT OFFICIAL FEE CENSUS ===")
r=s.get("https://miniapp.gate.com/announcements/fee",timeout=30)
sp=BeautifulSoup(r.text,"html.parser")
nd=sp.find("script",id="__NEXT_DATA__")
obj=json.loads(nd.string)
pp=((obj.get("props") or {}).get("pageProps") or {})
ld=pp.get("listData") or {}
total=int(ld.get("total") or 0)
allrows=list(ld.get("list") or [])
for pg in range(2,30):
    p={"cate_name":"fee","page":pg,"size":15,"tags":"","timer":"","cate_level":2}
    rr=s.post(ep,json=p,timeout=30)
    j=rr.json(); d=j.get("data") or {}; rows=d.get("list") or []
    allrows.extend(rows)
    if len({int(x["id"]):x for x in allrows if x.get("id") is not None})>=total:
        break
    if not rows:
        break
dd={int(x["id"]):x for x in allrows if x.get("id") is not None}
rows=list(dd.values())
def is_candidate(x):
    z=((x.get("title") or "")+" "+(x.get("brief") or "")).lower()
    return "funding" in z and ("interval" in z or "frequency" in z or "settlement" in z) and ("adjust" in z or "change" in z or "frequency" in z)
win=[]
for x in rows:
    ts=int(x.get("release_timestamp") or 0)
    if not ts: continue
    y=datetime.datetime.fromtimestamp(ts,datetime.timezone.utc).year
    if 2023<=y<=2025:
        win.append(x)
cand=[x for x in win if is_candidate(x)]
print("CENSUS_TOTAL_EXPECTED",total)
print("CENSUS_ENUMERATED",len(rows))
print("CENSUS_IN_WINDOW",len(win))
print("CENSUS_CANDIDATES",len(cand))
print("CENSUS_CANDIDATE_YEARS",json.dumps(sorted({datetime.datetime.fromtimestamp(int(x["release_timestamp"]),datetime.timezone.utc).year for x in cand})))
print("CENSUS_CANDIDATE_ROWS",json.dumps([
  {"id":x.get("id"),"date":x.get("release_time"),"cate_id":x.get("cate_id"),"title":x.get("title"),"brief":x.get("brief")}
  for x in sorted(cand,key=lambda q:int(q.get("release_timestamp") or 0))
],ensure_ascii=False))

print("=== FUNDING TIMESTAMP TRANSPORT BENCH ===")
import time as _time
for contract,eff in [
 ("RARE_USDT", datetime.datetime(2024,8,19,8,0,tzinfo=datetime.timezone.utc)),
 ("LPT_USDT", datetime.datetime(2025,5,30,12,0,tzinfo=datetime.timezone.utc)),
]:
    lo=int((eff-datetime.timedelta(days=5)).timestamp())
    hi=int((eff+datetime.timedelta(days=5)).timestamp())
    u="https://api.gateio.ws/api/v4/futures/usdt/funding_rate"
    t0=_time.time()
    try:
        rr=s.get(u,params={"contract":contract,"from":lo,"to":hi},timeout=30)
        elapsed=_time.time()-t0
        print("FUND_BENCH_HTTP",contract,rr.status_code,"ELAPSED",round(elapsed,3),"LEN",len(rr.content),"ERRBODY",(rr.text[:300] if rr.status_code!=200 else ""))
        if rr.status_code==200:
            arr=rr.json()
            ts=sorted({int(x["t"]) for x in arr if isinstance(x,dict) and str(x.get("t","")).isdigit()})
            gaps=[round((b-a)/3600,4) for a,b in zip(ts,ts[1:])]
            print("FUND_BENCH_TS",contract,"COUNT",len(ts),"FIRST",ts[:4],"LAST",ts[-4:],"GAPS",gaps[:12])
    except Exception as e:
        print("FUND_BENCH_ERR",contract,type(e).__name__,str(e))

print("=== GATE BATCH FUNDING TIMESTAMP RETENTION ===")
batch="https://api.gateio.ws/api/v4/futures/usdt/funding_rates"
for contracts in [["LPT_USDT"],["RARE_USDT"],["LPT_USDT","RARE_USDT"]]:
    try:
        rr=s.post(batch,json={"contracts":contracts},timeout=30)
        print("BATCH_HTTP",json.dumps(contracts),rr.status_code,"LEN",len(rr.content),
              "ERRBODY",(rr.text[:300] if rr.status_code!=200 else ""))
        if rr.status_code==200:
            obj=rr.json()
            recs=[]
            def walk(x):
                if isinstance(x,dict):
                    if "contract" in x and isinstance(x.get("data"),list):
                        ts=sorted({int(z["t"]) for z in x["data"] if isinstance(z,dict) and str(z.get("t","")).isdigit()})
                        recs.append({"contract":x.get("contract"),"count":len(ts),
                                     "min_t":min(ts) if ts else None,"max_t":max(ts) if ts else None})
                    for v in x.values(): walk(v)
                elif isinstance(x,list):
                    for v in x: walk(v)
            walk(obj)
            print("BATCH_TS_META",json.dumps(recs,sort_keys=True))
    except Exception as e:
        print("BATCH_ERR",json.dumps(contracts),type(e).__name__,str(e))

print("=== HISTORICAL ARTICLE CATEGORY PROBE ===")
u="https://miniapp.gate.com/announcements/article/31699"
try:
    rr=s.get(u,timeout=30)
    sp=BeautifulSoup(rr.text,"html.parser")
    nd=sp.find("script",id="__NEXT_DATA__")
    print("HIST_ARTICLE_HTTP",rr.status_code,"LEN",len(rr.text))
    if nd and nd.string:
        obj=json.loads(nd.string)
        pp=((obj.get("props") or {}).get("pageProps") or {})
        print("HIST_PAGEPROPS_KEYS",json.dumps(sorted(pp.keys())))
        for key in ["detail","article","categories","relatedList","query"]:
            if key in pp:
                print("HIST_"+key.upper(),json.dumps(pp.get(key),ensure_ascii=False)[:12000])
except Exception as e:
    print("HIST_ARTICLE_ERR",type(e).__name__,str(e))
