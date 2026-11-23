#!/usr/bin/env python3
"""BINANCE008: metadata-only trust inspection of HF redirect, and public free
post-bug Tardis Spot sample HEAD / bounded original-byte source validation.
No exchange orders, positions, historical strategy signals, or PnL.
"""
from __future__ import annotations
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import tempfile
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

OUT=Path("binance008-evidence")
WHITELISTED_HF_HOSTS=frozenset({
    "huggingface.co","cas-server.xethub.hf.co","cas-server.xethub-eu.hf.co",
    "transfer.xethub.hf.co","transfer.xethub-eu.hf.co",
    "us.aws.cdn.hf.co","us.gcp.cdn.hf.co",
    "cdn-lfs-us-1.hf.co","cdn-lfs-eu-1.hf.co"
})
HF_IMMUTABLE="2b8c544ae5b46dd57c6f8807a51965d61ea4b20c"
HF_URL=("https://huggingface.co/datasets/Goooddy/crypto-lob-stream/"
        "resolve/"+HF_IMMUTABLE+"/snapshots/binance/SOLUSDT/2026-08.parquet")
TARDIS_ROOT="https://datasets.tardis.dev/v1/binance/"
TARDIS_URLS={
    "l2":TARDIS_ROOT+"incremental_book_L2/2026/09/01/SOLUSDT.csv.gz",
    "trades":TARDIS_ROOT+"trades/2026/09/01/SOLUSDT.csv.gz"
}
MAX_ONE=90_000_000
MAX_TOTAL=120_000_000
MAX_UNPACKED=600_000_000
MAX_ROWS=100_000
MAX_WINDOW_MS=1_800_000
DATE="2026-09-01"
EXPECTED_L2={"exchange","symbol","timestamp","local_timestamp","is_snapshot","side","price","amount"}
EXPECTED_TRADES={"exchange","symbol","timestamp","local_timestamp","id","side","price","amount"}

class SourceBlocked(Exception):pass
class RedirectObserved(Exception):
    def __init__(self,url,status):
        super().__init__("HTTP_REDIRECT_OBSERVED")
        self.url=url;self.status=status

class DontFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise RedirectObserved(newurl,code)

OPENER=urllib.request.build_opener(DontFollow)

def official_hostname(host):
    return isinstance(host,str) and host.lower() in WHITELISTED_HF_HOSTS

def public_url(u,mode):
    p=urllib.parse.urlparse(u)
    if p.scheme!="https" or p.username is not None or p.password is not None or p.port not in (None,443):
        raise SourceBlocked("INVALID_HTTPS_URL")
    if mode=="hf":
        if p.hostname!="huggingface.co" or not p.path.startswith("/datasets/Goooddy/crypto-lob-stream/resolve/"+HF_IMMUTABLE+"/"):
            raise SourceBlocked("HF_UNPINNED_INITIAL_URL")
    elif mode=="tardis":
        if p.hostname!="datasets.tardis.dev" or u not in TARDIS_URLS.values():
            raise SourceBlocked("TARDIS_SOURCE_NOT_FROZEN")
    else:raise ValueError("BAD_MODE")
    return p

def head_once(url,mode):
    public_url(url,mode)
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"CryptoLab-008-free-L2-source-only/1.0"})
    try:
        with OPENER.open(req,timeout=19) as r:
            size=r.headers.get("Content-Length")
            return {"status":"HEAD_OK" if r.status==200 else "HTTP_NON200","http_status":r.status,
                    "compressed_content_length":int(size) if size is not None and size.isdecimal() else None,
                    "content_type":r.headers.get("Content-Type")}
    except RedirectObserved as exc:
        p=urllib.parse.urlparse(exc.url)
        return {"status":"REDIRECT_CAPTURED_NOT_FOLLOWED","http_status":exc.status,
                "location_scheme":p.scheme,"location_host":p.hostname,
                "location_port":p.port,"location_path_prefix":p.path[:90],
                "query_redacted":bool(p.query),
                "official_HF_documented_host":official_hostname(p.hostname)}
    except urllib.error.HTTPError as exc:
        return {"status":"HTTP_BLOCKED","http_status":exc.code,"error_type":"HTTPError"}
    except Exception as exc:
        return {"status":"SOURCE_BLOCKED","error_type":type(exc).__name__,
                "error":str(exc)[:160]}

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def persist(report):
    OUT.mkdir(exist_ok=True)
    p=OUT/"source_verdict.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    (OUT/"source_verdict.sha256").write_text(sha_file(p)+"  source_verdict.json\n")

def download_tardis_once(kind,meta,folder):
    url=TARDIS_URLS[kind]
    public_url(url,"tardis")
    limit=meta["compressed_content_length"]
    if not isinstance(limit,int) or limit<1 or limit>MAX_ONE:
        raise SourceBlocked("TARDIS_INVALID_OR_OVERSIZED_HEADER_"+kind)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-008-free-L2-source-only/1.0"})
    dest=Path(folder)/(kind+".csv.gz")
    count=0;digest=hashlib.sha256()
    try:
        with OPENER.open(req,timeout=85) as r,dest.open("wb") as f:
            if r.status!=200:raise SourceBlocked("TARDIS_DOWNLOAD_NOT_200")
            while True:
                block=r.read(1024*1024)
                if not block:break
                count+=len(block)
                if count>limit or count>MAX_ONE:raise SourceBlocked("TARDIS_GET_EXCEEDS_HEAD_CAP")
                digest.update(block);f.write(block)
    except RedirectObserved as ex:
        p=urllib.parse.urlparse(ex.url)
        raise SourceBlocked("TARDIS_UNVERIFIED_REDIRECT_HOST_"+str(p.hostname)) from ex
    if count!=limit:raise SourceBlocked("TARDIS_CONTENT_LENGTH_CHANGED")
    return dest,{"original_compressed_bytes":count,
                 "original_compressed_sha256":digest.hexdigest(),
                 "vendor_sha256_available":False,
                 "exact_url":url,
                 "license_and_redistribution_independently_verified":False}

def utc_parse_ms(value):
    s=str(value).strip()
    try:
        t=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        if t.tzinfo is None:raise ValueError("timezone missing")
    except Exception as exc:
        raise SourceBlocked("BAD_UTC_TIMESTAMP") from exc
    return round(t.timestamp()*1000)

def parse_numeric(value,allow_zero=False):
    try:x=float(value)
    except Exception as exc:raise SourceBlocked("BAD_DECIMAL_FIELD") from exc
    if not math.isfinite(x) or x<0 or (x==0 and not allow_zero):
        raise SourceBlocked("BAD_NONFINITE_OR_NEGATIVE_NUMERIC")
    return x

def file_rows(path,expected,limit_rows=MAX_ROWS):
    """Read a bounded first event window with explicit gzip CRC for whole file.
    Scan whole gzip for integrity but only keep/validate first requested sample.
    """
    with gzip.open(path,"rt",encoding="utf-8",newline="") as fh:
        reader=csv.DictReader(fh)
        header=reader.fieldnames or []
        if set(header)!=expected:
            raise SourceBlocked("UNKNOWN_NORMALIZED_CSV_SCHEMA_"+",".join(header[:18]))
        rowcount=0;sample=[];opened_bytes=0
        for row in reader:
            # gzip reads one decompressed CSV line, processed and released.
            opened_bytes+=sum(len(v) for v in row.values() if isinstance(v,str))+len(row)*2
            if opened_bytes>MAX_UNPACKED:raise SourceBlocked("TARDIS_UNPACKED_SOURCE_CAP")
            rowcount+=1
            if rowcount<=limit_rows:sample.append(row)
        return {"rows_in_original":rowcount,"approx_unpacked_csv_bytes":opened_bytes},sample

def verify_l2(rows,orig_row_count):
    """Tardis normalized L2: one price-level update per row, no native U/u!
    Receipt timestamp alignment and full snapshot are only feasibility proxies.
    """
    if not rows:raise SourceBlocked("L2_EMPTY_SAMPLE")
    bids={};asks={}
    started=False
    snap_bid=0;snap_ask=0
    last_local=None
    first_ts=None
    last_ts=None
    updates=0
    crossed=0
    censored=False
    for r in rows:
        if r["exchange"]!="binance" or r["symbol"]!="SOLUSDT":
            raise SourceBlocked("NOT_BINANCE_SPOT_SOLUSDT_L2")
        local=utc_parse_ms(r["local_timestamp"])
        source=utc_parse_ms(r["timestamp"])
        if dt.datetime.fromtimestamp(source/1000,dt.timezone.utc).strftime("%Y-%m-%d")!=DATE:
            raise SourceBlocked("WRONG_UTC_DAY")
        if local<source-1000:
            raise SourceBlocked("LOCAL_TIMESTAMP_BEFORE_SOURCE_TIME")
        if last_local is not None and local<last_local:
            raise SourceBlocked("RECEIPT_TIMESTAMP_REGRESSION")
        last_local=local
        if first_ts is None:first_ts=source
        if source-first_ts>MAX_WINDOW_MS:
            censored=True;break
        last_ts=source
        snapshot=str(r["is_snapshot"]).strip().lower() in ("true","1")
        if str(r["is_snapshot"]).strip().lower() not in ("true","false","1","0"):
            raise SourceBlocked("INVALID_SNAPSHOT_FLAG")
        side=r["side"].lower()
        if side not in ("bid","ask"):
            raise SourceBlocked("INVALID_BOOK_SIDE")
        px=parse_numeric(r["price"]);qty=parse_numeric(r["amount"],allow_zero=True)
        book=bids if side=="bid" else asks
        if snapshot:
            if started and updates>0:
                # A new snapshot is a new segment, not an uninterrupted one.
                censored=True;break
            if side=="bid":snap_bid+=1
            else:snap_ask+=1
            if qty<=0:raise SourceBlocked("SNAPSHOT_LEVEL_NOT_POSITIVE")
            if px in book:raise SourceBlocked("DUPLICATE_SNAPSHOT_PRICE")
            book[px]=qty
        else:
            if not started:
                if snap_bid<100 or snap_ask<100:
                    raise SourceBlocked("INITIAL_BOOK_NOT_COMPLETE")
                if max(bids)>=min(asks):raise SourceBlocked("INITIAL_CROSSED_BOOK")
                started=True
            updates+=1
            if qty==0:book.pop(px,None)
            else:book[px]=qty
            if not bids or not asks or max(bids)>=min(asks):
                crossed+=1
                raise SourceBlocked("REPLAY_CROSSED_OR_EMPTY_BOOK")
            if len(book)>1000:
                sorted_px=sorted(book,reverse=(side=="bid"))
                for p in sorted_px[1000:]:book.pop(p,None)
    if not started or updates<500:
        raise SourceBlocked("INSUFFICIENT_VALID_L2_SEGMENT_UPDATES_"+str(updates))
    return {"status":"NORMALIZED_L2_WINDOW_REPLAY_NO_NATIVE_UU",
            "native_binance_U_u_ids_seen":False,"native_sequence_gap_proven_absent":False,
            "initial_snapshot_bid_levels":snap_bid,
            "initial_snapshot_ask_levels":snap_ask,
            "replayed_price_level_diffs":updates,
            "first_source_timestamp_ms":first_ts,"last_source_timestamp_ms":last_ts,
            "snapshot_reset_or_30min_censored":censored,
            "rows_in_original_file":orig_row_count,
            "rows_sampled":len(rows),
            "full_24h_continuity_verified":False,
            "economic_strategy_tested":False}

def verify_trades(rows,window):
    count=0;first=None;last=None
    previous_local=None
    for r in rows:
        if r["exchange"]!="binance" or r["symbol"]!="SOLUSDT":
            raise SourceBlocked("TRADES_WRONG_SPOT_SYMBOL")
        ts=utc_parse_ms(r["timestamp"]);local=utc_parse_ms(r["local_timestamp"])
        if previous_local is not None and local<previous_local:
            raise SourceBlocked("TRADE_RECEPTION_REGRESSION")
        previous_local=local
        if dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc).strftime("%Y-%m-%d")!=DATE:
            raise SourceBlocked("TRADES_WRONG_UTC_DAY")
        parse_numeric(r["price"]);parse_numeric(r["amount"])
        if window["first_source_timestamp_ms"]<=ts<=window["last_source_timestamp_ms"]:
            count+=1
            if first is None:first=ts
            last=ts
    if count==0:raise SourceBlocked("NO_MATCHING_NORMALIZED_TRADES_IN_WINDOW")
    return {"matching_trade_rows":count,"first_trade_ms":first,"last_trade_ms":last,
            "sample_ended_before_original_file":True}

def main():
    OUT.mkdir(exist_ok=True)
    report={"study":"BINANCE-DIAMANTE-008",
        "frozen_scope":"HF redirect HEAD only + Tardis Binance Spot SOLUSDT 2026-09-01",
        "no_auth":True,"no_trades":True,"no_payments":True,"no_merge":True,
        "market_return_or_PnL_tested":False,
        "tardis_documented_public_sample_only":True,
        "original_source_HF_007E_immutable":True,
        "status":"SOURCE_BLOCKED"}
    report["huggingface_redirect"]=head_once(HF_URL,"hf")
    persist(report)
    report["tardis_heads"]={k:head_once(url,"tardis") for k,url in TARDIS_URLS.items()}
    persist(report)
    try:
        for k,v in report["tardis_heads"].items():
            if v["status"]!="HEAD_OK":
                raise SourceBlocked("TARDIS_FREE_FIRST_DAY_HEAD_BLOCKED_"+k+"_"+v["status"])
            size=v["compressed_content_length"]
            if not isinstance(size,int) or size<=0:
                raise SourceBlocked("TARDIS_HEAD_UNKNOWN_COMPRESSED_SIZE_"+k)
            if size>MAX_ONE:
                raise SourceBlocked("TARDIS_HEAD_SINGLE_FILE_SIZE_BLOCK_"+k+"_"+str(size))
        total=sum(x["compressed_content_length"] for x in report["tardis_heads"].values())
        report["total_head_bytes"]=total
        if total>MAX_TOTAL:raise SourceBlocked("TARDIS_HEAD_TOTAL_SIZE_BLOCK_"+str(total))
        with tempfile.TemporaryDirectory(prefix="binance008-tardis-spot-sample-") as tmp:
            paths={}
            for kind in ("l2","trades"):
                p,receipt=download_tardis_once(kind,report["tardis_heads"][kind],tmp)
                report.setdefault("original_source_receipts",{})[kind]=receipt
                paths[kind]=p
                persist(report)
            rows,book_sample=file_rows(paths["l2"],EXPECTED_L2)
            report["l2_csv_source"]=rows
            replay=verify_l2(book_sample,rows["rows_in_original"])
            report["l2_bounded_replay"]=replay
            persist(report)
            trades,trade_sample=file_rows(paths["trades"],EXPECTED_TRADES)
            report["trades_csv_source"]=trades
            report["trades_overlap"]=verify_trades(trade_sample,replay)
        report["status"]="NORMALIZED_L2_SAMPLE_PASS_NO_NATIVE_UU_NO_ECONOMIC_CLAIM"
        report["limitations"]=[
            "Normalized Tardis L2 stream may omit native Binance U/u sequence IDs",
            "No continuous 90-day history or replay proven",
            "First-day sample only; never strategy backtested or executed",
            "Original 2026 August Goooddy collection bug not repaired; September independent provider"
        ]
        persist(report)
        print(json.dumps({"study":report["study"],"status":report["status"],
            "huggingface_redirect":report["huggingface_redirect"],
            "tardis_heads":report["tardis_heads"],
            "l2_replay":replay,"trades_overlap":report["trades_overlap"],
            "actual_orders":0,"strategy_PnL":None},indent=2,sort_keys=True))
        return 0
    except Exception as exc:
        report["status"]="SOURCE_BLOCKED"
        report["first_blocker_type"]=type(exc).__name__
        report["first_blocker"]=str(exc)[:230]
        persist(report)
        print(json.dumps({"study":report["study"],"status":"SOURCE_BLOCKED",
            "huggingface_redirect":report["huggingface_redirect"],
            "tardis_heads":report["tardis_heads"],"first_blocker":report["first_blocker"],
            "no_actual_orders":True,"economic_PnL":None},indent=2,sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
