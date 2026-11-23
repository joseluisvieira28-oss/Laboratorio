#!/usr/bin/env python3
"""BINANCE007 anonymous Hugging Face public dataset + bounded L2 replay.
Read-only source validation. Never computes trading signals, returns or PnL.
All raw Parquet downloaded to ephemeral tmpdir and NOT uploaded to public GitHub.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from book_replay import StrictBook,timestamp

HOST="https://huggingface.co"
DATASET="MaximumLeverage/crypto-lob-stream"
SYMBOL="BTCUSDT"
MONTH="2026-08"
PARTS={
    "depth":f"depth/binance/{SYMBOL}/{MONTH}.parquet",
    "snapshots":f"snapshots/binance/{SYMBOL}/{MONTH}.parquet",
    "trades":f"trades/binance/{SYMBOL}/{MONTH}.parquet"
}
METADATA_OTHERS=("ETHUSDT","SOLUSDT")
MAX_CATALOG_BYTES=5_000_000
MAX_FILE_BYTES=80_000_000
MAX_ALL_BYTES=160_000_000
MAX_DEPTH_ROWS=200_000
MAX_REPLAY_MILLIS=30*60*1000
MIN_APPLIED_EVENTS=500
MAX_TRADE_SCAN_ROWS=500_000
OUT=Path("binance007-evidence")

class SourceStop(Exception):pass

def official_api_url(part):
    if part=="info":
        return f"{HOST}/api/datasets/{DATASET}"
    if part=="tree":
        return f"{HOST}/api/datasets/{DATASET}/tree/main?recursive=true&expand=true"
    raise ValueError("API_PART_NOT_ALLOWED")

def is_allowed_redirect(target):
    url=urllib.parse.urlparse(target)
    host=(url.hostname or "").lower()
    if url.scheme!="https":return False
    return (host in ("huggingface.co","cas-bridge.xethub.hf.co")
         or host.endswith(".xethub.hf.co")
         or host.endswith(".huggingface.co"))

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not is_allowed_redirect(newurl):
            raise SourceStop("UNTRUSTED_REDIRECT_HOST")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

OPENER=urllib.request.build_opener(SafeRedirect)

def http(url,method="GET",timeout=25):
    if not is_allowed_redirect(url):raise SourceStop("UNAPPROVED_INITIAL_HOST")
    return OPENER.open(urllib.request.Request(url,method=method,
              headers={"User-Agent":"CryptoLab-BINANCE007-FreeL2-ResearchOnly/0.1",
                       "Accept":"application/json,application/octet-stream"}),
                       timeout=timeout)

def json_source(url):
    with http(url) as res:
        if res.status!=200:raise SourceStop("API_NON_200")
        data=res.read(MAX_CATALOG_BYTES+1)
    if len(data)>MAX_CATALOG_BYTES:raise SourceStop("METADATA_RESPONSE_TOO_LARGE")
    return json.loads(data),hashlib.sha256(data).hexdigest()

def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

def persist(doc):
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"l2_source_manifest.json"
    path.write_text(json.dumps(doc,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    (OUT/"l2_source_manifest.sha256").write_text(sha_file(path)+"  "+path.name+"\n")

def license_check(info):
    if info.get("private") is not False:
        raise SourceStop("DATASET_NOT_EXPLICITLY_PUBLIC")
    gated=info.get("gated",False)
    if gated not in (False,None):
        raise SourceStop("DATASET_REQUIRES_ACCOUNT_OR_APPROVAL")
    card=info.get("cardData") or {}
    raw=card.get("license") or ""
    if isinstance(raw,list):ok=("mit" in [str(x).lower() for x in raw])
    else:ok=str(raw).lower().strip()=="mit"
    if not ok:raise SourceStop("DATASET_MIT_LICENSE_NOT_EXPLICIT")
    rev=info.get("sha")
    if not isinstance(rev,str) or len(rev)!=40 or any(c not in "abcdef0123456789" for c in rev.lower()):
        raise SourceStop("MISSING_IMMUTABLE_DATASET_REVISION")
    return rev,raw

def entries_from_tree(tree):
    if not isinstance(tree,list):raise SourceStop("HUGGING_FACE_TREE_INVALID")
    return {x["path"]:x for x in tree if isinstance(x,dict) and
            isinstance(x.get("path"),str) and x.get("type")=="file"}

def lfs_sha(e):
    lfs=e.get("lfs") or {}
    raw=lfs.get("oid") or lfs.get("sha256")
    if not isinstance(raw,str):return None
    if raw.startswith("sha256:"):raw=raw[7:]
    return raw.lower() if len(raw)==64 and all(c in "0123456789abcdef" for c in raw.lower()) else None

def checked_download(path,meta,revision,folder):
    if path not in PARTS.values():raise SourceStop("UNREGISTERED_FILE_DOWNLOAD")
    size=meta.get("size")
    if type(size) is not int or size<=0 or size>MAX_FILE_BYTES:
        raise SourceStop("MISSING_OR_OVERSIZED_FILE_METADATA")
    # Never request a branch head URL: pin the complete 40-char revision.
    encoded=urllib.parse.quote(path,safe="/")
    url=f"{HOST}/datasets/{DATASET}/resolve/{revision}/{encoded}"
    dest=Path(folder)/Path(path).name
    sha=hashlib.sha256()
    count=0
    with http(url,timeout=90) as res,dest.open("wb") as fd:
        if res.status!=200:raise SourceStop("DOWNLOAD_HTTP_NOT_200")
        while True:
            chunk=res.read(1024*1024)
            if not chunk:break
            count+=len(chunk)
            if count>size or count>MAX_FILE_BYTES:
                raise SourceStop("DOWNLOAD_EXCEEDED_SIZE_CAP_OR_TREE_EXPECTATION")
            sha.update(chunk);fd.write(chunk)
    if count!=size:raise SourceStop("TRUNCATED_PUBLIC_PARQUET")
    digest=sha.hexdigest()
    expected=lfs_sha(meta)
    if expected and digest!=expected:raise SourceStop("UPSTREAM_LFS_SHA256_MISMATCH")
    return dest,{"path":path,"source_revision":revision,"original_bytes":count,
                 "original_sha256":digest,"upstream_lfs_sha256":expected,
                 "upstream_sha256_confirmed":bool(expected),
                 "source_url":url,
                 "raw_file_publicly_redistributed":False}

def ensure_schema(pq_file,required,kind):
    actual=set(pq_file.schema_arrow.names)
    missing=sorted(set(required)-actual)
    if missing:raise SourceStop(kind+"_REQUIRED_SCHEMA_MISSING_"+",".join(missing))
    return {"columns":pq_file.schema_arrow.names,"row_count":pq_file.metadata.num_rows,
            "row_groups":pq_file.metadata.num_row_groups}

def read_initial_snapshot(pq,snapshot_file):
    required=("timestamp_ms","exchange","asset","side","price","quantity","last_update_id")
    info=ensure_schema(snapshot_file,required,"SNAPSHOT")
    columns=list(required)
    first_key=None
    rows=[]
    for batch in snapshot_file.iter_batches(batch_size=3000,columns=columns):
        for rec in batch.to_pylist():
            key=(rec["timestamp_ms"],rec["last_update_id"])
            if first_key is None:first_key=key
            if key!=first_key:
                book=StrictBook(SYMBOL)
                book.seed(rows)
                return book,info,{"snapshot_rows":len(rows),"selected_anchor":list(first_key)}
            rows.append(rec)
            if len(rows)>2500:raise SourceStop("SNAPSHOT_ANCHOR_TOO_MANY_ROWS")
    if not rows:raise SourceStop("NO_SNAPSHOT_ROWS")
    book=StrictBook(SYMBOL)
    book.seed(rows)
    return book,info,{"snapshot_rows":len(rows),"selected_anchor":list(first_key)}

def bounded_diff_replay(pq,depth_file,book):
    required=("timestamp_ms","exchange","asset","side","price","quantity","first_update_id","last_update_id")
    meta=ensure_schema(depth_file,required,"DEPTH")
    rows_read=0
    group=[]
    gkey=None
    source_from=None
    stop_reason="END_OF_FILE"
    groups_seen=set()
    def close_group():
        nonlocal source_from
        if not group:return
        key=(group[0]["timestamp_ms"],group[0]["first_update_id"],group[0]["last_update_id"])
        if key in groups_seen:
            raise SourceStop("NONCONTIGUOUS_REPEAT_OF_SAME_DEPTH_EVENT")
        groups_seen.add(key)
        ts=timestamp(group[0]["timestamp_ms"])
        # Old buffered diffs are validly ignored based on U/u per official bridge.
        if book.snapshot_id is not None and int(group[0]["last_update_id"])<=book.snapshot_id:
            return
        if source_from is None:
            source_from=ts
            if abs(ts-book.snapshot_timestamp)>5*60*1000:
                raise SourceStop("FIRST_BRIDGED_DIFF_TOO_FAR_FROM_SNAPSHOT_TIME")
        book.apply_event(group)
    try:
        for batch in depth_file.iter_batches(batch_size=5000,columns=list(required)):
            for rec in batch.to_pylist():
                rows_read+=1
                key=(rec["timestamp_ms"],rec["first_update_id"],rec["last_update_id"])
                if gkey is None:gkey=key
                if key!=gkey:
                    close_group()
                    group=[]
                    gkey=key
                    if (source_from is not None and
                        timestamp(rec["timestamp_ms"])-source_from>MAX_REPLAY_MILLIS):
                        stop_reason="PRE_REGISTERED_30MIN_CAPTURE_SPAN"
                        break
                group.append(rec)
                if rows_read>=MAX_DEPTH_ROWS:
                    stop_reason="PRE_REGISTERED_200K_PRICE_LEVEL_ROW_CAP"
                    break
            if stop_reason!="END_OF_FILE":break
        # Group only complete when we know the next event starts; at a hard
        # row cap the partial trailing event is intentionally excluded.
        if stop_reason=="END_OF_FILE":
            close_group()
    except (ValueError,KeyError,TypeError) as exc:
        raise SourceStop("L2_REPLAY_INVALID_"+str(exc)) from exc
    report=book.report()
    report.update({"depth_total_original_file_rows":meta["row_count"],
                   "depth_rows_scanned":rows_read,
                   "depth_source_fraction_sampled":round(rows_read/meta["row_count"],7) if meta["row_count"] else None,
                   "bounded_stop_reason":stop_reason,
                   "replayed_window_minutes":round((book.last_event_timestamp-source_from)/60000,4) if source_from is not None and book.last_event_timestamp is not None else None})
    if book.events_applied<MIN_APPLIED_EVENTS:
        raise SourceStop("INSUFFICIENT_REPLAY_EVENTS_"+str(book.events_applied))
    return meta,report

def read_trade_alignment(trades_file,window_start,window_end):
    required=("timestamp_ms","exchange","asset","price","quantity","buyer_maker")
    meta=ensure_schema(trades_file,required,"TRADES")
    observed=0
    scanned=0
    first=None
    last=None
    for batch in trades_file.iter_batches(batch_size=8000,columns=list(required)):
        for row in batch.to_pylist():
            scanned+=1
            t=timestamp(row["timestamp_ms"])
            if row["exchange"]!="binance" or row["asset"]!=SYMBOL:
                raise SourceStop("TRADES_WRONG_ASSET")
            if not isinstance(row["buyer_maker"],bool):
                raise SourceStop("TRADE_AGGRESSOR_SIDE_NOT_BOOLEAN")
            price=float(row["price"]);qty=float(row["quantity"])
            if not all(math.isfinite(v) and v>0 for v in (price,qty)):
                raise SourceStop("TRADES_PRICE_QUANTITY_INVALID")
            if window_start<=t<=window_end:
                observed+=1
                if first is None:first=t
                last=t
            if t>window_end or scanned>=MAX_TRADE_SCAN_ROWS:break
        if t>window_end or scanned>=MAX_TRADE_SCAN_ROWS:break
    return meta,{"trade_rows_scanned":scanned,
                 "trades_inside_audited_l2_window":observed,
                 "first_matched_trade_timestamp_ms":first,
                 "last_matched_trade_timestamp_ms":last,
                 "trade_scanner_exhaustive":scanned>=meta["row_count"]}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"study":"BINANCE-DIAMANTE-007",
            "status":"SOURCE_BLOCKED",
            "target_dataset":DATASET,
            "fixed_source_asset":SYMBOL,
            "fixed_source_month":MONTH,
            "original_primary_files":PARTS,
            "max_download_file_bytes":MAX_FILE_BYTES,
            "max_download_total_bytes":MAX_ALL_BYTES,
            "raw_market_data_uploaded":False,
            "no_order":True,"no_account":True,"no_paid_data":True,
            "tested_economic_strategy":False,
            "profit_loss":None,
            "candidate_metadata":{}}
    try:
        info,infohash=json_source(official_api_url("info"))
        rev,license=license_check(info)
        report["revision"]=rev
        report["provider_claimed_dataset_license"]=license
        report["hf_dataset_metadata_sha256"]=infohash
        catalog,cataloghash=json_source(official_api_url("tree"))
        report["hf_dataset_tree_sha256"]=cataloghash
        tree=entries_from_tree(catalog)
        report["catalog_items"]=len(tree)
        for other in METADATA_OTHERS:
            names={k:f"{k}/binance/{other}/{MONTH}.parquet" for k in PARTS}
            report["candidate_metadata"][other]={
                "file_presence":{k:v in tree for k,v in names.items()},
                "file_bytes":{k:tree.get(v,{}).get("size") for k,v in names.items()}
            }
        missing=[path for path in PARTS.values() if path not in tree]
        if missing:raise SourceStop("PINNED_SPOT_L2_PARTS_MISSING_"+",".join(missing))
        total=0
        for k,p in PARTS.items():
            item=tree[p]
            n=item.get("size")
            if type(n) is not int or n<=0:raise SourceStop("HF_FILE_SIZE_UNKNOWN_"+k)
            report["candidate_metadata"][k]={"file":p,"bytes":n,"lfs_sha":lfs_sha(item)}
            if n>MAX_FILE_BYTES:raise SourceStop("FILE_TOO_LARGE_"+k+"_"+str(n))
            total+=n
        report["planned_bytes"]=total
        if total>MAX_ALL_BYTES:
            raise SourceStop("TOTAL_HF_FILE_BYTES_OVER_FREE_RESEARCH_CAP_"+str(total))
        report["status"]="LICENSE_AND_FILE_METADATA_ACCEPTED_UNVERIFIED_L2"
        persist(report)
        import pyarrow.parquet as pq
        with tempfile.TemporaryDirectory(prefix="binance007-public-l2-") as scratch:
            acquired={}
            for kind,path in PARTS.items():
                f,rec=checked_download(path,tree[path],rev,scratch)
                report.setdefault("download_receipts",{})[kind]=rec
                acquired[kind]=f
                persist(report)
            with pq.ParquetFile(acquired["snapshots"]) as snapshots:
                book,sm,anchor=read_initial_snapshot(pq,snapshots)
            report["snapshot_schema"]=sm
            report["snapshot_anchor"]=anchor
            persist(report)
            with pq.ParquetFile(acquired["depth"]) as depth:
                dm,replay=bounded_diff_replay(pq,depth,book)
            report["depth_schema"]=dm
            report["strict_book_replay"]=replay
            persist(report)
            with pq.ParquetFile(acquired["trades"]) as trades:
                tm,trade=read_trade_alignment(trades,
                    replay["first_applied_event_ms"],replay["last_event_timestamp_ms"])
            report["trades_schema"]=tm
            report["trade_alignment"]=trade
        if trade["trades_inside_audited_l2_window"]<=0:
            raise SourceStop("NO_MATCHING_TRADES_IN_SAMPLE_OR_TRADE_SCAN_CAP")
        report["status"]="REAL_L2_BOUNDED_WINDOW_REPLAY_PASS_ONLY"
        report["limitations"]=[
            "Only one small Aug 2026 BTCUSDT window tested, NOT full month or 90 days",
            "No full reconstruction for ETHUSDT or SOLUSDT",
            "Third-party collection can contain unknown gaps, survivorship and clock offsets",
            "Book beyond top 1000 each side unknown; ghost-level pruning is necessary",
            "No 30s absorption signals or 60s returns evaluated; no economic GO"
        ]
        persist(report)
        print(json.dumps({"status":report["status"],
            "source_revision":rev,"raw_parquet_sha256":{x:y["original_sha256"] for x,y in report["download_receipts"].items()},
            "strict_book_replay":replay,"trade_alignment":trade,
            "no_trades":True,"no_economic_inference":True},indent=2))
        return 0
    except Exception as exc:
        report["status"]="SOURCE_BLOCKED"
        report["blocker_type"]=type(exc).__name__
        report["blocker"]=str(exc)[:600]
        persist(report)
        print(json.dumps({"status":report["status"],
            "source_revision":report.get("revision"),"blocker":report["blocker"],
            "candidate_metadata":report.get("candidate_metadata"),"no_trading":True},indent=2))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
