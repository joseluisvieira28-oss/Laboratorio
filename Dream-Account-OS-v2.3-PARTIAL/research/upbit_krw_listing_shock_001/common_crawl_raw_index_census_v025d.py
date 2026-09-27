#!/usr/bin/env python3
from __future__ import annotations
import bisect, gzip, hashlib, json, re, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

CRAWLS=[
 "CC-MAIN-2023-06","CC-MAIN-2023-14","CC-MAIN-2023-23","CC-MAIN-2023-40","CC-MAIN-2023-50",
 "CC-MAIN-2024-10","CC-MAIN-2024-18","CC-MAIN-2024-22","CC-MAIN-2024-26","CC-MAIN-2024-30",
 "CC-MAIN-2024-33","CC-MAIN-2024-38","CC-MAIN-2024-42","CC-MAIN-2024-46","CC-MAIN-2024-51",
]
TARGET="com,upbit,api-manager)/"
UPPER=TARGET+chr(0x10ffff)
MAX_BLOCKS_PER=20
MAX_BLOCKS_TOTAL=300
MAX_BYTES=1024**3
MAX_MATCHES=10000
ROOT="https://data.commoncrawl.org/cc-index/collections/{crawl}/indexes/"
OUT=Path("artifacts/UKLS_COMMON_CRAWL_RAW_INDEX_CENSUS_V0_2_5D.json")
RAW=Path("artifacts/UKLS_COMMON_CRAWL_RAW_INDEX_CENSUS_V0_2_5D_ROWS.json")
OUT.parent.mkdir(parents=True,exist_ok=True)

def fetch_full(url,timeout=180):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CC-Census/0.2.5D","Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read()
        return r.status,dict(r.headers),raw

def fetch_range(url,offset,length,timeout=180):
    end=offset+length-1
    req=urllib.request.Request(url,headers={
      "User-Agent":"CryptoLab-CC-Census/0.2.5D","Accept":"*/*",
      "Range":f"bytes={offset}-{end}",
    })
    with urllib.request.urlopen(req,timeout=timeout) as r:
        status=r.status
        cl=r.headers.get("Content-Length")
        if status==200 and cl and int(cl)>length:
            raise RuntimeError(f"Range ignored with oversized 200 body content_length={cl} requested={length}")
        raw=r.read(length+1)
    if len(raw)!=length:
        raise RuntimeError(f"Range byte count mismatch status={status} got={len(raw)} expected={length}")
    if status not in (200,206):
        raise RuntimeError(f"Range HTTP status {status}")
    return status,raw

def parse_cluster(raw):
    rows=[]; malformed=0; ordered=True; prev=None
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip(): continue
        parts=line.split("\t")
        if len(parts)<4:
            malformed+=1; continue
        key,part,off_s,len_s=parts[:4]
        if not re.fullmatch(r"cdx-\d+\.gz",part):
            malformed+=1; continue
        try:
            off=int(off_s); ln=int(len_s)
        except Exception:
            malformed+=1; continue
        if off<0 or ln<=0:
            malformed+=1; continue
        if prev is not None and key<prev: ordered=False
        prev=key
        rows.append((key,part,off,ln))
    return rows,ordered,malformed

def select_blocks(rows):
    keys=[x[0] for x in rows]
    if not keys: return []
    i=bisect.bisect_left(keys,TARGET)
    lo=max(0,i-1)
    hi=bisect.bisect_right(keys,UPPER)
    if hi<=lo: hi=min(len(rows),lo+1)
    selected=rows[lo:hi]
    # Dedupe exact block specs while preserving order.
    seen=set(); out=[]
    for x in selected:
        spec=x[1:]
        if spec not in seen:
            seen.add(spec); out.append(x)
    return out

def accept_url(u):
    try: p=urllib.parse.urlsplit(u)
    except Exception: return False,None
    if (p.hostname or "").lower()!="api-manager.upbit.com": return False,None
    path=p.path
    ok=(path=="/api/v1/announcements" or path.startswith("/api/v1/announcements/") or
        path=="/api/v1/notices" or path.startswith("/api/v1/notices/"))
    return ok,path

def path_class(path):
    if path=="/api/v1/announcements": return "MODERN_LIST"
    if path=="/api/v1/notices": return "LEGACY_LIST"
    if re.fullmatch(r"/api/v1/announcements/\d+",path): return "MODERN_NUMERIC_DETAIL"
    if re.fullmatch(r"/api/v1/notices/\d+",path): return "LEGACY_NUMERIC_DETAIL"
    if path.startswith("/api/v1/announcements/"): return "MODERN_OTHER_DETAIL"
    if path.startswith("/api/v1/notices/"): return "LEGACY_OTHER_DETAIL"
    return "OTHER"

receipt={
 "probe_id":"UKLS-COMMON-CRAWL-RAW-INDEX-CENSUS-V0.2.5D",
 "warc_payload_opened":False,
 "archived_response_payload_opened":False,
 "event_values_opened":False,
 "binance_opened":False,
 "trigger_run_id":36325097130,
 "classification":"COMMON_CRAWL_CENSUS_TECHNICAL_FAILURE",
 "crawls":[],
}
retained=[]
total_bytes=0; total_blocks=0; failures=[]
for crawl in CRAWLS:
    c={"crawl":crawl}
    try:
        root=ROOT.format(crawl=crawl)
        st,h,cluster=fetch_full(root+"cluster.idx",180)
        c["cluster_http_status"]=st
        c["cluster_bytes"]=len(cluster)
        c["cluster_sha256"]=hashlib.sha256(cluster).hexdigest()
        if st!=200 or not cluster: raise RuntimeError(f"cluster status={st}")
        rows,ordered,malformed=parse_cluster(cluster)
        c["secondary_index_rows"]=len(rows)
        c["secondary_index_ordered"]=ordered
        c["secondary_index_malformed"]=malformed
        if not rows or not ordered: raise RuntimeError("invalid/unordered cluster.idx")
        blocks=select_blocks(rows)
        c["selected_block_count"]=len(blocks)
        c["selected_parts"]=sorted({x[1] for x in blocks})
        if not blocks or len(blocks)>MAX_BLOCKS_PER:
            raise RuntimeError(f"selected block count {len(blocks)} outside cap")
        total_blocks+=len(blocks)
        if total_blocks>MAX_BLOCKS_TOTAL: raise RuntimeError("global block cap exceeded")
        block_receipts=[]; crawl_matches=[]
        for key,part,off,ln in blocks:
            if total_bytes+ln>MAX_BYTES: raise RuntimeError("global compressed range byte cap exceeded")
            bst,raw=fetch_range(root+part,off,ln,180)
            total_bytes+=len(raw)
            bmeta={"part":part,"offset":off,"length":ln,"http_status":bst,"sha256":hashlib.sha256(raw).hexdigest()}
            try:
                dec=gzip.decompress(raw)
            except Exception as e:
                raise RuntimeError(f"gzip block decode {part}@{off}+{ln}: {e}")
            matched=0
            for rawline in dec.splitlines():
                line=rawline.decode("utf-8","replace")
                if not line: continue
                parts=line.split(" ",2)
                if len(parts)!=3: continue
                surt,ts,jtxt=parts
                if not surt.startswith(TARGET): continue
                try: obj=json.loads(jtxt)
                except Exception: continue
                u=obj.get("url")
                ok,path=accept_url(u)
                if not ok: continue
                rec={
                  "crawl":crawl,"surt":surt,"timestamp":ts,"url":u,"path":path,
                  "path_class":path_class(path),"status":str(obj.get("status")) if obj.get("status") is not None else None,
                  "mime":obj.get("mime"),"digest":obj.get("digest"),
                  "filename":obj.get("filename"),"offset":obj.get("offset"),"length":obj.get("length"),
                  "source_part":part,"source_block_offset":off,"source_block_length":ln,
                }
                retained.append(rec); crawl_matches.append(rec); matched+=1
                if len(retained)>MAX_MATCHES: raise RuntimeError("matched row cap exceeded")
            bmeta["matched_rows"]=matched
            block_receipts.append(bmeta)
        c["blocks"]=block_receipts
        c["compressed_range_bytes"]=sum(b["length"] for b in block_receipts)
        c["matched_rows"]=len(crawl_matches)
        pc=Counter(r["path_class"] for r in crawl_matches)
        sc=Counter(r["status"] for r in crawl_matches)
        c["path_class_counts"]=dict(sorted(pc.items()))
        c["status_counts"]=dict(sorted(sc.items()))
        times=[r["timestamp"] for r in crawl_matches if r.get("timestamp")]
        c["earliest_timestamp"]=min(times) if times else None
        c["latest_timestamp"]=max(times) if times else None
        c["distinct_original_urls"]=len({r["url"] for r in crawl_matches})
        c["warc_locator_complete_rows"]=sum(
          r.get("filename") is not None and r.get("offset") is not None and r.get("length") is not None
          for r in crawl_matches
        )
        c["audit_pass"]=True
    except Exception as e:
        c["audit_pass"]=False
        c["failure"]=f"{type(e).__name__}: {str(e)[:3000]}"
        failures.append({"crawl":crawl,"failure":c["failure"]})
    receipt["crawls"].append(c)

RAW.write_text(json.dumps(retained,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
receipt["total_selected_blocks"]=total_blocks
receipt["total_compressed_range_bytes"]=total_bytes
receipt["matched_index_rows"]=len(retained)
receipt["index_rows_sha256"]=hashlib.sha256(RAW.read_bytes()).hexdigest()
receipt["technical_failure_count"]=len(failures)
receipt["technical_failures"]=failures

agg=Counter(r["path_class"] for r in retained)
receipt["aggregate_path_class_counts"]=dict(sorted(agg.items()))
receipt["aggregate_status_counts"]=dict(sorted(Counter(r["status"] for r in retained).items()))
receipt["modern_list_2023_http200"]=sum(
    r["crawl"].startswith("CC-MAIN-2023-") and r["path_class"]=="MODERN_LIST" and r["status"]=="200"
    for r in retained
)
receipt["modern_list_2024_http200"]=sum(
    r["crawl"].startswith("CC-MAIN-2024-") and r["path_class"]=="MODERN_LIST" and r["status"]=="200"
    for r in retained
)
receipt["legacy_list_2023_http200"]=sum(
    r["crawl"].startswith("CC-MAIN-2023-") and r["path_class"]=="LEGACY_LIST" and r["status"]=="200"
    for r in retained
)
receipt["legacy_list_2024_http200"]=sum(
    r["crawl"].startswith("CC-MAIN-2024-") and r["path_class"]=="LEGACY_LIST" and r["status"]=="200"
    for r in retained
)
exact_success=receipt["modern_list_2023_http200"]+receipt["modern_list_2024_http200"]+receipt["legacy_list_2023_http200"]+receipt["legacy_list_2024_http200"]
if failures:
    cls="COMMON_CRAWL_CENSUS_TECHNICAL_FAILURE"
elif receipt["modern_list_2023_http200"]>0:
    cls="COMMON_CRAWL_MODERN_2023_CANDIDATE"
elif exact_success>0:
    cls="COMMON_CRAWL_ARCHIVE_CANDIDATE"
else:
    cls="COMMON_CRAWL_NO_EXACT_LIST_CAPTURE"
receipt["classification"]=cls

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":cls,
 "technical_failure_count":len(failures),
 "total_blocks":total_blocks,
 "total_compressed_range_bytes":total_bytes,
 "matched_index_rows":len(retained),
 "modern_list_2023_http200":receipt["modern_list_2023_http200"],
 "modern_list_2024_http200":receipt["modern_list_2024_http200"],
 "legacy_list_2023_http200":receipt["legacy_list_2023_http200"],
 "legacy_list_2024_http200":receipt["legacy_list_2024_http200"],
 "aggregate_path_class_counts":receipt["aggregate_path_class_counts"],
},sort_keys=True))
