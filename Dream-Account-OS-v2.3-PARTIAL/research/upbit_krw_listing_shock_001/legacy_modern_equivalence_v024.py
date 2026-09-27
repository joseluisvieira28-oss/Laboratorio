#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt,gzip,hashlib,json,statistics,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
import brotli

CDX="https://web.archive.org/cdx/search/cdx"
FAMILIES=[
 ("MODERN","api-manager.upbit.com/api/v1/announcements*","/api/v1/announcements"),
 ("LEGACY","api-manager.upbit.com/api/v1/notices*","/api/v1/notices"),
]
UA={"User-Agent":"CryptoLab-Upbit-Equivalence/0.2.4","Accept":"application/json,*/*"}

def get(url,timeout=120,attempts=3):
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

def cdx(pattern):
    p={"url":pattern,"output":"json","from":"2024","to":"2024","filter":"statuscode:200",
       "fl":"timestamp,original,statuscode,mimetype,digest,length","limit":"5000"}
    st,h,raw,err=get(CDX+"?"+urllib.parse.urlencode(p),90,2)
    rows=[]
    if st==200:
        obj=json.loads(raw)
        if isinstance(obj,list) and obj:
            hdr=obj[0]
            for x in obj[1:]:
                if isinstance(x,list) and len(x)==len(hdr):
                    rows.append(dict(zip(hdr,x)))
    return st,raw,err,rows

def exact_lists(rows,path):
    out=[]
    for r in rows:
        try:p=urllib.parse.urlsplit(r.get("original") or "")
        except Exception:continue
        if p.path==path:
            k=(r.get("timestamp"),r.get("original"),r.get("digest"))
            out.append((k,r))
    seen=set(); uniq=[]
    for k,r in sorted(out):
        if k not in seen:
            seen.add(k); uniq.append(r)
    return uniq

def hget(headers,name):
    for k,v in headers.items():
        if k.lower()==name.lower(): return v
    return None

def decode(raw,headers):
    if raw[:2]==b"\x1f\x8b":
        return gzip.decompress(raw),"gzip_magic"
    enc=(hget(headers,"X-Archive-Orig-Content-Encoding") or "").lower().strip()
    if enc=="br":
        return brotli.decompress(raw),"brotli_header"
    if enc=="gzip":
        return gzip.decompress(raw),"gzip_header"
    return raw,"identity"

def tsdt(x):
    return dt.datetime.strptime(x,"%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)

def norm_iso(s):
    if not isinstance(s,str) or not s.strip(): raise ValueError("empty timestamp")
    x=s.strip().replace("Z","+00:00")
    d=dt.datetime.fromisoformat(x)
    if d.tzinfo is None: raise ValueError("naive timestamp")
    return d.astimezone(dt.timezone.utc).isoformat(timespec="seconds")

def replay_record(fam,cap):
    replay=f"https://web.archive.org/web/{cap['timestamp']}id_/{cap['original']}"
    st,h,raw,err=get(replay,120,3)
    meta={"capture":cap["timestamp"],"original":cap["original"],"http_status":st,"transport_error":err,
          "raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw)}
    if st!=200 or not raw: return meta,[]
    try:dec,mode=decode(raw,h)
    except Exception as e:
        meta["decode_error"]=repr(e); return meta,[]
    meta["decode_mode"]=mode; meta["decoded_sha256"]=hashlib.sha256(dec).hexdigest(); meta["decoded_bytes"]=len(dec)
    try:obj=json.loads(dec.decode("utf-8"))
    except Exception as e:
        meta["json_error"]=repr(e); return meta,[]
    data=obj.get("data") if isinstance(obj,dict) else None
    if not isinstance(data,dict): return meta,[]
    rows=data.get("notices") if fam=="MODERN" else data.get("list")
    if not isinstance(rows,list): return meta,[]
    vals=[]
    for r in rows:
        if not isinstance(r,dict): continue
        try:
            if fam=="MODERN":
                vals.append({
                  "id":str(r["id"]),"title":str(r["title"]),
                  "first":norm_iso(r["first_listed_at"]),"listed":norm_iso(r["listed_at"]),
                  "capture":cap["timestamp"],"payload_sha":meta["decoded_sha256"]
                })
            else:
                vals.append({
                  "id":str(r["id"]),"title":str(r["title"]),
                  "created":norm_iso(r["created_at"]),"updated":norm_iso(r["updated_at"]),
                  "capture":cap["timestamp"],"payload_sha":meta["decoded_sha256"]
                })
        except Exception:
            continue
    meta["usable_rows"]=len(vals)
    return meta,vals

out={"audit_id":"UKLS-LEGACY-MODERN-EQUIVALENCE-V0.2.4","event_values_emitted":False,
     "source_gate_opened":False,"binance_opened":False,"families":{}}
allvals={}
for fam,pat,path in FAMILIES:
    st,raw,err,rows=cdx(pat); caps=exact_lists(rows,path)
    vals=[]; metas=[]
    for i,cap in enumerate(caps):
        m,v=replay_record(fam,cap); metas.append(m); vals.extend(v)
        time.sleep(0.25)
    allvals[fam]=vals
    out["families"][fam]={
      "cdx_http_status":st,"cdx_sha256":hashlib.sha256(raw).hexdigest(),"cdx_error":err,
      "exact_list_capture_count":len(caps),
      "decoded_capture_count":sum(1 for m in metas if m.get("usable_rows",0)>0),
      "transport_or_decode_failure_count":sum(1 for m in metas if not m.get("usable_rows",0)),
      "usable_row_instances":len(vals),
      "decode_modes":dict(__import__("collections").Counter(m.get("decode_mode","FAIL") for m in metas)),
    }

by={}
for fam in ("MODERN","LEGACY"):
    d={}
    for r in allvals[fam]:
        d.setdefault(r["id"],[]).append(r)
    by[fam]=d
overlap=sorted(set(by["MODERN"]) & set(by["LEGACY"]))
comparisons=[]
for ident in overlap:
    best=None
    for m in by["MODERN"][ident]:
        mt=tsdt(m["capture"])
        for l in by["LEGACY"][ident]:
            lt=tsdt(l["capture"]); gap=abs((mt-lt).total_seconds())
            tie=(gap,m["capture"],l["capture"],m["payload_sha"],l["payload_sha"])
            if best is None or tie<best[0]:
                best=(tie,m,l)
    if best is None: continue
    gap,m,l=best[0][0],best[1],best[2]
    if gap<=7*86400:
        comparisons.append({
          "gap":gap,
          "title":l["title"]==m["title"],
          "created_first":l["created"]==m["first"],
          "updated_listed":l["updated"]==m["listed"],
          "canon_hash":hashlib.sha256(json.dumps(
             [ident,l["title"],l["created"],l["updated"],m["title"],m["first"],m["listed"]],
             ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        })

gaps=[x["gap"] for x in comparisons]
out["overlap_id_count"]=len(overlap)
out["comparable_id_count"]=len(comparisons)
out["title_exact_count"]=sum(x["title"] for x in comparisons)
out["created_to_first_exact_count"]=sum(x["created_first"] for x in comparisons)
out["updated_to_listed_exact_count"]=sum(x["updated_listed"] for x in comparisons)
out["all_fields_exact_count"]=sum(x["title"] and x["created_first"] and x["updated_listed"] for x in comparisons)
out["gap_seconds"]={
  "min":min(gaps) if gaps else None,
  "median":statistics.median(gaps) if gaps else None,
  "max":max(gaps) if gaps else None,
}
agg="\n".join(sorted(x["canon_hash"] for x in comparisons)).encode()
out["comparison_aggregate_sha256"]=hashlib.sha256(agg).hexdigest()
passed=(len(comparisons)>=5 and out["title_exact_count"]==len(comparisons)
        and out["created_to_first_exact_count"]==len(comparisons)
        and out["updated_to_listed_exact_count"]==len(comparisons)
        and out["all_fields_exact_count"]==len(comparisons))
out["classification"]="LEGACY_MODERN_SIGNAL_SCHEMA_EQUIVALENT" if passed else "LEGACY_MODERN_SIGNAL_SCHEMA_NOT_PROVEN"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_LEGACY_MODERN_EQUIVALENCE_V0_2_4.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
