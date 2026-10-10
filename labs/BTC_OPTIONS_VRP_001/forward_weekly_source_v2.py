#!/usr/bin/env python3
"""
BTC-OPTIONS-VRP-001 V2 prospective weekly SOURCE collector.

SOURCE ONLY:
- unauthenticated public Deribit API;
- captures raw point-in-time BBO evidence for one non-overlapping weekly cohort;
- closes the prior cohort exactly seven days later;
- NEVER computes returns, PnL, expectancy, hit rate or promotion metrics;
- NEVER sends orders or uses account/private endpoints.

Scientific rules are frozen in research/btc_options_vrp_v2/.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import pathlib
import time
import urllib.parse
import urllib.request

BASE="https://www.deribit.com/api/v2"
OUT=pathlib.Path("data/vrp_forward_v2/source_events.jsonl")
RECEIPTS=pathlib.Path("receipts/vrp_forward_v2")
DTE_MIN=14.0
DTE_MAX=60.0
TARGET_DTE=30.0
AMOUNT=0.1
FRESH_MS=30_000

def now_utc():
    return dt.datetime.now(dt.timezone.utc)

def ms(x):
    return int(x.timestamp()*1000)

def iso(x):
    return x.isoformat()

def api_get_timed(method, params):
    start=now_utc()
    url=f"{BASE}/{method}?{urllib.parse.urlencode(params)}"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-VRP-V2-SourceOnly/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        payload=json.loads(r.read().decode("utf-8"))
    end=now_utc()
    if "error" in payload:
        raise RuntimeError(f"{method}: {payload['error']}")
    if "result" not in payload:
        raise RuntimeError(f"{method}: missing result")
    return payload["result"], ms(start), ms(end)

def best(book, side):
    rows=book.get(side) or []
    if not rows:
        return None,None
    row=rows[0]
    if not isinstance(row,list) or len(row)<2:
        return None,None
    return float(row[0]),float(row[1])

def compact_book(name, book, req_ms, recv_ms):
    bid,bid_amt=best(book,"bids")
    ask,ask_amt=best(book,"asks")
    src=book.get("timestamp")
    fresh=False
    clock_diff=None
    if src is not None:
        clock_diff=int(recv_ms)-int(src)
        fresh=abs(clock_diff)<=FRESH_MS
    return {
        "instrument_name":name,
        "request_start_ms":req_ms,
        "response_received_ms":recv_ms,
        "source_timestamp_ms":src,
        "source_clock_diff_at_receive_ms":clock_diff,
        "fresh_30s":fresh,
        "bid_price":bid,"bid_amount":bid_amt,
        "ask_price":ask,"ask_amount":ask_amt,
        "mark_price":book.get("mark_price"),
        "mark_iv":book.get("mark_iv"),
        "index_price":book.get("index_price"),
        "underlying_price":book.get("underlying_price"),
        "greeks":book.get("greeks"),
        "open_interest":book.get("open_interest"),
    }

def get_book(name):
    b,s,e=api_get_timed("public/get_order_book",{"instrument_name":name,"depth":1})
    return compact_book(name,b,s,e)

def read_events():
    if not OUT.exists():
        return []
    out=[]
    for line in OUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out

def append_event(obj):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n")

def valid_book(b, side, amount=None):
    if not b.get("fresh_30s"):
        return False
    if b.get(f"{side}_price") is None or b.get(f"{side}_amount") is None:
        return False
    if amount is not None and float(b[f"{side}_amount"]) < amount:
        return False
    return True

def select_pair(now):
    idx,_,_=api_get_timed("public/get_index_price",{"index_name":"btc_usd"})
    index=float(idx["index_price"])
    insts,_,_=api_get_timed("public/get_instruments",{"currency":"BTC","kind":"option","expired":"false"})
    pairs={}
    now_ms=ms(now)
    for x in insts:
        if x.get("kind")!="option" or not x.get("is_active",True):
            continue
        exp=x.get("expiration_timestamp"); strike=x.get("strike"); typ=x.get("option_type")
        if exp is None or strike is None or typ not in {"call","put"}:
            continue
        dte=(float(exp)-now_ms)/86_400_000.0
        if not (DTE_MIN<=dte<=DTE_MAX):
            continue
        key=(int(exp),float(strike))
        pairs.setdefault(key,{})[typ]=x
    cands=[]
    for (exp,strike),legs in pairs.items():
        if "call" not in legs or "put" not in legs:
            continue
        dte=(exp-now_ms)/86_400_000.0
        cands.append((abs(dte-TARGET_DTE),exp,abs(math.log(strike/index)),strike,dte,legs))
    if not cands:
        raise RuntimeError("NO_CALL_PUT_PAIR_IN_FROZEN_DTE_ENVELOPE")
    # expiry-nearest-to-30 dominates; then earlier expiry; then nearest ATM; then lower strike.
    cands.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
    _,exp,_,strike,dte,legs=cands[0]
    return {
        "index_price_btc_usd":index,
        "expiration_timestamp":exp,
        "strike":strike,
        "dte_days":dte,
        "call":legs["call"]["instrument_name"],
        "put":legs["put"]["instrument_name"],
    }

def receipt_path(day):
    return RECEIPTS/f"capture_{day}.json"

def main():
    now=now_utc()
    # Weekly source authority is exact UTC. Fail closed outside window.
    if now.weekday()!=3 or not (8 <= now.hour < 9):
        raise SystemExit(f"OUTSIDE_FROZEN_CAPTURE_WINDOW now={iso(now)} expected Thursday 08:00-08:59 UTC")

    day=now.date().isoformat()
    events=read_events()
    has_entry=any(e.get("event_type")=="ENTRY" and e.get("cohort_id")==day for e in events)
    has_exit=any(e.get("event_type")=="EXIT" and e.get("exit_date")==day for e in events)

    # Resolve prior due cohort source only.
    entries={e["cohort_id"]:e for e in events if e.get("event_type")=="ENTRY"}
    exited={e["cohort_id"] for e in events if e.get("event_type")=="EXIT"}
    missed={e["cohort_id"] for e in events if e.get("event_type")=="EXIT_SOURCE_MISSED"}
    for cid,e in sorted(entries.items()):
        if cid in exited or cid in missed:
            continue
        due=dt.date.fromisoformat(e["target_exit_date"])
        if due < now.date():
            append_event({
                "schema_version":"OVRP_FWD_SOURCE_V2",
                "event_type":"EXIT_SOURCE_MISSED",
                "cohort_id":cid,
                "target_exit_date":due.isoformat(),
                "recorded_at_utc":iso(now),
                "reason":"capture_run_not_available_on_frozen_exit_date",
                "returns_computed":False,"pnl_computed":False
            })
        elif due == now.date() and not has_exit:
            call=get_book(e["call_instrument"])
            put=get_book(e["put_instrument"])
            perp=get_book("BTC-PERPETUAL")
            ok=valid_book(call,"ask",AMOUNT) and valid_book(put,"ask",AMOUNT) and valid_book(perp,"bid") and valid_book(perp,"ask")
            append_event({
                "schema_version":"OVRP_FWD_SOURCE_V2",
                "event_type":"EXIT" if ok else "EXIT_SOURCE_INCOMPLETE",
                "cohort_id":cid,
                "exit_date":day,
                "captured_at_utc":iso(now),
                "call":call,"put":put,"btc_perpetual":perp,
                "source_valid":ok,
                "returns_computed":False,"pnl_computed":False
            })

    # Open this week's cohort source only.
    if not has_entry:
        sel=select_pair(now)
        call=get_book(sel["call"])
        time.sleep(0.15)
        put=get_book(sel["put"])
        time.sleep(0.15)
        perp=get_book("BTC-PERPETUAL")
        ok=valid_book(call,"bid",AMOUNT) and valid_book(put,"bid",AMOUNT) and valid_book(perp,"bid") and valid_book(perp,"ask")
        event_type="ENTRY" if ok else "ENTRY_SOURCE_INCOMPLETE"
        obj={
            "schema_version":"OVRP_FWD_SOURCE_V2",
            "event_type":event_type,
            "cohort_id":day,
            "anchor_date":day,
            "target_exit_date":(now.date()+dt.timedelta(days=7)).isoformat(),
            "captured_at_utc":iso(now),
            "selection_rule":"expiry nearest 30 DTE within 14-60; then nearest ATM same-strike call+put",
            "index_price_btc_usd":sel["index_price_btc_usd"],
            "expiration_timestamp":sel["expiration_timestamp"],
            "dte_days":sel["dte_days"],
            "strike":sel["strike"],
            "call_instrument":sel["call"],
            "put_instrument":sel["put"],
            "call":call,"put":put,"btc_perpetual":perp,
            "source_valid":ok,
            "returns_computed":False,"pnl_computed":False
        }
        append_event(obj)

    final=read_events()
    complete=sum(1 for e in final if e.get("event_type")=="EXIT" and e.get("source_valid"))
    open_count=sum(1 for e in final if e.get("event_type")=="ENTRY" and e["cohort_id"] not in {x.get("cohort_id") for x in final if x.get("event_type") in {"EXIT","EXIT_SOURCE_MISSED","EXIT_SOURCE_INCOMPLETE"}})
    summary={
        "schema_version":"OVRP_FWD_SOURCE_V2_CAPTURE_RECEIPT",
        "run_utc":iso(now),"date":day,
        "valid_complete_cohorts":complete,
        "open_cohorts":open_count,
        "raw_event_records":len(final),
        "returns_computed":False,"pnl_computed":False,
        "orders":False,"authenticated":False
    }
    RECEIPTS.mkdir(parents=True,exist_ok=True)
    receipt_path(day).write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__":
    main()
