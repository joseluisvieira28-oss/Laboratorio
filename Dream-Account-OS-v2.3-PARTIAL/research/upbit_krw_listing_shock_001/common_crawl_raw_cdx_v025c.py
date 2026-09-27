#!/usr/bin/env python3
from __future__ import annotations
import gzip, hashlib, io, json, re, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

CRAWL="CC-MAIN-2024-10"
ROOT=f"https://data.commoncrawl.org/cc-index/collections/{CRAWL}/indexes/"
CLUSTER=ROOT+"cluster.idx"
TARGET="com,upbit,api-manager)/"
MAX_SHARDS=6
MAX_COMPRESSED=1024**3
MAX_MATCHES=2000
OUT=Path("artifacts/UKLS_COMMON_CRAWL_RAW_INDEX_V0_2_5C.json")
RAW=Path("artifacts/UKLS_COMMON_CRAWL_RAW_INDEX_V0_2_5C_ROWS.json")
OUT.parent.mkdir(parents=True,exist_ok=True)

def fetch(url,timeout=120):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CC-RawIndex/0.2.5C","Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.status,dict(r.headers),r.read()

def parse_cluster(raw:bytes):
    rows=[]
    prev=None
    ordered=True
    malformed=0
    for line in raw.decode("utf-8","replace").splitlines():
        if not line.strip(): continue
        parts=line.split("\t")
        if len(parts)<2:
            malformed+=1; continue
        key=parts[0]
        shard=parts[1]
        if not re.fullmatch(r"cdx-\d+\.gz",shard):
            malformed+=1; continue
        if prev is not None and key<prev: ordered=False
        prev=key
        rows.append((key,shard))
    return rows,ordered,malformed

def select_shards(rows):
    starts=[i for i,(k,s) in enumerate(rows) if k.startswith(TARGET)]
    idxs=set()
    if starts:
        lo=min(starts); hi=max(starts)
        idxs.update(starts)
        if lo>0: idxs.add(lo-1)
        if hi+1<len(rows): idxs.add(hi+1)
    else:
        # Exact prefix may fall inside a compressed block: select predecessor and successor summary blocks.
        greater=next((i for i,(k,s) in enumerate(rows) if k>TARGET),None)
        if greater is None:
            if rows: idxs.add(len(rows)-1)
        else:
            idxs.add(greater)
            if greater>0: idxs.add(greater-1)
    return sorted({rows[i][1] for i in idxs})

def accept_url(u):
    try:
        p=urllib.parse.urlsplit(u)
    except Exception:
        return False,None
    if (p.hostname or "").lower()!="api-manager.upbit.com":
        return False,None
    path=p.path
    good=(path=="/api/v1/announcements" or path.startswith("/api/v1/announcements/") or
          path=="/api/v1/notices" or path.startswith("/api/v1/notices/"))
    return good,path

def redact_path(path):
    return re.sub(r"(/api/v1/(?:announcements|notices)/)\d+",r"\1<ID>",path)

receipt={
 "probe_id":"UKLS-COMMON-CRAWL-RAW-CDX-V0.2.5C",
 "crawl":CRAWL,
 "warc_payload_opened":False,
 "archived_response_payload_opened":False,
 "event_values_opened":False,
 "binance_opened":False,
 "classification":"COMMON_CRAWL_RAW_INDEX_TRANSPORT_FAILURE",
}
retained=[]
try:
    st,h,cluster=fetch(CLUSTER)
    receipt["cluster_http_status"]=st
    receipt["cluster_bytes"]=len(cluster)
    receipt["cluster_sha256"]=hashlib.sha256(cluster).hexdigest()
    if st!=200 or not cluster: raise RuntimeError(f"cluster.idx unavailable status={st}")
    rows,ordered,malformed=parse_cluster(cluster)
    receipt["secondary_index_row_count"]=len(rows)
    receipt["secondary_index_ordered"]=ordered
    receipt["secondary_index_malformed_count"]=malformed
    if not rows or not ordered: raise RuntimeError("secondary index invalid/unordered")
    shards=select_shards(rows)
    receipt["selected_shards"]=shards
    receipt["selected_shard_count"]=len(shards)
    if not shards or len(shards)>MAX_SHARDS:
        raise RuntimeError(f"selected shard count outside cap: {len(shards)}")

    shard_meta=[]
    total=0
    for shard in shards:
        sst,sh,zb=fetch(ROOT+shard,180)
        if sst!=200 or not zb: raise RuntimeError(f"shard unavailable {shard} status={sst}")
        total+=len(zb)
        if total>MAX_COMPRESSED: raise RuntimeError("compressed download cap exceeded")
        meta={"shard":shard,"http_status":sst,"compressed_bytes":len(zb),"sha256":hashlib.sha256(zb).hexdigest()}
        matched=0
        with gzip.GzipFile(fileobj=io.BytesIO(zb),mode="rb") as gz:
            for rawline in gz:
                try: line=rawline.decode("utf-8","replace").rstrip("\n")
                except Exception: continue
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
                retained.append({
                  "surt":surt,
                  "timestamp":ts,
                  "url":u,
                  "path":path,
                  "status":obj.get("status"),
                  "mime":obj.get("mime"),
                  "digest":obj.get("digest"),
                  "filename":obj.get("filename"),
                  "offset":obj.get("offset"),
                  "length":obj.get("length"),
                  "source_shard":shard,
                })
                matched+=1
                if len(retained)>=MAX_MATCHES: break
        meta["matched_rows"]=matched
        shard_meta.append(meta)
        if len(retained)>=MAX_MATCHES: break
    receipt["shards"]=shard_meta
    receipt["total_compressed_bytes"]=total
    RAW.write_text(json.dumps(retained,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    receipt["matched_index_rows"]=len(retained)
    receipt["matched_rows_capped"]=len(retained)>=MAX_MATCHES
    pc=Counter(); sc=Counter(); urls=set(); timestamps=[]; locator=0
    for r in retained:
        p=r["path"]
        if p=="/api/v1/announcements": pc["announcements:LIST"]+=1
        elif p=="/api/v1/notices": pc["notices:LIST"]+=1
        elif re.fullmatch(r"/api/v1/announcements/\d+",p): pc["announcements:NUMERIC_DETAIL"]+=1
        elif re.fullmatch(r"/api/v1/notices/\d+",p): pc["notices:NUMERIC_DETAIL"]+=1
        elif p.startswith("/api/v1/announcements/"): pc["announcements:OTHER_DETAIL"]+=1
        elif p.startswith("/api/v1/notices/"): pc["notices:OTHER_DETAIL"]+=1
        sc[str(r.get("status"))]+=1
        urls.add(r.get("url"))
        if r.get("timestamp"): timestamps.append(r["timestamp"])
        if r.get("filename") is not None and r.get("offset") is not None and r.get("length") is not None:
            locator+=1
    receipt["path_family_counts"]=dict(sorted(pc.items()))
    receipt["fetch_status_counts"]=dict(sorted(sc.items()))
    receipt["distinct_original_url_count"]=len(urls)
    receipt["earliest_crawl_timestamp"]=min(timestamps) if timestamps else None
    receipt["latest_crawl_timestamp"]=max(timestamps) if timestamps else None
    receipt["warc_locator_complete_rows"]=locator
    receipt["index_rows_sha256"]=hashlib.sha256(RAW.read_bytes()).hexdigest()
    receipt["redacted_path_examples"]=sorted({redact_path(r["path"]) for r in retained})[:20]
    receipt["classification"]="COMMON_CRAWL_RAW_INDEX_TRANSPORT_PASS"
except Exception as e:
    receipt["failure"]=f"{type(e).__name__}: {str(e)[:5000]}"

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "cluster_http_status":receipt.get("cluster_http_status"),
 "cluster_bytes":receipt.get("cluster_bytes"),
 "secondary_index_rows":receipt.get("secondary_index_row_count"),
 "ordered":receipt.get("secondary_index_ordered"),
 "selected_shards":receipt.get("selected_shards"),
 "total_compressed_bytes":receipt.get("total_compressed_bytes"),
 "matched_rows":receipt.get("matched_index_rows"),
 "path_counts":receipt.get("path_family_counts"),
 "status_counts":receipt.get("fetch_status_counts"),
 "crawl_range":[receipt.get("earliest_crawl_timestamp"),receipt.get("latest_crawl_timestamp")],
 "failure":receipt.get("failure"),
},sort_keys=True))
