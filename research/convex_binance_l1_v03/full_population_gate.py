"""V03B — all pre-registered eligible original Binance Futures entries: L1 coverage only.

Research: no PnL replay, no private data, no order submission, no venue transfer.
"""
from __future__ import annotations
import argparse,csv,json,statistics
from collections import defaultdict,Counter
from decimal import Decimal
from pathlib import Path
from research.convex_binance_l1_v03.bookticker_gate import (
    SYMBOL_TF,LOWER_MS,UPPER_MS,dec,date_of,select_original_earliest_two,
    fetch_archive,last_causal_quotes,verdict_for_entry,
)
import datetime as dt

EXPECTED={"SOLUSDT":33,"BNBUSDT":6}
FRESH=("BOOK_QUOTE_CAUSAL_CANDIDATE","TOP_OF_BOOK_SIZE_INSUFFICIENT")

def source_entries(root,symbol):
    start=select_original_earliest_two(root,symbol)
    files=[f for f in root.rglob("RESULT.json") if json.loads(f.read_text()).get("symbol")==symbol]
    if len(files)!=1:raise ValueError("CANONICAL_SOURCE_NOT_UNIQUE")
    f=files[0]
    tf=SYMBOL_TF[symbol]
    path=f.parent/(tf+"_BASE_TRADES.csv")
    with path.open(encoding="utf-8",newline="") as file:
        raw=list(csv.DictReader(file))
    entries=[]
    for row in raw:
        t=int(row["open_t"])
        if LOWER_MS<=t<UPPER_MS:
            entries.append({
                "symbol":symbol,"tf":tf,"entry_ms":t,
                "entry_utc":dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "day":date_of(t),
                "modeled_entry":str(dec(row["entry_price"],"MODELED_ENTRY")),
                "modeled_qty":str(dec(row["qty"],"MODELED_QTY"))
            })
    if len(entries)!=EXPECTED[symbol] or start["eligible_count"]!=EXPECTED[symbol]:
        raise ValueError("FROZEN_ELIGIBLE_COUNT_CHANGED")
    if entries[:2]!=start["selected"]:
        raise ValueError("ORIGINAL_V03_FIRST_TWO_SAMPLE_DISAGREEMENT")
    if any(entries[i]["entry_ms"]>=entries[i+1]["entry_ms"] for i in range(len(entries)-1)):
        raise ValueError("DUPLICATED_OR_OUT_OF_ORDER_ENTRIES")
    return entries,start

def audit(root,symbol):
    if symbol not in EXPECTED:raise ValueError("UNREGISTERED_SYMBOL")
    entries, prior=source_entries(root,symbol)
    by_day=defaultdict(list)
    for e in entries:
        by_day[e["day"]].append(e)
    files=[]; results=[]
    for day,rows in sorted(by_day.items()):
        try:
            data,sha=fetch_archive(symbol,day)
            quotes,count=last_causal_quotes(data,day,[e["entry_ms"] for e in rows])
            files.append({"symbol":symbol,"day":day,"status":"SHA256_VALIDATED",
                          "zip_sha256":sha,"events_read":count})
            results.extend(verdict_for_entry(e,quotes[e["entry_ms"]]) for e in rows)
        except Exception as exc:
            reason=type(exc).__name__+":"+str(exc)[:150]
            files.append({"symbol":symbol,"day":day,"status":"SOURCE_BLOCKED","reason":reason})
            for e in rows:
                results.append({"symbol":symbol,"tf":e["tf"],"entry_utc":e["entry_utc"],
                                "source_day":e["day"],"status":"SOURCE_BLOCKED",
                                "reason":reason,"does_not_prove_fill":True})
        print("SOURCE_DAY_COMPLETE",json.dumps({"symbol":symbol,"day":day,
              "file_status":files[-1]["status"],
              "entries_on_day":len(rows)}),flush=True)
    if len(results)!=EXPECTED[symbol]:raise ValueError("OUTPUT_DENOMINATOR_LOSS")
    by_status=Counter(x["status"] for x in results)
    good=[x for x in results if x["status"] in FRESH]
    capacity=[x for x in good if x["status"]=="BOOK_QUOTE_CAUSAL_CANDIDATE"]
    values=[float(Decimal(x["ask_vs_modeled_entry_bps"])) for x in good]
    coverage=len(good)/len(results)
    size_rate=len(capacity)/len(good) if good else 0.0
    gate=(coverage>=0.95 and size_rate>=0.90)
    return {
        "status":"SOURCE_FEASIBLE_FROZEN_GATES" if gate else "SOURCE_ROUTE_INSUFFICIENT_FOR_FULL_HISTORICAL_EXECUTION_GATE",
        "symbol":symbol,"tf":SYMBOL_TF[symbol],"expected":EXPECTED[symbol],
        "count":len(results),"distinct_dates":len(by_day),
        "counts":dict(sorted(by_status.items())),
        "fresh_quote_coverage_fraction":coverage,
        "fresh_top_ask_size_fraction":size_rate,
        "threshold_fresh_quote_coverage":0.95,
        "threshold_fresh_top_ask_size":0.90,
        "fresh_ask_minus_model_entry_bps":{
            "n":len(values),
            "median":statistics.median(values) if values else None,
            "minimum":min(values) if values else None,
            "maximum":max(values) if values else None,
        },
        "source_files":files,"entry_checks":sorted(results,key=lambda x:x["entry_utc"]),
        "original_run":38432883246,
        "original_source_sha256":prior["source_sha256"],
        "original_ledger_sha256":prior["original_ledger_sha256"],
        "is_not_independent_OOS":True,
        "broker_fill_verified":False,
        "broker_stop_verified":False,
        "venue_portability_verified":False,
        "trading_authority":"NONE",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--symbol",choices=tuple(EXPECTED),required=True)
    a=p.parse_args()
    report=audit(a.source_dir,a.symbol)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"ALL_ORIGINAL_ELIGIBLE_L1_RECEIPTS.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("V03B_FINAL_COUNTS",json.dumps({k:v for k,v in report.items()
          if k in ("status","symbol","count","distinct_dates","counts",
                   "fresh_quote_coverage_fraction","fresh_top_ask_size_fraction",
                   "fresh_ask_minus_model_entry_bps","trading_authority")},
                   sort_keys=True),flush=True)
if __name__=="__main__":main()
