#!/usr/bin/env python3
from __future__ import annotations
import collections,hashlib,json,re,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path

COLLINFO="https://index.commoncrawl.org/collinfo.json"
BASES=[
 ("ANNOUNCEMENTS","https://api-manager.upbit.com/api/v1/announcements"),
 ("NOTICES","https://api-manager.upbit.com/api/v1/notices"),
]
UA={"User-Agent":"CryptoLab-CommonCrawl-Index/0.2.5","Accept":"application/json,text/plain,*/*"}

def get(url,timeout=90,attempts=3):
    last=None
    for i in range(attempts):
        req=urllib.request.Request(url,headers=UA)
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.status,dict(r.headers),r.read(),None
        except urllib.error.HTTPError as e:
            raw=e.read(); last=repr(e)
            if e.code not in (429,500,502,503,504):
                return e.code,dict(e.headers),raw,last
        except Exception as e:
            last=repr(e)
        if i+1<attempts: time.sleep(2*(i+1))
    return None,{},b"",last

def parse_isoish(x):
    return str(x or "")

def selected_crawls(obj):
    out=[]
    for c in obj:
        if not isinstance(c,dict) or not c.get("id") or not c.get("cdx-api"): continue
        cid=str(c["id"])
        frm=parse_isoish(c.get("from")); to=parse_isoish(c.get("to"))
        hit=False
        if frm and to:
            # lexicographic timestamps like 2023-... / 2024-...
            if to[:4] >= "2023" and frm[:4] <= "2024": hit=True
        if not frm or not to:
            hit=("CC-MAIN-2023-" in cid or "CC-MAIN-2024-" in cid)
        if hit: out.append({"id":cid,"cdx":c["cdx-api"],"from":frm,"to":to})
    return sorted(out,key=lambda x:x["id"])

def parse_json_lines(raw):
    out=[]
    for line in raw.decode("utf-8","replace").splitlines():
        line=line.strip()
        if not line: continue
        try:
            x=json.loads(line)
            if isinstance(x,dict): out.append(x)
        except Exception: pass
    return out

coll_st,h,coll_raw,coll_err=get(COLLINFO,90,3)
if coll_st!=200:
    raise SystemExit("collinfo unavailable")
coll=json.loads(coll_raw)
crawls=selected_crawls(coll)

out={"probe_id":"UKLS-COMMON-CRAWL-INDEX-V0.2.5","warc_payload_opened":False,"event_values_opened":False,
     "collinfo_sha256":hashlib.sha256(coll_raw).hexdigest(),"selected_crawls":[c["id"] for c in crawls],
     "queries":[]}
all_rows=[]
for c in crawls:
    for fam,base in BASES:
        p={"url":base,"matchType":"prefix","output":"json"}
        url=c["cdx"]+"?"+urllib.parse.urlencode(p)
        st,hh,raw,err=get(url,90,3)
        rows=parse_json_lines(raw) if st==200 else []
        ok=[r for r in rows if str(r.get("status"))=="200"]
        all_rows.extend((fam,c["id"],r) for r in ok)
        out["queries"].append({
          "crawl":c["id"],"family":fam,"http_status":st,"response_bytes":len(raw),
          "sha256":hashlib.sha256(raw).hexdigest(),"transport_error":err,
          "rows_total":len(rows),"rows_status_200":len(ok)
        })
        time.sleep(0.25)

paths=collections.Counter(); pages=set(); per_pages=set(); cats=set(); threads=set()
urls=set(); digests=set(); ts=[]; list_rows=0; detail_rows=0; warc_locator_complete=0
for fam,cid,r in all_rows:
    u=r.get("url") or ""
    try:p=urllib.parse.urlsplit(u)
    except Exception:continue
    paths[p.path]+=1; urls.add(u)
    q=dict(urllib.parse.parse_qsl(p.query,keep_blank_values=True))
    if "page" in q: pages.add(q["page"])
    if "per_page" in q: per_pages.add(q["per_page"])
    if "category" in q: cats.add(q["category"])
    if "thread_name" in q: threads.add(q["thread_name"])
    if r.get("digest"): digests.add(r["digest"])
    if r.get("timestamp"): ts.append(str(r["timestamp"]))
    if p.path in ("/api/v1/announcements","/api/v1/notices"): list_rows+=1
    elif re.fullmatch(r"/api/v1/(announcements|notices)/\d+",p.path): detail_rows+=1
    if r.get("filename") is not None and r.get("offset") is not None and r.get("length") is not None:
        warc_locator_complete+=1

def redact_path(path):
    return re.sub(r"(/api/v1/(?:announcements|notices)/)\d+",r"\1<ID>",path)

out["aggregate"]={
 "status_200_capture_count":len(all_rows),
 "exact_list_capture_count":list_rows,
 "numeric_detail_capture_count":detail_rows,
 "distinct_original_url_count":len(urls),
 "distinct_digest_count":len(digests),
 "earliest_capture":min(ts) if ts else None,
 "latest_capture":max(ts) if ts else None,
 "path_counts_redacted":dict(sorted(collections.Counter({redact_path(k):v for k,v in paths.items()}).items())),
 "page_values":sorted(pages,key=lambda x:(len(x),x)),
 "per_page_values":sorted(per_pages,key=lambda x:(len(x),x)),
 "category_values":sorted(cats),
 "thread_name_values":sorted(threads),
 "warc_locator_complete_rows":warc_locator_complete,
 "page_beyond_1_present":any(str(x)!="1" for x in pages),
}
out["classification"]="COMMON_CRAWL_LIST_COVERAGE_CANDIDATE" if list_rows>0 else "COMMON_CRAWL_NO_LIST_COVERAGE"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_COMMON_CRAWL_INDEX_V0_2_5.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":out["classification"],"selected_crawls":out["selected_crawls"],"aggregate":out["aggregate"],
                  "query_successes":sum(q["http_status"]==200 for q in out["queries"]),"query_count":len(out["queries"])},sort_keys=True))
