"""CONVEX V03 — immutable historical Binance USDM bookTicker L1 source witness.

ALL observations retrospective, source-only; NO venue fill, broker operation, OOS or trading.
Pure stdlib; downloads only official publisher SHA-checked historical daily files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

SYMBOL_TF = {"SOLUSDT": "1h", "BNBUSDT": "4h"}
SOURCE_RUN = 38432883246
LOWER_MS = 1684195200000  # 2023-05-16T00:00:00Z
UPPER_MS = 1711843200000  # 2024-03-31T00:00:00Z
MAX_ZIP_BYTES = 85_000_000
MAX_UNZIPPED = 500_000_000
MAX_EVENTS = 8_000_000
BASE = "https://data.binance.vision/data/futures/um/daily/bookTicker"
REQUIRED = (
    "update_id", "best_bid_price", "best_bid_qty", "best_ask_price",
    "best_ask_qty", "transaction_time", "event_time",
)

def dec(value, label):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("INVALID_DECIMAL:"+label) from exc
    if not d.is_finite() or d <= 0:
        raise ValueError("INVALID_NONPOSITIVE:"+label)
    return d

def date_of(ms):
    return dt.datetime.fromtimestamp(ms/1000, dt.timezone.utc).strftime("%Y-%m-%d")

def day_ms(day):
    return int(dt.datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()*1000)

def select_original_earliest_two(root, symbol):
    if symbol not in SYMBOL_TF:
        raise ValueError("UNREGISTERED_SYMBOL")
    candidates = []
    for f in root.rglob("RESULT.json"):
        try: doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc: raise ValueError("INVALID_SOURCE_RESULT_JSON") from exc
        if doc.get("symbol") == symbol:
            candidates.append((f, doc))
    if len(candidates) != 1:
        raise ValueError("ORIGINAL_SOURCE_RESULT_NOT_UNIQUE:"+symbol+":"+str(len(candidates)))
    f, doc = candidates[0]
    if (doc.get("status") != "COMMON_2023_25_8ALT_COMPLETED_NO_OOS_CREDIT"
        or doc.get("independent_OOS") is not False
        or doc.get("actual_venue_fills") is not False):
        raise ValueError("INVALID_CANONICAL_RESULT_STATUS")
    if doc.get("source_counts") != {"5m":333216,"1h":27768,"funding":3288}:
        raise ValueError("SOURCE_COUNTS_NOT_CANONICAL")
    if len(doc.get("source_manifest",[])) != 112:
        raise ValueError("PUBLISHER_MANIFEST_INCOMPLETE")
    tf = SYMBOL_TF[symbol]
    model = doc.get("model",{}).get(tf+"_BASE")
    if not isinstance(model,dict): raise ValueError("BASE_MODEL_NOT_FOUND")
    trades_file = f.parent/(tf+"_BASE_TRADES.csv")
    if not trades_file.is_file(): raise ValueError("CANONICAL_CSV_NOT_FOUND")
    with trades_file.open(encoding="utf-8",newline="") as handle:
        rows=list(csv.DictReader(handle))
    if len(rows)!=model.get("closed_trades"):
        raise ValueError("ORIGINAL_TRADE_COUNT_MISMATCH")
    entries=[]
    previous = -1
    for row in rows:
        t=int(row["open_t"])
        if t<previous: raise ValueError("ORIGINAL_LEDGER_NONCHRONOLOGICAL")
        previous=t
        if LOWER_MS<=t<UPPER_MS:
            entries.append({"symbol":symbol,"tf":tf,"entry_utc":date_of(t)+"T"+dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).strftime("%H:%M:%S")+"Z",
                           "entry_ms":t,"day":date_of(t),
                           "modeled_entry":str(dec(row["entry_price"],"MODELED_ENTRY")),
                           "modeled_qty":str(dec(row["qty"],"MODELED_QTY"))})
    return {"symbol":symbol,"tf":tf,"source_sha256":hashlib.sha256(f.read_bytes()).hexdigest(),
            "original_ledger_sha256":hashlib.sha256(trades_file.read_bytes()).hexdigest(),
            "original_closed":len(rows),"eligible_count":len(entries),
            "selected":entries[:2]}

def source_url(symbol,day):
    if symbol not in SYMBOL_TF: raise ValueError("UNREGISTERED_SYMBOL")
    if not (LOWER_MS<=day_ms(day)<UPPER_MS):
        raise ValueError("OUTSIDE_FROZEN_BOOKTICKER_PUBLISHING_WINDOW")
    return f"{BASE}/{symbol}/{symbol}-bookTicker-{day}.zip"

def publisher_get(url,max_bytes):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Research-Official-Publisher-Archive/0.1"})
    with urllib.request.urlopen(req,timeout=35) as h:
        if h.status!=200:
            raise ValueError("PUBLISHER_HTTP_"+str(h.status))
        result=h.read(max_bytes+1)
    if len(result)>max_bytes: raise ValueError("PUBLISHER_ARCHIVE_TOO_BIG")
    return result

def fetch_archive(symbol,day):
    url=source_url(symbol,day)
    try:
        data=publisher_get(url,MAX_ZIP_BYTES)
        chk=publisher_get(url+".CHECKSUM",300)
    except urllib.error.HTTPError as exc:
        raise ValueError("OFFICIAL_SOURCE_HTTP_"+str(exc.code)) from exc
    text=chk.decode("utf-8-sig",errors="strict").strip()
    digest=text.split()[0].lower() if text else ""
    if not re.fullmatch("[a-f0-9]{64}",digest):
        raise ValueError("PUBLISHER_CHECKSUM_NOT_64_HEX")
    actual=hashlib.sha256(data).hexdigest()
    if digest!=actual:raise ValueError("PUBLISHER_SHA256_MISMATCH")
    return data,actual

def last_causal_quotes(zbytes,day, entry_times):
    if not entry_times: raise ValueError("NO_REQUESTED_ENTRIES")
    times=sorted(set(entry_times))
    if any(not isinstance(t,int) or not day_ms(day)<=t<day_ms(day)+86400000 for t in times):
        raise ValueError("ENTRY_WRONG_DAY")
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        members=[p for p in z.infolist() if not p.is_dir()]
        if len(members)!=1 or not members[0].filename.lower().endswith(".csv"):
            raise ValueError("CSV_MEMBER_COUNT_OR_TYPE")
        if members[0].file_size>MAX_UNZIPPED:
            raise ValueError("UNZIPPED_SIZE_CAP")
        results={}
        previous=-1
        seen=0
        latest=None
        idx=0
        with z.open(members[0]) as raw:
            txt=io.TextIOWrapper(raw,encoding="utf-8-sig",newline="")
            reader=csv.DictReader(txt)
            if not set(REQUIRED).issubset(set(reader.fieldnames or [])):
                raise ValueError("CSV_SCHEMA_"+",".join(reader.fieldnames or []))
            for row in reader:
                seen+=1
                if seen>MAX_EVENTS: raise ValueError("EXCESS_EVENT_COUNT")
                event=int(row["event_time"])
                if not day_ms(day)<=event<day_ms(day)+86400000 or event<previous:
                    raise ValueError("BAD_BOOKTICKER_EVENT_SEQUENCE_OR_DATE")
                previous=event
                if idx>=len(times): break
                while idx<len(times) and event>times[idx]:
                    results[times[idx]]=latest
                    idx+=1
                if idx>=len(times): break
                bid=dec(row["best_bid_price"],"BID")
                ask=dec(row["best_ask_price"],"ASK")
                bid_qty=dec(row["best_bid_qty"],"BID_QTY")
                ask_qty=dec(row["best_ask_qty"],"ASK_QTY")
                if bid>=ask:raise ValueError("CROSSED_BOOK")
                latest={
                    "event_time":event,"transaction_time":int(row["transaction_time"]),
                    "update_id":row["update_id"],"bid":bid,"ask":ask,
                    "bid_qty":bid_qty,"ask_qty":ask_qty}
            for t in times[idx:]:
                results[t]=latest
    return results,seen

def verdict_for_entry(entry, quote):
    result={"symbol":entry["symbol"],"tf":entry["tf"],"entry_utc":entry["entry_utc"],
            "source_day":entry["day"],"status":"SOURCE_NO_PRIOR_QUOTE",
            "quote_age_ms":None,"ask_vs_modeled_entry_bps":None,
            "ask_qty_meets_original_modeled_qty":None,
            "does_not_prove_fill":True}
    if quote is None:return result
    age=entry["entry_ms"]-quote["event_time"]
    if age<0:raise ValueError("FUTURE_QUOTE_LOOKAHEAD")
    result["quote_age_ms"]=age
    if age>10000:
        result["status"]="SOURCE_STALE_OVER_10S"
        return result
    if age>2000:
        result["status"]="QUOTE_2S_TO_10S_SENSITIVITY_ONLY"
        return result
    entry_fill=dec(entry["modeled_entry"],"ENTRY_FILL")
    qty=dec(entry["modeled_qty"],"QTY")
    result["status"]="BOOK_QUOTE_CAUSAL_CANDIDATE" if quote["ask_qty"]>=qty else "TOP_OF_BOOK_SIZE_INSUFFICIENT"
    result["ask_vs_modeled_entry_bps"]=str((quote["ask"]/entry_fill-1)*Decimal("10000"))
    result["ask_qty_meets_original_modeled_qty"]=quote["ask_qty"]>=qty
    result["best_bid"]=str(quote["bid"])
    result["best_ask"]=str(quote["ask"])
    result["book_ask_qty"]=str(quote["ask_qty"])
    result["modeled_trade_qty"]=str(qty)
    return result

def run(root):
    selections=[select_original_earliest_two(root,s) for s in SYMBOL_TF]
    if any(len(s["selected"])<2 for s in selections):
        return {"status":"SAMPLE_INSUFFICIENT","selections":selections,"trading_authority":"NONE"}
    by_source=defaultdict(list)
    for s in selections:
        for row in s["selected"]:
            by_source[(row["symbol"],row["day"])].append(row)
    if len(by_source)>4: raise ValueError("TOO_MANY_FROZEN_SOURCE_DATES")
    receipts=[]; evaluations=[]
    for (symbol,day),rows in sorted(by_source.items()):
        try:
            data,source_hash=fetch_archive(symbol,day)
            quotes,count=last_causal_quotes(data,day,[r["entry_ms"] for r in rows])
            receipts.append({"symbol":symbol,"day":day,"status":"PUBLISHER_ZIP_SHA_PASS",
                             "archive_zip_sha256":source_hash,"events_scanned":count})
            evaluations.extend(verdict_for_entry(row,quotes[row["entry_ms"]]) for row in rows)
        except Exception as exc:
            reason=type(exc).__name__+":"+str(exc)[:130]
            receipts.append({"symbol":symbol,"day":day,"status":"SOURCE_BLOCKED","reason":reason})
            evaluations.extend({
                "symbol":row["symbol"],"tf":row["tf"],"entry_utc":row["entry_utc"],
                "source_day":row["day"],"status":"SOURCE_BLOCKED","reason":reason,
                "does_not_prove_fill":True} for row in rows)
    return {"status":"RETROSPECTIVE_L1_SOURCE_GATE_COMPLETED_NO_OOS",
            "original_run":SOURCE_RUN,
            "selections":[{k:v for k,v in s.items() if k!="selected"} for s in selections],
            "expected_entries":4,"observed_entries":len(evaluations),
            "archive_receipts":receipts,"entry_quote_checks":evaluations,
            "no_broker_fills":True,"no_native_stops_verified":True,
            "cross_venue_transfer_validated":False,"independent_OOS":False,
            "trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    report=run(a.source_dir)
    (a.output_dir/"BINANCE_CONVEX_L1_EXACT_ENTRY_GATES.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    for r in report.get("entry_quote_checks",[]):
        print("L1_CAUSAL_ENTRY",json.dumps(r,sort_keys=True))
    print("L1_SOURCE_FINAL",json.dumps({k:v for k,v in report.items() if k not in ("entry_quote_checks","archive_receipts")},sort_keys=True))
if __name__=="__main__":
    main()
