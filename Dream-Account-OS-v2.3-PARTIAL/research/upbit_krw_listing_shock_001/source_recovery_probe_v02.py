#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,urllib.error,urllib.request,urllib.parse
from pathlib import Path

ENDPOINTS=[
 ("LEGACY_GENERAL","https://api-manager.upbit.com/api/v1/notices?page=1&per_page=20&thread_name=general"),
 ("LEGACY_PRESS","https://api-manager.upbit.com/api/v1/notices?page=1&per_page=20&thread_name=press"),
 ("MODERN_TRADE_CONTROL","https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=30&category=trade"),
]
UA={
 "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154.0 Safari/537.36",
 "Accept":"application/json,text/plain,*/*",
 "Accept-Language":"ko-KR,ko;q=0.9,en;q=0.6",
 "Origin":"https://upbit.com",
 "Referer":"https://upbit.com/service_center/notice",
}

def fetch(url):
    req=urllib.request.Request(url,headers=UA,method="GET")
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read(); return r.status,dict(r.headers),raw,None
    except urllib.error.HTTPError as e:
        raw=e.read(); return e.code,dict(e.headers),raw,repr(e)
    except Exception as e:
        return None,{},b"",repr(e)

def analyze(raw):
    meta={"json_type":None,"top_level_keys":[],"row_field":None,"row_count":0,"row_field_names":[],"semantic_field_presence":{}}
    try: obj=json.loads(raw)
    except Exception as e:
        meta["json_parse_error"]=repr(e); return meta
    meta["json_type"]=type(obj).__name__
    rows=[]
    if isinstance(obj,dict):
        meta["top_level_keys"]=sorted(obj.keys())
        candidates=[]
        for k,v in obj.items():
            if isinstance(v,list):
                candidates.append((k,v))
            elif isinstance(v,dict):
                for k2,v2 in v.items():
                    if isinstance(v2,list):
                        candidates.append((f"{k}.{k2}",v2))
        if candidates:
            candidates.sort(key=lambda kv:len(kv[1]),reverse=True)
            meta["row_field"],rows=candidates[0]
    elif isinstance(obj,list):
        meta["row_field"]="<top_level_list>"; rows=obj
    meta["row_count"]=len(rows)
    fields=set()
    for r in rows[:3]:
        if isinstance(r,dict): fields.update(r.keys())
    meta["row_field_names"]=sorted(fields)
    groups={
      "event_id":["id","uuid","notice_id"],
      "title":["title","subject"],
      "listed_at":["listed_at","first_listed_at","created_at","created_date"],
      "category":["category","thread_name","thread","type"],
    }
    meta["semantic_field_presence"]={g:sorted(set(fields)&set(opts)) for g,opts in groups.items()}
    return meta

out={"probe_id":"UKLS-SOURCE-RECOVERY-V0.2","page_limit":1,"historical_enumeration_opened":False,
     "titles_emitted":False,"ids_emitted":False,"timestamps_emitted":False,"binance_opened":False,"results":[]}
passes=[]
for name,url in ENDPOINTS:
    status,h,raw,err=fetch(url)
    rec={"name":name,"http_status":status,"content_type":h.get("Content-Type") or h.get("content-type"),
         "response_bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"transport_error":err}
    rec.update(analyze(raw))
    out["results"].append(rec)
    sem=rec.get("semantic_field_presence",{})
    if name.startswith("LEGACY_") and status==200 and rec.get("row_count",0)>0 and sem.get("event_id") and sem.get("title") and sem.get("listed_at"):
        passes.append(name)
out["usable_legacy_candidates"]=passes
out["classification"]="LEGACY_OFFICIAL_SCHEMA_CANDIDATE_PASS" if passes else "LEGACY_OFFICIAL_ROUTE_NOT_USABLE"
Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_SOURCE_RECOVERY_PROBE_V0_2.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
