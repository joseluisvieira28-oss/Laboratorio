#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,urllib.parse,urllib.request,urllib.error
from pathlib import Path

CDX="https://web.archive.org/cdx/search/cdx"
FAMILIES=[
 ("MODERN","api-manager.upbit.com/api/v1/announcements*","/api/v1/announcements"),
 ("LEGACY","api-manager.upbit.com/api/v1/notices*","/api/v1/notices"),
]
UA={"User-Agent":"CryptoLab-Wayback-Schema/0.2.3","Accept":"application/json,*/*"}

def get(url,timeout=90):
    req=urllib.request.Request(url,headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(); return r.status,dict(r.headers),raw,None
    except urllib.error.HTTPError as e:
        raw=e.read(); return e.code,dict(e.headers),raw,repr(e)
    except Exception as e:
        return None,{},b"",repr(e)

def cdx_rows(pattern):
    p={"url":pattern,"output":"json","from":"2023","to":"2024","filter":"statuscode:200",
       "fl":"timestamp,original,statuscode,mimetype,digest,length","limit":"5000"}
    status,h,raw,err=get(CDX+"?"+urllib.parse.urlencode(p))
    rows=[]
    if status==200:
        obj=json.loads(raw)
        if isinstance(obj,list) and obj:
            hdr=obj[0]
            for x in obj[1:]:
                if isinstance(x,list) and len(x)==len(hdr):
                    rows.append(dict(zip(hdr,x)))
    return status,raw,err,rows

def exact_list(rows,path):
    out=[]
    for r in rows:
        u=r.get("original") or ""
        try: p=urllib.parse.urlsplit(u)
        except Exception: continue
        if p.path==path:
            out.append(r)
    # unique archive identity
    seen=set(); uniq=[]
    for r in sorted(out,key=lambda z:(z.get("timestamp",""),z.get("original",""),z.get("digest",""))):
        k=(r.get("timestamp"),r.get("original"),r.get("digest"))
        if k not in seen:
            seen.add(k); uniq.append(r)
    return uniq

def sample_schema(family,row):
    ts=row["timestamp"]; orig=row["original"]
    replay=f"https://web.archive.org/web/{ts}id_/{orig}"
    status,h,raw,err=get(replay,120)
    rec={"family":family,"capture_timestamp":ts,"original_url":orig,"archive_http_status":status,
         "content_type":h.get("Content-Type") or h.get("content-type"),"response_bytes":len(raw),
         "sha256":hashlib.sha256(raw).hexdigest(),"transport_error":err}
    try: obj=json.loads(raw)
    except Exception as e:
        rec["json_parse_error"]=repr(e); return rec
    rec["json_type"]=type(obj).__name__
    rec["top_level_keys"]=sorted(obj.keys()) if isinstance(obj,dict) else []
    rows=[]; row_path=None; data=None
    if isinstance(obj,dict):
        data=obj.get("data")
        if isinstance(data,dict):
            if isinstance(data.get("notices"),list):
                rows=data["notices"]; row_path="data.notices"
            elif isinstance(data.get("list"),list):
                rows=data["list"]; row_path="data.list"
            rec["pagination"]={k:data.get(k) for k in ("page","per_page","total_count","total_pages") if isinstance(data.get(k),(int,float,str,bool))}
        if row_path is None:
            for k,v in obj.items():
                if isinstance(v,list): rows=v; row_path=k; break
    rec["row_path"]=row_path
    rec["row_count"]=len(rows)
    fields=set()
    for x in rows[:3]:
        if isinstance(x,dict): fields.update(x.keys())
    rec["row_field_names"]=sorted(fields)
    groups={
      "event_id":["id","uuid","notice_id"],
      "title":["title","subject"],
      "listed_at":["listed_at","first_listed_at","created_at","created_date","published_at"],
      "category":["category","thread_name","thread","type"],
    }
    rec["semantic_fields"]={g:sorted(set(opts)&fields) for g,opts in groups.items()}
    rec["modern_exact_pass"]=(family=="MODERN" and row_path=="data.notices" and {"id","title","listed_at"}.issubset(fields))
    rec["legacy_candidate_pass"]=(family=="LEGACY" and bool(rec["semantic_fields"]["event_id"]) and bool(rec["semantic_fields"]["title"]) and bool(rec["semantic_fields"]["listed_at"]))
    return rec

out={"audit_id":"UKLS-WAYBACK-SCHEMA-V0.2.3","event_values_emitted":False,"historical_enumeration_opened":False,
     "binance_opened":False,"families":[],"samples":[]}
modern=False; legacy=False
for fam,pat,path in FAMILIES:
    st,raw,err,rows=cdx_rows(pat)
    lists=exact_list(rows,path)
    urls=sorted({r["original"] for r in lists})
    page_values=[]
    for u in urls:
        q=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(u).query,keep_blank_values=True))
        if "page" in q: page_values.append(q["page"])
    frec={"family":fam,"cdx_http_status":st,"cdx_sha256":hashlib.sha256(raw).hexdigest(),
          "cdx_transport_error":err,"exact_list_capture_count":len(lists),"distinct_list_urls":len(urls),
          "original_list_urls":urls,"observed_page_values":sorted(set(page_values),key=lambda x:(len(x),x))}
    if lists:
        chosen=[lists[0]]
        if (lists[-1]["timestamp"],lists[-1]["original"],lists[-1]["digest"]) != (lists[0]["timestamp"],lists[0]["original"],lists[0]["digest"]):
            chosen.append(lists[-1])
        frec["sample_capture_keys"]=[{"timestamp":r["timestamp"],"original":r["original"],"digest":r["digest"]} for r in chosen]
        for r in chosen:
            s=sample_schema(fam,r); out["samples"].append(s)
            modern = modern or bool(s.get("modern_exact_pass"))
            legacy = legacy or bool(s.get("legacy_candidate_pass"))
    out["families"].append(frec)
out["classification"]="MODERN_ARCHIVED_SCHEMA_EQUIVALENT" if modern else ("LEGACY_ARCHIVED_SCHEMA_CANDIDATE" if legacy else "ARCHIVE_SCHEMA_NOT_EQUIVALENT")

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_WAYBACK_SCHEMA_V0_2_3.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
