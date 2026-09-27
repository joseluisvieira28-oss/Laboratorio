#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, sys, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import duckdb

CRAWL="CC-MAIN-2024-10"
PREFIX=f"cc-index/table/cc-main/warc/crawl={CRAWL}/subset=warc/"
S3_LIST="https://commoncrawl.s3.amazonaws.com/"
DATA="https://data.commoncrawl.org/"
OUT=Path("artifacts/UKLS_COMMON_CRAWL_URL_INDEX_V0_2_5B.json")
RAW=Path("artifacts/UKLS_COMMON_CRAWL_URL_INDEX_V0_2_5B_ROWS.json")
OUT.parent.mkdir(parents=True,exist_ok=True)

def list_public_s3():
    keys=[]; total=0; token=None; pages=0
    while True:
        params={"list-type":"2","prefix":PREFIX,"max-keys":"1000"}
        if token: params["continuation-token"]=token
        url=S3_LIST+"?"+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CC-URLIndex/0.2.5B"})
        with urllib.request.urlopen(req,timeout=90) as r:
            raw=r.read()
        pages+=1
        root=ET.fromstring(raw)
        ns={"s3":"http://s3.amazonaws.com/doc/2006-03-01/"}
        for c in root.findall("s3:Contents",ns):
            k=c.findtext("s3:Key",default="",namespaces=ns)
            s=int(c.findtext("s3:Size",default="0",namespaces=ns))
            if k.endswith(".parquet"):
                keys.append(k); total+=s
        trunc=(root.findtext("s3:IsTruncated",default="false",namespaces=ns).lower()=="true")
        if not trunc: break
        token=root.findtext("s3:NextContinuationToken",default="",namespaces=ns)
        if not token: raise RuntimeError("S3 listing truncated without continuation token")
        if pages>100: raise RuntimeError("S3 listing pagination runaway")
    return keys,total,pages

def redact_url(u):
    try:
        p=urllib.parse.urlsplit(u)
        path=re.sub(r"(/api/v1/(?:announcements|notices)/)\d+",r"\1<ID>",p.path)
        return urllib.parse.urlunsplit((p.scheme,p.netloc,path,p.query,""))
    except Exception:
        return "<REDACTION_ERROR>"

receipt={
 "probe_id":"UKLS-COMMON-CRAWL-URL-INDEX-V0.2.5B",
 "crawl":CRAWL,
 "subset":"warc",
 "warc_payload_opened":False,
 "event_values_opened":False,
 "binance_opened":False,
 "classification":"COMMON_CRAWL_URL_INDEX_TRANSPORT_FAILURE",
}
try:
    keys,total,pages=list_public_s3()
    receipt["s3_listing_pass"]=True
    receipt["s3_listing_pages"]=pages
    receipt["parquet_object_count"]=len(keys)
    receipt["aggregate_parquet_bytes"]=total
    if not keys: raise RuntimeError("no parquet objects in frozen partition")

    urls=[DATA+k for k in keys]
    con=duckdb.connect(database=":memory:")
    receipt["duckdb_version"]=duckdb.__version__
    con.execute("SET enable_object_cache=true")
    # Query metadata only. Predicate pushdown is expected against host/path columns.
    sql="""
      SELECT url, url_path, url_query, fetch_time, fetch_status,
             content_digest, warc_filename, warc_record_offset, warc_record_length
      FROM read_parquet(?, union_by_name=true)
      WHERE url_host_name = 'api-manager.upbit.com'
        AND (
          url_path = '/api/v1/announcements'
          OR starts_with(url_path, '/api/v1/announcements/')
          OR url_path = '/api/v1/notices'
          OR starts_with(url_path, '/api/v1/notices/')
        )
      ORDER BY fetch_time, url
      LIMIT 500
    """
    rows=con.execute(sql,[urls]).fetchall()
    cols=[d[0] for d in con.description]
    docs=[dict(zip(cols,r)) for r in rows]
    # JSON-safe timestamps
    for d in docs:
        if d.get("fetch_time") is not None: d["fetch_time"]=str(d["fetch_time"])
    RAW.write_text(json.dumps(docs,indent=2,sort_keys=True,default=str)+"\n")
    receipt["query_pass"]=True
    receipt["matched_index_rows"]=len(docs)
    receipt["matched_rows_capped"]=len(docs)>=500

    path_counts=Counter()
    status_counts=Counter()
    urls_seen=set()
    fetch_times=[]
    locator_complete=0
    for d in docs:
        p=d.get("url_path") or ""
        if p in ("/api/v1/announcements","/api/v1/notices"):
            fam=p.rsplit("/",1)[-1]
            path_counts[f"{fam}:LIST"]+=1
        elif re.fullmatch(r"/api/v1/announcements/\d+",p):
            path_counts["announcements:NUMERIC_DETAIL"]+=1
        elif re.fullmatch(r"/api/v1/notices/\d+",p):
            path_counts["notices:NUMERIC_DETAIL"]+=1
        elif p.startswith("/api/v1/announcements/"):
            path_counts["announcements:OTHER_DETAIL"]+=1
        elif p.startswith("/api/v1/notices/"):
            path_counts["notices:OTHER_DETAIL"]+=1
        status_counts[str(d.get("fetch_status"))]+=1
        if d.get("url"): urls_seen.add(d["url"])
        if d.get("fetch_time"): fetch_times.append(d["fetch_time"])
        if d.get("warc_filename") is not None and d.get("warc_record_offset") is not None and d.get("warc_record_length") is not None:
            locator_complete+=1
    receipt["path_family_counts"]=dict(sorted(path_counts.items()))
    receipt["fetch_status_counts"]=dict(sorted(status_counts.items()))
    receipt["distinct_original_url_count"]=len(urls_seen)
    receipt["earliest_fetch_time"]=min(fetch_times) if fetch_times else None
    receipt["latest_fetch_time"]=max(fetch_times) if fetch_times else None
    receipt["warc_locator_complete_rows"]=locator_complete
    receipt["query_result_sha256"]=hashlib.sha256(RAW.read_bytes()).hexdigest()
    receipt["redacted_url_examples"]=sorted({redact_url(u) for u in urls_seen})[:20]
    receipt["classification"]="COMMON_CRAWL_URL_INDEX_TRANSPORT_PASS"
except Exception as e:
    receipt["failure"]=f"{type(e).__name__}: {str(e)[:5000]}"

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,default=str)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "crawl":CRAWL,
 "s3_listing_pass":receipt.get("s3_listing_pass"),
 "parquet_object_count":receipt.get("parquet_object_count"),
 "aggregate_parquet_bytes":receipt.get("aggregate_parquet_bytes"),
 "duckdb_version":receipt.get("duckdb_version"),
 "query_pass":receipt.get("query_pass"),
 "matched_index_rows":receipt.get("matched_index_rows"),
 "path_family_counts":receipt.get("path_family_counts"),
 "fetch_status_counts":receipt.get("fetch_status_counts"),
 "earliest_fetch_time":receipt.get("earliest_fetch_time"),
 "latest_fetch_time":receipt.get("latest_fetch_time"),
 "failure":receipt.get("failure"),
},sort_keys=True))
