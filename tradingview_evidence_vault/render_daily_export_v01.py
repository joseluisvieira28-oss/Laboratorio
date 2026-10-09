#!/usr/bin/env python3
"""Strict, outcome-blind Render TVFP -> immutable GitHub Evidence Vault staging.

Never reads private exchange accounts; this utility needs a read-only Render API
key solely for the /v1/logs endpoint. It does not deploy, place orders, resolve
returns or overwrite any existing daily archive.

Requires RENDER_API_KEY supplied via GitHub Actions Secret, never in the repo.
This script is deliberately not a self-scheduling background service.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib import error, parse, request

sys.path.insert(0,str(Path(__file__).resolve().parent))
from vault import BAR_MS, LAB_ID, SENSOR_VERSION, SYMBOL, TIMEFRAME, VaultError, validate_receipt, deduplicate, continuity, canonical_json

API_BASE="https://api.render.com/v1/logs"
OWNER_ID="tea-daffqvgu01pc73a9sad0"
SERVICE_ID="srv-daqgvt0u01pc7384vsa0"
MAX_PAGES=12
MAX_ROWS=1500
DAY_BARS=288
QUERY_LIMIT=100

class ArchiveBlocked(RuntimeError):
    pass

def parse_day(value: str) -> date:
    try:
        day=date.fromisoformat(value)
    except ValueError as exc:
        raise ArchiveBlocked("DAY_MUST_BE_YYYY_MM_DD") from exc
    if day.isoformat()!=value:
        raise ArchiveBlocked("DAY_FORMAT_NONCANONICAL")
    if day>=datetime.now(timezone.utc).date():
        raise ArchiveBlocked("ONLY_PREVIOUS_COMPLETED_UTC_DAYS")
    return day

def _request_page(token: str, params: dict[str,str], *, retry: int=3) -> dict:
    if not token or len(token)<15:
        raise ArchiveBlocked("MISSING_OR_INVALID_RENDER_API_KEY")
    query=parse.urlencode(params)
    req=request.Request(API_BASE+"?"+query,headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/json",
        "User-Agent":"CryptoLab-TVFP-VaultReadOnly/0.1"
    },method="GET")
    for attempt in range(retry):
        try:
            with request.urlopen(req,timeout=45) as response:
                if response.status!=200:
                    raise ArchiveBlocked("RENDER_LOG_API_NON_200")
                raw=response.read(1_500_001)
                if len(raw)>1_500_000: raise ArchiveBlocked("LOG_API_RESPONSE_OVERSIZE")
                obj=json.loads(raw)
                if not isinstance(obj,dict):
                    raise ArchiveBlocked("RENDER_LOG_API_INVALID_OBJECT")
                return obj
        except error.HTTPError as exc:
            # NEVER print the response body; it may carry request details.
            if exc.code in (429,500,502,503,504) and attempt<retry-1:
                time.sleep(2**attempt)
                continue
            raise ArchiveBlocked("RENDER_LOG_API_HTTP_"+str(exc.code)) from None
        except (error.URLError,TimeoutError) as exc:
            if attempt<retry-1:
                time.sleep(2**attempt)
                continue
            raise ArchiveBlocked("RENDER_LOG_API_TRANSPORT_BLOCKED") from None
        except json.JSONDecodeError:
            raise ArchiveBlocked("RENDER_LOG_API_BAD_JSON") from None
    raise ArchiveBlocked("RENDER_LOG_API_RETRIES_EXHAUSTED")

def validate_page(raw: object) -> tuple[list[dict],bool,str|None,str|None]:
    if not isinstance(raw,dict):
        raise ArchiveBlocked("API_PAGE_NOT_OBJECT")
    logs=raw.get("logs")
    if not isinstance(logs,list) or not isinstance(raw.get("hasMore"),bool):
        raise ArchiveBlocked("API_PAGE_SCHEMA_INVALID")
    if len(logs)>QUERY_LIMIT:
        raise ArchiveBlocked("API_PAGE_EXCEEDS_LIMIT")
    for log in logs:
        if not isinstance(log,dict) or not isinstance(log.get("message"),str):
            raise ArchiveBlocked("API_LOG_MESSAGE_INVALID")
    return logs,raw["hasMore"],raw.get("nextStartTime"),raw.get("nextEndTime")

def extract_for_day(day: date, pages: list[dict]):
    receipts=[]
    for log in pages:
        msg=log["message"]
        if "TVFP_RECEIPT " not in msg:
            continue
        try:
            rec=json.loads(msg.split("TVFP_RECEIPT ",1)[1].strip())
            validate_receipt(rec)
        except (json.JSONDecodeError,VaultError,TypeError,KeyError,ValueError) as exc:
            raise ArchiveBlocked("RENDER_RECEIPT_INVALID:"+type(exc).__name__) from None
        bc=int(rec["payload"]["bar_close_ms"])
        bc_day=datetime.fromtimestamp(bc/1000,timezone.utc).date()
        if bc_day==day:
            receipts.append(rec)
    try:
        unique,stats=deduplicate(receipts)
    except VaultError:
        raise ArchiveBlocked("CONFLICTING_SAME_KEY_RENDER_RECEIPTS") from None
    if len(unique)!=DAY_BARS:
        raise ArchiveBlocked("UTC_DAY_RECEIPT_COUNT_"+str(len(unique))+"_EXPECTED_288")
    cont=continuity(unique)
    day_start=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    if (cont["missing_slots"] or cont["first_bar_close_ms"]!=day_start or
       cont["last_bar_close_ms"]!=day_start+(DAY_BARS-1)*BAR_MS or
       cont["expected_slots"]!=DAY_BARS):
        raise ArchiveBlocked("INCOMPLETE_OR_GAPPED_UTC_DAY")
    return unique,stats

def fetch_render_day(day: date,token: str,fetch_page=_request_page):
    start=datetime(day.year,day.month,day.day,tzinfo=timezone.utc)
    end=start+timedelta(days=1,hours=1)  # catch last-close delivery/retry
    begin=start.isoformat().replace("+00:00","Z")
    until=end.isoformat().replace("+00:00","Z")
    records=[]
    cursors=set()
    pages=0
    while True:
        if pages>=MAX_PAGES:
            raise ArchiveBlocked("RENDER_LOG_PAGINATION_LIMIT")
        params={"ownerId":OWNER_ID,"resource":SERVICE_ID,"text":"TVFP_RECEIPT",
                "type":"app","direction":"forward","limit":str(QUERY_LIMIT),
                "startTime":begin,"endTime":until}
        raw=fetch_page(token,params)
        logs,more,next_start,next_end=validate_page(raw)
        records.extend(logs)
        pages+=1
        if len(records)>MAX_ROWS:
            raise ArchiveBlocked("LOG_RESULT_OVERFLOW")
        if not more:break
        if not isinstance(next_start,str) or not isinstance(next_end,str) or not next_start:
            raise ArchiveBlocked("RENDER_PAGINATION_CURSOR_MISSING")
        key=(next_start,next_end)
        if key in cursors or next_start<=begin:
            raise ArchiveBlocked("RENDER_PAGINATION_CURSOR_STALLED")
        cursors.add(key)
        begin,until=key
    return extract_for_day(day,records),{"pages":pages,"render_log_lines":len(records)}

def write_staging(day: date,records: list[dict],out_root:Path):
    staging=out_root/"staging"/(day.isoformat()+".raw.jsonl")
    archived=out_root/"archive"/day.isoformat()/(day.isoformat()+".manifest.json")
    corpus=out_root/"archive"/day.isoformat()/(day.isoformat()+".jsonl")
    if archived.exists() or corpus.exists() or staging.exists():
        raise ArchiveBlocked("IMMUTABLE_DAY_ALREADY_STAGED_OR_ARCHIVED")
    staging.parent.mkdir(parents=True,exist_ok=True)
    lines=[canonical_json(r).decode("utf-8") for r in records]
    body=("\n".join(lines)+"\n").encode("utf-8")
    # Exclusive file creation refuses overwrites even during races.
    with staging.open("xb") as fh:
        fh.write(body)
    return staging,hashlib.sha256(body).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day",required=True,help="Fully completed UTC YYYY-MM-DD")
    p.add_argument("--vault-root",default=str(Path(__file__).resolve().parent))
    p.add_argument("--receipt-out",required=True)
    args=p.parse_args()
    report={"schema":"tvfp.render_archive_source_only.v0.1","utc_day":args.day,
            "trading_authority":"NONE","economic_outcomes_unlocked":False}
    try:
        day=parse_day(args.day)
        token=os.environ.get("RENDER_API_KEY","")
        if not token:
            raise ArchiveBlocked("RENDER_API_KEY_SECRET_MISSING")
        (rec,stats),fetch_stats=fetch_render_day(day,token)
        path,digest=write_staging(day,rec,Path(args.vault_root))
        report.update({"state":"VALIDATED_288_STAGED","unique_receipts":len(rec),
           "exact_duplicates_removed":stats["exact_duplicates_removed"],
           "render_api_pages":fetch_stats["pages"],
           "staging_path":str(path),"staging_sha256":digest})
        exit_status=0
    except (ArchiveBlocked,OSError) as exc:
        report.update({"state":"SOURCE_ARCHIVAL_BLOCKED","reason":str(exc)})
        exit_status=2
    Path(args.receipt_out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.receipt_out).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("staging_path",)},sort_keys=True))
    raise SystemExit(exit_status)

if __name__=="__main__":
    main()
