#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, gzip, hashlib, json, re, time, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
import brotli

CDX="https://web.archive.org/cdx/search/cdx"
FAMILIES=[
 ("MODERN","api-manager.upbit.com/api/v1/announcements*","/api/v1/announcements"),
 ("LEGACY","api-manager.upbit.com/api/v1/notices*","/api/v1/notices"),
]
UA={"User-Agent":"CryptoLab-Upbit-TitleEquiv/0.2.6","Accept":"application/json,*/*"}

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

def accepted_caps(rows,fam,basepath):
    out=[]
    rx=re.compile("^"+re.escape(basepath)+r"/\d+$")
    for r in rows:
        try: p=urllib.parse.urlsplit(r.get("original") or "")
        except Exception: continue
        if p.path==basepath or rx.fullmatch(p.path):
            kind="LIST" if p.path==basepath else "DETAIL"
            out.append((r.get("timestamp"),r.get("original"),r.get("digest"),kind,r))
    seen=set(); uniq=[]
    for ts,orig,digest,kind,r in sorted(out):
        k=(ts,orig,digest)
        if k not in seen:
            seen.add(k); rr=dict(r); rr["_kind"]=kind; uniq.append(rr)
    return uniq

def hget(headers,name):
    for k,v in headers.items():
        if k.lower()==name.lower(): return v
    return None

def decode(raw,headers):
    if raw[:2]==b"\x1f\x8b":
        return gzip.decompress(raw),"gzip_magic"
    enc=(hget(headers,"X-Archive-Orig-Content-Encoding") or hget(headers,"Content-Encoding") or "").lower().strip()
    if enc=="br": return brotli.decompress(raw),"brotli_header"
    if enc=="gzip": return gzip.decompress(raw),"gzip_header"
    return raw,"identity"

def parse_json_transport(cap):
    attempts=[]
    for suffix in ("id_","if_"):
        replay=f"https://web.archive.org/web/{cap['timestamp']}{suffix}/{cap['original']}"
        st,h,raw,err=get(replay,120,3)
        m={"suffix":suffix,"http_status":st,"transport_error":err,"raw_bytes":len(raw),
           "raw_sha256":hashlib.sha256(raw).hexdigest()}
        attempts.append(m)
        if st!=200 or not raw:
            if suffix=="id_": continue
            return None,attempts
        try:
            dec,mode=decode(raw,h)
            m["decode_mode"]=mode
            m["decoded_bytes"]=len(dec)
            m["decoded_sha256"]=hashlib.sha256(dec).hexdigest()
            obj=json.loads(dec.decode("utf-8"))
            m["json_ok"]=True
            return obj,attempts
        except Exception as e:
            m["decode_or_json_error"]=repr(e)
            if suffix=="id_": continue
            return None,attempts
    return None,attempts

def norm_iso(s):
    if not isinstance(s,str) or not s.strip(): raise ValueError("empty timestamp")
    x=s.strip().replace("Z","+00:00")
    d=dt.datetime.fromisoformat(x)
    if d.tzinfo is None: raise ValueError("naive timestamp")
    return d.astimezone(dt.timezone.utc).isoformat(timespec="seconds")

def extract_records(fam,kind,obj):
    if not isinstance(obj,dict): return []
    data=obj.get("data")
    rows=[]
    if kind=="LIST":
        if not isinstance(data,dict): return []
        rows=data.get("notices") if fam=="MODERN" else data.get("list")
        if not isinstance(rows,list): return []
    else:
        if isinstance(data,dict):
            # Some detail responses wrap the notice in data, others data.notice.
            if isinstance(data.get("notice"),dict): rows=[data["notice"]]
            else: rows=[data]
        else: return []
    out=[]
    for r in rows:
        if not isinstance(r,dict): continue
        try:
            title=r["title"]
            if not isinstance(title,str): continue
            if fam=="MODERN":
                a=norm_iso(r["first_listed_at"]); b=norm_iso(r["listed_at"])
                out.append((title,a,b))
            else:
                a=norm_iso(r["created_at"]); b=norm_iso(r["updated_at"])
                out.append((title,a,b))
        except Exception:
            continue
    return out

out={
 "audit_id":"UKLS-TITLE-LINKED-EQUIVALENCE-V0.2.6",
 "event_values_emitted":False,
 "historical_enumeration_opened":False,
 "source_gate_opened":False,
 "binance_opened":False,
 "families":{},
}
family_records={}
for fam,pat,basepath in FAMILIES:
    st,raw,err,rows=cdx(pat)
    caps=accepted_caps(rows,fam,basepath)
    records=[]
    transport=[]
    for cap in caps:
        obj,atts=parse_json_transport(cap)
        usable=extract_records(fam,cap["_kind"],obj) if obj is not None else []
        records.extend(usable)
        transport.append({
          "kind":cap["_kind"],
          "capture":cap["timestamp"],
          "attempt_count":len(atts),
          "transport_ok":obj is not None,
          "usable_record_count":len(usable),
          "attempt_statuses":[a.get("http_status") for a in atts],
          "decode_modes":[a.get("decode_mode") for a in atts if a.get("decode_mode")],
        })
        time.sleep(0.12)
    family_records[fam]=records
    out["families"][fam]={
      "cdx_http_status":st,
      "cdx_sha256":hashlib.sha256(raw).hexdigest(),
      "cdx_error":err,
      "accepted_capture_count":len(caps),
      "accepted_list_capture_count":sum(c["_kind"]=="LIST" for c in caps),
      "accepted_detail_capture_count":sum(c["_kind"]=="DETAIL" for c in caps),
      "decoded_capture_count":sum(t["transport_ok"] for t in transport),
      "transport_or_decode_failure_count":sum(not t["transport_ok"] for t in transport),
      "usable_record_instances":len(records),
      "transport_status_counts":dict(Counter(str(s) for t in transport for s in t["attempt_statuses"])),
      "decode_mode_counts":dict(Counter(m for t in transport for m in t["decode_modes"])),
    }

grouped={}
ambiguous={}
for fam in ("MODERN","LEGACY"):
    d=defaultdict(set)
    for title,a,b in family_records[fam]:
        d[title].add((a,b))
    grouped[fam]={k:next(iter(v)) for k,v in d.items() if len(v)==1}
    ambiguous[fam]={k:len(v) for k,v in d.items() if len(v)>1}
    out["families"][fam]["distinct_exact_title_count"]=len(d)
    out["families"][fam]["unambiguous_title_count"]=len(grouped[fam])
    out["families"][fam]["ambiguous_title_count"]=len(ambiguous[fam])

common=sorted(set(grouped["MODERN"]) & set(grouped["LEGACY"]))
comp=[]
for title in common:
    la,lb=grouped["LEGACY"][title]
    ma,mb=grouped["MODERN"][title]
    created_first=(la==ma)
    updated_listed=(lb==mb)
    canon=json.dumps([title,la,lb,ma,mb],ensure_ascii=False,separators=(",",":")).encode()
    comp.append({
      "created_first":created_first,
      "updated_listed":updated_listed,
      "tuple_sha256":hashlib.sha256(canon).hexdigest(),
    })

out["comparable_exact_title_count"]=len(comp)
out["created_to_first_exact_count"]=sum(x["created_first"] for x in comp)
out["updated_to_listed_exact_count"]=sum(x["updated_listed"] for x in comp)
out["all_timestamp_fields_exact_count"]=sum(x["created_first"] and x["updated_listed"] for x in comp)
out["comparison_aggregate_sha256"]=hashlib.sha256(
    ("\n".join(sorted(x["tuple_sha256"] for x in comp))).encode()
).hexdigest()
passed=(len(comp)>=5 and
        out["created_to_first_exact_count"]==len(comp) and
        out["updated_to_listed_exact_count"]==len(comp) and
        out["all_timestamp_fields_exact_count"]==len(comp))
out["classification"]="TITLE_LINKED_LEGACY_MODERN_SIGNAL_SCHEMA_EQUIVALENT" if passed else "TITLE_LINKED_EQUIVALENCE_NOT_PROVEN"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/UKLS_TITLE_LINKED_EQUIVALENCE_V0_2_6.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
