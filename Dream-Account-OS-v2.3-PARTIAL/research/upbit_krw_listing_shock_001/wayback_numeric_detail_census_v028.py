#!/usr/bin/env python3
from __future__ import annotations
import collections, datetime as dt, hashlib, json, re, urllib.error, urllib.parse, urllib.request
from pathlib import Path

CDX="https://web.archive.org/cdx/search/cdx"
FAMILIES=[
 ("LEGACY","api-manager.upbit.com/api/v1/notices/*",re.compile(r"^/api/v1/notices/(\d+)$")),
 ("MODERN","api-manager.upbit.com/api/v1/announcements/*",re.compile(r"^/api/v1/announcements/(\d+)$")),
]
FIELDS="timestamp,original,statuscode,mimetype,digest,length"
UA={"User-Agent":"CryptoLab-Upbit-DetailCensus/0.2.8","Accept":"application/json"}

def fetch(url):
    req=urllib.request.Request(url,headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=120) as r:
            raw=r.read(); return r.status,raw,None
    except urllib.error.HTTPError as e:
        return e.code,e.read(),repr(e)
    except Exception as e:
        return None,b"",repr(e)

def iso(ts):
    return dt.datetime.strptime(ts,"%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)

out={"audit_id":"UKLS-WAYBACK-NUMERIC-DETAIL-CENSUS-V0.2.8","archived_payload_opened":False,"event_values_opened":False,"binance_opened":False,"families":{}}
any_pass=False
for fam,pat,rx in FAMILIES:
    p={"url":pat,"output":"json","from":"2023","to":"2024","filter":"statuscode:200","fl":FIELDS,"limit":"20000"}
    st,raw,err=fetch(CDX+"?"+urllib.parse.urlencode(p))
    rec={"cdx_http_status":st,"cdx_sha256":hashlib.sha256(raw).hexdigest(),"transport_error":err}
    rows=[]
    if st==200:
        try:
            obj=json.loads(raw)
            if isinstance(obj,list) and obj and isinstance(obj[0],list):
                hdr=obj[0]
                for x in obj[1:]:
                    if isinstance(x,list) and len(x)==len(hdr):
                        rows.append(dict(zip(hdr,x)))
        except Exception as e:
            rec["parse_error"]=repr(e)
    ids=set(); accepted=[]; mimetypes=collections.Counter(); statuses=collections.Counter(); digests=set(); caps=[]
    for r in rows:
        try:
            u=urllib.parse.urlsplit(r.get("original") or "")
            m=rx.fullmatch(u.path)
            if not m: continue
            i=int(m.group(1))
            ids.add(i); accepted.append(r); mimetypes[str(r.get("mimetype"))]+=1; statuses[str(r.get("statuscode"))]+=1
            if r.get("digest"): digests.add(r["digest"])
            if r.get("timestamp"): caps.append(r["timestamp"])
        except Exception:
            continue
    sids=sorted(ids)
    if sids:
        span=sids[-1]-sids[0]+1
        missing=span-len(sids)
        maxgap=max((b-a for a,b in zip(sids,sids[1:])), default=0)
        coverage=len(sids)/span
    else:
        span=missing=maxgap=0; coverage=0.0
    earliest=min(caps) if caps else None
    latest=max(caps) if caps else None
    pass_gate=(
      err is None and st==200 and len(sids)>=100 and coverage==1.0 and missing==0 and maxgap<=1 and
      earliest is not None and latest is not None and
      iso(earliest)<=dt.datetime(2023,1,7,23,59,59,tzinfo=dt.timezone.utc) and
      iso(latest)>=dt.datetime(2024,12,25,0,0,0,tzinfo=dt.timezone.utc) and
      set(statuses.keys()) <= {"200"}
    )
    rec.update({
      "accepted_capture_count":len(accepted),
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
    })
    out["families"][fam]=rec
    any_pass = any_pass or pass_gate

out["classification"]="WAYBACK_NUMERIC_DETAIL_CENSUS_CANDIDATE" if any_pass else "WAYBACK_NUMERIC_DETAIL_COVERAGE_INSUFFICIENT"
Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_WAYBACK_NUMERIC_DETAIL_CENSUS_V0_2_8.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
