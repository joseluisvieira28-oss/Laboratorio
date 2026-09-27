#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, gzip, hashlib, json, statistics, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
import brotli

CDX="https://web.archive.org/cdx/search/cdx"
UA={"User-Agent":"CryptoLab-Upbit-ArchiveCoverage/0.2.7","Accept":"application/json,*/*"}
START=dt.datetime(2023,1,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2025,1,1,tzinfo=dt.timezone.utc)

FAMILIES={
 "LEGACY":{
   "pattern":"api-manager.upbit.com/api/v1/notices*",
   "path":"/api/v1/notices",
   "from":"2023","to":"2024",
   "row_key":"list","time_field":"created_at",
   "query_guard":lambda q: q.get("page",[""])[0]=="1" and q.get("thread_name",[""])[0]=="general",
 },
 "MODERN":{
   "pattern":"api-manager.upbit.com/api/v1/announcements*",
   "path":"/api/v1/announcements",
   "from":"2024","to":"2024",
   "row_key":"notices","time_field":"first_listed_at",
   "query_guard":lambda q: q.get("page",[""])[0]=="1" and q.get("category",[""])[0]=="all",
 },
}

def get(url,timeout=120,attempts=3):
    last=None
    for i in range(attempts):
        req=urllib.request.Request(url,headers=UA)
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.status,dict(r.headers),r.read(),None
        except urllib.error.HTTPError as e:
            raw=e.read(); last=repr(e)
            if e.code not in (408,425,429,500,502,503,504):
                return e.code,dict(e.headers),raw,last
        except Exception as e:
            last=repr(e)
        if i+1<attempts: time.sleep(2*(i+1))
    return None,{},b"",last

def cdx(cfg):
    p={"url":cfg["pattern"],"output":"json","from":cfg["from"],"to":cfg["to"],
       "filter":"statuscode:200","fl":"timestamp,original,statuscode,mimetype,digest,length","limit":"5000"}
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

def hget(headers,name):
    for k,v in headers.items():
        if k.lower()==name.lower(): return v
    return None

def decode(raw,headers):
    if raw[:2]==b"\x1f\x8b": return gzip.decompress(raw),"gzip_magic"
    enc=(hget(headers,"X-Archive-Orig-Content-Encoding") or hget(headers,"Content-Encoding") or "").lower().strip()
    if enc=="br": return brotli.decompress(raw),"brotli_header"
    if enc=="gzip": return gzip.decompress(raw),"gzip_header"
    return raw,"identity"

def parse_ts(s):
    if not isinstance(s,str) or not s.strip(): raise ValueError("empty")
    x=s.strip().replace("Z","+00:00")
    d=dt.datetime.fromisoformat(x)
    if d.tzinfo is None: raise ValueError("naive")
    return d.astimezone(dt.timezone.utc)

def accepted_caps(rows,cfg):
    out=[]
    for r in rows:
        try:
            p=urllib.parse.urlsplit(r.get("original") or "")
            q=urllib.parse.parse_qs(p.query,keep_blank_values=True)
        except Exception:
            continue
        if p.path!=cfg["path"]: continue
        if not cfg["query_guard"](q): continue
        k=(r.get("timestamp"),r.get("original"),r.get("digest"))
        out.append((k,r))
    seen=set(); uniq=[]
    for k,r in sorted(out):
        if k not in seen:
            seen.add(k); uniq.append(r)
    return uniq

def replay_json(cap):
    attempts=[]
    for suffix in ("id_","if_"):
        url=f"https://web.archive.org/web/{cap['timestamp']}{suffix}/{cap['original']}"
        st,h,raw,err=get(url,120,3)
        a={"suffix":suffix,"status":st,"raw_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"error":err}
        attempts.append(a)
        if st!=200 or not raw:
            continue
        try:
            dec,mode=decode(raw,h); a["decode_mode"]=mode
            obj=json.loads(dec.decode("utf-8")); a["json_ok"]=True
            return obj,attempts
        except Exception as e:
            a["parse_error"]=repr(e)
            continue
    return None,attempts

def snapshot(fam,cfg,cap):
    obj,atts=replay_json(cap)
    meta={"capture":cap["timestamp"],"transport_ok":obj is not None,"attempts":atts}
    if not isinstance(obj,dict): return meta,None
    data=obj.get("data")
    if not isinstance(data,dict): return meta,None
    rows=data.get(cfg["row_key"])
    if not isinstance(rows,list) or not rows: return meta,None
    ids=[]; times=[]
    try:
        for r in rows:
            if not isinstance(r,dict): raise ValueError("non-object row")
            ident=str(r["id"])
            t=parse_ts(r[cfg["time_field"]])
            ids.append(ident); times.append(t)
    except Exception as e:
        meta["row_error"]=repr(e); return meta,None
    if len(set(ids))!=len(ids):
        meta["row_error"]="duplicate IDs within snapshot"; return meta,None
    monotonic=all(times[i]>=times[i+1] for i in range(len(times)-1))
    if not monotonic:
        meta["row_error"]="publication times not non-increasing"; return meta,None
    snap={
      "capture":dt.datetime.strptime(cap["timestamp"],"%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc),
      "ids":tuple(ids),
      "times":tuple(times),
      "oldest":min(times),"newest":max(times),
    }
    meta["row_count"]=len(ids)
    meta["valid"]=True
    return meta,snap

def collapse(snaps):
    out=[]; seen_seq=set(); collapsed=0
    for s in sorted(snaps,key=lambda x:x["capture"]):
        key=s["ids"]
        if key in seen_seq:
            collapsed+=1; continue
        seen_seq.add(key); out.append(s)
    return out,collapsed

def family_audit(fam,cfg):
    st,raw,err,rows=cdx(cfg)
    caps=accepted_caps(rows,cfg)
    metas=[]; snaps=[]
    for cap in caps:
        m,s=snapshot(fam,cfg,cap); metas.append(m)
        if s: snaps.append(s)
        time.sleep(0.1)
    snaps,collapsed=collapse(snaps)
    breaks=[]; shared=[]
    for a,b in zip(snaps,snaps[1:]):
        n=len(set(a["ids"]) & set(b["ids"]))
        shared.append(n)
        if n==0:
            breaks.append((a["capture"],b["capture"]))
    interval=None
    if snaps:
        interval=(min(s["oldest"] for s in snaps),max(s["newest"] for s in snaps))
    res={
      "cdx_http_status":st,
      "cdx_sha256":hashlib.sha256(raw).hexdigest(),
      "cdx_error":err,
      "accepted_capture_count":len(caps),
      "usable_snapshot_count_before_collapse":sum(1 for m in metas if m.get("valid")),
      "usable_snapshot_count":len(snaps),
      "collapsed_duplicate_snapshot_count":collapsed,
      "transport_or_parse_failure_count":sum(1 for m in metas if not m.get("valid")),
      "continuity_pair_count":max(0,len(snaps)-1),
      "continuity_break_count":len(breaks),
      "shared_id_count_min":min(shared) if shared else None,
      "shared_id_count_median":statistics.median(shared) if shared else None,
      "shared_id_count_max":max(shared) if shared else None,
      "coverage_start":interval[0].isoformat() if interval else None,
      "coverage_end":interval[1].isoformat() if interval else None,
      "first_capture":snaps[0]["capture"].isoformat() if snaps else None,
      "last_capture":snaps[-1]["capture"].isoformat() if snaps else None,
    }
    # hash only aggregate continuity facts, not IDs/times per row
    canon=json.dumps({
      "fam":fam,
      "usable":len(snaps),
      "collapsed":collapsed,
      "breaks":len(breaks),
      "shared":shared,
      "interval":[res["coverage_start"],res["coverage_end"]],
      "captures":[res["first_capture"],res["last_capture"]],
    },sort_keys=True,separators=(",",":")).encode()
    res["aggregate_sha256"]=hashlib.sha256(canon).hexdigest()
    return res,interval,snaps

out={
 "audit_id":"UKLS-ARCHIVE-LIST-CONTINUITY-V0.2.7",
 "event_values_emitted":False,
 "title_parser_opened":False,
 "source_gate_opened":False,
 "binance_opened":False,
 "families":{},
}
intervals={}; snaps_by={}
for fam,cfg in FAMILIES.items():
    res,interval,snaps=family_audit(fam,cfg)
    out["families"][fam]=res; intervals[fam]=interval; snaps_by[fam]=snaps

legacy=out["families"]["LEGACY"]; modern=out["families"]["MODERN"]
legacy_start=False
if snaps_by["LEGACY"]:
    s=snaps_by["LEGACY"][0]
    legacy_start=(s["oldest"]<=START<=s["newest"])
modern_end=False
if snaps_by["MODERN"]:
    s=snaps_by["MODERN"][-1]
    modern_end=(s["capture"]>=END and s["newest"]>=END)
out["legacy_start_boundary_pass"]=legacy_start
out["modern_end_boundary_pass"]=modern_end

overlap_s=0.0
if intervals["LEGACY"] and intervals["MODERN"]:
    lo=max(intervals["LEGACY"][0],intervals["MODERN"][0])
    hi=min(intervals["LEGACY"][1],intervals["MODERN"][1])
    overlap_s=max(0.0,(hi-lo).total_seconds())
out["cross_family_overlap_seconds"]=overlap_s
out["cross_family_overlap_days"]=overlap_s/86400.0
passed=(
    legacy["usable_snapshot_count"]>0 and modern["usable_snapshot_count"]>0 and
    legacy_start and modern_end and
    legacy["continuity_break_count"]==0 and modern["continuity_break_count"]==0 and
    overlap_s>=7*86400
)
out["classification"]="ARCHIVE_LIST_CONTINUITY_PASS" if passed else "ARCHIVE_LIST_CONTINUITY_NOT_PROVEN"
canon=json.dumps({
 "classification":out["classification"],
 "legacy_start":legacy_start,
 "modern_end":modern_end,
 "overlap_seconds":overlap_s,
 "legacy_agg":legacy["aggregate_sha256"],
 "modern_agg":modern["aggregate_sha256"],
},sort_keys=True,separators=(",",":")).encode()
out["audit_aggregate_sha256"]=hashlib.sha256(canon).hexdigest()

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_ARCHIVE_LIST_CONTINUITY_V0_2_7.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
