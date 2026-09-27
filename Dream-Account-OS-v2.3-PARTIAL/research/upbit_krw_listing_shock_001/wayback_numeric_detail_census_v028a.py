#!/usr/bin/env python3
from __future__ import annotations
import collections, datetime as dt, hashlib, json, re, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

CDX="https://web.archive.org/cdx/search/cdx"
FAMILIES=[
 ("LEGACY","api-manager.upbit.com/api/v1/notices/*",re.compile(r"^/api/v1/notices/(\d+)$")),
 ("MODERN","api-manager.upbit.com/api/v1/announcements/*",re.compile(r"^/api/v1/announcements/(\d+)$")),
]
FIELDS="timestamp,original,statuscode,mimetype,digest,length"
RETRY={408,425,429,500,502,503,504}
BACKOFF=[3,6,12]
UA={"User-Agent":"CryptoLab-Upbit-DetailCensus/0.2.8A","Accept":"application/json"}

def fetch(url):
    attempts=[]
    for i in range(4):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=120) as r:
                raw=r.read()
                attempts.append({"attempt":i+1,"status":r.status,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
                return r.status,raw,None,attempts
        except urllib.error.HTTPError as e:
            raw=e.read()
            attempts.append({"attempt":i+1,"status":e.code,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
            if e.code not in RETRY:
                return e.code,raw,repr(e),attempts
        except Exception as e:
            attempts.append({"attempt":i+1,"status":None,"error":repr(e)})
        if i<3: time.sleep(BACKOFF[i])
    return attempts[-1].get("status"),b"","retry_exhausted",attempts

def iso(ts):
    return dt.datetime.strptime(ts,"%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)

out={"audit_id":"UKLS-WAYBACK-NUMERIC-DETAIL-CENSUS-V0.2.8A","archived_payload_opened":False,"event_values_opened":False,"binance_opened":False,"families":{}}
technical=False; any_pass=False

for fam,pat,rx in FAMILIES:
    allrows=[]; query_meta=[]
    for year in (2023,2024):
        p={"url":pat,"output":"json","from":str(year),"to":str(year),"filter":"statuscode:200","fl":FIELDS,"collapse":"urlkey","limit":"10000"}
        st,raw,err,attempts=fetch(CDX+"?"+urllib.parse.urlencode(p))
        qm={"year":year,"http_status":st,"transport_error":err,"attempts":attempts,"response_sha256":hashlib.sha256(raw).hexdigest()}
        rows=[]
        if st==200:
            try:
                obj=json.loads(raw)
                if isinstance(obj,list) and obj and isinstance(obj[0],list):
                    hdr=obj[0]
                    for x in obj[1:]:
                        if isinstance(x,list) and len(x)==len(hdr): rows.append(dict(zip(hdr,x)))
            except Exception as e:
                qm["parse_error"]=repr(e)
        if st!=200 or qm.get("parse_error"):
            technical=True
        qm["row_count"]=len(rows)
        query_meta.append(qm)
        allrows.extend(rows)

    ids=set(); caps=[]; mimetypes=collections.Counter(); statuses=collections.Counter(); digests=set(); accepted=0
    for r in allrows:
        try:
            u=urllib.parse.urlsplit(r.get("original") or "")
            m=rx.fullmatch(u.path)
            if not m: continue
            accepted+=1
            ids.add(int(m.group(1)))
            if r.get("timestamp"): caps.append(r["timestamp"])
            if r.get("digest"): digests.add(r["digest"])
            mimetypes[str(r.get("mimetype"))]+=1
            statuses[str(r.get("statuscode"))]+=1
        except Exception:
            continue

    sids=sorted(ids)
    if sids:
        span=sids[-1]-sids[0]+1
        missing=span-len(sids)
        maxgap=max((b-a for a,b in zip(sids,sids[1:])),default=0)
        coverage=len(sids)/span
    else:
        span=missing=maxgap=0; coverage=0.0
    earliest=min(caps) if caps else None
    latest=max(caps) if caps else None
    pass_gate=(
      not technical and len(sids)>=100 and coverage==1.0 and missing==0 and maxgap<=1 and
      earliest is not None and latest is not None and
      iso(earliest)<=dt.datetime(2023,1,7,23,59,59,tzinfo=dt.timezone.utc) and
      iso(latest)>=dt.datetime(2024,12,25,0,0,0,tzinfo=dt.timezone.utc) and
      set(statuses.keys()) <= {"200"}
    )
    any_pass = any_pass or pass_gate
    out["families"][fam]={
      "queries":query_meta,
      "accepted_capture_count":accepted,
      "distinct_numeric_id_count":len(sids),
      "min_numeric_id":sids[0] if sids else None,
      "max_numeric_id":sids[-1] if sids else None,
      "numeric_span_size":span,
      "numeric_coverage_fraction":coverage,
      "missing_numeric_id_count":missing,
      "max_internal_numeric_id_gap":maxgap,
      "earliest_capture":earliest,
      "latest_capture":latest,
      "distinct_digest_count":len(digests),
      "status_counts":dict(statuses),
      "mimetype_counts":dict(mimetypes),
      "completeness_candidate_pass":pass_gate
    }

if technical:
    out["classification"]="WAYBACK_NUMERIC_DETAIL_CENSUS_TECHNICAL_FAILURE"
else:
    out["classification"]="WAYBACK_NUMERIC_DETAIL_CENSUS_CANDIDATE" if any_pass else "WAYBACK_NUMERIC_DETAIL_COVERAGE_INSUFFICIENT"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_WAYBACK_NUMERIC_DETAIL_CENSUS_V0_2_8A.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
