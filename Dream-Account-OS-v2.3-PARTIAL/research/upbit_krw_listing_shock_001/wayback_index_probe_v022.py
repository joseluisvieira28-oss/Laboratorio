#!/usr/bin/env python3
from __future__ import annotations
import collections,hashlib,json,re,urllib.parse,urllib.request,urllib.error
from pathlib import Path

CDX="https://web.archive.org/cdx/search/cdx"
PATTERNS=[
 ("ANNOUNCEMENTS","api-manager.upbit.com/api/v1/announcements*"),
 ("NOTICES","api-manager.upbit.com/api/v1/notices*"),
]
FIELDS="timestamp,original,statuscode,mimetype,digest,length"

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Wayback-Index/0.2.2","Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=90) as r:
            raw=r.read(); return r.status,dict(r.headers),raw,None
    except urllib.error.HTTPError as e:
        raw=e.read(); return e.code,dict(e.headers),raw,repr(e)
    except Exception as e:
        return None,{},b"",repr(e)

def redact_url(u):
    try:
        p=urllib.parse.urlsplit(u)
        q=urllib.parse.parse_qsl(p.query,keep_blank_values=True)
        red=[]
        for k,v in q:
            if re.fullmatch(r"\d+",v or ""): v="<N>"
            elif len(v)>80: v="<LONG>"
            red.append((k,v))
        return urllib.parse.urlunsplit((p.scheme,p.netloc,p.path,urllib.parse.urlencode(red),p.fragment))
    except Exception:
        return "<UNPARSEABLE>"

out={"probe_id":"UKLS-WAYBACK-INDEX-V0.2.2","archived_payload_opened":False,"event_values_opened":False,"results":[]}
total=0
for name,pat in PATTERNS:
    params={
      "url":pat,"output":"json","from":"2023","to":"2024",
      "filter":"statuscode:200","fl":FIELDS,"collapse":"digest","limit":"5000"
    }
    url=CDX+"?"+urllib.parse.urlencode(params)
    status,h,raw,err=fetch(url)
    rec={"name":name,"query_http_status":status,"response_bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"transport_error":err}
    rows=[]
    try:
        obj=json.loads(raw)
        if isinstance(obj,list) and obj:
            header=obj[0]
            if isinstance(header,list):
                for r in obj[1:]:
                    if isinstance(r,list) and len(r)==len(header):
                        rows.append(dict(zip(header,r)))
    except Exception as e:
        rec["json_parse_error"]=repr(e)
    rec["capture_rows"]=len(rows)
    total+=len(rows)
    ts=[r.get("timestamp") for r in rows if r.get("timestamp")]
    rec["earliest_capture"]=min(ts) if ts else None
    rec["latest_capture"]=max(ts) if ts else None
    originals=[r.get("original") for r in rows if r.get("original")]
    rec["distinct_original_urls"]=len(set(originals))
    rec["distinct_digests"]=len({r.get("digest") for r in rows if r.get("digest")})
    rec["status_counts"]=dict(collections.Counter(str(r.get("statuscode")) for r in rows))
    rec["mimetype_counts"]=dict(collections.Counter(str(r.get("mimetype")) for r in rows))
    rec["query_params_preserved"]=any("?" in u for u in originals)
    rec["redacted_original_templates"]=sorted({redact_url(u) for u in originals})[:20]
    out["results"].append(rec)
out["total_capture_rows"]=total
out["classification"]="WAYBACK_FIRSTPARTY_ARCHIVE_CANDIDATE" if total>0 else "WAYBACK_NO_QUALIFYING_ARCHIVE"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_WAYBACK_INDEX_V0_2_2.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
