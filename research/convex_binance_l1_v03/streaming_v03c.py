"""V03C — stream only V03B resource-blocked Binance L1 publisher ZIPs to disk.

No new trade selection, economic changes, alternate region, credentials, orders or 2026 data.
Original V03B accepted receipts preserved verbatim; fail closed for any other blocked reason.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,statistics,tempfile,urllib.request,urllib.error,zipfile
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path

from research.convex_binance_l1_v03.bookticker_gate import (
    REQUIRED,day_ms,source_url,dec,verdict_for_entry
)
from research.convex_binance_l1_v03.full_population_gate import (
    EXPECTED,FRESH,source_entries
)

MAX_ZIP_BYTES=320_000_000
MAX_UNZIPPED=2_500_000_000
MAX_EVENTS=35_000_000
CHUNK=4_194_304
ORIGINAL_RUN=39026521571
ALLOWED_REASONS={
    "ValueError:PUBLISHER_ARCHIVE_TOO_BIG",
    "ValueError:UNZIPPED_SIZE_CAP",
}

def stream_official_zip_to_temp(symbol,day,temp_path):
    url=source_url(symbol,day)
    request=urllib.request.Request(url,headers={
        "User-Agent":"CryptoLab-Publisher-Checksum-Source-Custody-V03C/1.0"})
    try:
        with urllib.request.urlopen(request,timeout=40) as h:
            if h.status!=200:raise ValueError("PUBLISHER_HTTP_"+str(h.status))
            used=0
            digest=hashlib.sha256()
            with Path(temp_path).open("wb") as f:
                while True:
                    chunk=h.read(CHUNK)
                    if not chunk:break
                    used+=len(chunk)
                    if used>MAX_ZIP_BYTES:raise ValueError("V03C_COMPRESSED_SIZE_CAP")
                    digest.update(chunk)
                    f.write(chunk)
        request2=urllib.request.Request(url+".CHECKSUM",headers={
            "User-Agent":"CryptoLab-Publisher-Checksum-Source-Custody-V03C/1.0"})
        with urllib.request.urlopen(request2,timeout=40) as h:
            if h.status!=200:raise ValueError("CHECKSUM_HTTP_"+str(h.status))
            check=h.read(301)
        if len(check)>300:raise ValueError("CHECKSUM_TOO_BIG")
        txt=check.decode("utf-8-sig").strip()
        expected=txt.split()[0].lower() if txt else ""
        if not re.fullmatch("[a-f0-9]{64}",expected):
            raise ValueError("CHECKSUM_SCHEMA_NOT_64_HEX")
        if expected!=digest.hexdigest():
            raise ValueError("OFFICIAL_PUBLISHER_SHA256_MISMATCH")
        return {"zip_bytes":used,"publisher_zip_sha256":digest.hexdigest()}
    except urllib.error.HTTPError as exc:
        raise ValueError("OFFICIAL_HTTP_"+str(exc.code)) from exc

def causal_quotes_from_zip_path(filename,day,entry_times):
    times=sorted(set(entry_times))
    if not times or any(type(x) is not int or not day_ms(day)<=x<day_ms(day)+86400000 for x in times):
        raise ValueError("FROZEN_ENTRY_TIME_INVALID")
    day_start=day_ms(day)
    results={}
    count=0
    with zipfile.ZipFile(filename) as archive:
        files=[x for x in archive.infolist() if not x.is_dir()]
        if len(files)!=1 or not files[0].filename.lower().endswith(".csv"):
            raise ValueError("CSV_ONLY_ONE_MEMBER_REQUIRED")
        if files[0].file_size>MAX_UNZIPPED:raise ValueError("V03C_UNCOMPRESSED_SIZE_CAP")
        with archive.open(files[0],"r") as inp:
            reader=csv.DictReader(io.TextIOWrapper(inp,encoding="utf-8-sig",newline=""))
            if not set(REQUIRED).issubset(set(reader.fieldnames or [])):
                raise ValueError("BOOKTICKER_SCHEMA_INVALID")
            idx=0;previous=-1;latest=None
            for row in reader:
                count+=1
                if count>MAX_EVENTS:raise ValueError("V03C_EVENT_COUNT_CAP")
                ts=int(row["event_time"])
                if not day_start<=ts<day_start+86400000 or ts<previous:
                    raise ValueError("BOOK_TIME_NONCAUSAL_OR_OUT_OF_DATE")
                previous=ts
                if idx>=len(times):break
                while idx<len(times) and ts>times[idx]:
                    results[times[idx]]=latest
                    idx+=1
                if idx>=len(times):break
                bid=dec(row["best_bid_price"],"BID")
                ask=dec(row["best_ask_price"],"ASK")
                bq=dec(row["best_bid_qty"],"BID_QTY")
                aq=dec(row["best_ask_qty"],"ASK_QTY")
                if bid>=ask:raise ValueError("CROSSED_BOOK")
                latest={"event_time":ts,"transaction_time":int(row["transaction_time"]),
                        "update_id":row["update_id"],"bid":bid,"ask":ask,
                        "bid_qty":bq,"ask_qty":aq}
            for t in times[idx:]:results[t]=latest
    return results,count

def root_cause_group(doc,symbol):
    if doc.get("symbol")!=symbol or doc.get("count")!=EXPECTED[symbol] or doc.get("trading_authority")!="NONE":
        raise ValueError("V03B_RECEIPT_IDENTITY_INVALID")
    source_days={}
    for f in doc["source_files"]:
        if f["day"] in source_days:raise ValueError("DUPLICATE_ORIGINAL_DAY")
        source_days[f["day"]]=f
    target={}
    for day,item in source_days.items():
        if item["status"]=="SOURCE_BLOCKED":
            if item.get("reason") not in ALLOWED_REASONS:
                raise ValueError("OUT_OF_SCOPE_SOURCE_REMediation:"+str(item.get("reason")))
            target[day]=item
    if symbol=="SOLUSDT" and (len(target)!=18):
        raise ValueError("EXACT_SOL_DATE_BLOCKERS_NOT_18")
    if symbol=="BNBUSDT" and (len(target)!=3):
        raise ValueError("EXACT_BNB_DATE_BLOCKERS_NOT_3")
    return target

def run(original_root, v03b_root,symbol):
    if symbol not in EXPECTED:raise ValueError("UNREGISTERED_SYMBOL")
    entries, prior=source_entries(original_root,symbol)
    paths=list((v03b_root/symbol).rglob("ALL_ORIGINAL_ELIGIBLE_L1_RECEIPTS.json"))
    if len(paths)!=1:raise ValueError("V03B_IMMUTABLE_ARTIFACT_NOT_UNIQUE")
    v03b_path=paths[0]
    v03b=json.loads(v03b_path.read_text(encoding="utf-8"))
    if (v03b["original_source_sha256"]!=prior["source_sha256"]
        or v03b["original_ledger_sha256"]!=prior["original_ledger_sha256"]):
        raise ValueError("ORIGINAL_PROVENANCE_SHA_MISMATCH")
    blocked=root_cause_group(v03b,symbol)
    by_day=defaultdict(list)
    for e in entries:by_day[e["day"]].append(e)
    if not set(blocked).issubset(set(by_day)):
        raise ValueError("BLOCKED_DATE_WITHOUT_FROZEN_TRADE")
    old_checks={x["entry_utc"]:x for x in v03b["entry_checks"]}
    if len(old_checks)!=EXPECTED[symbol]:raise ValueError("ORIGINAL_ENTRY_RECEIPT_COUNT_BAD")
    repair_files=[]; patched=dict(old_checks)
    for day,item in sorted(blocked.items()):
        rows=by_day[day]
        for e in rows:
            if old_checks[e["entry_utc"]]["status"]!="SOURCE_BLOCKED":
                raise ValueError("ATTEMPT_TO_REPLACE_VERIFIED_ORIGINAL")
        try:
            with tempfile.TemporaryDirectory(prefix="convex-v03c-") as d:
                f=Path(d)/"single_official_daily_source.zip"
                sha=stream_official_zip_to_temp(symbol,day,f)
                quotes,count=causal_quotes_from_zip_path(f,day,[e["entry_ms"] for e in rows])
            repair_files.append({"day":day,"status":"V03C_SHA256_VERIFIED",
                                 "events_read":count,**sha,"prior_block_reason":item["reason"]})
            for e in rows:
                patched[e["entry_utc"]]=verdict_for_entry(e,quotes[e["entry_ms"]])
        except Exception as exc:
            reason=type(exc).__name__+":"+str(exc)[:140]
            repair_files.append({"day":day,"status":"SOURCE_STILL_BLOCKED",
                                 "reason":reason,"prior_block_reason":item["reason"]})
            for e in rows:
                patched[e["entry_utc"]]={"symbol":symbol,"tf":e["tf"],
                    "entry_utc":e["entry_utc"],"source_day":day,
                    "status":"SOURCE_STILL_BLOCKED","reason":reason,
                    "does_not_prove_fill":True}
        print("V03C_REPAIRED_DATE",json.dumps(repair_files[-1],sort_keys=True),flush=True)
    old_dates={x["day"] for x in v03b["source_files"] if x["status"]!="SOURCE_BLOCKED"}
    if any(e["day"] in old_dates and patched[e["entry_utc"]]!=old_checks[e["entry_utc"]] for e in entries):
        raise ValueError("ACCEPTED_V03B_EVIDENCE_WAS_MUTATED")
    final=[patched[e["entry_utc"]] for e in entries]
    by_status=Counter(x["status"] for x in final)
    fresh=[x for x in final if x["status"] in FRESH]
    sufficient=[x for x in fresh if x["status"]=="BOOK_QUOTE_CAUSAL_CANDIDATE"]
    coverage=len(fresh)/len(final)
    capacity=len(sufficient)/len(fresh) if fresh else 0.
    changes=sum(old_checks[e["entry_utc"]]!=patched[e["entry_utc"]] for e in entries)
    vals=[float(Decimal(x["ask_vs_modeled_entry_bps"])) for x in fresh]
    return {
        "status":"L1_HISTORICAL_SOURCE_GATES_PASS" if coverage>=.95 and capacity>=.9
            else "L1_HISTORICAL_SOURCE_GATES_INSUFFICIENT",
        "symbol":symbol,"source_original_run":38432883246,
        "source_v03b_run":ORIGINAL_RUN,"source_v03b_receipt_sha256":hashlib.sha256(v03b_path.read_bytes()).hexdigest(),
        "original_ledger_sha256":prior["original_ledger_sha256"],
        "full_population":len(final),"original_blocked_dates":len(blocked),
        "repaired_or_still_blocked_days":repair_files,
        "original_status_counts":v03b["counts"],
        "new_status_counts":dict(sorted(by_status.items())),
        "updated_entry_receipts":changes,
        "fresh_quote_fraction":coverage,"fresh_top_ask_qty_fraction":capacity,
        "frozen_gates":{"fresh_fraction":.95,"ask_capacity_fraction":.90},
        "historical_ask_minus_modeled_entry_bps":{
            "n":len(vals),"median":statistics.median(vals) if vals else None,
            "min":min(vals) if vals else None,
            "max":max(vals) if vals else None},
        "all_entry_checks":final,
        "cross_venue_execution_proven":False,
        "net_OOS_edge_proven":False,
        "broker_native_stop_proven":False,
        "protected_2026_opened":False,
        "trading_authority":"NONE",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-dir",type=Path,required=True)
    p.add_argument("--v03b-dir",type=Path,required=True)
    p.add_argument("--symbol",choices=tuple(EXPECTED),required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    d=run(a.original_dir,a.v03b_dir,a.symbol)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"V03C_STREAMING_SOURCE_CAP_REMEDIATION.json").write_text(
        json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("V03C_FINAL_VERDICT",json.dumps({k:v for k,v in d.items() if k in (
        "symbol","status","full_population","original_blocked_dates",
        "original_status_counts","new_status_counts","fresh_quote_fraction",
        "fresh_top_ask_qty_fraction","updated_entry_receipts",
        "historical_ask_minus_modeled_entry_bps","trading_authority"
    )},sort_keys=True))
if __name__=="__main__":main()
