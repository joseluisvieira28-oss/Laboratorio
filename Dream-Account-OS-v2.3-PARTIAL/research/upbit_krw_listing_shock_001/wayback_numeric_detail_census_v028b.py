#!/usr/bin/env python3
import collections,datetime as dt,hashlib,json,re,urllib.error,urllib.parse,urllib.request
from pathlib import Path
CDX="https://web.archive.org/cdx/search/cdx"
FAMS=[("LEGACY","api-manager.upbit.com/api/v1/notices*",re.compile(r"^/api/v1/notices/(\d+)$")),("MODERN","api-manager.upbit.com/api/v1/announcements*",re.compile(r"^/api/v1/announcements/(\d+)$"))]
FIELDS="timestamp,original,statuscode,mimetype,digest,length"
def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Upbit-DetailCensus/0.2.8B","Accept":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=90) as r:return r.status,r.read(),None
 except urllib.error.HTTPError as e:return e.code,e.read(),repr(e)
 except Exception as e:return None,b"",repr(e)
def iso(x):return dt.datetime.strptime(x,"%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
out={"audit_id":"UKLS-WAYBACK-NUMERIC-DETAIL-CENSUS-V0.2.8B","archived_payload_opened":False,"event_values_opened":False,"binance_opened":False,"families":{}}
tech=False; anypass=False
for fam,pat,rx in FAMS:
 p={"url":pat,"output":"json","from":"2023","to":"2024","filter":"statuscode:200","fl":FIELDS,"limit":"5000"}
 st,raw,err=fetch(CDX+"?"+urllib.parse.urlencode(p))
 rows=[]; perr=None
 if st==200:
  try:
   obj=json.loads(raw); hdr=obj[0] if isinstance(obj,list) and obj and isinstance(obj[0],list) else []
   rows=[dict(zip(hdr,x)) for x in obj[1:] if isinstance(x,list) and len(x)==len(hdr)]
  except Exception as e: perr=repr(e)
 if st!=200 or perr: tech=True
 ids=set(); caps=[]; digs=set(); mts=collections.Counter(); sts=collections.Counter()
 for r in rows:
  try:
   u=urllib.parse.urlsplit(r.get("original") or ""); m=rx.fullmatch(u.path)
   if not m: continue
   ids.add(int(m.group(1)))
   if r.get("timestamp"):caps.append(r["timestamp"])
   if r.get("digest"):digs.add(r["digest"])
   mts[str(r.get("mimetype"))]+=1; sts[str(r.get("statuscode"))]+=1
  except: pass
 s=sorted(ids)
 if s:
  span=s[-1]-s[0]+1; miss=span-len(s); gap=max((b-a for a,b in zip(s,s[1:])),default=0); cov=len(s)/span
 else: span=miss=gap=0; cov=0.0
 earliest=min(caps) if caps else None; latest=max(caps) if caps else None
 pg=(st==200 and perr is None and len(s)>=100 and cov==1.0 and miss==0 and gap<=1 and earliest and latest and iso(earliest)<=dt.datetime(2023,1,7,23,59,59,tzinfo=dt.timezone.utc) and iso(latest)>=dt.datetime(2024,12,25,tzinfo=dt.timezone.utc))
 anypass=anypass or bool(pg)
 out["families"][fam]={"cdx_http_status":st,"transport_error":err,"parse_error":perr,"response_sha256":hashlib.sha256(raw).hexdigest(),"raw_index_rows":len(rows),"distinct_numeric_id_count":len(s),"min_numeric_id":s[0] if s else None,"max_numeric_id":s[-1] if s else None,"numeric_span_size":span,"numeric_coverage_fraction":cov,"missing_numeric_id_count":miss,"max_internal_numeric_id_gap":gap,"earliest_capture":earliest,"latest_capture":latest,"distinct_digest_count":len(digs),"mimetype_counts":dict(mts),"status_counts":dict(sts),"completeness_candidate_pass":bool(pg)}
out["classification"]="WAYBACK_NUMERIC_DETAIL_CENSUS_TECHNICAL_FAILURE" if tech else ("WAYBACK_NUMERIC_DETAIL_CENSUS_CANDIDATE" if anypass else "WAYBACK_NUMERIC_DETAIL_COVERAGE_INSUFFICIENT")
Path("artifacts").mkdir(exist_ok=True);Path("artifacts/UKLS_WAYBACK_NUMERIC_DETAIL_CENSUS_V0_2_8B.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,sort_keys=True))
