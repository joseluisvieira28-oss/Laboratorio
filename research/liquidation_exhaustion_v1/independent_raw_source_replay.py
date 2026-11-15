#!/usr/bin/env python3
"""Independent stdlib-only replay of public Bybit source artifact (NO future returns)."""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

SYMBOLS = ("BTCUSDT", "ETHUSDT")
TOPICS = {f"{k}.{s}" for s in SYMBOLS for k in
          ("publicTrade", "orderbook.50", "allLiquidation")}

def replay(zip_path):
    archive = Path(zip_path).read_bytes()
    with ZipFile(zip_path) as z:
        raw = z.read("raw_public_frames.ndjson")
        receipt = json.loads(z.read("source_receipt.json"))
    source_hash = hashlib.sha256(raw).hexdigest()
    if source_hash != receipt["raw_sha256"]:
        raise ValueError("RAW_HASH_MISMATCH")
    counts = Counter()
    last_recv = None
    book = {}
    last_u = {}
    last_seq = {}
    last_bbo = {}
    last_trade_recv = {}
    deltas = Counter()
    liqs = []
    seen_ids = {s:set() for s in SYMBOLS}
    nframes = 0
    for n,line in enumerate(raw.splitlines(),1):
        nframes += 1
        envelope = json.loads(line)
        received = envelope["received_utc_ms"]
        if last_recv is not None and received < last_recv:
            raise ValueError("RECEIVE_CLOCK_REGRESSION")
        last_recv = received
        msg = json.loads(envelope["raw"])
        topic = msg.get("topic")
        if topic is None:
            continue
        if topic not in TOPICS:
            raise ValueError("UNKNOWN_TOPIC")
        counts[topic] += 1
        sym = topic.rsplit(".",1)[1]
        if topic.startswith("orderbook.50."):
            data = msg["data"]
            u = data["u"]
            seq = data["seq"]
            if msg["type"] == "snapshot":
                book[sym] = {"b":{}, "a":{}}
            else:
                if sym not in book:
                    raise ValueError("DELTA_BEFORE_SNAPSHOT")
                if u != last_u[sym]+1:
                    raise ValueError("MISSING_BOOK_UPDATE")
                if seq < last_seq[sym]:
                    raise ValueError("BOOK_SEQUENCE_REGRESSION")
                deltas[sym] += 1
            last_u[sym], last_seq[sym] = u, seq
            if abs(received-msg["ts"]) > 2000:
                raise ValueError("STALE_BOOK_TIMESTAMP")
            for side in ("b","a"):
                for price,qty in data[side]:
                    p, q = Decimal(price), Decimal(qty)
                    if q == 0:book[sym][side].pop(p,None)
                    else:book[sym][side][p] = q
            if not book[sym]["b"] or not book[sym]["a"]:
                raise ValueError("EMPTY_BEST_QUOTE")
            bid,ask = max(book[sym]["b"]),min(book[sym]["a"])
            if bid>=ask:raise ValueError("CROSSED_BOOK")
            last_bbo[sym] = (received, bid, ask)
        elif topic.startswith("publicTrade."):
            for x in msg["data"]:
                if x["s"]!=sym or x["i"] in seen_ids[sym]:
                    raise ValueError("INVALID_OR_DUPLICATE_TRADE")
                seen_ids[sym].add(x["i"])
                if abs(received-x["T"])>2000:
                    raise ValueError("STALE_TRADE")
                last_trade_recv[sym]=received
        else:
            for x in msg["data"]:
                if x["s"] != sym or x["S"] not in ("Buy","Sell"):
                    raise ValueError("BAD_LIQUIDATION")
                if Decimal(x["p"])<=0 or Decimal(x["v"])<=0:
                    raise ValueError("INVALID_LIQUIDATION_VALUES")
                if abs(received-x["T"])>2000:
                    raise ValueError("STALE_LIQUIDATION")
                if sym not in last_bbo or sym not in last_trade_recv:
                    raise ValueError("NO_CAUSAL_PRECEDING_BOOK_OR_TRADE")
                prev, bid, ask = last_bbo[sym]
                if prev>received:
                    raise ValueError("FUTURE_BOOK")
                liqs.append({
                    "symbol":sym,"receive_lag_ms":received-x["T"],
                    "prior_book_age_ms":received-prev,
                    "prior_trade_age_ms":received-last_trade_recv[sym]})
    if any(counts[t]!=receipt["counts"][t] for t in TOPICS):
        raise ValueError("RECEIPT_COUNT_MISMATCH")
    if len(liqs)!=receipt["liquidation_children"]:
        raise ValueError("LIQUIDATION_CHILD_COUNT_MISMATCH")
    if any(deltas[s]<1 for s in SYMBOLS):
        raise ValueError("BOOK_DELTA_MISSING")
    return {
      "verdict":"SOURCE_WINDOW_TECHNICAL_PASS_CENSUS_UNPROVEN",
      "artifact_sha256":hashlib.sha256(archive).hexdigest(),
      "raw_sha256":source_hash,
      "raw_frames":nframes,
      "liquidation_children":len(liqs),
      "liquidation_children_by_symbol":dict(Counter(x["symbol"] for x in liqs)),
      "book_contiguous_updates":dict(deltas),
      "observed_liquidation_max_receive_lag_ms":max(x["receive_lag_ms"] for x in liqs) if liqs else None,
      "max_prior_book_age_ms":max(x["prior_book_age_ms"] for x in liqs) if liqs else None,
      "max_prior_trade_age_ms":max(x["prior_trade_age_ms"] for x in liqs) if liqs else None,
      "full_exchange_liquidation_census_certified":False,
      "execution_venue_parity_certified":False,
      "outcomes_evaluated":False,
      "economic_edge_certified":False
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive_zip")
    args = ap.parse_args()
    print(json.dumps(replay(args.archive_zip),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
